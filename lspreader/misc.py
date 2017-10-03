'''
Miscellaneous shared definitions.
'''
try:
    import cPickle as pickle;
except ImportError:
    import pickle
import numpy as np;
from matplotlib import colors;
import h5py as h5;
import subprocess;

def conv(arg,default=None,func=None):
    if func:
        return func(arg) if arg else default;
    else:
        return arg if arg else default;

test = lambda d,k: k in d and d[k];

def readfile(filename, stuff='s',
             dumpfull=False,hdf=False,
             group=None):
    if hdf:
        with h5.File(filename, "r") as f:
            if group:
                g=f[group];
            else:
                g=f;
            if not stuff or dumpfull:
                d={l:np.array(g[l]) for l in g.keys()};
            elif type(stuff) == str:
                d = np.array(g[stuff]);
            else:
                d={l:np.array(g[l]) for l in stuff};
    else:
        with open(filename, "rb") as f:
            d=pickle.load(f);
        if not stuff or dumpfull:
            pass
        elif type(stuff) == str:
            d = d[stuff];
        else:
            d={l:d[l] for l in stuff};
    return d;

def dump_pickle(name, obj):
    with open(name,"wb") as f:
        pickle.dump(obj,f,2);
    pass;

def chunks(l,n):
    #http://stackoverflow.com/a/3226719
    #...not that this is hard to understand.
    return [l[x:x+n] for x in xrange(0, len(l), n)];

def check_vprint(s, vprinter):
    if vprinter is True:
        print(s);
    elif callable(vprinter):
        vprinter(s);

def mkvprint(opts):
    return lambda s: check_vprint(s,opts['--verbose']);

 
def h5w(file,d,group='/',compression=None):
    if type(file) == str:
        with h5.File(file, 'a') as f:
            h5w(f,d,group=group,
                compression=compression);
            return;
    if group not in file:
        file.create_group(group);
    group = file[group];
    for k in d:
        if k in group: del group[k];
        if type(d[k]) != np.ndarray:
            cmp = None;
        else:
            cmp = compression;
        group.create_dataset(
            k, data=d[k],  compression=cmp)
    pass;

def subcall(cmd):
    return subprocess.check_output(cmd).split('\n');

def filelines(fname,strip=False):
    with open(fname,'r') as f:
        lines = f.readlines();
    if strip:
        lines[:] = [line.strip() for line in lines]
    return lines;
