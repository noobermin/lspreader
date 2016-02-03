#!/usr/bin/env python2
'''
Search a p4 for good indices. This imports a file called
scanner from the current directory, reads a function called "f"
and runs this on each frame. It should return a numpy array of
good trajectories.

Usage:
    ./search.py [options] <input> <output>

Options:
    --help -h                    Print this help.
    --hash=HASHFILE -H HASHFILE  Read this hash file.
    --gzip -Z                    Read gzipped files.
'''
from lspreader import read;
from lspreader.pmovie import addhash, filter_hashes_from_file;
from lspreader.misc import readfile;
import numpy as np;

#expects a "scanner.py" file in the same directory
#
from scanner import f;
if __name__ == "__main__":
    from docopt import docopt;
    opts=docopt(__doc__,help=True);
    hashd = readfile(opts['--hash'],dumpfull=True);
    np.save(
        opts['<output>'],
        filter_hashes_from_file(opts['<input>'],hashd,f,
                                removedupes=True,
                                gzip=opts['--gzip']));
