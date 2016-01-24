#!/usr/bin/env python2
'''
Get the first timestep's hashes and output them to a standalone file.

Usage:
    ./gather.py [options] <input> <output>

Options:
    --help -h                 Print this help.
'''
from docopt import docopt;
opts=docopt(__doc__,help=True);
import numpy as np;
hash = np.load(opts['<input>'])['data']['hash']
hash = hash[hash != -1];
np.save(opts['<output>'], hash);

