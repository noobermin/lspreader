#!/usr/bin/env python2
'''
Randomly select from a parts of a trajectory npz file.

Usage:
    ./trajscan.py [options] <input> <output>

Options:
    --help -h                Print this help.
    --sample=N -n N          Read out to the end END. [default: 2000]
'''

import numpy as np;
from docopt import docopt;

opts=docopt(__doc__,help=True);
n = int(opts['--sample'])
with np.load(opts['<input>']) as f :
    d=f['data']
    time=f['time']
s=np.random.choice(d.shape[1],size=n,replace=False);
d=d[:,s]
np.savez_compressed(opts['<output>'],data=d,time=time);
