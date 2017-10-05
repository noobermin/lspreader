'''
pmovie reading functions
'''

import numpy as np;
import numpy.lib.recfunctions as rfn;
from lspreader import read;
from pys import sd;
#
# this is mainly hashing
#

def firsthash(frame, removedupes=False):
    '''
    Hashes the first time step. Only will work as long as
    the hash can fit in a i8.

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
    ips = (((ip - mins)/avgdiffs).round().astype('i8'))
    pws  = np.floor(np.log10(ips.max(axis=0))).astype('i8')+1
    pws = list(pws);
    pw = [0]+[ ipw+jpw for ipw,jpw in
               zip([0]+pws[:-1],pws[:-1]) ];
    pw = 10**np.array(pw);
    #the dictionary used for hashing
    d=dict(dims=dims, mins=mins, avgdiffs=avgdiffs, pw=pw);
    if removedupes:
        hashes = genhash(frame,d,removedupes=False);
        #consider if the negation of this is faster for genhash
        uni,counts = np.unique(hashes,return_counts=True);
        d.update({'dupes': uni[counts>1]})
    return d;

def firsthash_new(frame,**kw):
    kw['new']=True;
    hashes = genhash(frame);
    uni,counts = np.unique(hashes,return_counts=True);
    retd=sd(kw,dupes=uni[counts>1],removedupes=True);
    dupei = np.in1d(hashes, retd['dupes'])
    hashes[dupei] = -1
    return frame, retd;
  

def genhash(frame,d=None,new=False,removedupes=False,dims=None):
    '''
    Generate the hashes for the given frame for a specification
    given in the dictionary d returned from firsthash.

    Parameters:
    -----------
      frame :  frame to hash.

    Keywords:
    ---------
      d         : hash specification generated from firsthash.
      removedups: put -1 in duplicates
      dims      : specify dims. Supercedes the setting in d.
      new       : use new hashing.
      
    Returns an array of the shape of the frames with hashes.
    '''
    dupes = None;
    if d is not None:
        if dims is None: dims = d['dims'];
        dupes = d['dupes'];
    if not new:
        if d is None:
            raise ValueError("old hashing requires hash spec");
        ip = np.array([frame['data'][l] for l in dims]).T;
        scaled = ((ip - d['mins'])/d['avgdiffs']).round().astype('i8');
        hashes = (scaled*d['pw']).sum(axis=1);
    else:
        if not dims: dims=['xi','yi','zi'];
        hashes = np.array(
            [hash(tuple((p[l] for l in dims)))
             for p in frame])
    if removedupes:
        #marking duplicated particles
        if not dupes:
            hashes =  np.unique(hashes);
        else:
            dupei = np.in1d(hashes, dupes)
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
