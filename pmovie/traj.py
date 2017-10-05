#!/usr/bin/env python2
'''
Make found timesteps into trajectories.

Usage:
    ./traj.py [options] <output> <input>...

Options:
    --help -h       Print this help.
    --sort -s       Sort by time.
    --new -n        New npz format, in which each particle has its own file.
'''
from docopt import docopt;
import numpy as np;
opts=docopt(__doc__,help=True);

files = opts['<input>']
def load(file):
    with np.load(file) as f:
        d,t=f['data'],f['time'][()]
    return d,t;
arrays = [load(file) for file in files];
data = np.array([arr[0] for arr in arrays]);
time = np.array([arr[1] for arr in arrays]);
if opts['--sort']:
    s=np.argsort(time);
    data=data[s];
    time=time[s];
if not opts['--new']:
    np.savez(opts['<output>'],data=data,time=time);
else:
    ps = data.shape[1];
    sz=len('{}'.format(ps));
    fmt = '{{:0{}}}'.format(sz);
    out={fmt.format(i) : data[:,i] for i in xrange(ps) };
    out['time'] = time;
    np.savez(opts['<output>'],**out);
