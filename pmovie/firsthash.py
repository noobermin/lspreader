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
#firsthash = firsthash_new;;
from pys import dump_pickle;
fs=read(opts['<input>'], gzip='guess');
frame1 = fs[0];
frame1, hashd  = firsthash(frame1);
frame1 = addhash(frame1, new=True, removedupes=True);
hashd['gzip']='guess' #hack
hashes = frame1['data']['hash']
hashes = hashes[hashes != -1];
hashes.sort();
np.save(opts['<hashesout>'], hashes);
dump_pickle(opts['<hashdout>'], hashd);
