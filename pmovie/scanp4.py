#!/usr/bin/env python2
'''
Search a p4 for good indices.

Usage:
    ./search.py [options] <input> <output>

Options:
    --help -h                    Print this help.
    --hash=HASHFILE -H HASHFILE  Read this hash file.
    --gzip -Z                    Read gzipped files.
    --minE=E -e E                Give the minimum E in MeV. [default: 0.5].
    --maxX=X -x X                Filter on position with energy [default: -10e-4].
'''
from lspreader import read;
from lspreader.pmovie import addhash, filter_hashes_from_file;
from lspreader.misc import readfile;
import numpy as np;

if __name__ == "__main__":
    from docopt import docopt;
    opts=docopt(__doc__,help=True);
    minE = float(opts['--minE']);
    maxX = float(opts['--maxX']);
    def f(frame):
        data=frame['data'];
        E   = (np.sqrt(data['ux']**2+data['uz']**2+1)-1)*0.511;
        return np.logical_and(E>minE, data['x'] < maxX);
    hashd = readfile(opts['--hash'],dumpfull=True);
    np.save(
        opts['<output>'],
        filter_hashes_from_file(opts['<input>'],hashd,f,
                                removedupes=True,
                                gzip=opts['--gzip']));
