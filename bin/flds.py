#!/usr/bin/env python2
'''
Parse a lsp fields or scalar file.

Usage:
  flds.py [options] <input> <output>
  flds.py [options] <input> <output> <var>...

Options:
  --help -h              Show this help.
  --verbose -v           Turn on verbosity.
  --pickle -p            Use pickle over compressed npz.
  --reshape -r           Use rectangular reshaping for contiguous simulations.
'''
from time import time;
import numpy as np;
from docopt import docopt;
from lspreader.misc import dump_pickle,mkvprint;
from lspreader import lspreader as rd;
from lspreader.flds import rect;
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
if opts['--pickle']:
    dump_pickle(opts['<output>'],d);
else:
    np.savez_compressed(opts['<output>'],**d);