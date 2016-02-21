#!/usr/bin/env python2
'''Render volumetric render of a sclr.py output files.

Usage:
  render3d.py [options] IN_FORMAT OUT_FORMAT LABEL_FORMAT <lownum> <highnum> [<step>]
  render3d.py [options] (--render-single | -s) INFILE [OUTFILE [LABEL] ]

Options:
   --min=MIN -n MIN              Set vmin in the volumetric plot to MIN. [default: 15.0]
   --max=MAX -x MAX              Set vmax in the volumetric plot to MAX. [default: 23.5]
   --render-single -s            Output single scalar.
   --clabel=CLABEL               Set the colorbar label. [default: log10 of electron density (cm^-3)]
   --zero-x=XRANGE               Set a range of x to zero, as a python tuple.
   --zero-y=YRANGE               Set a range of y to zero, as a python tuple.
   --zero-z=ZRANGE               Set a range of z to zero, as a python tuple.
   --azimuth=AZIMUTH -a AZIMUTH  Set the azimuth [default: 125].
   --polar=POLAR -p POLAR        Set the polar angle [default: 110].
   --roll=ROLL                   Roll after setting the angle [default: 0].
   --trajectories=FMT -t FMT     Look for trajectories files with the following format FMT. For
                                 single render mode, treat FMT as an actual filename.
   --xlabel=XLABEL               Label for x axis. [default: k].
   --ylabel=YLABEL               Label for y axis. [default: h].
   --zlabel=ZLABEL               Label for x axis. [default: pol.].
   --no-log                      Do not log10 the data.
   --otf=O                       Choose an otf type. See mk_otf for details. [default: 0]
'''
import numpy as np;
from scipy.misc import imsave;
import cPickle as pickle;
from docopt import docopt;
import re;
import math;
from lspreader.misc import conv,readfile,test;
from tvtk.util.ctf import ColorTransferFunction, PiecewiseFunction;

def main():
    #reading in arguments
    opts=docopt(__doc__,help=True);
    vmin = float(opts['--min']);
    vmax = float(opts['--max']);
    kw = {};
    kw['zeros']=[conv(opts['--zero-x'],func=eval,default=(None,None)),
                     conv(opts['--zero-y'],func=eval,default=(None,None)),
                     conv(opts['--zero-z'],func=eval,default=(None,None))];
    kw['zeros'] = None if kw['zeros'] == [(None,None)]*3 else kw['zeros'];
    angle = [ float(opts['--polar']),
              float(opts['--azimuth']),
              float(opts['--roll']) ];
    kw['clabel'] = opts['--clabel'];
    kw['xlabel'] = opts['--xlabel'];
    kw['ylabel'] = opts['--ylabel'];
    kw['zlabel'] = opts['--zlabel'];
    kw['log']    = not opts['--no-log'];
    kw['otf'] =  opts['--otf'];
    if opts['--trajectories']:
        kw['traj']=True;
        if type(opts['--trajectories']) == str:
            traj = opts['--trajectories'];
        else:
            traj = 'strung*.pt' if not opts['--plot-single'] else 'strung.pt';
    if not opts['--render-single']:
        #getting range
        lownum=int(opts['<lownum>']);
        highnum=int(opts['<highnum>']);
        numrange = range(lownum,highnum+1);
        if opts['<step>']:
            step = int(opts['<step>']);
            numrange = numrange[::step];
        #gathering things to collate
        stepdata = [('in',opts['IN_FORMAT']),
                    ('out',opts['OUT_FORMAT']),
                    ('label',opts['LABEL_FORMAT'])];
        if opts['--trajectories']:
            stepdata.append(('traj',traj));
            kw['traj_firsti'] = lownum;
            kw['traj_step']   = step;
        wildcardfmt='{{:0>{}}}'.format(len(opts['<highnum>']))
        stuff = {}
        for label,fmt in stepdata:
            if '*' not in fmt:
                print("point format should contain '*'");
                print(usage); quit(-1);
            fmt = re.sub(r'\*',wildcardfmt,fmt)
            stuff[label] = [fmt.format(i) for i in numrange];
        files = [ dict(zip(stuff.keys(),d)) for d in zip(*stuff.values())];
        render_series(files,(vmin,vmax),angle,suppress=False,**kw);
    else: #render single mode
        name_tuple = (opts['INFILE'],opts['OUTFILE'],opts['LABEL']);
        if opts['--trajectories']: name_tuple+=(traj)
        render(name_tuple, (vmin,vmax), angle, suppress=False,**kw);
    pass;
pass;


def logprint(s):
    print(s);
    
def zero_range(S,zeros):
    S[zeros[0][0]:zeros[0][1],zeros[1][0]:zeros[1][1],zeros[2][0]:zeros[2][1]]=0.0;
    return S;

def mk_otf(vlim, orange):
    '''
    Create an opacity transfer function.

    Arguments:
      vlim   -- data limits
      orange -- list of (fraction,opacity) pairs
    '''
    orange[:] = [(i[0]*(vlim[1]-vlim[0])+vlim[0],i[1]) for i in orange];
    otf = PiecewiseFunction();
    for i in orange:
        otf.add_point(*i);
    return otf;

def mk_ctf(vlim,hr,sr,mode='linear'):
    '''
    Create the color transfer function.

    Arguments:
      vlim -- Data limits
      hr   -- Hue range from min to max.
      sr   -- Saturation range from min to max.
      mode -- The interpolation mode.
    '''
    from mayavi.modules import volume;
    return volume.make_CTF(vlim[0],vlim[1],
                           hue_range=hr,
                           sat_range=sr,
                           mode=mode);
def set_otf(v,otf):
    '''Set the volume object's otf'''
    v._otf = otf;
    v._volume_property.set_scalar_opacity(v._otf);

def set_ctf(v,ctf):
    '''Set the volume object's ctf'''
    from tvtk.util.ctf import set_lut;
    v._ctf = ctf;
    v._volume_property.set_color(v._ctf);
    v.update_ctf = True;
    set_lut(v.module_manager.scalar_lut_manager.lut,
            v._volume_property);



def volumetric(S,colorbar=True,**kw):
    '''
    Creates the a volumetric render on a given figure
    For the sake of scripted changes, data made are returned as a dictionary.
    
    Arguments:
      S -- 3D Numpy array or filename.

    Keyword arguments:
      mlab     -- mlab instance, if None, make our own instance.
      fig      -- Figure to render on. If None, create one sized 1280x1024 with white
                  background and dark gray foreground.
      vlim     -- Tuple that specifies the limits for the volumetric render (min,max),
                  Default (if None) is the minimum and maximum of the data.
      zeros    -- If zero a particular range of indices on the volume render.
      X,Y,Z    -- Render with the given mgrid like points.
      ctf      -- Use the given ctf. If a ColorTransferFunction instance, use it. This
                  also supports using a tuple of the form ((h1,h2),(s1,s2),mode) where
                  hx are the range of hues and sx are the range of saturation values
                  and mode is a string representing the interpolation mode.
                  The ctf is saved to the returned dict under the key 'ctf'
      otf      -- Use the given otf. If a PiecewiseFunction instance, use it. This also
                  supports using a tuple of the form (o1,o2) where ox are the ranges of
                  opacity values. Moreover, a list of (value,opacity) points are accepted.
                  The otf is saved to the returned dict under the key 'otf'.
      log      -- If True, render the log10 of the data, specifically, log10(S+0.1).
      inttype  -- Set the interpolation type. Default is "nearest".
      colorbar -- Render a colorbar. You're going to have a lot of trouble if you do
                  not let me do this and try to do it yourself since volume rendering
                  does not use the LUT.
      clabel   -- Set the color bar label.
      render   -- If True, render immediately after creating the volumetric. If this is
                  False, the caller should set fig.scene.disable_render to False to
                  see the updated scene.
    '''
    ret = {};
    if type(S) == str:
        logprint('loading file {}'.format(S));
        tmp = readfile(S, dumpfull=True);
        if type(tmp) == dict:
            S = tmp['s'];
            assert(type(tmp['x']) == type(tmp['y']));
            assert(type(tmp['z']) == type(tmp['y']));
            if type(tmp['x']) == tuple:
                m = -np.log10(np.abs(min(tmp['x']+tmp['y']+tmp['z'])))+2;
                m = 10**np.ceil(m);
                kw['X'],kw['Y'],kw['Z'] = np.mgrid[
                    tmp['x'][0]:tmp['x'][1]:S.shape[0]*1j,
                    tmp['y'][0]:tmp['y'][1]:S.shape[1]*1j,
                    tmp['z'][0]:tmp['z'][1]:S.shape[2]*1j]*m;
            else:
                kw['X'],kw['Y'],kw['Z']=tmp['x'],tmp['y'],tmp['z'];
        else:
            S = tmp;
    if 'mlab' in kw:
        ret['mlab'] = mlab = kw['mlab'];
    else:
        import mayavi.mlab as mlab; ret['mlab']=mlab;
    if test(kw,'zeros'):
        S=zero_range(S,kw['zeros'])
    #taking the logarithm.
    if test(kw,'log'):
        S=np.log10(np.where(S <= 1.0, 1, S))
    #creating the figure.
    vmin,vmax = S.min(),S.max();
    if test(kw,'vlim'):
        if kw['vlim'][0]: vmin = kw['vlim'][0];
        if kw['vlim'][1]: vmax = kw['vlim'][1];
    vlim=vmin,vmax;
    
    if 'fig' not in kw:
        fig=mlab.figure(
            size=(1280,1024),
            bgcolor=(1.0,1.0,1.0),
            fgcolor=(0.3,0.3,0.3));
        ret['fig']=fig;
    else:
        fig = ret['fig'] = kw['fig'];
    #end boilerplate
    fig.scene.disable_render=True;
    if 'X' in kw:
        src=mlab.pipeline.scalar_field(kw['X'], kw['Y'], kw['Z'],S);
    else:
        src=mlab.pipeline.scalar_field(S);
    #volume rendering
    v=mlab.pipeline.volume(src,vmin=vlim[0],vmax=vlim[1]);
    #setting otf and ctf.
    if 'otf' in kw:
        if type(kw['otf']) == PiecewiseFunction:
            otf = kw['otf'];
        else:
            if len(kw['otf']) == 2:
                otfl = [(0.0, kw['otf'][0]), (1.0, kw['otf'][1])]
            else:
                otfl = kw['otf'];
            otf = mk_otf(vlim,otfl);
    else:
        otf = mk_otf(vlim,[(0.0, 0.0), (1.0, 1,0)]);
    set_otf(v,otf);
    if 'ctf' in kw:
        if type(kw['ctf']) == ColorTransferFunction:
            ctf = ret['ctf'];
        elif type(kw['ctf']) == tuple:
            mode = kw['ctf'][2] if len(kw['ctf']) >= 3 else 'linear';
            ctf = mk_ctf(vlim, hr=kw['ctf'][0], sr=kw['ctf'][1]);
        else:
            raise ValueError("Invalid ctf keyword argument.")
    else:
        ctf = mk_ctf(vlim, hr=(0.8,0.0), sr=(0.6,0.6));
    set_ctf(v,ctf);
    #putting in custom stuff
    if 'inttype' in kw:
        v._volume_property.interpolation_type = kw['inttype'];
    else:
        v._volume_property.interpolation_type = 'nearest';
    #colorbar hacks. A lot of this is needed because
    #the colorbar doesn't use the LUT.
    if colorbar==True:
        if 'clabel' in kw:
            sb=mlab.scalarbar(object=v,title=kw['clabel']);
        else:
            sb=mlab.scalarbar(object=v);
        v.module_manager.scalar_lut_manager.title_text_property.font_family = 'courier';
        v.module_manager.scalar_lut_manager.label_text_property.font_family = 'courier';
        v.module_manager.scalar_lut_manager.title_text_property.italic = False;
        v.module_manager.scalar_lut_manager.label_text_property.bold = False;
        v.module_manager.scalar_lut_manager.label_text_property.italic = False;

    if test(kw,'render'):
        fig.scene.disable_render=False;
    else:
        fig.scene.disable_render=True;
    #setting colorbar range
    v.module_manager.scalar_lut_manager.use_default_range = False;
    v.module_manager.scalar_lut_manager.data_range = np.array([vlim[0], vlim[1]]);
    ret['v']=v;
    
    return ret;


def otf_type(vlim,otftype):
    '''Create the opacity transfer function based on options to this script.'''
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
    if (otftype=='new'):
        r = [(vlim[0], 0.0),
             (vlim[0] + (vlim[1]-vlim[0])*0.999,0.7),
             (vlim[1],0.0)];
        return otf_mkr(r,otf);
    return otf_mkr(mid_pt(*vs[otftype]),otf);

def render(name,vlim,angle,suppress=True,**kw):
    '''
    Render a single sclr file.

    Arguments:
      name -- A tuple of the form
    '''
    logprint("loading mlab");
    import mayavi.mlab as mlab;
    
    if len(name)==3:
        inname,outname,label = name;
    else:
        inname, outname, label, traj = name;
    
    if outname:
        print("hi");
        mlab.options.offscreen = True;
    #setting otf
    kw['otf']=otf_type(vlim,kw['otf']);
    d=volumetric(inname, mlab=mlab, vlim=vlim, **kw);
    #label
    if label:
        l = label;
        d['t'] = mlab.text(0.075,0.875, l, width=len(l)*0.015);
    #show the nubs
    kw['oa'] = mlab.orientation_axes(xlabel=kw['xlabel'],
                                ylabel=kw['ylabel'],
                                zlabel=kw['zlabel']);
    kw['oa'].marker.set_viewport(0,0,0.4,0.4);
    #setting the view
    mlab.view(elevation=angle[0],azimuth=angle[1],
              focalpoint='auto',distance='auto');
    mlab.roll(angle[2]);
    
    #doing the crazy trajectory stuff.
    if 'traj' in kw:
        #the first index into the start
        firsti = d['traj_firsti'] = kw['traj_firsti'] if 'traj_firsti' in kw else 0;#ugh
        step = d['traj_step'] = kw['traj_step'] if 'traj_step' in kw else 1;
        full_traj = readfile(traj);
        #the shape of each dimension is d[dimension,particle,step]
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
        d['tracks'] = tracks;
        d['traj_cur'] = cur_traj;
        d['traj_full'] = full_traj;
    d['fig'].scene.disable_render = False;
    d['image'] = mlab.screenshot();
    if not suppress:
        if not outname:
            logprint('showing');
            mlab.show();
        else:
            logprint('saving {}'.format(outname));
            #hack to avoid the lines, now mayavi really is headless
            imsave(outname, d['image']);
    return d;
    
def render_series(names_list,vlim,angle,**kw):
    '''
    Render a series of files. The names_list
    '''
    first = names_list[0];
    names_list = names_list[1:];
    logprint("processing first file {}...".format(first['in']));
    
    d = render(first,vlim,angle,**kw);
        
    for i,names in enumerate(names_list):
        logprint("processing {}...".format(names['in']))
        S=readfile(names['in']);
        if 'zeros' in kw and kw['zeros'] is not None:
            S=zero_range(S,kw['zeros']);
        if kw['log']: S=np.log10(S+0.1);
        d['fig'].scene.disable_render=True;
        d['v'].mlab_source.set(scalars=S);
        d['t'].text=names['label'];
        if 'traj' in kw:
            #lord have mercy
            d['traj_cur'][:,:,d['traj_firsti']+d['traj_step']]\
                = d['traj_full'][:,:,d['traj_firsti']+d['traj_step']];
            x = np.hstack(d['traj_cur'][0,:,:]);
            y = np.hstack(d['traj_cur'][1,:,:]);
            z = np.hstack(d['traj_cur'][2,:,:]);
            tracks.mlab_source.set(x=x,y=y,z=z);
        d['fig'].scene.disable_render=False;
        logprint("saving {}".format(names['out']));
        imsave(names['out'],mlab.screenshot());
    pass

    
if __name__=="__main__":
    main()
