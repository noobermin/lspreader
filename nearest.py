#!/usr/bin/env python2

# Copyright (c) 2015, 2016 Gregory K. Ngirmang
# All rights reserved.
#
# Copyright (C)  Pauli Virtanen, 2010.
# All rights reserved.
#
# Copyright (c) 2001, 2002 Enthought, Inc.
# All rights reserved.
#
# Copyright (c) 2003-2012 SciPy Developers.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of Enthought nor the names of the SciPy Developers
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.

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

import lspreader as rd;
import numpy as np;
import matplotlib.pyplot as plt;
from scipy.spatial import cKDTree;
from scipy.interpolate.interpnd import _ndim_coords_from_arrays,NDInterpolatorBase;
from time import time;

def nearest_indices(xs, XS):
    '''
    Returns indices that perform nearest interpolation given a
    set of points. Similar to scipy.interpolate.griddata with
    method set to "nearest". In fact, it's construction is based
    on that function and related types.

    Parameters
    ----------

    xs : ndarray of floats, shape (n,D)
        Data point coordinates. Can either be an array of
        shape (n,D), or a tuple of `ndim` arrays.
    XS : ndarray of floats, shape (M, D)
        Points at which to interpolate/sample data.
    '''
    xs=_ndim_coords_from_arrays(xs);
    XS = _ndim_coords_from_arrays(XS, ndim=xs.shape[1])
    if XS.shape[-1] != xs.shape[1]:
        raise ValueError("dimensions of the points don't the sample points")
    #the magical kd-tree
    _,i = cKDTree(xs).query(XS)
    return i;

def simple_nearest_indices(xs,res):
    '''
    Simple nearest interpolator that interpolates based on
    the minima and maxima of points based on the passed
    resolution in res.

    Parameters
    ----------

    xs : A collection of `ndim` arrays of points.
    res: List of resolutions.
    '''
    maxs = [max(a) for a in xs]
    mins = [min(a) for a in xs]
    XS = [np.linspace(mn, mx, r) for mn,mx,r in zip(mins,maxs,res)];
    XS = tuple(np.meshgrid(*XS,indexing='ij'));
    if type(xs) != tuple:
        xs = tuple(xs);
    return nearest_indices(xs,XS);
    
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

