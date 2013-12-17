from pyraf import iraf
import pyfits
import numpy as np
# why won't logging work in PyRAF :(
from aotools.util import debug, info, warn, error, parse_coo_file

from aotools.strehl import daofind_brightest

def findbright(image, fwhmpsf, threshold):
    bright = daofind_brightest(image, fwhmpsf, threshold)
    print "Brightest source:"
    print "XCENTER\tYCENTER\tMAG\tID"
    print "{0}\t{1}\t{2}\t{3}".format(bright['XCENTER'], bright['YCENTER'], bright['MAG'], bright['ID'])

parfile = iraf.osfn("aotools$findbright.par")
t = iraf.IrafTaskFactory(taskname="findbright", value=parfile, function=findbright)
