'''
Useful functions for pext files.
'''
import numpy as np;
import itertools as itools;
import numpy.lib.recfunctions as rfn;

def add_quantities(d, coords=None, massE=0.511e6):
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
      massE  : rest mass energy of particles.
    Returns a copy with the quantities appended.
    '''
    keys,items = zip(*calc_quantities(d,coords=coords,massE=massE).items());
    return rfn.rec_append_fields(
        d, keys, items);

def calc_quantities(d, coords=None, massE=0.511e6):
    '''
    Calculate physically interesting quantities from pext

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
      massE  : rest mass energy of particles.
    Returns a dictionary of physical quantities.
    '''
    quants = dict();
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
        quants['phi']   = np.arctan2(d[coords[1]],d[coords[0]]);
    return quants;
