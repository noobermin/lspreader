#!/usr/bin/env python
'''
Search a p4 for good indices. This imports the file specified by
the modulepath option, reads a function called "f" from it,
and filters the frames using it. Outputs a numpy array of
good trajectories.

Usage:
    ./search.py [options] <input> <hashd> <output>

Options:
    --help -h                    Print this help.
    --modulepath=M               Set the path to the file to read "f"
                                 from. [default: ./scanner.py]
'''
from lspreader import read;
from pys import load_pickle;
from lspreader.pmovie import filter_hashes_from_file;
import numpy as np;
import re;
import imp;
if __name__ == "__main__":
    from docopt import docopt;
    opts=docopt(__doc__,help=True);
    fname = opts['--modulepath'];
    m=re.search(r'(^.*)/(\w+)\.py$', fname);
    if not m:
        raise ValueError("module should be well named!");
    path =m.group(1);
    mname=m.group(2);
    fp, path,desc = imp.find_module(mname, [path]);
    try:
        f=imp.load_module(mname, fp, path, desc).f
    finally:
        if fp:
            fp.close();
    hashd = load_pickle(opts['<hashd>']);
    np.save(
        opts['<output>'],
        filter_hashes_from_file(opts['<input>'], f, **hashd));

