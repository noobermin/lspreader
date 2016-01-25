#!/usr/bin/env python2
'''
Extract data directly.

Usage: read.py <input> <output>
'''
from lspreader import lspreader as rd;
from lspreader.misc import dump_pickle;
from docopt import docopt;

opts = docopt(__doc__,help=True);
dump_pickle(
    opts['<output>'],
    rd.read(opts['<input>']));

