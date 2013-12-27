from pyraf import iraf
import math
import pyfits
import os
import numpy as np
import tempfile
import shutil
import scipy.ndimage
import matplotlib
matplotlib.use('agg') # cannot import pyplot within pyraf without this
from matplotlib import pyplot as plt
# why won't logging work in PyRAF :(
from aotools.util import debug, info, warn, error, parse_coo_file

def generate_pupil(dim, aperture_radius, obscuration_radius=0):
    """
    Generate a circular aperture with optional central obscuration (dimensions are in arbitrary units)
    
    dim - pupil plane dimensions
    aperture_radius - outer radius
    obscuration_radius - inner radius (central obscuration to add, default: 0)
    """
    pupil = np.zeros((dim, dim))
    center = int(round(dim / 2)), int(round(dim / 2))
    pupil[generate_circular_mask(dim, center, aperture_radius, obscuration_radius)] = 1
    return pupil

# def generate_circular_mask(dim, center, outer_radius, inner_radius=0):
#     """
#     Generate a circular or annular boolean mask with optional central
#     obscuration. All dimensions in pixels.
#     
#     dim - image dimensions
#     center or (cx, cy) - center coordinates as tuple
#     outer_radius - outer radius
#     inner_radius - inner radius (default: 0)
#     """
#     mask = np.zeros((dim, dim), dtype='bool')
#     x = outer_radius
#     y = 0
#     radius_error = 1 - x
#     
#     # center coords
#     ccol, crow = center
#     
#     while x >= y:
#         mask[crow + y][ccol - x:ccol + x] = True
#         mask[crow - y][ccol - x:ccol + x] = True
#         mask[crow + x][ccol - y:ccol + y] = True
#         mask[crow - x][ccol - y:ccol + y] = True
#         
#         y += 1
#         if radius_error < 0:
#             radius_error += 2*y + 1
#         else:
#             x -= 1
#             radius_error += 2 * (y - x + 1)
#     
#     # if we don't need to zero out the obscured region, we're done
#     if inner_radius == 0:
#         return mask
#     
#     x = inner_radius
#     y = 0
#     radius_error = 1 - x
#     
#     while x >= y:
#         mask[crow + y][ccol - x:ccol + x] = False
#         mask[crow - y][ccol - x:ccol + x] = False
#         mask[crow + x][ccol - y:ccol + y] = False
#         mask[crow - x][ccol - y:ccol + y] = False
#         
#         y += 1
#         if radius_error < 0:
#             radius_error += 2*y + 1
#         else:
#             x -= 1
#             radius_error += 2 * (y - x + 1)
#     
#     return mask

# def generate_pupil(dim, aperture_radius, obscuration_radius=0):
#     """
#     Generate a circular aperture with optional central obscuration (dimensions are in arbitrary units)
#     
#     dim - pupil plane dimensions
#     aperture_radius - outer radius
#     obscuration_radius - inner radius (central obscuration to add, default: 0)
#     """
#     inner_squared = obscuration_radius**2
#     outer_squared = aperture_radius**2
#     pupil = np.array(
#         [
#          [1 if inner_squared <= (a-dim/2)**2 + (b-dim/2)**2 <= outer_squared else 0 for b in range(0,dim)]
#          for a in range(0,dim)
#         ],
#         dtype="f"
#     )
#     return pupil

# def generate_circular_mask(dim, center, outer_radius, inner_radius=0):
#     """
#     Generate a circular or annular boolean mask 
#     with optional central obscuration (dimensions are in arbitrary units)
#     
#     dim - image dimensions
#     center or (cx, cy) - center coordinates as tuple
#     outer_radius - outer radius
#     inner_radius - inner radius (default: 0)
#     """
#     cx, cy = center
#     inner_squared = inner_radius**2
#     outer_squared = outer_radius**2
#     mask = np.array(
#         [
#          [True if inner_squared <= (x-cx)**2 + (y-cy)**2 <= outer_squared else False for x in range(0,dim)]
#          for y in range(0,dim)
#         ],
#         dtype="bool"
#     )
#     return mask

def generate_circular_mask(dim, center, aperture_radius, obscuration_radius=0):
    """
    Generate a circular or annular boolean mask with optional central
    obscuration. All dimensions in pixels.
    
    dim - image dimensions
    center or (cx, cy) - center coordinates as tuple
    outer_radius - outer radius
    inner_radius - inner radius (default: 0)
    """
    inner_squared = obscuration_radius**2
    outer_squared = aperture_radius**2
    ccol, crow = center
    mask = np.zeros((dim,dim), dtype="bool")
    
    def round_away(i):
        """Round i away from zero"""
        import math
        return int(math.floor(i)) if i < 0.0 else int(math.ceil(i))
    
    # only touch elements in these ranges; ignore rest of array
    row_from, row_to = round_away(crow - aperture_radius), round_away(crow + aperture_radius)
    col_from, col_to = round_away(ccol - aperture_radius), round_away(ccol + aperture_radius)
    
    for a in range(row_from, row_to):
        aidx2 = (a-crow)**2
        for b in range(col_from, col_to):
            r_squared = aidx2 + (b-ccol)**2
            if r_squared > outer_squared:
                mask[a][b] = False
            else:
                mask[a][b] = True if r_squared >= inner_squared else False

    return mask

def generate_psf_full(dim, aperture_radius, obscuration_radius=0):
    """
    Generate PSF for an aperture
    with optional central obscuration.
    Returns a dim^2 array. (Dimensions are in arbitrary units.)
    
    dim - pupil image size in pixels
    aperture_radius - outer radius
    obscuration_radius - inner radius (central obscuration to add, default: 0)
    """
    pupilfft = np.fft.fft2(generate_pupil(dim, aperture_radius, obscuration_radius))
    absfft = np.abs(pupilfft)**2
    return np.fft.fftshift(absfft)

#pretty basic/naive way to find first minimum, assuming we sample finely enough that it's not a subpixel
def first_min_from_core(psf):
    dim = psf.shape[0]
    row = psf[dim/2]
    for i in range(dim/2, dim):
        if row[i + 1] > row[i]:
            #print "climbing again from {0} to {1}".format(i, i + 1)
            debug("turning point at radius {0}px (row[{1}] = {2} < row[{3}] = {4})".format(i - dim/2, i, row[i], i + 1, row[i + 1]))
            return i

def compute_psf_scale(dimension, primary, secondary, f_number, lambda_mean, pixel_scale):
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
    return scale_to_physical, plate_scale_px, min_radius_real

def generate_scaled_psf(dimension, primary, secondary, scale_to_physical):
    # regenerate the PSF with obscuration in the aperture
    unscaled_psf_obscured = generate_psf_full(dimension, primary, secondary)
    scaled_psf = scipy.ndimage.zoom(unscaled_psf_obscured, scale_to_physical)
    scaled_psf_ctr = scipy.ndimage.center_of_mass(scaled_psf)
    max_aperture_radius = scaled_psf.shape[0] / 2
    debug("Scaled PSF to", scaled_psf.shape)
    debug("max aperture radius = ", max_aperture_radius)
    return scaled_psf, scaled_psf_ctr, max_aperture_radius

class Frame(object):
    """
    Carries around data for a frame we're analyzing and saves us
    polluting the namespace with names like `bp_stack_open_medsub_profile2`.
    
    data - square NumPy array from PyFITS or similar
    center - (col, row) tuple from imexam or similar
    """
    def __init__(self, data, center):
        self.center = center
        self.data = data
        self._data = data.copy()
    
    @property
    def x(self): return self.center[0]
    @property
    def y(self): return self.center[1]
    @property
    def intx(self): return int(self.center[0])
    @property
    def inty(self): return int(self.center[1])

    def xbounds(self, r=40): return (self.intx - r, self.intx + r)

    def ybounds(self, r=40): return (self.inty - r, self.inty + r)
    
    def show_center(self):
        fig, axes = plt.subplots()
        img = axes.imshow(self.data, interpolation="nearest", origin="lower")
        fig.colorbar(img)
        axes.set_xlim(self.xbounds())
        axes.set_ylim(self.ybounds())
        axes.add_artist(matplotlib.patches.Circle(self.center, 20, fill=False, linewidth=2, color="white"))

def avgrow(frame, exclude_from, exclude_to):
    """
    calculate an average row from the image, excluding rows
    from `exclude_from` to `exclude_to`
    """
    try:
        ydim, xdim = frame.data.shape
    except ValueError:
        raise ValueError("Data array has >2 axes. Is this a data cube?")
    ydim = ydim - (exclude_to - exclude_from)
    imgcopy = np.zeros((ydim, xdim))
    imgcopy[:exclude_from] = frame.data[:exclude_from]
    imgcopy[exclude_from:] = frame.data[exclude_to:]
    return np.average(imgcopy, axis=0)

def avgrow_median_subtract(frame, exclude_from, exclude_to):
    """
    takes a frame and subtracts an average row from it, then subtracts the
    median of the image.
    
    exclude_from - beginning of excluded rows range
    exclude_to - end of excluded rows range
    """
    frame.data = frame._data.copy()
    avg = avgrow(frame, exclude_from, exclude_to)
    frame.data = frame.data - avg[np.newaxis,:]
    frame.data -= np.median(frame.data)
    return frame.data

def curve_of_growth(frame, max_aperture, step=1, quiet=True):
    """
    Calculate a curve of growth by integrating flux in circular apertures
    (centered on frame.center) of successively larger radii
    
    max_aperture - radius in pixels from center where we
                   stop growing our aperture
    step - number of pixels to grow radius by (default: 1)
    quiet - do not emit a line for each step (default: True)
    """
    radii, fluxes, npix = [], [], []
    
    # special-case central pixel
    # radii.append(1)
    # fluxes.append(frame.data[frame.center[1]][frame.center[0]])
    # npix.append(1)
    # 
    # debug("central pixel {0} has value {1}".format(frame.center, fluxes[0]))
    
    current_r = 1
    
    while current_r <= max_aperture:
        mask = generate_circular_mask(frame.data.shape[0], frame.center, current_r)
        if not np.any(mask):
            print "skipping r = {0} because it didn't enclose at least 1 pixel".format(current_r)
            current_r += 1
            continue
        flux = np.sum(frame.data[mask])
        if not quiet:
            print "r = {0} encloses {1} counts".format(current_r, flux)
        radii.append(current_r)
        fluxes.append(flux)
        npix.append(np.sum(mask))
        current_r += step
    
    frame.radii, frame.fluxes, frame.npix = np.array(radii), np.array(fluxes), np.array(npix)
    return frame.radii, frame.fluxes, frame.npix

def plot_with_arcseconds(outfile, radii, real_values, ideal_values, min_radius_real,
        max_extent_px, plate_scale_px, ylabel="Values at Radius", marker=None):

    # Plot with twinned axis in arcseconds
    fig, host = plt.subplots()

    plt.plot(radii, real_values, 'r', marker=marker, label="Science Image")
    plt.plot(radii, ideal_values, 'g', marker=marker, label="Ideal PSF")
    plt.axvspan(0, min_radius_real, facecolor='g', alpha=0.25)

    plt.ylabel(ylabel)
    plt.xlabel("Radius (pixels from center)")

    plt.xlim(1, max_extent_px)
    plt.ylim(0, np.max(ideal_values))
    xfrom, xto = fig.axes[0].get_xlim()
    par1 = host.twiny()
    par1.axes.set_xlabel("Radius (arcseconds from center)")
    par1.set_xlim((xfrom * plate_scale_px, xto * plate_scale_px))
    par1.grid()
    host.legend(loc=4)
    
    plt.savefig(outfile)
    debug("saved plot to", outfile)
    

def profile_from_growthcurve(frame):
    """
    Calculate the flux enclosed in a radius 1px annulus at
    different radii. Uses curve_of_growth results to speed up
    calculations
    """
    encflux = zip(frame.radii, frame.fluxes, frame.npix)
    
    profile = np.zeros(len(encflux))
    profile[0] = frame.fluxes[0]
    
    diff_npix = np.zeros(len(encflux))
    diff_npix[0] = frame.npix[0]
    
    for idx, (r1, r2) in enumerate(zip(encflux, encflux[1:])):
        profile[idx+1] =  r2[1] - r1[1]
        diff_npix[idx+1] = r2[2] - r1[2]
    
    profile = np.array(profile)
    diff_npix = np.array(diff_npix)
    frame.profile_npix = diff_npix
    frame.profile = profile / diff_npix
    return frame.profile

def daofind_brightest(filename, fwhmpsf=2.5, threshold=20.0):
    iraf.digiphot(_doprint=0)
    iraf.digiphot.apphot(_doprint=0)
    datapars = iraf.noao.digiphot.apphot.datapars
    findpars = iraf.noao.digiphot.apphot.findpars
    datapars.scale = 1.0
    datapars.fwhmpsf = fwhmpsf
    
    data = pyfits.getdata(filename)
    datapars.sigma = np.std(data) # background stddev
    
    # not important for source finding
    datapars.readnoise = 0.0
    datapars.epadu = 1.0
    
    findpars.threshold = threshold # only care about brightest
    
    tmp_target_dir = tempfile.mkdtemp()
    outfile = os.path.join(tmp_target_dir, 'daofind.coo')
    
    iraf.noao.digiphot.apphot.daofind.run(
        image=filename,
        output=outfile,
        interactive=False,
        verify=False,
    )

    found_stars = parse_coo_file(outfile)
    debug(found_stars)
    found_stars.sort(order=['MAG'])
    brightest = found_stars[0]
    debug("brightest found @", brightest['XCENTER'], ',', brightest['YCENTER'], 'with mag', brightest['MAG'])
    
    shutil.rmtree(tmp_target_dir)
    return brightest
