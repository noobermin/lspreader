'''
Functions for flds and sclr files.
'''
import numpy as np;

def sort(d,s):
    '''
    Sort based on position. Sort with s as a tuple of the sort
    indices and shape from first sort.

    Parameters:
    -----------

    d   -- the flds/sclr data
    s   -- (si, shape) sorting and shaping data from firstsort.
    '''
    labels = [ key for key in d.keys()
               if key not in ['xs', 'ys', 'zs'] ];
    si,shape = s;
    for l in labels:
        d[l] = d[l][si].reshape(shape);
    return d;

def firstsort(d):
    '''
    Perform a lexsort and return the sort indices and shape as a tuple.
    '''
    shape = [ len( np.unique(d[l]) )
              for l in ['xs', 'ys', 'zs'] ];
    si = np.lexsort((d['z'],d['y'],d['x']));
    return si,shape;
