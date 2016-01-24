#!/usr/bin/env python2
'''
Show an angular/energy/charge plot movie.

Usage:
  angular.py [options] <input>
  angular.py [options] <input> <output>

Options:
  --angle-bins=BINS -a BINS   Set the number of angle bins.  [default: 180]
  --energy-bins=BINS -r BINS  Set the number of energy bins. [default: 40]
  --ltitle=TITLE -t TITLE     Set the title.
  --rtitle=TITLE -T TITLE     Set the right title.
  --clabel=CLABEL -c CLABEL   Set colorbar label. [default: $p C$]
  --no-cbar                   Turn off the colorbar.
  --keV -k                    Scale by 100s of KeV instead of MeV.
  --max-e=MAXE -e MAXE        Set the maximum energy value (in units depending on --keV flag)
  --e-step=ESTEP              Set the step of grid lines for Energy.
  --high-res -H               Output a high resolution plt.
  --max-q=MAXQ -q MAXQ        Set the maximum for the charge (pcolormesh's vmax value).
  --min-q=MINQ                Set a minimum charge.
  --normalize -n              Normalize the histogram to 1 *eV^-1 rad^-1 .
  --factor=F -f F             Multiply histogram by F. [default: 1.0]
  --polar -p                  Plot polar angles, letting the east direction be forward.
  --oap=ANGLE -o ANGLE        Set the width angle of the OAP. [default: 50.47]
  --log10 -l                  Plot a logarithmic pcolor instead of a linear one.
  --cmap=CMAP                 Use the following cmap [default: pastel].
  --e-direction=ANGLE         The angle for the radial labels.
  --e-units=UNIT              The units for the radial labels.
  --agg                       Use the agg backend.
'''
import numpy as np;
import matplotlib;
import matplotlib.pyplot as plt;
import matplotlib.patheffects as pe;
from matplotlib import colors;
from misc import conv, test, readfile
from cmaps import pastel_clear,plasma_clear,viridis_clear,magma_clear_r;
import re;


def prep(opts):
    '''I put this here in order to reuse this'''
    
    inname = opts['<input>'];
    kev = opts['--keV'];
    def getdef_kev(label):
        
        if kev:
            return defaults[label+'_kev'];
        else:
            return defaults[label];
    kw = {
        'angle_bins' : float(opts['--angle-bins']),
        'energy_bins': float(opts['--energy-bins']),
        'max_e': float(opts['--max-e']) if opts['--max-e'] else (
            getdef_kev('max_e')),
        'max_q': float(opts['--max-q']) if opts['--max-q'] else None,
        'min_q': float(opts['--min-q']) if opts['--min-q'] else None,
        'keV': kev,
        'clabel' : opts['--clabel'],
        'colorbar' : not opts['--no-cbar'],
        'e_step' : float(opts['--e-step']) if opts['--e-step'] else None,
        'labels': 'tdefault' if opts['--polar'] else 'default',
        'rtitle':opts['--rtitle'],
        'ltitle':opts['--ltitle'],
        'oap': float(opts['--oap']) if opts['--oap'] != 'none' else None,
        'log_q': opts['--log10'],
    };
    cmap = _str2cmap(opts['--cmap']);
    if not cmap:
        cmap = opts['--cmap'];
    kw['cmap'] = cmap;
    kw['rgridopts'] = {};
    if opts['--e-direction']:
        kw['rgridopts'].update({'angle':opts['--e-direction']});
    if opts['--e-units']:
        kw['rgridopts'].update({'unit':opts['--e-units']});
    if opts['--normalize']:
        kw['clabel'] += defaults['norm_units'];

    #end of setting up kws into angular.
    #this deals with pre-processing.
    s,phi,e,d = load(inname,
                     F=float(opts['--factor']),
                     normalize=kw if opts['--normalize'] else None,
                     polar=opts['--polar'], keV=kev)
    return s,phi,e,kw,d;

def load(fname,
         F=None,normalize=False,polar=False, keV=False):
    '''
    load the pext data and normalize

    parameters:
    -----------

    fname       -- name of file or data
    F           -- Factor to scale by, None doesn't scale.
    normalize   -- if None, don't normalize. Otherwise, pass a dict with
                   {'angle_bins': ,'energy_bins': , 'max_e': }
                   with the obvious meanings. Normalize with max_phi as phi.
    polar       -- if polar, use phi_n over phi in the file/data.
    keV         -- scale by keV over MeV
    '''
    d = np.load(fname, allow_pickle=True);
    e = d['KE'];
    phi = d['phi_n'] if polar else d['phi'];
    if keV:
        e/=1e3;
    else:
        e/=1e6;
    s = -d['q']*1e6;
    if F is not None: s*=F;
    if normalize:
         kw = normalize
         Efactor = kw['max_e']/kw['energy_bins'];
         if kw['keV']: Efactor *= 1e-3;
         s /= Efactor*2*np.pi/kw['angle_bins'];
    return s,phi,e,d

def _str2cmap(i):    
    if i == 'viridis':
        return viridis_clear;
    elif i == 'plasma':
        return plasma_clear;
    elif i == 'magma_r':
        return magma_clear_r;
    elif i == 'pastel':
        return pastel_clear;
    pass;

defaults = {
    'tlabels': ['Forward\n0$^{\circ}$',
               '45$^{\circ}$',
               'Up\n90$^{\circ}$',
               '135$^{\circ}$',
               'Backwards\n180$^{\circ}$',
               '215$^{\circ}$',
               'Down\n270$^{\circ}$',
               '315$^{\circ}$'],
    'labels': ['Forward\n0$^{\circ}$',
               '45$^{\circ}$',
               'Left\n90$^{\circ}$',
               '135$^{\circ}$',
               'Backwards\n180$^{\circ}$',
               '215$^{\circ}$',
               'Right\n270$^{\circ}$',
               '315$^{\circ}$'],
    'angle_bins': 180,
    'energy_bins': 40,
    'max_e': 4.0,
    'max_e_kev': 1000,
    'e_step' : 1.0,
    'e_step_kev': 250,
    'max_q': None,
    'min_q': None,
    'cmap': pastel_clear,
    'clabel': '$pC$',
    'log_q' : None,
    'norm_units': ' rad$^{-1}$ MeV$^{-1}$',
};

def getkw(kw,label):
    return kw[label] if test(kw,label) else defaults[label];
def getkw_kev(kw,label,kev):
    if kev: label+='_kev';
    return getkw(kw,label);
def angular(s, phi, e,
            colorbar=True,**kw):
    '''
    Make the angular plot.

    Arguments:
      s   -- the charges.
      phi -- the angles of ejection.
      e   -- energies of each charge.

    Keyword Arugments:
      max_e       -- Maximum energy.
      max_q       -- Maximum charge.
      angle_bins  -- Set the number of angle bins.
      energy_bins -- Set the number of energy bins.
      clabel      -- Set the colorbar label.
      colorbar    -- If true, plot the colorbar.
      e_step      -- Set the steps of the radius contours.
      labels      -- Set the angular labels. If not a list, if
                     'default', use default. If 'tdefault', use
                     default for theta. (See defaults dict);
      keV         -- Use keV isntead of MeV.
      fig         -- If set, use this figure, Otherwise,
                     make a new figure.
      ax          -- If set, use this axis. Otherwise,
                     make a new axis.
      ltitle      -- Make a plot on the top left.
      rtitle      -- Make a plot on the top right.
      log_q       -- log10 the charges.
      cmap        -- use the colormap cmap.
      rgridopts   -- pass a dictionary that sets details for the
                     rgrid labels.
    '''
    kev = test(kw, 'keV');
    phi_spacing = getkw(kw,'angle_bins');
    E_spacing =   getkw(kw,'energy_bins');
    maxE  = getkw_kev(kw,'max_e',kev);
    maxQ  = getkw(kw,'max_q');
    minQ  = getkw(kw,'min_q');
    Estep = getkw_kev(kw,'e_step',kev);
    clabel = getkw(kw,'clabel');
    cmap = getkw(kw, 'cmap');

    phi_bins = np.linspace(-np.pi,np.pi,phi_spacing+1);
    E_bins   = np.linspace(0, maxE, E_spacing+1);
            
    PHI,E = np.mgrid[ -np.pi : np.pi : phi_spacing*1j,
                      0 : maxE : E_spacing*1j];
    S,_,_ = np.histogram2d(phi,e,bins=(phi_bins,E_bins),weights=s);
    if test(kw,'fig'):
        fig = kw['fig']
    else:
        fig = plt.figure(1,facecolor=(1,1,1));
    if test(kw,'ax'):
        ax= kw['ax']
    else:
        ax= plt.subplot(projection='polar',axisbg='white');
    norm = matplotlib.colors.LogNorm() if test(kw,'log_q') else None;
    surf=plt.pcolormesh(PHI,E,S,norm=norm, cmap=cmap,vmin=minQ,vmax=maxQ);
    #making radial guides. rgrids only works for plt.polar calls
    full_phi = np.linspace(0.0,2*np.pi,100);
    for i in np.arange(0.0,maxE,Estep)[1:]:
        plt.plot(full_phi,np.ones(full_phi.shape)*i,
                 c='gray',alpha=0.9,
                 lw=1, ls='--');
    ax.set_theta_zero_location('N');
    ax.patch.set_alpha(0.0);
    ax.set_axis_bgcolor('red');
    #making rgrid
    if test(kw, 'rgridopts'):
        ropts = kw['rgridopts'];
        if test(ropts, 'unit'):
            runit = ropts['unit'];
        else:
            runit = 'keV' if kev else 'MeV';
        if test(ropts, 'angle'):
            rangle = ropts['angle'];
        else:
            rangle = 45;
        if test(ropts, 'size'):
            rsize = ropts['size'];
        else:
            rsize = 10.5;
        if test(ropts, 'invert'):
            c1,c2 = "w","black";
        else:
            c1,c2 = "black","w";
    else:
        runit = 'keV' if kev else 'MeV';
        rangle = 45;
        rsize = 10.5;
        c1,c2 = "black","w";
    rlabel_str = '{} ' + runit;
    rlabels    = np.arange(0.0,maxE,Estep)[1:];
    _,ts=plt.rgrids(rlabels,
                    labels=map(rlabel_str.format,rlabels),
                    angle=rangle);
    for t in ts:
        t.set_path_effects([
            pe.Stroke(linewidth=1.5, foreground=c2),
            pe.Normal()
        ]);
        t.set_size(rsize);
        t.set_color(c1);
    if test(kw,'oap'):
        oap = kw['oap']/2 * np.pi/180;
        maxt = oap+np.pi; mint = np.pi-oap;
        maxr  = maxE*.99;
        minr = 120 if kev else .12;
        ths=np.linspace(mint, maxt, 20);
        rs =np.linspace(minr, maxr, 20);
        mkline = lambda a,b: plt.plot(a,b,c=(0.2,0.2,0.2),ls='-',alpha=0.5);
        mkline(ths, np.ones(ths.shape)*minr)
        mkline(mint*np.ones(ths.shape), rs);
        mkline(maxt*np.ones(ths.shape), rs);
    if test(kw,'labels'):
        if kw['labels'] == 'default':
            labels = defaults['labels'];
        elif kw['labels'] == 'tdefault':
            labels = defaults['tlabels'];
        else:
            labels= kw['labels'];
        ax.set_xticks(np.pi/180*np.linspace(0,360,len(labels),endpoint=False));
        ax.set_xticklabels(labels);
    if colorbar:
        c=fig.colorbar(surf,pad=0.1);
        c.set_label(clabel);
    if test(kw,'ltitle'):
        if len(kw['ltitle']) <= 4:
            ax.set_title(kw['ltitle'],loc='left',fontdict={'fontsize':28});
        else:
            ax.text(np.pi/4+0.145,maxE+Estep*2.5,kw['ltitle'],fontdict={'fontsize':28});
    if test(kw,'rtitle'):
        if '\n' in kw['rtitle']:
            fig.text(0.60,0.875,kw['rtitle'],fontdict={'fontsize':22});
        else:
            plt.title(kw['rtitle'],loc='right',fontdict={'fontsize':22});
    return (surf, ax, fig, (phi_bins, E_bins));

if __name__ == "__main__":
    import cPickle as pickle;
    from docopt import docopt;
    opts=docopt(__doc__,help=True);
    s,phi,e,kw,_ = prep(opts);
    if opts['<output>'] and opts['--agg']:
        plt.change_backend('agg');
    angular(s,phi,e,**kw);
    if opts['<output>']:
        if opts['--high-res']:
            plt.savefig(opts['<output>'],dpi=1000);
        else:
            plt.savefig(opts['<output>']);
    else:
        plt.show();
    
    pass;
