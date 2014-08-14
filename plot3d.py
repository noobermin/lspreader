#!/usr/bin/env python
import numpy as np;
import cPickle;
from docopt import docopt;
import re;
import math;
usage='''Render volumetric render of a scalar field

Usage:
  plot3d.py [options] IN_FORMAT OUT_FORMAT LABEL_FORMAT <lownum> <highnum>
  plot3d.py [options] (--plot-single | -s) INFILE

Options:
   --min=MIN -n MIN             Set vmin in the volumetric plot to MIN.
   --max=MAX -x MAX             Set vmax in the volumetric plot to MAX.
   --plot-single -s             Just show, don't output, single scalar.
'''

def read_file(filename):
    print('loading file {}'.format(filename));
    with open(filename,'rb') as f:
        d=cPickle.load(f);
    return d;

def tozero(v):
    if math.isnan(v):
        return 0;
    else:
        return v;

def zero_nan(S):
    return np.array([[[tozero(k) for k in j] for j in i] for i in S]);

def plot(names,vmin,vmax):
    print("loading mlab");
    import mayavi.mlab as mlab;
    mlab.options.offscreen = True;
    outname,inname,label = names[0];
    names = names[1:];
    print("processing first file {}...".format(inname));
    S=read_file(inname);
    S=np.log10(zero_nan(S)+0.1);
    fig=mlab.figure(size=(1280,1024));
    fig.scene.disable_render=True;
    src=mlab.pipeline.scalar_field(S);
    #volume rendering
    v=mlab.pipeline.volume(src,vmin=vmin,vmax=vmax);
    #cut plane 1
    #zp=mlab.pipeline.image_plane_widget(src,plane_orientation="x_axes",
    #                                    slice_index=50,vmin=vmin,vmax=vmax);
    mlab.view(azimuth=0,elevation=150,focalpoint='auto',distance='auto');
    mlab.scalarbar(object=v,title="log10 of number density");
    #Unfortunately, the volume renderer doesn't work out of the box.
    #The main issue is the colorbar. So, we do this instead.
    e=mlab.get_engine();
    module_manager = e.scenes[0].children[0].children[0];
    module_manager.scalar_lut_manager.use_default_range = False;
    module_manager.scalar_lut_manager.data_range = np.array([vmin, vmax]);
    t=mlab.text(0.075,0.875,label,width=0.1);
    fig.scene.disable_render=False;
    print("saving {}".format(outname));
    mlab.savefig(outname,size=(1280,1024));
    for outname,inname,label in names:
        print("processing {}...".format(inname))
        S=read_file(inname);
        S=np.log10(zero_nan(S)+0.1);
        fig.scene.disable_render=True;
        v.mlab_source.set(scalars=S);
        #zp.mlab_source.set(scalars=S);
        t.text=label;
        fig.scene.disable_render=False;
        print("saving {}".format(outname));
        mlab.savefig(outname,size=(1280,1024));
    pass

def plot_single(inname,vmin,vmax):
    print("loading mlab");
    import mayavi.mlab as mlab;
    #mlab.options.offscreen = True;
    S=read_file(inname);
    S=np.log10(zero_nan(S)+0.1);
    fig=mlab.figure(size=(1280,1024));
    fig.scene.disable_render=True;
    src=mlab.pipeline.scalar_field(S);
    #volume rendering
    v=mlab.pipeline.volume(src,vmin=vmin,vmax=vmax);
    #cut plane 1
    #zp=mlab.pipeline.image_plane_widget(src,plane_orientation="x_axes",
    #                                    slice_index=50,vmin=vmin,vmax=vmax);
    mlab.view(azimuth=0,elevation=150,focalpoint='auto',distance='auto');
    mlab.scalarbar(object=v,title="log10 of number density");
    #Unfortunately, the volume renderer doesn't work out of the box.
    #The main issue is the colorbar. So, we do this instead.
    e=mlab.get_engine();
    module_manager = e.scenes[0].children[0].children[0];
    module_manager.scalar_lut_manager.use_default_range = False;
    module_manager.scalar_lut_manager.data_range = np.array([vmin, vmax]);
    fig.scene.disable_render=False;
    print('plotting');
    mlab.show();


    
if __name__=="__main__":
    #reading in arguments
    opts=docopt(usage,help=True);
    vmin = float(opts['--min']) if opts['--min'] else -1;
    vmax = float(opts['--max']) if opts['--max'] else 23.5;
    if not opts['--plot-single']:
        if '*' not in opts['IN_FORMAT'] or '*' not in opts['OUT_FORMAT']:
            print(usage);
            quit(1);
        lownum=int(opts['<lownum>']);
        highnum=int(opts['<highnum>']);
        fmt='{{:0>{}}}'.format(len(opts['<highnum>']))
        out_fmt=re.sub(r'\*',fmt,opts['OUT_FORMAT']);
        in_fmt =re.sub(r'\*',fmt,opts['IN_FORMAT']);
        label_fmt=re.sub(r'\*',fmt,opts['LABEL_FORMAT']);
        numrange = range(lownum,highnum+1);
        outnames = [out_fmt.format(i) for i in numrange];
        innames = [in_fmt.format(i) for i in numrange];
        labels = [label_fmt.format(i) for i in numrange];
        files = zip(outnames,innames,labels);
        plot(files,vmin,vmax);
    else:
        plot_single(opts['INFILE'],vmin,vmax);
    pass;
pass;
