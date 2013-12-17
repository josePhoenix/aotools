import tempfile
import shutil
from aotools.util import debug, info, warn, error, combine_cube_frames
import os.path
from pyraf import iraf

def cubestack(cubefile, rangespec='', clobber=False):
    ranges = []
    for rangestr in rangespec.split(','):
        a, b = rangestr.split('-')
        ranges.append((int(a), int(b)))
    debug("stacking range pairs:", ranges)
    path, filename = os.path.split(cubefile)
    filebase = cubefile.rsplit('.', 1)[0]
    target_dir = os.path.join(path, '{0}_stacks'.format(filebase))
    debug("target:", target_dir)
    
    tmp_target_dir = tempfile.mkdtemp()
    outimgs = combine_cube_frames(cubefile, ranges, tmp_target_dir)
    if os.path.isdir(target_dir):
        debug("target dir exists, removing", target_dir)
        shutil.rmtree(target_dir)
    shutil.copytree(tmp_target_dir, target_dir)

parfile = iraf.osfn("aotools$cubestack.par")
t = iraf.IrafTaskFactory(taskname="cubestack", value=parfile, function=cubestack)
