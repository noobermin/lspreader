'''
Miscellaneous definitions.
'''

import cPickle as pickle;
import numpy as np;
from matplotlib import colors;

def conv(arg,default=None,func=None):
    if func:
        return func(arg) if arg else default;
    else:
        return arg if arg else default;

def read(filename,dictlabel='s', dumpfull=False):
    with open(filename,'r') as f:
        d=pickle.load(f);
    if type(d) == np.ndarray or dumpfull:
        return d;
    elif type(d) == dict:
        return d[dictlabel];
    else:
        s = str(type(d));
        errstr='Unknown pickle type "{}" loaded from file "{}".'.format(s,filename);
        raise IOError(errstr);
    pass;

cmap_min = 0.001;
def rgbfromhsv(h,s=None,v=None,split=True):
    if  s is None and v is None:
        hsv = h.T;
    elif s is not None and v is not None:
        hsv = np.array([h,s,v]).T;
    else:
        raise ValueError("Usage of rgbfromhsv is incorrect.");
    rgb = colors.hsv_to_rgb(hsv);
    rgb=np.array([rgb,rgb]);
    rgb[0,0,:]=1.0;
    inter = np.linspace(cmap_min, 1.0, rgb.shape[1]);
    inter = np.array([inter,inter,inter]);
    rgb = np.concatenate(([inter.T],rgb));
    top = np.array([[[0.0,1.0,1.0]]]*3);
    rgb = np.concatenate((top,rgb.T),axis=1);
    if split:#     r      g      b
        return rgb[0],rgb[1],rgb[2];
    else:
        return rgb;
    pass;
    
def cmap(r,g=None,b=None):
    if g is None and b is None:
        r,g,b = r;
    cd={'red':r,'green':g,'blue':b};
    return colors.LinearSegmentedColormap('cmap',cd, 1024);

_pastel_h = np.linspace(0.0, 0.8, 9);
_pastel_s = np.ones(_pastel_h.shape)*0.6;
_pastel_v = np.ones(_pastel_h.shape);
_pastel_hsv = np.array([_pastel_h,_pastel_s,_pastel_v]);
_pastel_rgb = rgbfromhsv(_pastel_hsv,split=False)
pastel = cmap(_pastel_rgb);

def mkstrip(rgb,vmin,vmax,val,
            strip=[1.0,0.0,0.0]):
    val = (val-vmin)/(vmax-vmin);
    strip = np.array(strip);
    rng = rgb[0,:,0];
    
    for i,v in enumerate(rng):
        if v > val: break;
    #finding the good point
    dx = (val-rng[i-1])/(rng[i]-rng[i-1]);
    ep = 0.03
    #interpolating
    b = (rgb[:,i,:]-rgb[:,i-1,:])*(dx-ep)+rgb[:,i-1,:];
    a = (rgb[:,i,:]-rgb[:,i-1,:])*(dx+ep)+rgb[:,i-1,:];
    #setting the strip color
    b[:,2] = a[:,1] = strip;
    c = np.concatenate([b.T,a.T]).T.reshape(3,2,3);
    #and placing it inside rgb
    return np.concatenate((rgb[:,:i,:],c,rgb[:,i:,:]),axis=1);

mkstrip_cmap = lambda vmin, vmax, val, strip=[1.0,0.0,0.0]: cmap(mkstrip(_pastel_rgb,
                                                                         vmin, vmax, val,
                                                                         strip));
