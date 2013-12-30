import os.path
import numpy
import pyfits
from pyraf import iraf
from aotools.util import debug, info, warn, error, parse_ranges

def cubeflatfield(cubefile, flatfile, outfile):
    flatdata = pyfits.getdata(flatfile)
    hdulist = pyfits.open(cubefile)
    cubedata = hdulist[0].data

    for idx in xrange(0, cubedata.shape[0]):
        cubedata[idx] = cubedata[idx] / flatdata

    hdulist.writeto(outfile)
    info("Wrote to", outfile)

parfile = iraf.osfn("aotools$cubeflatfield.par")
t = iraf.IrafTaskFactory(taskname="cubeflatfield", value=parfile, function=cubeflatfield)