#!/usr/bin/env python2
'''
Pointless script to concatenate numpy arrays, shape (1,) only.

Usage: arrcat.py [--help | -h] <output> <input>...
'''
import numpy as np;
from docopt import docopt;

opts = docopt(__doc__,help=True);
np.save(opts['<output>'], np.concatenate(
    tuple([np.load(name) for name in opts['<input>']])));
