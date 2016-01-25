#!/usr/bin/env python2
'''
Select values of dict of a numpy arrays, shape (1,) only based on a range
(python tuple), range is inclusive (excluding is open).

Usage:
  dictrestrict.py [options] <input> <var> <range>

Options:
  --output=OUTPUT -o OUTPUT    Output to OUTPUT instead of stdout.
  --exclude -x                 Exclude range instead of including it.    
'''
import cPickle as pickle;
import numpy as np;
from docopt import docopt;

opts = docopt(__doc__,help=True);
name = opts['<input>'];
var  = opts['<var>'];
r    = eval(opts['<range>']);
with open(name) as f:
    d=pickle.load(f);
good = (d[var] >= r[0]) & (d[var] <= r[1])
if opts['--exclude']:
    good = np.logical_not(good);
#removing
for k in d.keys():
    d[k] = d[k][good];
if opts['--output']:
    with open(opts['--output'],"wb") as f:
        pickle.dump(d,f,2);
    pass;
else:
    print(pickle.dumps(d,2));

