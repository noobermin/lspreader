'''
Functions for flds and sclr files.
'''
import lspreader
from lspreader import read;
from .lspreader import get_header;
import numpy as np;
import numpy.linalg as lin;
import os;

def getvector(d,s):
    '''
    Get a vector flds data.

    Parameters:
    -----------

    d -- flds data.
    s -- key for the data.
    '''
    return np.array([d[s+"x"],d[s+"y"],d[s+"z"]]);

def vector_norm(d,k):
    '''
    Get a norm of vector flds data.

    Parameters:
    -----------

    d -- flds data.
    s -- key for the data.
    '''
    return lin.norm(getvector(d,k),axis=0)

def read_indexed(i,flds=None,sclr=None,
                 gzip='guess', dir='.', vector_norms=True,
                 keep_xs=False,gettime=False):
    '''
    A smart indexing reader that reads files by names. Looks for files
    like "<dir>/flds<i>.p4<compression>" where dir and the index are
    passed, as well as stuff from sclrs and saves them into one
    dictionary. Essentially useful for reading by timestep instead
    of by file. Assumes that both the flds and sclr are in the same
    direction.

    Parameters:
    -----------

    i -- index of file

    Required Keywords:
    ------------------

    flds  -- list of var's to load from the flds file
    sclr  -- list of var's to load from the sclr file
    
    Either one or both are required.

    Keywords:
    ---------

    gzip         -- files are gzipped. If gzip is "guess",
                    find a matching file.
    dir          -- Directory to look for files. Default is .
    vector_norms -- save the norm of the flds vectors under the
                    the name of the quantity. Default is True.
    keep_xs      -- Keep the edges. By default, False.
    gettime      -- Get the timestamp.
    '''
    fldsp4  = '{}/flds{}.p4'.format(dir,i);
    sclrp4  = '{}/sclr{}.p4'.format(dir,i);
    fldsgz  = fldsp4 + '.gz';
    sclrgz  = sclrp4 + '.gz';
    if gzip == 'guess':
        fldsname = fldsp4 if os.path.exists(fldsp4) else fldsgz
        sclrname = sclrp4 if os.path.exists(sclrp4) else sclrgz
    else:
        fldsname = fldsgz if gzip else fldsp4;
        sclrname = sclrgz if gzip else sclrp4;
    if not (flds or sclr):
        raise ValueError("Must specify flds or sclr to read.");
    elif flds is not None and sclr is not None:
        sd,srt=read(sclrname,
                    var=sclr,first_sort=True, gzip='guess',
                    keep_xs=keep_xs);
        fd=read(fldsname,
                var=flds, sort=srt, gzip='guess',
                keep_xs=keep_xs);
        ret = dict(sd=sd,fd=fd);
        ret.update({k:sd[k] for k in sd});
        ret.update({k:fd[k] for k in fd});
        if vector_norms:
            ret.update({k:vector_norm(ret,k) for k in flds})
        if gettime:
            ret['t'] = get_header(sclrname,gzip='guess')['timestamp'];
    else:
        if flds:
            var = flds;
            name= fldsname;
        else:
            var = sclr;
            name= sclrname;
        ret,_ = read(name,var=var,first_sort=True,gzip='guess');
        if flds and vector_norms:
            ret.update({k:vector_norm(ret,k) for k in flds})
        if gettime:
            ret['t'] = get_header(name,gzip='guess')['timestamp'];
    return ret;

def restrict(d,restrict):
    '''
    Restrict data by indices.

    Parameters:
    ----------

    d         -- the flds/sclr data
    restrict  -- a tuple of [xmin,xmax,...] etx
    '''
    notqs = ['t','xs','ys','zs','fd','sd']
    keys  = [k for k in d if k not in notqs];
    if len(restrict) == 2:
        for k in keys:
            d[k] = d[k][restrict[0]:restrict[1]]
    elif len(restrict) == 4:
        for k in keys:
            d[k] = d[k][
                restrict[0]:restrict[1],
                restrict[2]:restrict[3]
            ];
    elif len(restrict) == 6:
        for k in keys:
            d[k] = d[k][
                restrict[0]:restrict[1],
                restrict[2]:restrict[3],
                restrict[4]:restrict[5]
            ];
    else:
        raise ValueError("restrict of length {} is not valid".format(
            len(restrict)));


