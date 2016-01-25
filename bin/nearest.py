#!/usr/bin/env python2

'''
Interpolate something. Without an output file, interpolate in place.
There is the option of generating nearest interpolation sample files
and reusing these index files to save time on sample further files.
I intend to include this sampling in pbs scripts so that they sample
the first time step once, and then perform what I hope is a constant
time construction for later files. See the --gen-samples and --sample
options.

Usage:
  interp.py [options] <input> [<output> [<var>...]]
  interp.py [options] [--gen-samples | -G ] <input> <output>

Options:
  -h --help                   Show this help.
  -v --verbose                Turn on verbosity.
  -x --X                      Use X in interpolation.
  -y --Y                      Use Y in interpolation.
  -z --Z                      Use Z in interpolation.
  --xres=XRES                 Set the resolution along the x direction [default: 100].
  --yres=XRES                 Set the resolution along the y direction [default: 100].
  --zres=XRES                 Set the resolution along the z direction [default: 100].
  --permute -p                Swap the order of axes for 2D data.
  --gen-samples -G            Instead of interpolating, generate a sample file
                              and output to <output>.
  --sample=S -s S             Load the sample file S and use these indices to sample
                              the input file to create a interpolated file.
  --zip -z                    Compress for hdf5.
'''

from lspreader import lspreader as rd;
from lspreader.nearest import simple_nearest_indices;
import numpy as np;
import matplotlib.pyplot as plt;
from scipy.spatial import cKDTree;
from scipy.interpolate.interpnd import _ndim_coords_from_arrays,NDInterpolatorBase;
from time import time;
def handle_dims(opts):
    '''
    Script option handling.
    '''
    use,res = [],[];
    if opts['--X']:
        use.append('x');
        res.append(int(opts['--xres']));
    if opts['--Y']:
        use.append('y');
        res.append(int(opts['--yres']));
    if opts['--Z']:
        use.append('z');
        res.append(int(opts['--zres']));
    if use == []:
        use = ['x','y','z'];
        res = map(lambda k: int(opts[k]),['--xres','--yres','--zres']);
    # A couple of things to note; written in this way, whatever
    # this list (and thus, what is read) becomes, it is ordered
    # alphabetically. This is important, as this determines what
    # each resulting row and column and breadth in the output
    # array corresponds to from the actual simulation.
    #
    # It is probably worth mentioning that the xz in simulation
    # axes will be [0,1] in numpy axes, that is, it will be left-handed.
    # Using xz leads to this anyway, but it's worth reminding the reader.
    # To permute in 2D, use the --permute flag.
    return use,res;
if __name__ == "__main__":
    from docopt import docopt;
    from misc import readfile, mkvprint, dump_pickle;
    opts=docopt(__doc__,help=True);
    dims,res = handle_dims(opts);
    vprint = mkvprint;
    var = opts['<var>'];
    readvars = list(var);
    if readvars:
        readvars+=dims;
    if opts['--gen-samples']:
        xs = tuple([d[l] for l in dims]);
        i = simple_nearest_indices(xs,res);
        dump_pickle(opts["<output>"],(i,xs));
        exit(1);
    if opts['--sample']:
        i,xs = readfile(opts['--sample'], dumpfull=True);
    else:
        xs = tuple([d[l] for l in dims]);
        i = simple_nearest_indices(xs,res);
    did = {v:d[v][i] for v in var};
    #Has _D_ been _I_nterpolate_D_?  Yes it DID.
    did.update({l:x for l,x in zip(dims,xs)});
    #get it?
    #alright I'll stop
    dump_pickle(opts['<output>'], did);

