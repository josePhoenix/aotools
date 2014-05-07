# KAPAO Monitoring and Performance Characterization Tools #
### Joseph Long, Spring 2014 ###

Tools to work with time-series data from the KAPAO science cameras and more.

## Installation ##

To install and load by default, create a loginuser.cl file (in the folder with 
your login.cl file) with the following content:

    reset aotools = /Users/josephoenix/Dropbox/Software/Joseph/aotools/
    task aotools.pkg = aotools$aotools.cl

    aotools

Edit the path on the `reset aotools` line to point to this folder in your installation. Don't forget the trailing slash!

(Note to text-file readers: this file is written in Markdown, which indicates code listings by indenting with four spaces. You will need to remove those from the above text. Consult loginuser.cl.example if you're confused!)

## Usage ##

### aoavgcube ###

**Note:** should really be named `aosumcube`.

Uses `imcombine` and `aotools.util.combine_cube_frames` to recombine a datacube in such a way that it creates a new cube with frames of a greater integration time. For example, 100 frames of 0.1 seconds could be processed to create a 10 frame cube where each frame covers 1 second of integration time.

*Developer note:* Under the hood, this is just calling `imcombine` to break up and reassemble the cube. Could be reimplemented using only PyFITS, since we aren't using any fancy rejection features.

**Parameters:**

  - `cubefile`: Path to a FITS file with a data cube in the first extension (prompted every time)
  - `outfile`: Name of output file (prompted every time)
  - `fromidx`: Frame number (1-indexed) at which to start combining (default: 1, remembered between invocations)
  - `toidx`: Frame number (1-indexed) at which to end combining (if < fromidx, use whole cube) (default: -1, remembered between invocations)

### cubeflatfield ###

Divides every frame of a FITS data cube by a given single-frame FITS image.

**Parameters:**

  - `infile` - Path to FITS cube
  - `flatfile` - FITS file containing image to divide by
  - `outfile` - Path to FITS cube output


### cubemedian ###

Generates a median frame from a FITS data cube and outputs it as a FITS file with a user-specified `EXPOSURE` time header.

**Parameters:**

  - `infile` - Path to FITS cube
  - `outfile` - Path for output FITS file"
  - `exposure` - Exposure in seconds (to be stored in FITS header)

### cubestack ###

Stacks one or more ranges of frames from a data cube using `imcombine` to sum them. Useful when you know, e.g., frames 10-40 are open loop operation and 60-90 are closed loop. Then you can run this task with the range specification "10-40,60-90" and get two FITS files containing the summed open and closed frames, respectively.

*Developer note:* Under the hood, this too is just calling `imcombine` to break up and reassemble the cube.

**Parameters:**

  - `cubefile`: Path to a FITS file with a data cube in the first extension (prompted every time)
  - `rangespec`: Comma-separated one-indexed ranges to combine (e.g. "1-3,6-10") (prompted every time)
  - `clobber`: *currently unused* (default: False, remembered between invocations)

### cubetoframes ###

Explodes a FITS data cube into a folder with one `.fit` file for each frame. Useful in development, or when you are just sick and tired of data cubes and want to blink between two frames in ds9.

**Parameters:**

  - `cubefile`: Path to a FITS file with a data cube in the first extension (prompted every time)
  - `rangespec`: Comma-separated one-indexed ranges to split into frames (e.g. "1-3,6-10") (prompted every time)
  - `clobber`: When True, delete the `{cubefile}_frames/` directory if it exists before running. When False, exit with an error rather than clobber an existing directory. (default: False, remembered between invocations)

### findbright ###

A quick and dirty wrapper around the `daofind_brightest` function used in the `strehlframe` and `strehlcube` tasks. Prints out the location of the brightest source in the input image, as determined by `daofind`. (Useful for tuning the fwhmpsf and threshold parameters when centroiding is failing in `photstrehl` or `photstrehlframe`.)

**Parameters:**

  - `image`: Path to a FITS file to analyze
  - `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
  - `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)

### photstrehl ###

Computes a time series of Strehl measurements for an entire FITS data cube (or specified ranges). This process is described in more detail under `strehlframe` below. Aside from operating on data cubes, the other major difference is that there is (currently) no way to disable the `daofind`-powered auto-centroiding that detects the source in the frame. (On the plus side, that means that tracking / tip-tilt wander will not cause totally bogus Strehl measurements. On the down side, if `daofind` is way off on one or more of the frames, you can't correct it for that frame.)

**Note:** This differs from strehlcube mainly in using `phot` for "accurate" sub-pixel photometry at small radii. True fractional pixel intersections could probably be implemented, but `phot` gets us closer than our previous Curve of Growth integration code.

**Parameters:**

  - `cubefile`: Path to a FITS file with a data cube to analyze in the first extension (prompted every time)
  - `rangespec`: Comma-separated one-indexed ranges to analyze (e.g. "1-3,6-10") (prompted every time)
  - `primary`: Primary mirror diameter (same units as secondary) (default: 40.9 inches, remembered between invocations)
  - `secondary`: Secondary mirror diameter (same units as primary) (default: 11.5 inches, remembered between invocations)
  - `dimension`: Dimension of intermediate PSF array (default: 1600, remembered between invocations)
  - `f_number`: Adjusted f number for image (f_Andor: 34.875, remembered between invocations)
  - `pixel_scale`: Pixel scale in mm (Andor: 0.013 mm, remembered between invocations)"
  - `lambda_mean`: Mean wavelength in nm (default: 800 nm, remembered between invocations)
  - `growth_step`: Pixel radius increment step for curve of growth (default: 1 px, remembered between invocations)
  - `normalize_at`: Pixel radius at which all flux is contained (default: 0, meaning calculate 2.5'' in px)
  - `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
  - `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)
  - `quiet`: Silence debugging messages (specifically curve of growth radius step information) (default: True, remembered between invocations)

### photstrehlframe ###

**Note:** This differs from strehlframe mainly in using `phot` for "accurate" sub-pixel photometry at small radii. True fractional pixel intersections could probably be implemented, but `phot` gets us closer than our previous Curve of Growth integration code.

**Parameters:**

- `image`: Path to a FITS image to analyze (prompted every time)
- `rangespec`: Comma-separated one-indexed ranges to analyze (e.g. "1-3,6-10") (prompted every time)
- `primary`: Primary mirror diameter (same units as secondary) (default: 40.9 inches, remembered between invocations)
- `secondary`: Secondary mirror diameter (same units as primary) (default: 11.5 inches, remembered between invocations)
- `dimension`: Dimension of intermediate PSF array (default: 1600, remembered between invocations)
- `f_number`: Adjusted f number for image (f_Andor: 34.875, remembered between invocations)
- `pixel_scale`: Pixel scale in mm (Andor: 0.013 mm, remembered between invocations)"
- `lambda_mean`: Mean wavelength in nm (default: 800 nm, remembered between invocations)
- `growth_step`: Pixel radius increment step for curve of growth (default: 1 px, remembered between invocations)
- `normalize_at`: Pixel radius at which all flux is contained (default: 0, meaning calculate 2.5'' in px)
- `find_source`: Detect and automatically centroid brightest source with daofind, ignoring `xcenter` and `ycenter` values (default: True, remembered between invocations)
- `xcenter`: Bright source X Center (column), if not auto-centroiding (default: 511.5 px, remembered between invocations)
- `ycenter`: Bright source Y Center (row), if not auto-centroiding (default: 511.5 px, remembered between invocations)
- `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
- `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)
- `quiet`: Silence debugging messages (specifically curve of growth radius step information) (default: True, remembered between invocations)

### pngtocube ###

Turn a sequence of numbered PNG files into a FITS cube. Xenics data are output as a series of PNGs with an incrementing integer index at the end of the filename. Specify a pattern for the filename, with `$i` in place of the integer index, and this task will collect all the matching frames and turn them into a data cube.

**Parameters:**

  - `directory` - Directory with grayscale PNG images ('.' for current directory)
  - `filepattern` - Pattern for image filenames (Use $i for the index. Example: "target\_foo\_$i.png")
  - `outfile` - Path and filename for destination FITS file
  - `exposure` - Exposure in seconds (to be stored in FITS header)

### pngtofits ###

Convert a grayscale PNG image (e.g. from the Xenics camera) to a FITS file. (Note: counts are not calibrated!)

**Parameters:**

  - `infile` - Path to grayscale PNG image
  - `exposure` - Exposure in seconds (to be stored in FITS header)

### removeband ###

Computes an "average row" for the image and subtracts it off the image row-by-row to remove a banding artifact. The options `exclude_from` and `exclude_to` determine which rows are excluded from the averaging. (Generally you want to exclude the rows that contain the star.)

  - `cubefile` - Path to a FITS frame or cube to analyze
  - `outfile` - Path to write the corrected frame to
  - `exclude_from` - Row at which to begin excluded range
  - `exclude_to` - Row at which to end excluded range

### strehlcube ###

Computes a time series of Strehl measurements for an entire FITS data cube (or specified ranges). This process is described in more detail under `strehlframe` below. Aside from operating on data cubes, the other major difference is that there is (currently) no way to disable the `daofind`-powered auto-centroiding that detects the source in the frame. (On the plus side, that means that tracking / tip-tilt wander will not cause totally bogus Strehl measurements. On the down side, if `daofind` is way off on one or more of the frames, you can't correct it for that frame.)

**Parameters:**

  - `cubefile`: Path to a FITS file with a data cube to analyze in the first extension (prompted every time)
  - `rangespec`: Comma-separated one-indexed ranges to analyze (e.g. "1-3,6-10") (prompted every time)
  - `primary`: Primary mirror diameter (same units as secondary) (default: 40.9 inches, remembered between invocations)
  - `secondary`: Secondary mirror diameter (same units as primary) (default: 11.5 inches, remembered between invocations)
  - `dimension`: Dimension of intermediate PSF array (default: 1600, remembered between invocations)
  - `f_number`: Adjusted f number for image (f_Andor: 34.875, remembered between invocations)
  - `pixel_scale`: Pixel scale in mm (Andor: 0.013 mm, remembered between invocations)"
  - `lambda_mean`: Mean wavelength in nm (default: 800 nm, remembered between invocations)
  - `growth_step`: Pixel radius increment step for curve of growth (default: 1 px, remembered between invocations)
  - `normalize_at`: Pixel radius at which all flux is contained (default: 0, meaning calculate 2.5'' in px)
  - `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
  - `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)
  - `quiet`: Silence debugging messages (specifically curve of growth radius step information) (default: True, remembered between invocations)

### strehlframe ###

**Parameters:**

- `image`: Path to a FITS image to analyze (prompted every time)
- `rangespec`: Comma-separated one-indexed ranges to analyze (e.g. "1-3,6-10") (prompted every time)
- `primary`: Primary mirror diameter (same units as secondary) (default: 40.9 inches, remembered between invocations)
- `secondary`: Secondary mirror diameter (same units as primary) (default: 11.5 inches, remembered between invocations)
- `dimension`: Dimension of intermediate PSF array (default: 1600, remembered between invocations)
- `f_number`: Adjusted f number for image (f_Andor: 34.875, remembered between invocations)
- `pixel_scale`: Pixel scale in mm (Andor: 0.013 mm, remembered between invocations)"
- `lambda_mean`: Mean wavelength in nm (default: 800 nm, remembered between invocations)
- `growth_step`: Pixel radius increment step for curve of growth (default: 1 px, remembered between invocations)
- `normalize_at`: Pixel radius at which all flux is contained (default: 0, meaning calculate 2.5'' in px)
- `find_source`: Detect and automatically centroid brightest source with daofind, ignoring `xcenter` and `ycenter` values (default: True, remembered between invocations)
- `xcenter`: Bright source X Center (column), if not auto-centroiding (default: 511.5 px, remembered between invocations)
- `ycenter`: Bright source Y Center (row), if not auto-centroiding (default: 511.5 px, remembered between invocations)
- `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
- `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)
- `quiet`: Silence debugging messages (specifically curve of growth radius step information) (default: True, remembered between invocations)
