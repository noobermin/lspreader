#!/usr/bin/env python2
'''
Parse a lsp fields or scalar file.

Usage:
  flds.py [options] <input> <output>
  flds.py [options] <input> <output> <var>...

Options:
  --help -h              Show this help.
  --verbose -v           Turn on verbosity.
  --npz -n               Use compressed npz over pickle.
  --reshape -r           Use rectangular reshaping for contiguous simulations.
'''
from time import time;
import numpy as np;

def rect_flds(d,s=None):
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

if __name__ == "__main__":
    from docopt import docopt;
    from misc import dump_pickle,mkvprint;
    import lspreader as rd;
    
    opts=docopt(__doc__,help=True);
    vprint = mkvprint(opts);
    if len(opts['<var>']) == 0:
        opts['<var>'] = False;
    b=time();
    d=rd.read(opts['<input>'],
              var=opts['<var>'],vprint=vprint,
              remove_edges=opts['--reshape']);
    
    vprint("time to read file {}: {}".format(opts['<input>'],time()-b));
    vprint("read: {}".format(",".join(d.keys())));
    if opts['--reshape']:
        d = rect_flds(d);
    if opts['--npz']:
        np.savez_compressed(opts['<output>'],**d);
    else:
        dump_pickle(opts['<output>'],d);
