#!/usr/bin/env python2
'''
Show an angular/energy/charge plot movie.

Usage:
  angularmov.py [options] <input> [<output>]

Options:
  --angle-bins=BINS -a BINS   Set the number of angle bins.  [default: 180]
  --radial-bins=BINS -r BINS  Set the number of radial bins. [default: 40]
  --ltitle=TITLE -t TITLE     Set the title.
  --rtitle=TITLE -T TITLE     Set the right title.
  --clabel=CLABEL -c CLABEL   Set colorbar label. [default: $p C$]
  --timestep=S -s S           Set timestep in ns. [default: 1e-6]
  --initial-time=T -i T       Set initial timestep in ns. [default: 0]
  --minus-time=T -m T         Subtract this time. [default: 0]
  --no-cbar                   Turn off the colorbar.
  --KeV -k                    Scale by 100s of KeV instead of MeV.
  --max-e=MAXE -e MAXE        Set the maximum energy value (in units depending on --KeV flag)
  --e-step=ESTEP              Set the step of grid lines for Energy.
  --high-res -H               Output a high resolution plt.
  --max-q=MAXQ -q MAXQ        Set the maximum for the charge (pcolormesh's vmax value).
  --normalize -n              Normalize the histogram to 1 *eV^-1 rad^-1 .
  --factor=F -f F             Multiply histogram by F. [default: 1.0]
  --polar -p                  Plot polar angles, letting the east direction be forward.
  --oap=ANGLE -o ANGLE        Set the width angle of the OAP. [default: 49.0]
'''
import numpy as np;
import matplotlib.pyplot as plt;
import cPickle as pickle;
from matplotlib import colors;
import matplotlib.animation as anim;
from docopt import docopt;
from misc import conv,test;
from cmaps import pastel,pastel_b2r;
from angular import angular,prep;

opts = docopt(__doc__,help=True);
s,phi,e,kw,d = prep(opts);

tstep = float(opts['--timestep']);
ti    = float(opts['--initial-time']);
mt    = float(opts['--minus-time']);
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

a=anim.FuncAnimation(fig, animate, list(enumerate(Is[1:])),interval=0.1);
if opts['<output>']:
    a.save(opts['<output>'],fps=15);
else:
    plt.show();
pass;
    

#if __name__ == "__main__":
#    main();
