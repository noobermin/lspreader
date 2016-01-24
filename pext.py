#!/usr/bin/env python2
'''
Read in pext files and output a dict. Assumes that the names
are in order of the restart files. It still isn't general enough
for any setup (which axes  you want for the angles you want
to measure phi and theta wrt). Currently, it works for angle
wrt -x for 3d and -x for 2d.

Usage:
    pext.py [options] <output> <names>...

Options:
    --X -x                    Use X.
    --Y -y                    Use Y.
    --Z -z                    Use Z.
    --late-time=TIME -l TIME  Cut out after this time.
    --reverse -r              Reverse Y and Z.
    --massE=ME                Rest energy of the particle.
    --verbose -v              Print verbose.
    --dict -d                 Output a dict instead of a recarray.
'''
import lspreader as rd;
import numpy as np;
import itertools as itools;
import numpy.lib.recfunctions as rfn;

massE = 0.511e6;


def _vprint(s):
    print(s);

def add_quantities(d, coords=None):
    '''
    Add physically interesting quantities to
    pext data.

    Parameters:
    -----------
      d      : pext array

    Keywords:
    ---------
      coords : sequence of positions for angle calculation. None
               or by default, calculate no angles.
               For 2D, takes the angle depending on the order passed,
               so this can be used for left-handed coordinate systems
               like LSP's xz.

    Returns a copy with the quantities appended.
    '''
    quants = {}
    quants['u_norm'] = np.sqrt(d['ux']**2+d['uy']**2+d['uz']**2)
    quants['KE']     =(np.sqrt(quants['u_norm']**2+1)-1)*massE;
    coords[:] = ['u'+coord for coord in coords];
    if not coords:
        pass;
    elif len(coords) == 3:
        quants['theta'] = np.arccos(d[coords[2]]/quants['u_norm']);
        quants['phi']   = np.arctan2(d[coords[1]],d[coords[0]]);
        quants['phi_n'] = np.arctan2(d[coords[2]],d[coords[0]]);
    elif len(coords) == 2:
        quants['phi']   = np.arctan2(d[coords[0]],d[coords[1]]);
    keys,items = zip(*quants.items());
    return rfn.rec_append_fields(
        d, keys, items);

def main():
    from docopt import docopt;
    opts = docopt(__doc__,help=True);
    vprint = _vprint if opts['--verbose'] else  (lambda s: None);
    outname = opts['<output>']
    names = opts['<names>'];
    coords = {'x':opts['--X'],'y':opts['--Y'],'z':opts['--Z']};
    num_of_coords = len([i for i in coords.values() if i]);
    latetime = float(opts['--late-time']) if opts['--late-time'] else None;
    if num_of_coords==0:
        num_of_coords=3;
    vprint('reading in files');
    d = [ rd.read(name)
          for name in names ];
    vprint('length of d={}'.format(len(d)));
    if opts['--verbose']:
        vprint("printing d's");
        for i in d:
            vprint(i['t'].shape[0]);
    d = [ i for i in d if i['t'].shape[0] > 0];
    vprint('length of d={} after remove empties'.format(len(d)));
    vprint('cutting out duplicate times');
    #make a mask of times less than the minimum of the next pexts
    #only take those in the previous run
    #only assign up to the last element of d.
    d[:-1] = [i[ i['t'] < j['t'].min() ] for i,j in zip(d[:-1],d[1:])]
    if len(d) > 1:
        d = np.concatenate(d);
    else:
        d=d[0];
    if latetime:
        print('cutting out times greater than {}'.format(latetime));
        d = d[ d['t'] <= latetime ];
    #calculating quantities
    if num_of_coords == 2:
        #notice this only does x-y, y-z, and inverts the first.
        x = 'x' if opts['--X'] else 'y';
        y = 'y' if opts['--Y'] else 'z';
        coords = [x,y]
        if opts['--reverse']:
            coords.reverse();
    elif num_of_coords ==3:
        if opts['--reverse']:
            coords = ['x','z','y'];
        else:
            coords = ['x','y','z'];
    d = add_quantities(d, coords);
    if opts['--dict']:
        d = {k:d[k] for k in d.dtype.names};
        from misc import dump_pickle;
        dump_pickle(outname, d);
    else:
        np.save(outname, d);

if __name__ == '__main__':
    main();
