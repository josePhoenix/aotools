from pyraf import iraf
import math
import os
import re
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
from aotools.strehl import Frame, avgrow, avgrow_median_subtract

def removeband(infile, outfile, exclude_from, exclude_to):
    imagehdul = pyfits.open(infile)
    data = imagehdul[0].data
    if len(data.shape) == 3:
        debug("Operating on a data cube")
        for idx in range(0, data.shape[0]):
            debug("Processing frame", idx + 1, "of", data.shape[0])
            frame = Frame(data[idx], None)
            avgrow_median_subtract(frame, exclude_from, exclude_to)
            data[idx] = frame.data
        imagehdul[0].data = data
    else:
        frame = Frame(data, None)
        avgrow_median_subtract(frame, exclude_from, exclude_to)
        imagehdul[0].data = frame.data
    imagehdul.writeto(outfile)
    info("Wrote corrected (de-banded and median subtracted) image to", outfile)
    
parfile = iraf.osfn("aotools$removeband.par")
t = iraf.IrafTaskFactory(taskname="removeband", value=parfile, function=removeband)
