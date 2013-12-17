import sys
import tempfile
import shutil
import os.path
from pyraf import iraf
import pyfits
# why won't logging work in PyRAF :(
from aotools.util import debug, info, warn, error, combine_cube_frames
# from aotools.util import frames_to_cube

import logging

def aoavgcube(cubefile, outfile, newexposure, fromidx=1, toidx=None):
    """
    Combine (without rejection) many short exposures in a data cube
    to approximate a "seeing disk" from a longer integration time.
    
    cubefile - input data cube path
    outfile - output data cube path
    fromidx - 1-based index of start of combining range (default: 1)
    toidx - 1-based index of end of range (default: None, end of cube)
    """
    newexposure = float(newexposure)
    ffile = pyfits.open(cubefile)
    header = ffile[0].header
    data = ffile[0].data

    if 'EXPOSURE' in header.keys():
        oldexposure = float(header['EXPOSURE'])
    elif 'EXPTIME' in header.keys():
        oldexposure = float(header['EXPTIME'])
    else:
        raise Exception("No exposure time value found in the datacube header!")

    assert newexposure > oldexposure, ("Can't get a shorter exposure time by combining frames! "
        "oldexposure {0} > newexposure {1}".format(oldexposure, newexposure))

    frames_per_combined = int(newexposure / oldexposure)
    epsilon = (newexposure / oldexposure) - int(newexposure / oldexposure)
    if epsilon > 0.01:
        warn("New exposure is not an integer multiple of old exposure, rounding to", frames_per_combined)
    assert frames_per_combined > 1, "Only one old frame per combined frame; this is probably not what you want"

    if toidx <= fromidx:
        # use entire cube
        toidx = data.shape[0]
    else:
        assert toidx <= data.shape[0], "toidx ({0}) > number of frames ({1})".format(toidx, data.shape[0])
    assert data.shape[0] > 1, "Only one frame found! Is this a data cube?"

    total_frames = toidx - fromidx
    debug("toidx=",toidx,"fromidx=",fromidx)

    if total_frames % frames_per_combined != 0:
        warn("Total frames in range (toidx - fromidx =", toidx - fromidx, ") is not an integer multiple "
             "of the number of frames per combined exposure (", frames_per_combined,
             ") so", total_frames % frames_per_combined, "frames from the end of "
             "the range will be left off.")
        toidx = toidx - (total_frames % frames_per_combined)
        total_frames = toidx - fromidx

    total_combined_frames = int(total_frames / frames_per_combined)
    info("Output data cube will have", total_combined_frames, "total frames of", newexposure, "sec exposure")
    info("Processing input data cube frames", fromidx, "to", toidx)
    target_dir = tempfile.mkdtemp()
    info("Created working directory {0} for intermediate data".format(target_dir))

    try:
        range_pairs = list((
            fromidx + n * frames_per_combined,
            fromidx + (n+1) * frames_per_combined - 1
        ) for n in range(0, total_combined_frames))
        
        frame_paths = combine_cube_frames(cubefile, range_pairs, target_dir)
        # frames_to_cube(frame_paths, outfile)
    finally:
        # Don't leave clutter if the task fails
        # shutil.rmtree(target_dir)
        info("Removed working directory {0}".format(target_dir))

# def frames_to_cube(frames, outfile):
    

parfile = iraf.osfn("aotools$aoavgcube.par")
t = iraf.IrafTaskFactory(taskname="aoavgcube", value=parfile, function=aoavgcube)
