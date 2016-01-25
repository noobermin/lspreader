'''
pmovie reading functions
'''

import numpy as np;
import numpy.lib.recfunctions as rfn;

#
# this is mainly hashing
#

def firsthash(frame,dims,removedupes=False):
    '''
    Hashes the first time step. Only will work as long as
    the hash can fit in a i8.

    Parameters:
    -----------
      frame : first frame.
      dims  :  iterable of strings for dimensions.

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
        return np.average(d[np.nonzero(d)]);
    ip    = np.array([frame['data'][l] for l in dims]).T;
    avgdiffs = np.array([avgdiff(a) for a in ip.T]);
    mins  = ip.min(axis=0);
    ips = (((ip - mins)/avgdiffs).round().astype('i8'))
    pws  = np.floor(np.log10(ips.max(axis=0))).astype('i8')+1
    pws = list(pws);
    pw = [0]+[ ipw+jpw for ipw,jpw in
               zip([0]+pws[:-1],pws[:-1]) ];
    pw = 10**np.array(pw);
    #the dictionary used for hashing
    d=dict(labels=dims, mins=mins, avgdiffs=avgdiffs, pw=pw);
    if removedupes:
        hashes = genhash(frame,d,removedupes=False);
        #consider if the negation of this is faster for genhash
        uni,counts = np.unique(hashes,return_counts=True);
        d.update({'dupes': uni[counts>1]})
    return d;

def genhash(frame,d,removedupes=False):
    '''
    Generate the hashes for the given frame for a specification
    given in the dictionary d returned from firsthash.

    Parameters:
    -----------
      frame :  frame to hash.
      d     :  hash specification generated from firsthash.

    Keywords:
    ---------
      removedups: put -1 in duplicates
    
    Returns an array of the shape of the frames with hashes.
    '''
    ip = np.array([frame['data'][l] for l in d['labels']]).T;
    scaled = ((ip - d['mins'])/d['avgdiffs']).round().astype('i8');
    hashes = (scaled*d['pw']).sum(axis=1);
    #marking duplicated particles
    if removedupes:
        dups = np.in1d(hashes,d['dupes'])
        hashes[dups] = -1
    return hashes;

def addhash(frame,d,removedupes=False):
    '''
    helper function to add hashes to the given frame
    given in the dictionary d returned from firsthash.

    Parameters:
    -----------
      frame :  frame to hash.
      d     :  hash specification generated from firsthash.

    Keywords:
    ---------
      removedups: put -1 in duplicates
    
    Returns frame with added hashes, although it will be added in
    place.
    '''
    hashes = genhash(frame,d,removedupes);
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

