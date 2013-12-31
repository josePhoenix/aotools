import tempfile
import shutil
from aotools.util import debug, info, warn, error, combine_cube_frames, ensure_dir, parse_ranges
import os.path
from pyraf import iraf

def split_frames(cubefile, range_pairs, target_dir):
    dirname, filename = os.path.split(cubefile)
    filebase = filename.rsplit('.', 1)[0]
    if len(filebase) > 8:
        warn("IRAF doesn't like long filenames. "
             "Consider shortening the cube filename ({0})".format(filebase))
    
    outfiles = []
    
    for fromidx, toidx in range_pairs:
        for i in range(fromidx, toidx+1):
            infile = cubefile + "[*,*,{0}]".format(i)
            outfile = '{0}/frame_{1}.fit'.format(target_dir, i)
            debug("imcopy", infile, outfile)
            iraf.imcopy( # easier to use imcopy and preserve headers than to use pyfits I think
                input=infile,
                output=outfile
            )
            outfiles.append(outfile)
        
        # f = open(inlst, 'w')
        # f.writelines(infiles)
        # f.write('\n')
        # f.close()
        
        # outfile = '{0}/{1}_{2}-{3}.fit'.format(target_dir, filebase, fromidx, toidx)
        # debug("imcombine input={input} output={output} combine=sum reject=none".format(
        #     input="@{0}".format(inlst), #','.join(infiles),
        #     output=outfile,
        # ))
        # outfiles.append(outfile)
        # iraf.imcombine(
        #     input=','.join(infiles),
        #     output=outfile,
        #     combine="sum",
        #     reject="none",
        #     # project='no', # IRAF wants bools specified / default is nonboolean?
        #     # mclip='no',
        # )
    return outfiles

def cubetoframes(cubefile, rangespec='', clobber=False):
    ranges = parse_ranges(rangespec)
    path, filename = os.path.split(cubefile)
    filebase = cubefile.rsplit('.', 1)[0]

    target_dir = os.path.join(path, '{0}_frames'.format(filebase))
    debug("target:", target_dir)
    if os.path.isdir(target_dir):
        debug("target dir exists:", target_dir)
        if clobber:
            shutil.rmtree(target_dir)
        else:
            error("target dir exists (remove dir or set clobber=True)", target_dir)
            raise RuntimeError("target dir exists (remove dir or set clobber=True)")
    ensure_dir(target_dir)
    outimgs = split_frames(cubefile, ranges, target_dir)
    debug("made outimgs", outimgs)

if __name__ == "__builtin__":
    parfile = iraf.osfn("aotools$cubetoframes.par")
    t = iraf.IrafTaskFactory(taskname="cubetoframes", value=parfile, function=cubetoframes)
