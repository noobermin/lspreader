#!/usr/bin/env python2
'''
Turn old trajectories.npz into new trajectories.npz format.

Usage:
    ./trajnewfmt.py [options] <input> <output>

Options:
    --help -h       Print this help.
'''
from docopt import docopt;
import numpy as np;
opts=docopt(__doc__,help=True);

with np.load(opts['<input>']) as f:
    data = d['data']
    time = d['time'];
ps = data.shape[1];
out={ i:data[:,i] for i in xrange(ps) }
out['time'] = time;
np.savez(opts['<output>'],**out);
