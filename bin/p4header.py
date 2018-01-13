#!/usr/bin/env python2
'''
Just get the header of a .p4 and output it.

Usage:
  p4header.py [options] <input>

Options:
  --help -h               Show this help.
  --verbose -v            Turn on verbosity.
  --size -s               Output the size of the header in bytes.
  --gzip -Z               Use gzip. Otherwise guess based on name.
'''

from lspreader import lspreader as rd;
import numpy as np;
from docopt import docopt;

opts=docopt(__doc__,help=True);
verbose = opts['--verbose'];
name = opts['<input>'];
gzip = True if opts['--gzip'] else 'guess';
h = rd.get_header(
    opts['<input>'],
    size=opts['--size'], gzip=gzip);
if opts['--size']:
    print("{}".format(h[1]));
else:
    print(h);
