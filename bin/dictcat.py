#!/usr/bin/env python2
'''
Concatenate dictionaries of numpy arrays, shape (1,) only.

Usage:
  dictcat.py [options] <input>...

Options:
  -o OUTPUT --output=OUTPUT         Output to OUTPUT instead of stdout.
'''
import cPickle as pickle;
import numpy as np;
from docopt import docopt;

opts = docopt(__doc__,help=True);
names = opts['<input>'];
d=[]
for name in names:
    with open(name) as f:
        d.append(pickle.load(f));
#making into lists
out = {k:np.concatenate([i[k] for i in d]) for k in d[0].keys()};
if opts['--output']:
    with open(opts['--output'],"wb") as f:
        pickle.dump(out,f,2);
    pass;
else:
    print(pickle.dumps(out,2));

