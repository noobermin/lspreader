#!/usr/bin/env python2
'''
Output the efficiency of a sim from a pext.py output.
All units are SI.

Usage:
  quantities.py [options] <input>

Options:
  --2D -2                    Calculate 2D quantities instead.
  --E-cut=ECUT -e ECUT       Cutoff at this energy in MeV. [default: 0.0]
  --E_0=E0 -E E0             Enter the peak electric field in V/m. [default: 4.763e12]
  --W=SPOTSIZE -w SPOTSIZE   Set the spotsize meters. [default: 2.26e-6]
  --T=FWHM -t FWHM           Set the Full-Width Half-Max in seconds. [default: 30e-15]
  --angle=ANGLE -a ANGLE     Restrict the angle. In 2D, this is just phi; in 3D, it is solid angle.
'''
import numpy as np;

e_0 = 8.85418782e-12;
c = 2.99792458e8;
e = 1.60217657e-19


def totalKE(d, ecut=0, anglecut=None,return_bools=False):
    '''
    Get total energy across a pext plane.

    Parameters and Keywords
    -----------------------
    d            -- array
    ecut         -- energy cut in eV
    anglecut     -- None or a tuple of (angle, dimension) where dimension
                    is "2D" or "3D". If None or falsey, don't cut on angle.
    return_bools -- return the boolean array that selects uncut particles.

    Returns total energy.
    '''
    good = d['KE'] > ecut;
    if anglecut:
        angle, dim = anglecut;
        if dim == '2D':
            good &= np.abs(d['phi']) > np.pi - angle/180*np.pi;
        elif dim == '3D':
            good &= np.cos(angle/180*np.pi) < -np.sin(d['theta'])*np.cos(d['phi']);
        else:
            raise ValueError("anglecut is not None, '2D' or '3D'");
    KE = (np.abs(d['q'][good]*1e-6)*d['KE'][good]).sum();
    if return_bools:
        return KE,good;
    else:
        return KE;
    
def laserE(E_0, T, w,dim="3D"):
    '''
    Get total energy in a Gaussian Laser.
    

    Parameters and Keywords
    -----------------------
    E_0   -- Peak E field.
    T     -- FWHM of the pulse.
    w     -- Spotsize.
    dim   -- Spatial dimension, either "2D", or "3D" or None for "3D"

    Returns laser energy.
    '''

    if dim == "2D":
        return w * np.sqrt(np.pi/2) * (c*e_0*E_0**2)/2 * T*1e-2;
    elif not dim or dim == "3D":
        return w**2 * (np.pi/2) * (c*e_0*E_0**2)/2 * T;
    else:
        raise ValueError("dim is not None, '2D' or '3D'");

if __name__ == "__main__":
    from docopt import docopt;
    opts = docopt(__doc__,help=True);
    E_0 = float(opts['--E_0']);
    ecut = float(opts['--E-cut'])*1e6;
    w    = float(opts['--W']);
    T    = float(opts['--T']);
    d = np.load(opts['<input>'],allow_pickle=True);

    dim  = "2D" if opts['--2D'] else "3D";
    if opts['--angle']:
        angle = float(opts['--angle']);
        angleopt = (angle,dim);
    else:
        angleopt = None;
    KE, good = totalKE(d, ecut, angleopt, return_bools=True);
    LE = laserE(E_0, T, w, dim=dim);
    totalq = d['q'][good].sum()*1e12;
    print('total charge: {} {}'.format(totalq,'pC/cm' if opts['--2D'] else 'pC'));
    print("total energy: {} J".format(KE));
    print('pulse energy: {} J'.format(LE));
    print('efficiency is {}'.format(KE/LE));

