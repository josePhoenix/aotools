from PIL import Image
import matplotlib
matplotlib.use('agg') # cannot import pyplot within pyraf without this
from matplotlib import pyplot as plt
import numpy
import os.path
from pyraf import iraf
import pyfits
from aotools.util import debug, info, warn, error

def pngtofits(infile, exposure):
    base, ext = os.path.splitext(infile)
    img = Image.open(infile)
    data = numpy.array(img)
    hdu = pyfits.PrimaryHDU(data)
    hdu.header['EXPOSURE'] = exposure
#    hdulist = pyfits.HDUList([hdu])
    hdu.writeto('{0}.fits'.format(base))
    info("Wrote to",'{0}.fits'.format(base))

parfile = iraf.osfn("aotools$pngtofits.par")
t = iraf.IrafTaskFactory(taskname="pngtofits", value=parfile, function=pngtofits)
