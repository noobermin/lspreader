#!/usr/bin/env python2
'''Render volumetric render of a sclr.py output files.

Usage:
  render3d.py [options] IN_FORMAT OUT_FORMAT LABEL_FORMAT <lownum> <highnum> [<step>]
  render3d.py [options] (--plot-single | -s) INFILE [OUTFILE [LABEL] ]

Options:
   --min=MIN -n MIN              Set vmin in the volumetric plot to MIN. [default: 15.0]
   --max=MAX -x MAX              Set vmax in the volumetric plot to MAX. [default: 23.5]
   --plot-single -s              Just show, don't output, single scalar.
   --clabel=CLABEL               Set the colorbar label. [default: log10 of electron density (cm^-3)]
   --zero-x=XRANGE               Set a range of x to zero, as a python tuple.
   --zero-y=YRANGE               Set a range of y to zero, as a python tuple.
   --zero-z=ZRANGE               Set a range of z to zero, as a python tuple.
   --azimuth=AZIMUTH -a AZIMUTH  Set the azimuth [default: 125].
   --polar=POLAR -p POLAR        Set the polar angle [default: 110].
   --roll=ROLL                   Roll after setting the angle [default: 0].
   --trajectories=TRAJ_FORMAT    Look for trajectories files.
   --xlabel=XLABEL               Label for x axis. [default: k].
   --ylabel=YLABEL               Label for y axis. [default: h].
   --zlabel=ZLABEL               Label for x axis. [default: pol.].
   --no-log                      Do not log10 the data.
   --new-ctf                     Use the new ctf. Only valid for plot-single mode.
   --otf=O                       Choose an otf type. See mk_otf for details. [default: 0]
'''
import numpy as np;
from scipy.misc import imsave;
import cPickle as pickle;
from docopt import docopt;
import re;
import math;
from misc import conv,read;

def main():
    #reading in arguments
    opts=docopt(__doc__,help=True);
    vmin = float(opts['--min']);
    vmax = float(opts['--max']);
    kwargs = {};
    kwargs['zeros']=[conv(opts['--zero-x'],func=eval,default=(None,None)),
                     conv(opts['--zero-y'],func=eval,default=(None,None)),
                     conv(opts['--zero-z'],func=eval,default=(None,None))];
    kwargs['zeros'] = None if kwargs['zeros'] == [(None,None)]*3 else kwargs['zeros'];
    angle = [ float(opts['--polar']),
              float(opts['--azimuth']),
              float(opts['--roll']) ];
    kwargs['clabel'] = opts['--clabel'];
    kwargs['xlabel'] = opts['--xlabel'];
    kwargs['ylabel'] = opts['--ylabel'];
    kwargs['zlabel'] = opts['--zlabel'];
    kwargs['log']    = not opts['--no-log'];
    kwargs['otf'] =  opts['--otf'];
    kwargs['new-ctf'] = opts['--new-ctf'];
    if kwargs['new-ctf'] and not opts['--plot-single']:
        print("--new-ctf doesn't work with multi plot mode yet.");
        quit(1);
    if opts['--trajectories']:
        traj = opts['--trajectories'];
        if not opts['--plot-single']:
                if '*' not in traj:
                        print('point format should contain \'*\'');
                        print(usage)
                        quit(1);
                else:
                        points_fmt = 'strung*.pt'
                points_fmt=re.sub(r'\*',fmt,traj);
                starti = lownum if not opts['<first>'] else lownum/step;
                traj_arg = (points_fmt.format(highnum), starti);
        else:
                traj_arg = (traj, -1);
        kwargs.update({'traj':traj_arg});
    if not opts['--plot-single']:
        if '*' not in opts['IN_FORMAT'] or '*' not in opts['OUT_FORMAT']:
            print('point format should contain \'*\'');
            print(usage);
            quit(1);
        lownum=int(opts['<lownum>']);
        highnum=int(opts['<highnum>']);
        numrange = range(lownum,highnum+1);
        if opts['<step>']:
            step = int(opts['<step>']);
            numrange = numrange[::step];
        fmt='{{:0>{}}}'.format(len(opts['<highnum>']))
        out_fmt=re.sub(r'\*',fmt,opts['OUT_FORMAT']);
        in_fmt =re.sub(r'\*',fmt,opts['IN_FORMAT']);
        label_fmt=re.sub(r'\*',fmt,opts['LABEL_FORMAT']);
        outnames = [out_fmt.format(i) for i in numrange];#this so I don't need to check for None
        innames  = [in_fmt.format(i) for i in numrange];
        labels   = [label_fmt.format(i) for i in numrange];
        stuff = {'out':outnames,'in':innames,'label':labels};
        files = [ dict(zip(stuff.keys(),d)) for d in zip(*stuff.values())];
        plot(files,(vmin,vmax),angle,**kwargs);
    else: #plot single mode
        name_tuple = (opts['INFILE'],opts['OUTFILE'],opts['LABEL']);
        plot_single(name_tuple,(vmin,vmax),angle,**kwargs);
    pass;
pass;


def logprint(s):
    print(s);
    
def zero_range(S,zeros):
    S[zeros[0][0]:zeros[0][1],zeros[1][0]:zeros[1][1],zeros[2][0]:zeros[2][1]]=0.0;
    return S;

def mk_otf(vlim,otftype):
    '''Create the opacity transfer function.'''
    from tvtk.util.ctf import PiecewiseFunction;
    otf = PiecewiseFunction();
    def otf_mkr(pts,otf):
        map(lambda i: otf.add_point(*i), pts);
        return otf;
    def mid_pt(r,m,b=0.001,e=1.0):
        return [
            (vlim[0], b),
            (vlim[0]+(vlim[1]-vlim[0])*r, m),
            (vlim[1], e)
        ];
    vs={'0': (0.85, 0.06),
        '1': (0.90, 0.06),
        '2': (0.90, 0.08),
        '3': (0.90, 0.10),
        '4': (0.99, 0.20),
        'solid': (0.01,0.7,0.0)}
    return otf_mkr(mid_pt(*vs[otftype]),otf);

def set_otf(v,otf):
    '''Set the volume object's otf'''
    v._otf = otf;
    v._volume_property.set_scalar_opacity(v._otf);

def mk_ctf(vlim):
    '''Create the color transfer function.'''
    from mayavi.modules import volume;
    return volume.make_CTF(vlim[0],vlim[1],
                           hue_range=(0.8,0.0),
                           sat_range=(0.6,0.6),
                           mode="linear");

def set_ctf(v,ctf):
    '''Set the volume object's ctf'''
    from tvtk.util.ctf import set_lut;
    v._ctf = ctf;
    v._volume_property.set_color(v._ctf);
    v.update_ctf = True;
    set_lut(v.module_manager.scalar_lut_manager.lut,
            v._volume_property);


def initial_volumetric(mlab,S,vlim,angle,colorbar=True,**kwargs):
    '''
    Creates the first volumetric render. This creates most of the data
    structures to be used and returns them as a dictionary.
    '''
    ret = {};
    if type(S) == str:
        logprint('loading file {}'.format(S));
        tmp = read(S, dumpfull=True);
        if type(tmp) == dict:
            S = tmp['s'];
            assert(type(tmp['x']) == type(tmp['y']));
            assert(type(tmp['z']) == type(tmp['y']));
            if type(tmp['x']) == tuple:# check order
                print(tmp['x']+tmp['y']+tmp['z']);
                m = -np.log10(np.abs(min(tmp['x']+tmp['y']+tmp['z'])))+2;
                m = 10**np.ceil(m);
                kwargs['X'],kwargs['Y'],kwargs['Z'] = np.mgrid[
                    tmp['x'][0]:tmp['x'][1]:S.shape[0]*1j,
                    tmp['y'][0]:tmp['y'][1]:S.shape[1]*1j,
                    tmp['z'][0]:tmp['z'][1]:S.shape[2]*1j]*m;
            else:
                kwargs['X'],kwargs['Y'],kwargs['Z']=tmp['x'],tmp['y'],tmp['z'];
        else:
            S = tmp;
    S=np.nan_to_num(S);
    if 'zeros' in kwargs and kwargs['zeros'] is not None:
        S=zero_range(S,kwargs['zeros'])
    #taking the logarithm.
    if kwargs['log']: S=np.log10(S+0.1);
    #creating the figure.
    if 'fig' not in kwargs:
        fig=mlab.figure(size=(1280,1024),
                        bgcolor=(1.0,1.0,1.0),
                        fgcolor=(0.3,0.3,0.3));
        ret['fig']=fig;
    else:
        ret['fig']=kwargs['fig'];
    #fig.scene.disable_render=True;
    #creating the source.
    if 'X' in kwargs:
        src=mlab.pipeline.scalar_field(kwargs['X'], kwargs['Y'], kwargs['Z'],S);
    else:
        src=mlab.pipeline.scalar_field(S);
    #volume rendering.
    v=mlab.pipeline.volume(src,vmin=vlim[0],vmax=vlim[1]);
    set_otf(v,mk_otf(vlim,kwargs['otf']));
    if kwargs['new-ctf']:
        ret['ctf'] = mk_ctf(vlim);
        set_ctf(v,ret['ctf']);
    #putting in custom stuff
    v._volume_property.interpolation_type = 'nearest';
    ret['v']=v;
    #doing the crazy trajectory stuff.
    if 'traj' in kwargs:
        strung_name, firsti = kwargs['traj'];
        full_traj = read(strung_name);
        #the shape of each dimension is d[x|y|z,particle,step]
        steps = full_traj.shape[2];
        N = full_traj.shape[1];
        #creating connections between points, this should be an
        #array of pairs that give indices of coordinates that should
        #be connected.
        sarray=np.arange(steps);
        conn_1 = np.array(zip(sarray[:-1],sarray[1:]));
        conn = np.vstack([conn_1+steps*i for i in range(N)]);
        del sarray,conn_1;#cleaning up.
        
        #making current part of the track to be plotted
        cur_traj = np.empty(full_traj.shape);
        cur_traj.fill(np.nan);
        cur_traj[:,:,:firsti] = full_traj[:,:,:firsti];
        x = np.hstack(cur_traj[0,:,:]);
        y = np.hstack(cur_traj[1,:,:]);
        z = np.hstack(cur_traj[2,:,:]);
        #trajectory source
        tracks_src=mlab.pipeline.scalar_scatter(x,y,z,
                                                np.ones(x.shape));
        tracks_src.mlab_source.dataset.lines = conn;
        lines = mlab.pipeline.stripper(tracks_src);
        #creating tracks.
        tracks = mlab.pipeline.surface(lines,line_width=2,opacity=1.0);
        ret['tracks'] = tracks;
        ret['cur_traj'] = cur_traj;
        ret['full_traj'] = full_traj;
    #scalarbar
    if colorbar==True:
        if 'clabel' in kwargs:
            mlab.scalarbar(object=v,title=kwargs['clabel']);
        else:
            mlab.scalarbar(object=v);
    #The colorbar doesn't work if we change the
    #vmin and vmax, so, we have to do this instead.    
    v.module_manager.scalar_lut_manager.use_default_range = False;
    v.module_manager.scalar_lut_manager.data_range = np.array([vlim[0], vlim[1]]);
    if kwargs['label']:
        l = kwargs['label'];
        t=mlab.text(0.075,0.875, l, width=len(l)*0.015);
        ret['t'] = t;
    #show the nubs
    oa=mlab.orientation_axes(xlabel=kwargs['xlabel'],
                             ylabel=kwargs['ylabel'],
                             zlabel=kwargs['zlabel']);
    oa.marker.set_viewport(0,0,0.4,0.4);
    #begin rendering
    if 'render' not in kwargs or kwargs['render']:
        fig.scene.disable_render=False;
    #setting the view
    mlab.view(elevation=angle[0],azimuth=angle[1],
              focalpoint='auto',distance='auto');
    mlab.roll(angle[2]);
    return ret;

def plot(names_list,vlim,angle,
         **kwargs):
    print("loading mayavi");
    import mayavi.mlab as mlab;
    mlab.options.offscreen = True;
    first = names_list[0];
    names_list = names_list[1:];
    print("processing first file {}...".format(first['in']));
    d=initial_volumetric(mlab,first['in'],vlim,angle,
                   label=first['label'],
                   **kwargs);
    if 'traj' in kwargs:
        firsti = kwargs['traj'][1];
    d['fig'].scene.disable_render = False;
    print("saving {}".format(first['out']));
    imsave(first['out'],mlab.screenshot());
    for i,names in enumerate(names_list):
        print("processing {}...".format(names['in']))
        S=read(names['in']);
        S=np.nan_to_num(S)
        if 'zeros' in kwargs and kwargs['zeros'] is not None:
            S=zero_range(S,kwargs['zeros']);
        if kwargs['log']: S=np.log10(S+0.1);
        d['fig'].scene.disable_render=True;
        d['v'].mlab_source.set(scalars=S);
        # if kwargs['new-ctf']:
        #     set_ctf(d['v'],d['ctf']);
        d['t'].text=names['label'];
        if 'traj' in kwargs:
            d['cur_traj'][:,:,firsti+i] = d['full_traj'][:,:,firsti+i];
            x = np.hstack(d['cur_traj'][0,:,:]);
            y = np.hstack(d['cur_traj'][1,:,:]);
            z = np.hstack(d['cur_traj'][2,:,:]);
            tracks.mlab_source.set(x=x,y=y,z=z);
        d['fig'].scene.disable_render=False;
        print("saving {}".format(names['out']));
        imsave(names['out'],mlab.screenshot());
    pass

def plot_single(name,vlim,angle,
                **kwargs):
    print("loading mlab");
    import mayavi.mlab as mlab;
    inname,outname,label = name;
    if outname:
        mlab.options.offscreen = True;
    initial_volumetric(mlab,inname,vlim,angle,label=label,**kwargs);
    if not outname:
        print('plotting');
        mlab.show();
    else:
        print('saving {}'.format(outname));
        #hack to avoid the lines, now mayavi really is headless
        imsave(outname,mlab.screenshot());
    pass;

if __name__=="__main__":
    main()
