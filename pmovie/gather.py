#!/usr/bin/env python2
'''
Gather found particles hashes from input files.

Usage:
    ./gather.py [options] <output> <input>...

Options:
    --help -h                 Print this help.
    --intersect=I -i I        Perform intersection with this file.
'''
from docopt import docopt;
import re;
import numpy as np;


opts=docopt(__doc__,help=True);
good = set();
for fname in opts['<input>']:
    good.update(np.load(fname));
if opts['--intersect']:
    intersect = np.load(opts['--intersect']);
    good.intersection_update(good);
good = np.array(list(good));
good.sort();
np.save(opts['<output>'],good);
