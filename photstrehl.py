from pyraf import iraf
import math
import os
import re
import uuid
import shutil
import time
import tempfile
import pyfits
import numpy as np
import matplotlib
matplotlib.use('agg') # cannot import pyplot within pyraf without this
from matplotlib import pyplot as plt
# why won't logging work in PyRAF :(
from aotools.util import debug, info, warn, error, write_table, parse_ranges
from aotools.strehl import (Frame, generate_pupil, generate_circular_mask, 
    generate_psf_full, compute_psf_scale, generate_scaled_psf, first_min_from_core, avgrow,
    avgrow_median_subtract, phot_curve_of_growth, profile_from_growthcurve,
    daofind_brightest
)
from aotools.cubetoframes import split_frames

def photstrehl(cubefile, rangespec, primary, secondary, dimension, f_number,
        pixel_scale, lambda_mean, growth_step, fwhmpsf, threshold, quiet):
    start_time = time.time()
    info("Started at:", start_time)
    if not os.path.exists(cubefile):
        raise RuntimeError("No file named {0}".format(cubefile))
    cubefile_base = os.path.splitext(os.path.basename(cubefile))[0]
    # I: compute ideal psf
    
    scale_to_physical, plate_scale_px, min_radius_real = compute_psf_scale(
        dimension,
        primary,
        secondary,
        f_number,
        lambda_mean,
        pixel_scale
    )
    
    info("The radius of the first minimum in physical pixels is", min_radius_real, "px")
    
    scaled_psf, scaled_psf_ctr, max_aperture_radius = generate_scaled_psf(
        dimension,
        primary,
        secondary,
        scale_to_physical
    )
    
    # wrap psf in a frame
    psf = Frame(scaled_psf, scaled_psf_ctr)
    
    max_extent_px = 2.5 / plate_scale_px # After 2.5" we're almost certainly measuring noise
    debug("after 2.5'' or", max_extent_px, "px we'll be almost certainly measuring noise")
    growth_max = max_extent_px + growth_step * 3 # do 3 steps beyond the 2.5" mark
    assert growth_max < max_aperture_radius, "Curve of Growth won't fit on PSF frame with this max extent"
    
    # precompute CoG and profile to be rescaled later
    
    # phot CoG needs a FITS file, so write one:
    psftmpfilename = os.path.abspath('./{0}.fits'.format(uuid.uuid1()))
    hdu = pyfits.PrimaryHDU(psf.data)
    hdu.writeto(psftmpfilename)
    debug("psf FITS file temporarily stored in", psftmpfilename)
    
    phot_curve_of_growth(psf, psftmpfilename, growth_max, step=growth_step, quiet=quiet)
    profile_from_growthcurve(psf)
    
    # II: analyze images
    
    # functions to rescale our PSF Frame computed values
    # to physical counts
    
    def max_flux(frame):
        """Frame max integrated flux (for a radius less than 2.5'')"""
        return np.max(frame.fluxes[frame.radii <= max_extent_px])
    
    def scale_psf_fluxes(frame, psf):
        """
        Returns a profile and curve of growth values for the ideal PSF
        scaled such that the total integrated flux is equivalent to the
        maximum flux in the frame passed as the first argument.
        """
        scale_factor = (max_flux(frame) / max_flux(psf))
        return psf.profile * scale_factor, psf.fluxes * scale_factor

    tmp_target_dir = tempfile.mkdtemp()
    ranges = parse_ranges(rangespec)
    debug("splitting ranges", ranges)
    fits_frames = split_frames(cubefile, ranges, tmp_target_dir)
    debug("working in", tmp_target_dir, "with frames", fits_frames)

    # set up array to hold each frame's analysis data
    radii_count = psf.radii.shape[0]
    frame_count = len(fits_frames)
    shape = (frame_count, 5, radii_count)
    analysis_frames = np.zeros(shape)
    # [cog x count, prof x count, ideal x count, idealprof x count, strehl x count] x frames
    
    strehl_rows = []
    
    for fits_frame in fits_frames:
        bright = daofind_brightest(fits_frame, fwhmpsf, threshold)
        center_col, center_row = bright['XCENTER'], bright['YCENTER']
        # this is slightly dumb... parse the frame # out of the filename
        frame_num = int(re.findall(r'\d+', os.path.basename(fits_frame))[0])
        debug("frame #", frame_num, "has brightest at", center_col, center_row)
        frame = Frame(pyfits.getdata(fits_frame), (float(center_col), float(center_row)))
        debug("loaded frame from", fits_frame)
    
        # subtract median row to handle light/charge leakage biasing measurements
        exclude_from, exclude_to = frame.ybounds(r=int(max_extent_px)) # exclude region of max_extent_px around center of frame
        avgrow_median_subtract(frame, exclude_from, exclude_to)
        debug("median subtracted frame")
        phot_curve_of_growth(frame, fits_frame, growth_max, step=growth_step, quiet=quiet)
        debug("curve of growth generated")
        profile_from_growthcurve(frame)
        debug("profile generated")
    
        # scale psf.fluxes and psf.profile to a max value determined from frame
        ideal_profile, ideal_fluxes = scale_psf_fluxes(frame, psf)
        strehls_for_all_radii = frame.fluxes / ideal_fluxes
        strehl_rows.append((frame_num, strehls_for_all_radii))

    outfile = "{0}_{1}_strehlseries.txt".format(cubefile_base, rangespec)
    debug("writing strehl series to", outfile)
    with open(outfile, 'w') as f:
        f.write("# columns 2 and up are the pixel radii at which we computed the Strehl ratio")
        f.write("# frameidx\t")
        f.write('\t'.join(map(str, psf.radii)))
        f.write('\n')
        for idx, ratios in strehl_rows:
            f.write(str(idx))
            f.write('\t')
            f.write('\t'.join(map(str, ratios)))
            f.write('\n')

    debug("removing exploded cube from", tmp_target_dir)
    shutil.rmtree(tmp_target_dir)

    info("Completed at:", time.time())
    info("Total time:", time.time() - start_time)

parfile = iraf.osfn("aotools$photstrehl.par")
t = iraf.IrafTaskFactory(taskname="photstrehl", value=parfile, function=photstrehl)
