#!/usr/bin/env python2
'''
Search a p4 for the given indices.

Usage:
    ./searchp4.py [options] <input> <hashd> <indexfile>

Options:
    --help -h                    Print this help.
    --gzip -Z                    Read gzipped files.
    --dir=D -D D                 Output to this directory.
'''
from docopt import docopt;
opts=docopt(__doc__,help=True);
from pys import load_pickle;
from lspreader.pmovie import read_and_hash;
import numpy as np;

indices = np.load(opts['<indexfile>']);
hashd = load_pickle(opts['<hashd>']);
#reading in using the reader.
frames = read_and_hash(opts['<input>'], **hashd);
#frames = read_and_hash(opts['<input>'], hashd,
#                       removedups=True,
#                       gzip='guess');
for frame in frames:
    data = frame['data'];
    found = np.in1d(data['hash'],indices);
    data  = data[found];
    data.sort(order='hash');
    out   = np.empty(indices.shape, dtype=data.dtype);
    out[:]      = np.nan
    out['hash'] = -1;
    outbools= np.in1d(indices, data['hash']);
    out[outbools] = data;
    outname = "{}".format(frame['step']);
    if opts['--dir']:
        outname = '{}/{}'.format(opts['--dir'], outname);
    np.savez(outname, data=out, time=frame['t']);
