#!/usr/bin/env python2
'''
Show an angular/energy/charge plot.

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

import cPickle as pickle;
from docopt import docopt;
from lspreader.plot.angular import angular_load, angular, defaults;

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
    s,phi,e,d = angular_load(
        inname,
        F=float(opts['--factor']),
        normalize=kw if opts['--normalize'] else None,
        polar=opts['--polar'], keV=kev)
    return s,phi,e,kw,d;

if __name__ == "__main__":
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
