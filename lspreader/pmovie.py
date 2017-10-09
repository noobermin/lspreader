'''
pmovie reading functions
'''

import numpy as np;
import numpy.lib.recfunctions as rfn;
from lspreader import read;
from pys import sd, mk_getkw;
import struct;
#
# this is mainly hashing
#

def firsthash(frame, removedupes=False):
    '''
    Hashes the first time step. Only will work as long as
    the hash can fit in a uint64.

    Parameters:
    -----------
      frame : first frame.

    Keywords:
    ---------
      removedups: specify duplicates for the given frame.
    
    Returns a dictionary of everything needed
    to generate hashes from the genhash function.
    
    '''
    #hashes must have i8 available
    #overwise, we'll have overflow
    def avgdiff(d):
        d=np.sort(d);
        d = d[1:] - d[:-1]
        ret = np.average(d[np.nonzero(d)]);
        if np.isnan(ret):
            return 1.0;
        return ret;
    def hasextent(l,eps=1e-10):
        #will I one day make pic sims on the pm scale??
        dim = frame['data'][l];
        return np.abs(dim.max()-dim.min()) > eps;
    fields = list(frame['data'].dtype.names);
    dims = [ i for i in ['xi','yi','zi']
             if i in fields and hasextent(i) ];
    ip = np.array([ frame['data'][l]
                    for l in dims ]).T;
    avgdiffs = np.array([avgdiff(a) for a in ip.T]);
    mins  = ip.min(axis=0);
    ips = (((ip - mins)/avgdiffs).round().astype('uint64'))
    pws  = np.floor(np.log10(ips.max(axis=0))).astype('uint64')+1
    pws = list(pws);
    pw = [0]+[ ipw+jpw for ipw,jpw in
               zip([0]+pws[:-1],pws[:-1]) ];
    pw = 10**np.array(pw);#.astype('int64');
    #the dictionary used for hashing
    d=dict(dims=dims, mins=mins, avgdiffs=avgdiffs, pw=pw);
    hashes = genhash(frame,removedupes=False,**d);
    if removedupes:
        #consider if the negation of this is faster for genhash
        uni,counts = np.unique(hashes,return_counts=True);
        d['dupes']=uni[counts>1]
        dupei = np.in1d(hashes, d['dupes']);
        hashes[dupei] = -1;
        d['removedupes']=True;
    return hashes,d

def firsthash_new(frame,**kw):
    kw['new']=True;
    kw['dupes']=None;
    hashes = genhash(frame,**kw);
    uni,counts = np.unique(hashes,return_counts=True);
    d=sd(kw,dupes=uni[counts>1],removedupes=True);
    dupei = np.in1d(hashes, d['dupes'])
    hashes[dupei] = -1
    return hashes, retd;

genhash_defaults = dict(
    d=None,
    new=False,
    dupes=None,
    removedupes=False,
    dims=('xi','yi','zi'),
    ftype='f',
);
def genhash(frame,**kw):
    '''
    Generate the hashes for the given frame for a specification
    given in the dictionary d returned from firsthash.

    Parameters:
    -----------
      frame :  frame to hash.

    Keywords:
    ---------
      d         : hash specification generated from firsthash.
      new       : use new hashing, which isn't really hashing.
      removedups: put -1 in duplicates,
      dims      : specify dims. Supercedes the setting in `d'.
      dupes     : array of hashes known to be dupes.
      ftype     : type of floats. defaults to 'f'.

    -- old keywords from old hashing --
      mins      : minima of each axis
      avgdifs   : average differences
      pw        : powers of each axis

    Returns an array of the shape of the frames with hashes.
    '''
    getkw = mk_getkw(kw,genhash_defaults,prefer_passed=True);
    dims = getkw('dims');
    dupes= getkw('dupes');
    if not getkw('new'):
        ip = np.array([frame['data'][l] for l in dims]).T;
        scaled = ((ip - getkw('mins'))/getkw('avgdiffs')).round().astype('int64');
        hashes = (scaled*getkw('pw')).sum(axis=1).astype('int64');
    else:
        hashes = np.array([
            struct.pack('{}{}'.format(len(dims),getkw('ftype')), *[p[l] for l in dims])
            for p in frame['data']]);
    if getkw('removedupes'):
        #marking duplicated particles
        if not getkw('dupes'):
            hashes =  np.unique(hashes);
        else:
            dupei = np.in1d(hashes, getkw('dupes'));
            hashes[dupei] = -1
    return hashes;

def addhash(frame,**kw):
    '''
    helper function to add hashes to the given frame
    given in the dictionary d returned from firsthash.

    Parameters:
    -----------
      frame :  frame to hash.

    Keywords:
    ---------
      same as genhash
    
    Returns frame with added hashes, although it will be added in
    place.
    '''
    hashes = genhash(frame,**kw);
    frame['data'] = rfn.rec_append_fields(
        frame['data'],'hash',hashes);
    return frame;

def sortframe(frame):
    '''
    sorts particles for a frame
    '''
    d = frame['data'];
    sortedargs = np.lexsort([d['xi'],d['yi'],d['zi']])
    d = d[sortedargs];
    frame['data']=d;
    return frame;

def read_and_hash(fname, **kw):
    '''
    Read and and addhash each frame.
    '''
    return [addhash(frame, **kw) for frame in read(fname, **kw)];

def filter_hashes_from_file(fname, f, **kw):
    '''
    Obtain good hashes from a .p4 file with the dict hashd and a
    function that returns good hashes. Any keywords will be
    sent to read_and_hash.

    Parameters:
    -----------

    fname -- filename of file.
    f     -- function that returns a list of good hashes.
    '''
    return np.concatenate([
        frame['data']['hash'][f(frame)]
        for frame in read_and_hash(fname, **kw)
    ]);
