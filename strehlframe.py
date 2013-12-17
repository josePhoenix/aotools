from pyraf import iraf
import math
import os
import time
import pyfits
import scipy.ndimage
import numpy as np
import matplotlib
matplotlib.use('agg') # cannot import pyplot within pyraf without this
from matplotlib import pyplot as plt
# why won't logging work in PyRAF :(
from aotools.util import debug, info, warn, error, write_table
from aotools.strehl import (Frame, generate_pupil, generate_circular_mask, 
    generate_psf_full, first_min_from_core, avgrow, avgrow_median_subtract,
    curve_of_growth, profile_from_growthcurve, daofind_brightest)

def strehlframe(image, primary, secondary, dimension, f_number, pixel_scale,
        lambda_mean, growth_step, find_source, xcenter, ycenter, fwhmpsf,
        threshold, quiet):
    start_time = time.time()
    info("Started at:", start_time)
    
    # Were we given coordinates, or do we need to find the source?
    if find_source:
        bright = daofind_brightest(image, fwhmpsf, threshold)
        center_col, center_row = bright['XCENTER'], bright['YCENTER']
    else:
        center_col, center_row = xcenter, ycenter

    # set the scaling for the PSF from the first min of the unobscured PSF
    unscaled_psf = generate_psf_full(dimension, primary, 0)
    first_min_px = first_min_from_core(unscaled_psf)
    first_min_radius = first_min_px - dimension/2
    plate_scale_mm = 206265.0 / (1000 * f_number) # TODO: 1000 mm primary hardcoded
    plate_scale_px = plate_scale_mm * pixel_scale # 13 micron pixels on Andor
    theta = math.asin(1.22 * (lambda_mean / 1.0e9)) # TODO: 1e9 nm for our 1m primary
    theta_arcseconds = theta * 206265.0
    min_radius_real = theta_arcseconds * (1.0 / plate_scale_px) # pixel radius to first min
    scale_to_physical = min_radius_real / first_min_radius
    
    # regenerate the PSF with obscuration in the aperture
    unscaled_psf_obscured = generate_psf_full(dimension, primary, secondary)
    scaled_psf = scipy.ndimage.zoom(unscaled_psf_obscured, scale_to_physical)
    scaled_psf_ctr = scipy.ndimage.center_of_mass(scaled_psf)
    max_aperture_radius = scaled_psf.shape[0] / 2
    debug("Scaled PSF to", scaled_psf.shape)
    debug("max aperture radius = ", max_aperture_radius)
    
    # wrap psf in a frame
    psf = Frame(scaled_psf, scaled_psf_ctr)
    # precompute CoG and profile to be rescaled later
    curve_of_growth(psf, max_aperture_radius, step=growth_step, quiet=quiet)
    profile_from_growthcurve(psf)
    
    # values and functions to rescale our PSF Frame computed values
    # to physical counts
    max_extent_px = 2.5 / plate_scale_px # After 2.5" we're almost certainly measuring noise
    debug("after 2.5'' or", max_extent_px, "px we're almost certainly measuring noise")
    
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
    curve_of_growth(frame, max_aperture_radius, step=growth_step, quiet=quiet)
    debug("curve of growth generated")
    profile_from_growthcurve(frame)
    debug("profile generated")
    
    # scale psf.fluxes and psf.profile to a max value determined from frame
    ideal_profile, ideal_fluxes = scale_psf_fluxes(frame, psf)
    
    write_table("{0}_strehl.dat".format(image_base), (
        ("Pixel Radius", frame.radii),
        ("Image Enclosed Energy (counts)", frame.fluxes),
        ("Ideal Enclosed Energy (counts)", ideal_fluxes),
        ("Strehl Ratio (for peak in this radius)", frame.fluxes / ideal_fluxes),
        ("Image Radial Profile (counts at radius)", frame.profile),
        ("Ideal Radial Profile (counts at radius)", ideal_profile)
    ))
    
    # Plot Curve of Growth with twinned axis in arcseconds
    # TODO: make a helper function? but this wants a bunch of random values
    # that are in scope here... maybe a nested function
    fig, host = plt.subplots()

    plt.plot(frame.radii, frame.fluxes, 'r', label="Science Image")
    plt.plot(psf.radii, ideal_fluxes, 'g', label="Ideal PSF")
    plt.axvspan(0, min_radius_real, facecolor='g', alpha=0.25)

    plt.ylabel("Enclosed Flux at Radius")
    plt.xlabel("Radius (pixels from center)")

    plt.xlim(1, max_extent_px)
    plt.ylim(0, np.max(ideal_fluxes))
    xfrom, xto = fig.axes[0].get_xlim()
    par1 = host.twiny()
    par1.axes.set_xlabel("Radius (arcseconds from center)")
    par1.set_xlim((xfrom * plate_scale_px, xto * plate_scale_px))
    par1.grid()
    host.legend(loc=4)
    
    plt.savefig('{0}_growth.pdf'.format(image_base))
    debug("saved plot to", '{0}_growth.pdf'.format(image_base))

    # Plot profile with twinned axis in arcseconds
    fig, host = plt.subplots()

    plt.plot(frame.radii, frame.profile, c='r', marker=".", label="Science Image")
    plt.plot(psf.radii, ideal_profile, c='g', marker='.', label="Ideal PSF")
    plt.axvspan(0, min_radius_real, facecolor='g', alpha=0.25)

    plt.ylabel("Flux at Radius")
    plt.xlabel("Radius (pixels from center)")

    plt.xlim(1, 10)
    plt.ylim(0, np.max(ideal_profile))
    xfrom, xto = fig.axes[0].get_xlim()
    par1 = host.twiny()
    par1.axes.set_xlabel("Radius (arcseconds from center)")
    par1.set_xlim((xfrom * plate_scale_px, xto * plate_scale_px))
    par1.grid()
    host.legend(loc=4)
    
    plt.savefig('{0}_profile.pdf'.format(image_base))
    debug("saved plot to", '{0}_profile.pdf'.format(image_base))
    info("Completed at:", time.time())
    info("Total time:", time.time() - start_time)

parfile = iraf.osfn("aotools$strehlframe.par")
t = iraf.IrafTaskFactory(taskname="strehlframe", value=parfile, function=strehlframe)
