#!/usr/bin/env python2
'''
Scan a pmovie file for trajectories. Use this as a template.

Usage:
    ./Escan.py [options] <input> <output>

Options:
    --help -h                 Print this help.
    --minE=E -e E             Give the minimum E in MeV. [default: 0.5]
    --maxX=X -x X             Filter on position with energy [default: -10e-4]
'''

import numpy as np;
from functools import reduce;
from docopt import docopt;

opts=docopt(__doc__,help=True);
minE = float(opts['--minE']);
maxX = float(opts['--maxX']);
with np.load(opts["<input>"]) as f:
    data=f['data'];
E   = (np.sqrt(data['ux']**2+data['uz']**2+1)-1)*0.511;
good = np.logical_and(E>minE, data['x'] < maxX);
hs  = data['hash'][good];
if len(hs)>0:
    np.save(opts['<output>'], hs);
