from pyraf import iraf
import math
import os
import time
import pyfits
import uuid
import numpy as np
import matplotlib
matplotlib.use('agg') # cannot import pyplot within pyraf without this
from matplotlib import pyplot as plt
# why won't logging work in PyRAF :(
from aotools.util import debug, info, warn, error, write_table
from aotools.strehl import (Frame, generate_pupil, generate_circular_mask, 
    generate_psf_full, compute_psf_scale, generate_scaled_psf, 
    first_min_from_core, avgrow, avgrow_median_subtract, phot_curve_of_growth,
    profile_from_growthcurve, plot_with_arcseconds, daofind_brightest
)

def photstrehlframe(image, primary, secondary, dimension, f_number, pixel_scale,
        lambda_mean, growth_step, normalize_at, find_source, xcenter, ycenter, fwhmpsf,
        threshold, quiet):
    start_time = time.time()
    info("Started at:", start_time)
    if not os.path.exists(image):
        raise RuntimeError("No file named {0}".format(image))
    # Were we given coordinates, or do we need to find the source?
    if find_source:
        bright = daofind_brightest(image, fwhmpsf, threshold)
        center_col, center_row = bright['XCENTER'], bright['YCENTER']
    else:
        center_col, center_row = xcenter, ycenter
    
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
    
    if normalize_at != 0:
        max_extent_px = normalize_at
        debug("Rescaling to max integrated flux @ r=", max_extent_px, "pixels")
    else:
        max_extent_px = 2.5 / plate_scale_px # After 2.5" we're almost certainly measuring noise
        debug("after 2.5'' or", max_extent_px, "px we'll be almost certainly measuring noise")
    growth_max = max_extent_px + growth_step * 3 # do 3 steps beyond the 2.5" mark
    assert growth_max < max_aperture_radius, "Curve of Growth won't fit on PSF frame with this max extent"
    
    # phot CoG needs a FITS file, so write one:
    psftmpfilename = os.path.abspath('./{0}.fits'.format(uuid.uuid1()))
    hdu = pyfits.PrimaryHDU(psf.data)
    hdu.writeto(psftmpfilename)
    debug("psf FITS file temporarily stored in", psftmpfilename)
    
    # precompute CoG and profile to be rescaled later
    phot_curve_of_growth(psf, psftmpfilename, growth_max, step=growth_step, quiet=quiet, fitsky=False)
    profile_from_growthcurve(psf)
    
    # values and functions to rescale our PSF Frame computed values
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

    image_base = os.path.splitext(os.path.basename(image))[0]
    frame = Frame(pyfits.getdata(image), (float(center_col), float(center_row)))
    debug("loaded frame from", image)
    # subtract median row to handle light/charge leakage biasing measurements
    exclude_from, exclude_to = frame.ybounds(r=int(max_extent_px)) # exclude region of max_extent_px around center of frame
    avgrow_median_subtract(frame, exclude_from, exclude_to)
    debug("median subtracted frame")
    phot_curve_of_growth(frame, image, growth_max, step=growth_step, quiet=quiet, fitsky=True)
    debug("curve of growth generated")
    profile_from_growthcurve(frame)
    debug("profile generated")
    
    # scale psf.fluxes and psf.profile to a max value determined from frame
    ideal_profile, ideal_fluxes = scale_psf_fluxes(frame, psf)
    
    write_table("{0}_strehl.dat".format(image_base), (
        ("Pixel Radius", frame.radii),
        ("Enclosed Pixels", frame.npix),
        ("Image Enclosed Energy (counts)", frame.fluxes),
        ("Ideal Enclosed Energy (counts)", ideal_fluxes),
        ("Strehl Ratio (for peak in this radius)", frame.fluxes / ideal_fluxes),
        ("Image Radial Profile (counts at radius)", frame.profile),
        ("Ideal Radial Profile (counts at radius)", ideal_profile)
    ))
    
    # Plot Curve of Growth with twinned axis in arcseconds
    
    plot_with_arcseconds(
        image_base + "_growth.pdf",
        psf.radii,
        frame.fluxes,
        ideal_fluxes,
        min_radius_real,
        max_extent_px,
        plate_scale_px,
        ylabel="Enclosed Flux at Radius"
    )
    
    # Plot profile with twinned axis in arcseconds
    
    plot_with_arcseconds(
        image_base + "_profile.pdf",
        psf.radii,
        frame.profile,
        ideal_profile,
        min_radius_real,
        10, # xlim max
        plate_scale_px,
        ylabel="Flux at Radius",
        marker="."
    )
    
    info("Completed at:", time.time())
    info("Total time:", time.time() - start_time)

parfile = iraf.osfn("aotools$photstrehlframe.par")
t = iraf.IrafTaskFactory(taskname="photstrehlframe", value=parfile, function=photstrehlframe)
