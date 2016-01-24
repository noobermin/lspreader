#!/usr/bin/env python2
'''
Gather found particles sorted by the filename's time. Assumes a 
form of .*([0-9]+).npy where the group is the step.

Usage:
    ./gather.py [options] <inputregex> <output>

Options:
    --help -h                 Print this help.
    --unique -u               Run unique on this and sort on the
                              constructed array.
    --intersect=I -i I        Perform intersection with this file.
    --axis=A -a A             Concatenate along this axis. [default: 0]
'''
from docopt import docopt;
import subprocess;
import re;
import numpy as np;
def call(cmd):
    return subprocess.check_output(cmd).split('\n');
def lsdir(dir='.'):
    return call(('ls',dir));

def lsgrep(rx,dir='.',order=None):
    rx = re.compile(rx);
    files = [file for file in lsdir(dir)
             if rx.match(file)];
    return files;

if __name__ == "__main__":
    opts=docopt(__doc__,help=True);
    files=lsgrep(opts['<inputregex>'])
    cataxis = int(opts['--axis']);
    arrays = [np.load(file) for file in files];
    good   = np.concatenate(arrays,axis=cataxis);
    if opts['--unique']:
        good = np.unique(good);
        good.sort();
    if opts['--intersect']:
        intersect = np.load(opts['--intersect']);
        good = np.intersect1d(good,intersect);
    np.save(opts['<output>'],good);
