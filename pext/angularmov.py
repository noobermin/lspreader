#!/usr/bin/env python2
'''
Show an angular/energy/charge plot movie.

Usage:
  angularmov.py [options] <input> [<output>]

Options:
  --angle-bins=BINS -a BINS   Set the number of angle bins.  [default: 180]
  --energy-bins=BINS -r BINS  Set the number of energy bins. [default: 40]
  --ltitle=TITLE -t TITLE     Set the title.
  --rtitle=TITLE -T TITLE     Set the right title.
  --clabel=CLABEL -c CLABEL   Set colorbar label. [default: $p C$]
  --timestep=S -s S           Set timestep in ns. [default: 1e-6]
  --initial-time=T -i T       Set initial timestep in ns. [default: 0]
  --minus-time=T -m T         Subtract this time. [default: 0]
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
  --cmap=CMAP                 Use the following cmap [default: pastel_clear].
  --e-direction=ANGLE         The angle for the radial labels.
  --e-units=UNIT              The units for the radial labels.
  --interval=I                Set animate interval. [default: 100]
'''
from docopt import docopt;
import numpy as np;
import matplotlib.pyplot as plt;
import matplotlib.animation as anim;
from lspreader.plot.angular import _prep,angular

opts = docopt(__doc__,help=True);
s,phi,e,kw,d = _prep(opts);

tstep = float(opts['--timestep']);
ti    = float(opts['--initial-time']);
mt    = float(opts['--minus-time']);

interval=float(opts['--interval']);
#process by times.
good = np.argsort(d['t'])
s   = s[good];
e   = e[good];
phi = phi[good];
t   = d['t'][good];

tbins = np.arange(ti,t[-1]+tstep,tstep);
#fucking c like loop shit mother fucker.
i=0;
Is=[];
for j,ct in enumerate(t):
    if ct > tbins[i]:
        Is.append(j);
        i+=1;
#do first
#surf,_,fig,bins = angular(s[Is[0]:],phi[Is[0]:],e[Is[0]:],**kw);
surf,_,fig,bins = angular(s, phi, e,**kw);
#surf,_,fig,bins = angular([],[],[],**kw);
t=fig.text(0.02,0.05,'t = {:3.2f}e-4 ns'.format(tbins[0]*1e4),
           fontdict={'fontsize':22});
def animate(ii):
    j,i = ii;
    S,_,_ = np.histogram2d(phi[:i],e[:i],bins=bins,weights=s[:i]);
    surf.set_array(S[::,:-1].ravel());
    t.set_text('t = {:3.2f}e-4 ns'.format((tbins[j]-mt)*1e4));
    return surf;

a=anim.FuncAnimation(fig, animate,
                     list(enumerate(Is[1:])),
                     interval=interval);
if opts['<output>']:
    a.save(opts['<output>'],fps=15);
else:
    plt.show();
pass;
    
