#!/usr/bin/env python2
'''
Search a file for the given indices.

Usage:
    ./search.py [options] <input> <indexfile> <output>

Options:
    --help -h                 Print this help.
'''
from docopt import docopt;
opts=docopt(__doc__,help=True);
import numpy as np;
from time import time;
def vprint(s):
    print("{}: {}".format(opts['<input>'], s));
indices = np.load(opts['<indexfile>']);
with np.load(opts['<input>']) as f:
    data = f['data'];
    time = f['t'];
found   = np.in1d(data['hash'],indices);
data       = data[found];#destructive
data.sort(order='hash');
out     = np.empty(indices.shape, dtype=data.dtype);
out[:]      = np.nan
out['hash'] = -1;
outbools= np.in1d(indices, data['hash']);
out[outbools] = data;
np.savez(opts['<output>'],data=out,time=time);
