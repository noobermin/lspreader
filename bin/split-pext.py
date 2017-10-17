#!/usr/bin/env python
'''
Read in pext files from directories with restart runs and output a recarray.
Requires a .lsp file to be in the path, or to be passed.

Usage:
   simple-pext.py [options] <dirs>...

Options:
    --help -h                 This help.
    --lsp=L -L l              Read this .lsp file specifically.
    --late-time=TIME -l TIME  Cut out after this time.
    --reverse -r              Reverse Y and Z.
    --massE=ME                Rest energy of the particle. [default: 0.511e6]
    --verbose -v              Print verbose.
    --range=R -R R            Only restrict to this number range of pexts.
    --output=O -o O           Output to this file. Otherwise, reckon based on the
                              .lsp file name.
'''
from docopt import docopt;
from lspreader.lspreader import read_pext, get_header;
from lspreader.pext import add_quantities;
import numpy as np;
from pys import parse_ituple, mkvprint
import re;
from lspreader.dotlsp import getdim,getpexts
import os
import numpy.lib.recfunctions as rfn;
import gzip;

def _vprint(s):
    print(s);
opts = docopt(__doc__,help=True);
vprint = mkvprint(opts['--verbose']);

if opts['--lsp']:
    lspf=opts['--lsp'];
else:
    files = os.listdir('.');
    lspf=[f for f in files if re.search(".*\.lsp$",f)][0];
with open(lspf,"r") as f:
    lsp=f.read();
if not opts['--output']:
    outname = re.search("(.*)\.lsp$",lspf).group(1)+"-pext";
else:
    outname = opts['--output'];
dim=getdim(lsp);
pext_info = getpexts(lsp);

if opts['--range']:
    a=parse_ituple(opts['--range'],length=2);
    mnpext,mxpext = min(*a),max(*a);
else:
    mnpext,mxpext = float('-inf'),float('inf');
outkeys = set();
allkeys = [];
def getpextfnames(path):
    files = os.listdir(path);
    pext = [f for f in files if re.search("pext[0-9]+.p4",f)];
    key = [ float(re.search("pext([0-9]+).p4",f).group(1))
            for f in pext ];
    return [ ('{}/{}'.format(path,i),k) for i,k in zip(pext,key)
             if mnpext <= k <= mxpext];
dirs = [ i for path in opts['<dirs>'] for i in getpextfnames(path)];
keys = np.unique([ i[1] for i in dirs ]);
pextplanes = {k:[] for k in keys};
for d in enumerate(dirs):
    pextplanes[d[1]].append(d[0]);
    
def process_plane(paths, header, k):
    #invariant: the files should be in order they are passed.
    vprint('reading in files for {}'.format(k));
    d = [];
    for path in paths:
        openf = gzip.open if re.search(r'\.gz$', path) else open;
        with openf(path) as f:
            d.append(read_pext(f,header));
    d[:] = [
        rfn.rec_append_fields(
            di, 'species',
            np.ones(len(id)).astype(int)*pext_info[k]['species'])
        for di in d ];
    d = [ i for i in d if i['t'].shape[0] > 0];
    #make a mask of times less than the minimum of the next pexts
    #only take those in the previous run
    #only assign up to the last element of d.
    if len(d) > 1:
        d[:-1] = [ i[ i['t'] < j['t'].min() ] for i,j in zip(d[:-1],d[1:]) ];
    return d
vprint('');
d = [ di
      for paths,k in zip(pextplanes,keys)
      for di in process_plane(paths,k)   ];
if len(d) == 0:
    print("no pext data");
    quit();
d = np.concatenate(d);
latetime = float(opts['--late-time']) if opts['--late-time'] else None;
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
