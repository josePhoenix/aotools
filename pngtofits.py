import glob
from PIL import Image
import numpy
import os.path
from pyraf import iraf
import pyfits
from aotools.util import debug, info, warn, error

def pngtofits(infile, exposure):
    # Is this a wildcard pattern?
    if '*' in infile:
        files = glob.glob(infile) # list of all matching
        debug("converting all of", files)
    else:
        files = [infile,] # list of one
    
    for fn in files:
        base, ext = os.path.splitext(fn)
        img = Image.open(fn)
        data = numpy.array(img)
        hdu = pyfits.PrimaryHDU(data)
        hdu.header['EXPOSURE'] = exposure
        hdu.writeto('{0}.fits'.format(base))
        info("Wrote to",'{0}.fits'.format(base))

parfile = iraf.osfn("aotools$pngtofits.par")
t = iraf.IrafTaskFactory(taskname="pngtofits", value=parfile, function=pngtofits)
