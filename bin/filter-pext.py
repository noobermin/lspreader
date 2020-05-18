#!/usr/bin/env python
'''
Simple script for basic filtering of particle extraction files, using
lspreader.dump_pext on the backend, but offered as convienience for simple
cases, for example, removing particles after a certain time for restarting
gracefully.

Usage:
    ./filter-pext.py [options] <input> <output>

Options:
    -h --help               Help.
    -v --verbose            Make verbose.
    -O --overwrite          By default, this script does NOT clobber. This option
                            allows overwriting the output file even if it exists.
                            For now, it seems it is save to overwrite the input file
                            but this may change in the future.

Filtering options.

All options are logically and'ed together, and thus form the intersection
of all specified options to the command.
    -t R --time-range=R     Include particles within this time range, as a
                            tuple of times in lsp units (usually nanoseconds).
                            For example, "(0,1e-5)" means between 0 and 10 fs.
    -x R --x-restrict=X     Restrict by these dimensions, that iz, z,y,x values.
                            Six-tuple of (zmin,zmax,ymin,ymax,xmin,xmax) in lsp
                            units (usually cm). For 
                            example: "(-1e-4,1e-4,-1e-4,1e-4,-1e-4,1e-4)" for a 
                            cube 2 microns wide on each side centered at the origin.
'''
from lspreader import read;
from lspreader.lspreader import get_header;
from lspreader.p4writer import dump_pext, dump_header;
from docopt import docopt;
from pys import parse_ftuple, choose_autovp;
import numpy as np;
import os.path
opts = docopt(__doc__,help=True);

vprint = choose_autovp(opts['--verbose']);
fname   = opts['<input>'];
outname = opts['<output>'];
if os.path.isfile(outname) and not opts['--overwrite']:
    raise ValueError(
        "file {} exists and --overwrite not specified".format(outname));

vprint("loading {}".format(fname));
d = read(fname);
hd  = get_header(fname);
lb = len(d);
if opts['--time-range']:
    tr = parse_ftuple(opts['--time-range'],length=2);
    vprint("filtering time with range {}".format(tr));
    g = np.logical_and(tr[0] <= d['t'], d['t'] <= tr[1]);
    d = d[g];

if opts['--x-restrict']:
    res = parse_ftuple(opts['--x-restrict'],length=6);
    zr,yr,xr = np.array(res).reshape(3,2);
    g = np.logical_and(zr[0] <= d['z'], d['z'] <=zr[1]);
    g&= np.logical_and(yr[0] <= d['y'], d['y'] <=yr[1]);
    g&= np.logical_and(xr[0] <= d['x'], d['x'] <=xr[1]);
    d = d[g];
vprint("before filter to after, len(d): {} -> {}".format(lb,len(d)));
vprint("outputting to {}".format(outname))
with open(outname, 'wb+') as f:
    dump_header(f,hd);
    dump_pext(f,d);


