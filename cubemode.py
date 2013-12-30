import os.path
import numpy
import pyfits
from pyraf import iraf
from aotools.util import debug, info, warn, error, parse_ranges

def cubemode(infile, outfile, exposure):
    datacube = pyfits.getdata(infile)
    median_frame = numpy.median(datacube, axis=0)
    hdu = pyfits.PrimaryHDU(median_frame)
    hdu.header['EXPOSURE'] = exposure
    hdu.writeto(outfile)
    info("Wrote to", outfile)

parfile = iraf.osfn("aotools$cubemode.par")
t = iraf.IrafTaskFactory(taskname="cubemode", value=parfile, function=cubemode)
