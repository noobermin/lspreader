#!/usr/bin/env python2
'''
Usage:
    ./track.py <fldsrx> <sclrrx>

Options:
    --help -h
    --track=T -t T     Specify track file.
    --numrx=N -n N     The regex for numbers. [default: ([0-9]+).p4 ]
'''
from docopt import docopt;
from .. import flds,misc,lspreader;
import re;
import numpy as np;
import matplotlib.pyplot as plt;
files=subcall(('ls'))
fldsrx=re.compile(opts['<fldsrx>']);
sclrrx=re.compile(opts['<sclrrx>']);
numrx=re.compile(opts['--numrx']);
flds = [file for file in files
         if fldsrx.match(file) ];
sclr = [file for file in files
         if sclrrx.match(file) ];
nums = [numrx.match(file).group(1)
        for file in files
        if numrx.match(file) ];
s=np.argsort(nums);
flds[:] = np.array(flds)[s];
sclr[:] = np.array(sclr)[s];
tracksf=np.load(opts['--track']);
tracks    = tracksf['data'];
tracktime = tracksf['time'];

flabels = ['Ex','Ey','Ez','Bx','By','Bz'];
slabels = ['RhoN{}'.format(i) for i in range(1,12)];
for i,(ff,sf,t) in enumerate(zip(flds,sclr,tracktime)):
    print("reading {} and {}".format(ff,sf));
    fd=lspreader.read(ff,var=flabels,
                      gzip=True, remove_edges=True);
    sd=lspreader.read(sf,var=slabels,
                      gzip=True, remove_edges=True);
    if i == 0:
        s = np.lexsort((fd['z'],fd['y'],fd['x']));
    fd = flds.rect_flds(fd,s);
    sd = flds.rect_flds(sd,s);
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
    np.savez_compressed('data{}'.format(i),**out);
    print("saved");

