# KAPAO Monitoring and Performance Characterization Tools #
### Joseph Long, Fall 2013 ###

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

A quick and dirty wrapper around the `daofind_brightest` function used in the `strehlframe` and `strehlcube` tasks. Prints out the location of the brightest source in the input image, as determined by `daofind`.

**Parameters:**

  - `image`: Path to a FITS file to analyze
  - `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
  - `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)

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
- `find_source`: Detect and automatically centroid brightest source with daofind, ignoring `xcenter` and `ycenter` values (default: True, remembered between invocations)
- `xcenter`: Bright source X Center (column), if not auto-centroiding (default: 511.5 px, remembered between invocations)
- `ycenter`: Bright source Y Center (row), if not auto-centroiding (default: 511.5 px, remembered between invocations)
- `fwhmpsf`: FWHM in pixels (initial guess), passed on to `daofind` (default: 2.5 px, remembered between invocations)
- `threshold`: Threshold for detection in sigma, passed on to `daofind` (default: 20.0 sigma, remembered between invocations)
- `quiet`: Silence debugging messages (specifically curve of growth radius step information) (default: True, remembered between invocations)

## Overview ##

As of 12/26/2013, here's the purpose for every file included in aotools.

  - `__init__.py` -- Python source
    
    Empty file, tells Python this folder contains things to import
    
  - `addpath.py` -- Python source
    
    Executed by aotools.cl to ensure PyRAF loads aotools functions correctly by adding this folder (whereever it may be) to the Python path
    
  - `aoavgcube.par` -- PyRAF parameters
    
    Defines default parameters for the aoavgcube task
    
  - `aoavgcube.py` -- Python source, PyRAF task
    
    Recombines a range (1-indexed) of frames from a data cube to simulate longer integration times using imcombine in sum mode without rejection.
    
  - `aotools.cl` -- PyRAF CL script
    
    Loads the aotools package into PyRAF (reference this in your loginuser.cl!)
    
  - `colorama.py` -- Python source
    
    Helper functions for colorful terminal output in PyRAF
    
  - `cubestack.par` -- PyRAF parameters
    
    Defines default parameters for the cubestack task
    
  - `cubestack.py` -- Python source, PyRAF task
    
    Stacks arbitrary ranges (1-indexed) of frames in a data cube using imcombine in sum mode without rejection (Something like a less opinionated aoavgcube)
    
  - `cubetoframes.par` -- PyRAF parameters
    
    Defines default parameters for the cubetoframes task
    
  - `cubetoframes.py` -- Python source, PyRAF task
    
    Explodes a FITS data cube into individual FITS frames
    
  - `findbright.par` -- PyRAF parameters
    
    Defines default parameters for the findbright task
    
  - `findbright.py` -- Python source, PyRAF task
    
    A quick and dirty wrapper around the `daofind_brightest` function used in the `strehlframe` and `strehlcube` tasks. Prints out the location of the brightest source in the input image.
    
  - `loginuser.cl.example` -- PyRAF CL script template
    
    Example of how to include aotools in your loginuser.cl. (Copy this file, update the paths, and drop the copy in the folder with your login.cl.)
    
  - `README` -- Must-read documentation
    
    You're reading it!
    
  - `strehl.py` -- Python source
    
    A variety of helper functions employed in the strehlframe and strehlcube tasks, including circular mask generation, PSF generation, PSF scaling, plotting with a twinned axis in arcseconds, curve of growth and profile calculation, a Frame helper class used to wrap data from images, and a function that uses PyRAF daofind to locate the brightest source in the image. (In other words, an excellent candidate for refactoring!)
    
  - `strehlcube.par` -- PyRAF parameters
    
    Defines default parameters for the strehlcube task. You can change the calculation to account for different peak wavelengths, different f-numbers at the camera you are imaging with, different pixel scale on the detector, etc.
    
  - `strehlcube.py` -- Python source, PyRAF task
    
    Computes Strehl ratios frame by frame for ranges of frames in a data cube (1-indexed, specified like "3-5,9-10"). Output is a text table where the first column of each row contains a frame number, and subsequent columns contain the Strehl ratio for a core radius at r = 1...n px.
    
  - `strehlframe.par` -- PyRAF parameters
    
    Defines default parameters for the strehlframe task. Similarly to `strehlcube`, you can change various parameters of the optical system for PSF generation. You may also supply an x and y center for the star in the input frame, if you disable the auto-centroiding through daofind.
    
  - `strehlframe.py` -- Python source, PyRAF task
    
    Generates plots of the curve of growth and profile for a source in an image, overplotting the same for an ideally diffraction limited source. Outputs a text table with Strehl ratios for different core radii, as well as profile values and enclosed energies for those radii.
    
  - `util.py` -- Python source
    
    Every project has one. Currently harboring logging helpers, a parser for range specifications (like "3-5,9-10") called `parse_ranges`, a parser for daofind `.coo.?` files (`parse_coo_file`), a helper for writing a text table (`write_table`), a helper function to create a directory if it does not exist (`ensure_dir`), and a function `combine_cube_frames` that uses imcombine to sum frames in ranges from an input file into a new directory.
