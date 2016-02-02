#!/usr/bin/env python2
'''
Search a p4 for the given indices.

Usage:
    ./searchp4.py [options] <input> <indexfile>

Options:
    --help -h                    Print this help.
    --hash=HASHFILE -H HASHFILE  Read this hash file.
    --gzip -Z                    Read gzipped files.
'''
from docopt import docopt;
opts=docopt(__doc__,help=True);
import numpy as np;
from time import time;
def vprint(s):
    print("{}: {}".format(opts['<input>'], s));
opts = docopt(__doc__,help=True);
vprint = mkvprint(opts);

indices = np.load(opts['<indexfile>']);
hashd = readfile(opts['--hash'],dumpfull=True);
#reading in using the reader.
frames = read_and_hash(opts['<input>'], hashd,
                       removedups=True,
                       gzip=opts['--gzip']);
for frame in frames:
    data = frame['data'];
    found = np.in1d(data['hash'],indices);
    data  = data[found];#destructive
    data.sort(order='hash');
    out     = np.empty(indices.shape, dtype=data.dtype);
    out[:]      = np.nan
    out['hash'] = -1;
    outbools= np.in1d(indices, data['hash']);
    out[outbools] = data;
    outname = "{}.{}".format(opts['<input>'],frame['step']);
    if opts['--dir']:
        outname = '{}/{}'.format(opts['--dir'], outname);
    np.savez(outname, data=out, time=frame['time']);
