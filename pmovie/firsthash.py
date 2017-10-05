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
from lspreader.pmovie import firsthash;
#firsthash = firsthash_new;;
from pys import dump_pickle;
fs=read(opts['<input>'], gzip='guess');
frame1 = fs[0];
hashes, hashd  = firsthash(frame1);
hashd['gzip']='guess' #hack
hashes.sort();
np.save(opts['<hashesout>'], hashes);
dump_pickle(opts['<hashdout>'], hashd);
