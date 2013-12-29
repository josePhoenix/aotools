from PIL import Image
import numpy
import re
import glob
import os.path
from pyraf import iraf
import pyfits
from aotools.util import debug, info, warn, error

def pngtocube(directory, filepattern, outfile, exposure):
    if os.path.exists(outfile):
        error("File", outfile, "already exists!")
        return
    files = glob.glob(os.path.join(directory, "*"))
    
    # turn filepattern into a regex
    filepattern = filepattern.replace('$i', r'(\d+)')
    
    # sort files by index instead of lexically
    # (i.e. [99.png, 100.png, 990.png] not [100.png, 99.png, 990.png])
    filetuples = []
    for f in files:
        _, fname = os.path.split(f)
        match = re.match(filepattern, fname)
        if match:
            index = int(match.groups()[0])
            filetuples.append((index, fname))

    filetuples.sort()
    
    
    # from pprint import pprint
    # pprint(filetuples)
    debug("Have", len(filetuples), "frames, numbered", filetuples[0][0], "to", filetuples[-1][0])
    
    # get image dimensions from first input file
    # (assuming all frames are the same shape, which should be true)
    img = Image.open(filetuples[0][1])
    data = numpy.array(img)
    debug("Input frame shape:", data.shape)
    
    shape = (len(filetuples), data.shape[0], data.shape[1])
    cubedata = numpy.zeros(shape)
    debug("Output cube shape:", shape)
    
    for idx, infile in filetuples:
        img = Image.open(infile)
        data = numpy.array(img)
        cubedata[idx] = data
    
    hdu = pyfits.PrimaryHDU(cubedata)
    hdu.header['EXPOSURE'] = exposure
    hdulist = pyfits.HDUList([hdu])
    hdu.writeto(outfile)
    info("Wrote to", outfile)

parfile = iraf.osfn("aotools$pngtocube.par")
t = iraf.IrafTaskFactory(taskname="pngtocube", value=parfile, function=pngtocube)
