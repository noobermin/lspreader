'''
Functions for flds and sclr files.
'''

def rect(d,s=None):
    dims = ['xs', 'ys', 'zs'];
    labels = [ key for key in d.keys()
               if key not in dims ];
    shape = [ len( np.unique(d[l]) )
              for l in dims ];
    if not s:
        s = np.lexsort((d['z'],d['y'],d['x']));
    for l in labels:
        d[l] = d[l][s].reshape(shape);
    return d;
