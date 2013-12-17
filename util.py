import os.path
import os, errno
from pyraf import iraf
import numpy
from aotools.colorama import red, yellow, green, cyan, white

# TODO: figure out why PyRAF eats output from normal Python logging
def _args_to_string(*args):
    return u' '.join(a if type(a) in (str, unicode) else repr(a) for a in args)
    

def debug(*args):
    print white('[DEBUG] ' + _args_to_string(*args))

def info(*args):
    print cyan('[INFO] ' + _args_to_string(*args))

def warn(*args):
    print yellow('[WARN] ' + _args_to_string(*args))

def error(*args):
    print red('[ERROR] ' + _args_to_string(*args))

def ensure_dir(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

def combine_cube_frames(cubefile, range_pairs, target_dir):
    dirname, filename = os.path.split(cubefile)
    filebase = filename.rsplit('.', 1)[0]
    if len(filebase) > 8:
        warn("IRAF doesn't like long filenames. "
             "Consider shortening the cube filename ({0})".format(filebase))
    
    outfiles = []
    
    for fromidx, toidx in range_pairs:
        inlst = os.path.join(target_dir, 'in.lst')
        infiles = []
        for i in range(fromidx, toidx+1):
            infiles.append(cubefile + "[*,*,{0}]".format(i))
        
        f = open(inlst, 'w')
        f.writelines(infiles)
        f.write('\n')
        f.close()
        
        outfile = '{0}/{1}_{2}-{3}.fit'.format(target_dir, filebase, fromidx, toidx)
        debug("imcombine input={input} output={output} combine=sum reject=none".format(
            input="@{0}".format(inlst), #','.join(infiles),
            output=outfile,
        ))
        outfiles.append(outfile)
        iraf.imcombine(
            input=','.join(infiles),
            output=outfile,
            combine="sum",
            reject="none",
            # project='no', # IRAF wants bools specified / default is nonboolean?
            # mclip='no',
        )
    return outfiles

def write_table(filename, columns, **kwargs):
    names = []
    data = []
    for colname, coldata in columns:
        names.append(colname)
        data.append(coldata)
    
    zipped_data = zip(*data)
    kwargs['delimiter'] = u'\t'
    kwargs['header'] = kwargs['delimiter'].join(names)
    if not 'fmt' in kwargs.keys():
        kwargs['fmt'] = "%5.5f"
    numpy.savetxt(filename, zipped_data, **kwargs)
    debug("Wrote file", filename)

def parse_coo_file(filename):
    arr = numpy.genfromtxt(
        filename,
        dtype=[
            ('XCENTER', numpy.float64),
            ('YCENTER', numpy.float64),
            ('MAG', numpy.float64),
            ('SHARPNESS', numpy.float64),
            ('SROUND', numpy.float64),
            ('GROUND', numpy.float64),
            ('ID', numpy.int32)
        ]
    )
    if len(arr.shape) < 1:
        return arr[numpy.newaxis] # want single row file to behave like rows
    else:
        return arr
