#!/usr/bin/env python2
'''
Plot the angular/energy/charge plot.

Usage:
  angular.py [options] <input> <output>
  angular.py [options] <input>

Options:
  --angle-bins=BINS -a BINS   Set the number of angle bins.  [default: 180]
  --radial-bins=BINS -r BINS  Set the number of radial bins. [default: 40]
  --title=TITLE -t Title      Set the title.
  --clabel=CLABEL             Set colorbar label.
  --KeV                       Scale by 100s of KeV instead of MeV.
  --max-E=MAXE                Set the maximum energy value (in units depending on --KeV flag)
  --E-step=ESTEP              Set the step of grid lines for Energy.
  --high-res -H               Output a high resolution plt.
  --max-Q=MAXQ                Set the maximum for the charge (pcolormesh's vmax value).
  --normalize                 Normalize the histogram to 1 *eV^-1 rad^-1 .
  --factor=F                  Multiply histogram by F. [default: 1.0]
  --polar                     Plot polar angles, letting the east direction be forward.
'''
import numpy as np;
import matplotlib.pyplot as plt;
import cPickle as pickle;
from matplotlib import colors;
from docopt import docopt;
import math as m;
from misc import conv;
def mk_cmap():
    hsv = np.array([[[0.00, 0.6, 1.0],
                     [0.10, 0.6, 1.0],
                     [0.20, 0.6, 1.0],
                     [0.30, 0.6, 1.0],
                     [0.40, 0.6, 1.0],
                     [0.50, 0.6, 1.0],
                     [0.60, 0.6, 1.0],
                     [0.70, 0.6, 1.0],
                     [0.80, 0.6, 1.0]]]);
    rgb = colors.hsv_to_rgb(hsv);
    def mk_component(cmp):
        l = len(cmp);
        inter = np.linspace(0.001,1.0,l);
        ret = [[i,j,j]  for i,j in zip(inter,cmp)];
        ret[0][1]=1.0;
        ret = [[0.0,1.0,1.0]]+ret;
        return tuple(ret);
    r = np.array(mk_component(rgb.T[0]));
    g = np.array(mk_component(rgb.T[1]));
    b = np.array(mk_component(rgb.T[2]));
    cd={'red':r,'green':g,'blue':b};
    return colors.LinearSegmentedColormap('cmap',cd, 1024);

def main():
    opts = docopt(__doc__,help=True);
    inname = opts['<input>'];
    outname = opts['<output>'];
    phi_spacing = float(opts['--angle-bins']);
    E_spacing = float(opts['--radial-bins']);
    clabel = opts['--clabel'] if opts['--clabel'] else '$p C$';
    maxE = conv(opts['--max-E'],default=(400 if opts['--KeV'] else 4.0),func=float);
    maxQ = float(opts['--max-Q']) if opts['--max-Q'] else None;
    Estep = conv(opts['--E-step'],default=(100 if opts['--KeV'] else 1.0),func=float);
    F = float(opts['--factor']);
    with open(inname,'r') as f:
        d = pickle.load(f)
    e = d['KE'];
    if opts['--KeV']:
        e/=1e3;
    else:
        e/=1e6;
    s =-d['q']*1e6*F;
    if opts['--polar']:
        m = ((-np.pi/2 <= d['phi'] )& (d['phi'] <= np.pi/2)).astype(int)*2 - 1 #black magic
        phi = m*d['theta'];
        plt.hist(phi,bins=100,label='foo');
        plt.legend();
        plt.show();
    else:
        phi = d['phi'];
    phi_bins = np.linspace(min(phi),max(phi),phi_spacing+1);
    E_bins   = np.linspace(0, maxE, E_spacing+1);
    PHI,E = np.mgrid[ min(phi) : max(phi) : phi_spacing*1j,
                      0 : maxE : E_spacing*1j];
    S,_,_ = np.histogram2d(phi,e,bins=(phi_bins,E_bins),weights=s);
    if opts['--normalize']:
        Efactor = maxE/E_spacing;
        if opts['--KeV']:
            Efactor *= 1e-3;
        S /= Efactor * 2*np.pi/phi_spacing;
    fig = plt.figure(1);
    ax=plt.subplot(projection='polar',axisbg='white');
    surf=plt.pcolormesh(PHI,E,S,cmap=mk_cmap(),vmax=maxQ);
    #making radial guides. rgrids only works for plt.polar calls
    full_phi = np.linspace(0.0,2*np.pi,100);
    for i in np.arange(0.0,maxE,Estep)[1:]:
        plt.plot(full_phi,np.ones(full_phi.shape)*i,c='gray', lw=1, ls='--');
    ax.set_theta_zero_location('N');
    unit = 'KeV' if opts['--KeV'] else 'MeV';
    label_str = '{} '+unit;
    labels    = np.arange(0.0,maxE,Estep)[1:];
    plt.rgrids(labels,labels=map(label_str.format,labels),angle=350);
    ax.set_xticklabels(['Forward\n0$^{\circ}$',
                        '45$^{\circ}$',
                        'Left\n90$^{\circ}$',
                        '135$^{\circ}$',
                        'Backwards\n180$^{\circ}$',
                        '215$^{\circ}$',
                        'Right\n270$^{\circ}$',
                        '315$^{\circ}$']);
    c=fig.colorbar(surf,pad=0.075);
    c.set_label(clabel);
    if opts['--title']:
        plt.title(opts['--title'],loc='left',fontdict={'fontsize':28});
    if outname:
        if opts['--high-res']:
            plt.savefig(outname,dpi=1000);
        else:
            plt.savefig(outname);
    else:
        plt.show();
    pass;

if __name__ == "__main__":
    main();
