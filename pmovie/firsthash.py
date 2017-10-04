#!/usr/bin/env python
'''
Get the first pmovie's frame's hashes  output them to a standalone file as well as the
hash specification.

Usage:
    ./firsthash.py [options] <input> <hashdout> <hashesout>

Options:
    --help -h                 Print this help.
'''
from docopt import docopt;
opts=docopt(__doc__,help=True);
import numpy as np;
from lspreader import read;
from lspreader.pmovie import firsthash,addhash;
from pys import dump_pickle;
fs=read(opts['<input>'], gzip='guess');
frame1 = fs[0];
hashd  = firsthash(frame1, removedupes=True);
frame1 = addhash(frame1, hd, removedupes=True);
hashes = frame1['data']['hash']
hashes = hashes[hashes != -1];
np.save(opts['<hashesout>'], hashes);
dump_pickle(opts['<hashdout>'], hashd);


