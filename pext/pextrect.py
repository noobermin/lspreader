#!/usr/bin/env python2
'''
Plot a charge vs. two other components, x and y of a pext.py output.

Usage:
  pextrect.py [options] <input> <x> <y> [<output>]

Options:
  --x-bins=BINS -x BINS       Set the number of x bins. [default: 100]
  --y-bins=BINS -y BINS       Set the number of y bins. [default: 100]
  --x-label=LABEL LABEL       Set the x label.
  --y-label=LABEL LABEL       Set the y label.
  --xlim=LIM                  Set limits on the x variable.
  --ylim=LIM                  Set limits on the y variable.
  --x-no-restrict             Set limits, but don't restrict x.
  --y-no-restrict             Set limits, but don't restrict y.
  --title=TITLE -t TITLE      Set the title.
  --clabel=CLABEL             Set colorbar label. [default: $p C$]
  --high-res -H               Output a high resolution plt.
  --max-Q=MAXQ                Set the maximum for the charge (pcolormesh's vmax value).
  --normalize                 Normalize the histogram.
  --factor=F                  Multiply histogram by F. [default: 1.0]
'''
import numpy as np;
import matplotlib.pyplot as plt;
import cPickle as pickle;
from docopt import docopt;
from lspreader.misc import conv,test;
from lspreader.plot.cmaps import pastel;

def restrict(x,xlim):
    return x[good];

def pextrect(d,xname,yname,**kw):
    xlim = kw['xlim'] if test(kw,'xlim') else None;
    ylim = kw['ylim'] if test(kw,'ylim') else None;
    x_spacing = kw['x_spacing'] if test(kw,'x_spacing') else 100;
    y_spacing = kw['y_spacing'] if test(kw,'y_spacing') else 100;
    xlabel = kw['xlabel'] if test(kw,'xlabel') else xname;
    ylabel = kw['ylabel'] if test(kw,'ylabel') else yname;
    x = d[xname];
    y = d[yname];
    F = kw['F'] if test(kw,'F') else 1.0;
    
    good = np.ones(len(x)).astype(bool);
    if xlim and not test(kw,'x_no_restrict'):
        good &= (x >= xlim[0]) & (x <= xlim[1]);
    else:
        xlim = (x.min(), x.max());
    if ylim and not test(kw,'y_no_restrict'):
        good &= (y >= ylim[0]) & (y <= ylim[1]);
    else:
        ylim = (x.min(), x.max());
    s =-d['q'][good]*1e6*F;
    x = x[good];
    y = y[good];
    
    maxQ = kw['maxQ'] if test(kw,'maxQ') else None;
    
    x_bins = np.linspace(xlim[0],xlim[1],x_spacing+1);
    y_bins = np.linspace(ylim[0],ylim[1],y_spacing+1);
    
    X,Y = np.mgrid[ xlim[0] : xlim[1] : x_spacing*1j,
                    ylim[0] : ylim[1] : y_spacing*1j];
    S,_,_ = np.histogram2d(x,y,bins=(x_bins,y_bins),weights=s);
    if test(kw,'normalize'):
        S /= np.abs(xlim[1]-xlim[0])/x_spacing;
        S /= np.abs(ylim[1]-ylim[0])/y_spacing;
    fig = kw['fig'] if test(kw,'fig') else plt.figure(1);
    ax  = kw['ax'] if test(kw,'ax') else plt.subplot();
    plt.xlim(xlim);
    plt.ylim(ylim);
    
    plt.xlabel(xlabel);
    plt.ylabel(ylabel);
    surf=ax.pcolormesh(X,Y,S,cmap=pastel,vmax=maxQ);
    c=fig.colorbar(surf,pad=0.075);
    if test(kw,'clabel'):
        c.set_label(kw['clabel']);
    if test(kw,'title'):
        ax.set_title(kw['title'],fontdict={'size':28});
    pass;
    
def main():
    opts = docopt(__doc__,help=True);
    inname = opts['<input>'];
    outname = opts['<output>'];

    xname = opts['<x>'];
    yname = opts['<y>'];
    
    with open(inname,'r') as f:
        d = pickle.load(f);
    kw = {
        'xlim':   opts['--xlim'],
        'ylim':   opts['--ylim'],
        'xlabel': opts['--x-label'],
        'ylabel': opts['--y-label'],
        'x_spacing': float(opts['--x-bins']),
        'y_spacing': float(opts['--y-bins']),
        'F': float(opts['--factor']),
        'maxQ': float(opts['--max-Q']) if opts['--max-Q'] else None,
        'clabel': opts['--clabel'],
        'normalize': opts['--normalize'],
        'fig': None,
        'ax':  None
    };
    pextrect(d,xname,yname,**kw);
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
