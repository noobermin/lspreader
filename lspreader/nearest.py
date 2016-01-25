
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
My very own nearest interpolation for the sake of making uniform grids
'''

def nearest_indices(xs, XS):
    '''
    Returns indices that perform nearest interpolation given a
    set of points. Similar to scipy.interpolate.griddata with
    method set to "nearest". In fact, it's construction is based
    on that function and related types.

    Parameters:
    -----------

    xs -- ndarray of floats, shape (n,D)
          Data point coordinates. Can either be an array of
          shape (n,D), or a tuple of `ndim` arrays.
    XS -- ndarray of floats, shape (M, D)
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

    Parameters:
    -----------

    xs  -- A collection of `ndim` arrays of points.
    res -- List of resolutions.
    '''
    maxs = [max(a) for a in xs]
    mins = [min(a) for a in xs]
    XS = [np.linspace(mn, mx, r) for mn,mx,r in zip(mins,maxs,res)];
    XS = tuple(np.meshgrid(*XS,indexing='ij'));
    if type(xs) != tuple:
        xs = tuple(xs);
    return nearest_indices(xs,XS);
