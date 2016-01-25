'''
Functions for flds and sclr files.
'''
import numpy as np;

def rect(d,s=None):
    dims = ['xs', 'ys', 'zs'];
    labels = [ key for key in d.keys()
               if key not in dims ];
    shape = [ len( np.unique(d[l]) )
              for l in dims ];
    if s is not None:
        s = np.lexsort((d['z'],d['y'],d['x']));
    for l in labels:
        d[l] = d[l][s].reshape(shape);
    return d;
