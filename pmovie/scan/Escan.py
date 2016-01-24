#!/usr/bin/env python2
'''
Scan a pmovie file for trajectories. Use this as a template.

Usage:
    ./Escan.py [options] <input> <output>

Options:
    --help -h                 Print this help.
    --minE=E -e E             Give the minimum E in MeV. [default: 0.5]
'''

import numpy as np;
#from misc import readfile;
from functools import reduce;
from docopt import docopt;

opts=docopt(__doc__,help=True);
minE = float(opts['--minE']);
with np.load(opts["<input>"]) as f:
    data=f['data'];
E   = (np.sqrt(data['ux']**2+data['uz']**2+1)-1)*0.511;
hs  = data['hash'][E>minE]
if len(hs)>0:
    np.save(opts['<output>'], hs);
