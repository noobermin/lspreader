#!/usr/bin/env python2
'''
Read in pext files from a path with no restart run and output a recarray.
Requires a .lsp file to be in the path, or to be passed. If <output> is
not passed, determine the name from the .lsp name.

Usage:
   simple-pext.py [options] [<output>]

Options:
    --help -h                 This help.
    --lsp=L -L l              Read this .lsp file specifically.
    --late-time=TIME -l TIME  Cut out after this time.
    --reverse -r              Reverse Y and Z.
    --massE=ME                Rest energy of the particle. [default: 0.511e6]
    --verbose -v              Print verbose.
    --range=R -R R            Only restrict to this number range of pexts.
    --path=P -P P             Specify a path instead of the cwd. [default: .]
'''
from docopt import docopt;
from lspreader import lspreader as rd;
from lspreader.pext import add_quantities;
import numpy as np;
from pys import parse_ituple;
import re;
from lspreader.dotlsp import getdim,getpexts
import os
import numpy.lib.recfunctions as rfn;

def _vprint(s):
    print(s);
opts = docopt(__doc__,help=True);
vprint = _vprint if opts['--verbose'] else  (lambda s: None);
path = opts['--path'];

files = os.listdir(path);
pext = [f for f in files if re.search("pext[0-9]+.p4",f)];
if opts['--range']:
    a=parse_ituple(opts['--range'],length=2);
    mn,mx = min(*a),max(*a);
else:
    mn,mx = float('-inf'),float('inf');
key = [ float(re.search("pext([0-9]+).p4",f).group(1))
        for f in pext ];
pext,key = zip(*[
    (i,k) for i,k in zip(pext,key)
    if mn <= k <= mx]);
if opts['--lsp']:
    lspf=opts['--lsp'];
else:
    lspf=[f for f in files if re.search(".*\.lsp$",f)][0];
with open(lspf,"r") as f:
    lsp=f.read();
if not opts['<output>']:
    outname = re.search("(.*)\.lsp$",lspf).group(1)+"-pext";
else:
    outname = opts['<output>'];
dim=getdim(lsp);
pexts = getpexts(lsp);
latetime = float(opts['--late-time']) if opts['--late-time'] else None;
vprint('reading in files');
d = [ rd.read(name)
      for name in pext ];

d[:] = [
    rfn.rec_append_fields(
        id, 'species',
        np.ones(len(id)).astype(int)*pexts[i]['species'])
    for id,i in zip(d,key) ];
vprint('length of d={}'.format(len(d)));

d = [ i for i in d if i['t'].shape[0] > 0];
vprint('length of d={} after remove empties'.format(len(d)));
vprint('cutting out duplicate times');
if len(d) > 1:
    d = np.concatenate(d);
elif d == []:
    print("empty pext");
    quit();
else:
    d = d[0];
vprint('sorting by times')
d.sort(order='t');
if latetime:
    print('cutting out times greater than {}'.format(latetime));
    d = d[ d['t'] <= latetime ];
#calculating quantities
if opts['--reverse']:
    dim = dim[:-2] + list(reversed(dim[-2:]))
massE = float(opts['--massE']) if opts['--massE'] else None;
d = add_quantities(d, dim, massE=massE);
np.save(outname, d);
