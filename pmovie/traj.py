#!/usr/bin/env python2
'''
Make found timesteps into trajectories.

Usage:
    ./traj.py [options] <inputregex> <output>

Options:
    --help -h                 Print this help.
'''
from docopt import docopt;
opts=docopt(__doc__,help=True);
import subprocess;
from gather import lsgrep;
import numpy as np;

files = lsgrep(opts['<inputregex>']);
def load(file):
    with np.load(file) as f:
        d,t=f['data'],f['time'][()]
    return d,t;
arrays = [load(file) for file in files];
data = np.array([arr[0] for arr in arrays]);
time = np.array([arr[1] for arr in arrays]);
s=np.argsort(time);
data=data[s];
time=time[s];
np.savez(opts['<output>'],data=data,time=time);
