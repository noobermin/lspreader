#!/usr/bin/env python
'''
Extract data directly.

Usage: 
    p4read.py [options] <input> <output>

Options:
    --npy -n          Output to npy instead of pickle.
    --pickle -p       Output to pickle independent of file ending of output.
'''
from lspreader import read;
from pys import dump_pickle;
from docopt import docopt;
import numpy as np;
import re;

opts = docopt(__doc__,help=True);
if opts['--npy'] or (re.search("\.npy$",opts['<output>']) and not opts['--pickle']):
    np.save(
        opts['<output>'],
        read(opts['<input>'],return_array=True,gzip='guess'),);
else:
    dump_pickle(opts['<output>'],read(opts['<input>'],gzip='guess'));
