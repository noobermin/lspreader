#!/usr/bin/env python2
'''
Basic, slow, sequential script for reading tracks and field data together.

Usage:
    ./track.py [options]

Options:
    --help -h
    --track=T -t T     Specify track file.
    --numrx=N -n N     The regex for numbers in flds. [default: flds([0-9]+).p4]
    --fldsrx=R -f R    The regex for numbers in flds. [default: flds.*.p4.gz]
    --sclrrx=R -s R    The regex for numbers in sclr. [default: sclr.*.p4.gz]
'''
from docopt import docopt;
from lspreader import flds,misc
from lspreader import read;
import re;
import numpy as np;
import matplotlib.pyplot as plt;
opts = docopt(__doc__,help=True);
files=misc.subcall(('ls'))
fldsrx=re.compile(opts['--fldsrx']);
sclrrx=re.compile(opts['--sclrrx']);
numrx=re.compile(opts['--numrx']);
ffs = [file for file in files
       if fldsrx.match(file) ];
sfs = [file for file in files
       if sclrrx.match(file) ];
nums = [int(numrx.match(file).group(1))
        for file in ffs
        if numrx.match(file) ];
s=np.argsort(nums);
ffs[:] = np.array(ffs)[s];
sfs[:] = np.array(sfs)[s];
tracksf=np.load(opts['--track']);
tracks    = tracksf['data'];
tracktime = tracksf['time'];
flabels = ['Ex','Ey','Ez','Bx','By','Bz'];
slabels = ['RhoN{}'.format(i) for i in range(1,12)];
for i,(ff,sf,t) in enumerate(zip(ffs,sfs,tracktime)):
    print("reading {} and {}".format(ff,sf));
    fd=read(ff,var=flabels,
            gzip=True, remove_edges=True);
    sd=read(sf,var=slabels,
            gzip=True, remove_edges=True);
    if i == 0:
        srt = flds.firstsort(fd);
    fd = flds.sort(fd,srt);
    sd = flds.sort(sd,srt);
    td=tracks[:i]
    out = {sl:sd[sl] for sl in slabels};
    out.update(
        {fl:fd[fl] for fl in flabels});
    out.update(
        {'x':sd['x'],'y':sd['y'],'z':sd['z']});
    out.update(
        {'tracks':td});
    out.update(
        {'time':t });
    np.savez_compressed('/home/ngirmang.1/fasttmp/data{}'.format(i),**out);
    

