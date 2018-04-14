'''
Reader for LSP output xdr files (.p4's)

'''
import xdrlib as xdr;
import re;
import numpy as np;
import gzip;
from pys import test,chunks;
import sys;
if sys.version_info >= (3,0):
    strenc = lambda b: b.decode('latin1');
else:
    strenc = lambda b: b;
#get basic dtypes
def get_int(file,N=1,forcearray=False):
    ret=np.frombuffer(file.read(4*N),dtype='>i4',count=N);
    #microoptimization for GB arrays, although fromstring works easier.
    ret.flags.writeable = True
    if N==1 and not forcearray:
        return ret[0];
    return ret;

def get_float(file,N=1,forcearray=False):
    ret=np.frombuffer(file.read(4*N),dtype='>f4',count=N);
    ret.flags.writeable = True
    if N==1 and not forcearray:
        return ret[0];
    return ret;

def get_str(file):
    l1 = get_int(file);
    l2 = get_int(file);
    if l1 != l2:
        print("warning, string prefixes are not equal...");
        print("{}!={}".format(l1,l2));
    size=l1;
    if l1%4:
        size+=4-l1%4;
    #fu python3
    return strenc(xdr.Unpacker(file.read(size)).unpack_fstring(l1));

def get_list(file,fmt):
    '''makes a list out of the fmt from the LspOutput f using the format
       i for int
       f for float
       d for double
       s for string'''
    out=[]
    for i in fmt:
        if i == 'i':
            out.append(get_int(file));
        elif i == 'f' or i == 'd':
            out.append(get_float(file));
        elif i == 's':
            out.append(get_str(file));
        else:
            raise ValueError("Unexpected flag '{}'".format(i));
    return out;
def get_dict(file,fmt,keys):
    return dict(
        zip(keys, get_list(file,fmt))
    );

def get_header(file,**kw):
    '''gets the header for the .p4 file, note that this
       Advanced the file position to the end of the header.
       
       Returns the size of the header, and the size of the header,
       if the header keyword is true.
    '''
    if type(file) == str:
        #if called with a filename, recall with opened file.
        if test(kw, "gzip") and kw['gzip'] == 'guess':
            kw['gzip'] = re.search(r'\.gz$', file) is not None;
        if test(kw, "gzip"):
            with gzip.open(file,'rb') as f:
                return get_header(f,**kw);
        else:
            with open(file,'rb') as f:
                return get_header(f,**kw);
    if test(kw, "size"):
        size = file.tell();
    header = get_dict(
        file,'iiss',
        ['dump_type','dversion', 'title','revision']);
    if header['dump_type'] == 1:
        #this is a particle dump file
        d = get_dict(file,
            'fiiii',
            ['timestamp','geometry','sflagsx','sflagsy','sflagsz']);
        header.update(d);
        #reading params
        
        header['num_species'] = get_int(file);
        header['num_particles'] = get_int(file);
        nparams = get_int(file);
        units = [get_str(file) for i in range(nparams)];
        labels = ['q', 'x', 'y', 'z', 'ux', 'uy', 'uz']
        if nparams == 7:
            pass;
        elif nparams == 8 or nparams == 11:
            labels += ['H']
        elif nparams == 10 or nparams == 11:
            labels += ['xi', 'yi', 'zi'];
        else:
            raise NotImplementedError(
                'Not implemented for these number of parameters:{}.'.format(n));
        header['params'] = list(zip(labels,units));
    elif header['dump_type'] == 2 or header['dump_type'] == 3:
        #this is a fields file or a scalars file.
        d = get_dict(file,'fii',['timestamp','geometry','domains']);
        header.update(d);
        #reading quantities
        n = get_int(file);
        names=[get_str(file) for i in range(n)];
        units=[get_str(file) for i in range(n)];
        header['quantities'] = list(zip(names,units));
    elif header['dump_type'] == 6:
        #this is a particle movie file
        d = get_dict(file,
            'iiii',
            ['geometry','sflagsx','sflagsy','sflagsz']);
        header.update(d);
        #reading params
        n = get_int(file);
        flags=[bool(get_int(file)) for i in range(n)];
        units=[get_str(file) for i in range(n)];
        labels=['q','x','y','z','ux','uy','uz','E'];
        if n == 8:
            pass;
        elif n == 7:
            labels = labels[:-1];
        elif n == 11:
            labels+=['xi','yi','zi'];
        else:
            raise NotImplementedError(
                'Not implemented for these number of parameters:{}.'.format(n));
        header['params'] = [
            (label,unit) for (label,unit,flag) in zip(labels,units,flags) if flag
        ];
    elif header['dump_type'] == 10:
        #this is a particle extraction file:
        header['geometry'] = get_int(file);
        #reading quantities
        n = get_int(file);
        header['quantities'] = [get_str(file) for i in range(n)];
    else:
        raise ValueError('Unknown dump_type: {}'.format(header['dump_type']));
    if test(kw,'size'):
        return header, file.tell()-size;
    return header;


def flds_argsort(d):
    '''
    Perform a lexsort to make a square array.
    '''
    return np.lexsort((d['z'],d['y'],d['x']));

def flds_shape(xs=None,ys=None,zs=None,d=None):
    '''
    Figure shape. Only works for square, structured data
    '''
    if xs is ys is zs is None:
        xs,ys,zs = d['xs'],d['ys'],d['zs']
    return [len(np.unique(i)) for i in [xs,ys,zs]];

def flds_firstsort(d,xs=None,ys=None,zs=None):
    '''
    Perform a lexsort and return the sort indices and shape as a tuple.
    '''
    return flds_argsort(d), flds_shape(d=d,xs=xs,ys=ys,zs=zs)


def flds_sort(d,s,shape=None):
    '''
    Sort based on position. Sort with s as a tuple of the sort
    indices and shape from first sort.

    Parameters:
    -----------

    d   -- the flds/sclr data
    s   -- (si, shape) sorting and shaping data from firstsort.
    shape -- if you want to add the shape separately, with s
             the argsort.
    '''
    labels = [ key for key in d.keys()
               if key not in ['t', 'xs', 'ys', 'zs', 'fd', 'sd'] ];
    if shape is None:
        si,shape = s;
    else:
        si=s;
    for l in labels:
        d[l] = d[l][si].reshape(shape);
        d[l] = np.squeeze(d[l]);
    return d;

def flds_concat_doms(doms,vprint,mempattern='fast'):
    '''
    Concatenate domains. Includes other memory patterns that probably
    don't really help if I'm honest.

    Parameters:
    -----------

    doms       -- domains
    vprint     -- vprinter, required
    mempattern -- memory pattern
    '''
    out=dict();
    if mempattern == 'memsave_1':
        keys = list(doms[0].keys());
        for k in keys:
            out[k] = np.concatenate([d[k] for d in doms]);
            for d in doms:
                del d[k];
    elif mempattern == 'memsave_2':
        keys = list(doms[0].keys());
        for k in keys:
            vprint("filtering for quantity '{}'".format(k));
            out[k] = doms[0][k]
            del doms[0][k];
            for i,d in enumerate(doms[1:]):
                vprint("processing domain {}".format(i));
                out[k] = np.concatenate((out[k],d[k]));
                del d[k]
    elif re.match('^chunk_', mempattern):
        keys = list(doms[0].keys());
        n = int(re.match('chunk_([0-9]+)',mempattern).group(1));
        vprint("dividing by {}-sized chunks".format(n));
        cs = chunks(doms, n);
        for k in keys:
            vprint("concatenating for quantity '{}'".format(k));
            out[k] = [];
            for i,ic in enumerate(cs):
                vprint('processing chunk {} of {}'.format(i,len(cs)-1));
                con = (out[k],) + tuple((di[k] for di in ic ))
                out[k] = np.concatenate(con)
                del con;
                for di in ic:
                    del di[k];
    else:
        out = { k : np.concatenate([d[k] for d in doms]) for k in doms[0] };
    return out;
        
def flds_shave_doms(doms,mins=None):
    dims = ['xs','ys','zs'];
    readqs = [k for k in doms[0].keys()
              if k not in dims ] if len(doms) > 0 else None;
    if mins is None:
        mins = [ min([d[l].min() for d in doms])
                 for l in dims ];
    def cutdom(d):
        ldim = [len(d[l]) for l in dims];
        cuts = [ np.isclose(d[l][0], smin)
                 for l,smin in zip(dims,mins) ];
        cuts[:] = [None if i else 1
                   for i in cuts];
        for quantity in readqs:
            d[quantity]=d[quantity].reshape((ldim[2],ldim[1],ldim[0]));
            d[quantity]=d[quantity][cuts[2]:,cuts[1]:,cuts[0]:].ravel();
        for l,cut in zip(dims,cuts):
            d[l] = d[l][cut:];
        return d;
    return [cutdom(d) for d in doms];


def read_flds_new(
        file, header, var, vprint,
        vector=True,keep_edges=False,
        return_array=False,**kw):
    vprint("!!Using new flds reader");
    loglvl=100;
    if vector:
        size=3;
        readin = set();
        for i in var:#we assume none of the fields end in x
            if i[-1] == 'x' or i[-1] == 'y' or i[-1] == 'z':
                readin.add(i[:-1]);
            else:
                readin.add(i);
    else:
        size=1;
        readin = set(var);
    doms = [];
    qs = [i[0] for i in header['quantities']];
    #get global array size
    start = file.tell();
    for i in range(header['domains']):
        #seek over indices
        iR, jR, kR = get_int(file, N=3);
        nI = get_int(file); xs = get_float(file,N=nI, forcearray=True);
        nJ = get_int(file); ys = get_float(file,N=nJ, forcearray=True);
        nK = get_int(file); zs = get_float(file,N=nK, forcearray=True);
        nAll=nI*nJ*nK;
        doms.append(dict(xs=xs,ys=ys,zs=zs,nAll=nAll,point=file.tell()));
        if (i+1) % loglvl == 0:
            vprint("{:04}...".format(i+1));
        file.seek(nAll*4*len(qs)*size,1);
    vprint("making grid");
    grid = [
        np.unique(np.array([d[l+'s'] for d in doms]).ravel())
        for l in 'xyz'];
    for g in grid:
       I = np.argsort(g)
    mins = [g[0] for g in grid];
    vprint("determining shave offs");
    for d in doms:
        Ps = [d['xs'],d['ys'],d['zs']]
        d['preshape']=(len(xs),len(ys),len(zs));
        d['sub'] = [ None if np.isclose(i[0],mn) else 1
               for i,mn in zip(Ps,mins) ];
        d['start'] = [ g.index(ip[0]) for g,ip in zip(grid,Ps) ]
    outsz = [ len(g) for g in grid ]
    vprint("Allocating output. If this fails, you don't have enough memory!");
    vprint("outsz of {} ({})".format(outsz,hex(outsz)));
    if size == 3:
        out = { iq+di:np.zeros(outsz)
                for iq in qs for di in 'xyz' };
    else:
        out = { iq:np.zeros(outsz) for iq in qs };
    #position in output
    outi = 0;
    vprint("reading quantities {}".format([q for q in qs if q in readin]));
    for i,dom in enumerate(doms):
        if (i+1) % loglvl == 0:
            vprint("reading domain {:04}...".format(i+1));
        file.seek(dom['point']);
        nAll = dom['nAll'];
        outend = outi+nAll;
        st = dom['start']
        for quantity in qs:
            if quantity not in readin:
                file.seek(nAll*4*size,1);
            else:
                data = get_float(file,N=nAll*size);
                if size == 1:
                    data = data.reshape(dom['preshape']);
                    data = data[sub[0]:,sub[1]:,sub[2]:]
                    datsh = data.shape;
                    out[quantity][st[0]:datsh[0],st[1]:datsh[1],st[2]:datsh[2]] = data;
                else:
                    datas = data.reshape(nAll,3).T;
                    for data,dim in zip(datas,'xyz'):
                        data = data.reshape(dom['preshape']);
                        data = data[sub[0]:,sub[1]:,sub[2]:]
                        datsh = data.shape
                        out[quantity+dim][st[0]:datsh[0],st[1]:datsh[1],st[2]:datsh[2]] = data;
                del data;
    for k in out:
        out[k] = out[k].astype('=f4',copy=False);
    grid[:] = [g.astype('=f4',copy=False) for g in grid];
    
    vprint('sorting rows, time this');
    #argsort = flds_firstsort(out,xs=xs,ys=ys,zs=zs)
    #out = flds_sort(out,argsort);
    return out;


def read_flds_unstructured(
        file, header, var, vprint,
        lims=None,
        vector=True,
        mempattern='fast',
        return_array=False,
        loglvl=100,
        **kw):
    vprint("!!Reading unstructured data");
    xlims = lims[0:2];
    ylims = lims[2:4];
    zlims = lims[4:6];
    if vector:
        size=3;
        readin = set();
        for i in var:#we assume none of the fields end in x
            if i[-1] == 'x' or i[-1] == 'y' or i[-1] == 'z':
                readin.add(i[:-1]);
            else:
                readin.add(i);
    else:
        size=1;
        readin = set(var);
    doms = [];
    qs = [i[0] for i in header['quantities']];
    for i in range(header['domains']):
        iR, jR, kR = get_int(file, N=3);
        #getting grid parameters (real coordinates)
        nI = get_int(file); Ip = get_float(file,N=nI, forcearray=True);
        nJ = get_int(file); Jp = get_float(file,N=nJ, forcearray=True);
        nK = get_int(file); Kp = get_float(file,N=nK, forcearray=True);
        nAll = nI*nJ*nK;
        if loglvl == 1:
            vprint('reading domain {} with dimensions {}x{}x{}={}.'.format(i,nI,nJ,nK,nAll));
        elif (i+1)%loglvl==0:
            vprint("reading domain {:04}...".format(i+1));
        d={}
        d['xs'], d['ys'], d['zs'] = Ip, Jp, Kp;
        d['z'], d['y'], d['x'] = np.meshgrid(Kp,Jp,Ip,indexing='ij')
        d['z'], d['y'], d['x'] = d['z'].ravel(), d['y'].ravel(), d['x'].ravel();
        good =np.logical_and(xlims[0] <= d['x'],d['x']<= xlims[1]);
        good&=np.logical_and(ylims[0] <= d['y'],d['y']<= ylims[1]);
        good&=np.logical_and(zlims[0] <= d['z'],d['z']<= zlims[1]);

        d['x'] = d['x'][good];
        d['y'] = d['y'][good];
        d['z'] = d['z'][good];
        
        d['xs'] = d['xs'][xlims[0] <= d['xs']];
        d['xs'] = d['xs'][xlims[1] >= d['xs']];
        d['ys'] = d['ys'][ylims[0] <= d['ys']];
        d['ys'] = d['ys'][ylims[1] >= d['ys']];
        d['zs'] = d['zs'][zlims[0] <= d['zs']];
        d['zs'] = d['zs'][zlims[1] >= d['zs']];
        
        for quantity in qs:
            if quantity not in readin:
                file.seek(nAll*4*size,1);
            else:
                data = get_float(file,N=nAll*size);
                if size==3:
                    data=data.reshape(nAll,3).T;
                    d[quantity+'x'] = data[0][good]
                    d[quantity+'y'] = data[1][good]
                    d[quantity+'z'] = data[2][good]
                else:
                    d[quantity] = data[good];
                del data
        doms.append(d);
    vprint('stringing domains together');
    vprint('mempattern used is {}'.format(mempattern));
    flds_concat_doms(doms, vprint, mempattern=mempattern);
        

def read_flds_restricted(
        file, header, var, vprint,
        lims=None,
        vector=True,keep_edges=False,
        argsort = None,first_sort=False,
        mempattern='fast',
        return_array=False,
        loglvl=100,
        **kw):
    vprint("!!Reading with restrictions");
    vprint("Possible issues with irregularly strided arrays.");
    xlims = lims[0:2];
    ylims = lims[2:4];
    zlims = lims[4:6];
    mins=[float('inf'),float('inf'),float('inf')];
    if vector:
        size=3;
        readin = set();
        for i in var:#we assume none of the fields end in x
            if i[-1] == 'x' or i[-1] == 'y' or i[-1] == 'z':
                readin.add(i[:-1]);
            else:
                readin.add(i);
    else:
        size=1;
        readin = set(var);
    doms = [];
    qs = [i[0] for i in header['quantities']];
    for i in range(header['domains']):
        iR, jR, kR = get_int(file, N=3);
        #getting grid parameters (real coordinates)
        nI = get_int(file); Ip = get_float(file,N=nI, forcearray=True);
        nJ = get_int(file); Jp = get_float(file,N=nJ, forcearray=True);
        nK = get_int(file); Kp = get_float(file,N=nK, forcearray=True);
        nAll = nI*nJ*nK;
        if loglvl < 1:
            vprint('reading domain {} with dimensions {}x{}x{}={}.'.format(i,nI,nJ,nK,nAll));
        elif (i+1)%loglvl==0:
            vprint("reading domain {:04}...".format(i+1));
        d={}
        d['xs'], d['ys'], d['zs'] = Ip, Jp, Kp;
        #lowest index will be minimum always
        if d['xs'][0] < mins[0]: mins[0] = d['xs'][0]
        if d['ys'][0] < mins[1]: mins[1] = d['ys'][0]
        if d['zs'][0] < mins[2]: mins[2] = d['zs'][0]
        
        d['z'], d['y'], d['x'] = np.meshgrid(Kp,Jp,Ip,indexing='ij')
        d['z'], d['y'], d['x'] = d['z'].ravel(), d['y'].ravel(), d['x'].ravel();
        good =np.logical_and(xlims[0] <= d['x'],d['x']<= xlims[1]);
        good&=np.logical_and(ylims[0] <= d['y'],d['y']<= ylims[1]);
        good&=np.logical_and(zlims[0] <= d['z'],d['z']<= zlims[1]);
        if np.max(good) == False:
            #entire domain is out of restriction
            #skip ahead
            file.seek(nAll*4*size*len(qs),1);
            continue;
        d['x'] = d['x'][good];
        d['y'] = d['y'][good];
        d['z'] = d['z'][good];
        d['xs'] = d['xs'][xlims[0] <= d['xs']];
        d['xs'] = d['xs'][xlims[1] >= d['xs']];
        d['ys'] = d['ys'][ylims[0] <= d['ys']];
        d['ys'] = d['ys'][ylims[1] >= d['ys']];
        d['zs'] = d['zs'][zlims[0] <= d['zs']];
        d['zs'] = d['zs'][zlims[1] >= d['zs']];
        
        for quantity in qs:
            if quantity not in readin:
                file.seek(nAll*4*size,1);
            else:
                data = get_float(file,N=nAll*size);
                if size==3:
                    data=data.reshape(nAll,3).T;
                    d[quantity+'x'] = data[0][good]
                    d[quantity+'y'] = data[1][good]
                    d[quantity+'z'] = data[2][good]
                else:
                    d[quantity] = data[good];
                del data
        doms.append(d);
    if not keep_edges:
        vprint("removing edges");
        doms = flds_shave_doms(doms,mins=mins)
    vprint('stringing domains together');
    vprint('mempattern used is {}'.format(mempattern));
    out = flds_concat_doms(doms,vprint,mempattern=mempattern)
    del doms;
    for k in out:
        out[k] = out[k].astype('=f4');
    if not argsort or first_sort:
        vprint('sorting rows...');
        argsort = flds_firstsort(out)
    out = flds_sort(out,argsort);
    del out['xs'], out['ys'], out['zs'];
    if return_array:
        vprint('stuffing into array'.format(k));
        keys = sorted(out.keys());
        dt = list(zip(keys,['f4']*len(out)));
        rout = np.zeros(out['x'].shape,dtype=dt);
        for k in keys:
            vprint('saving {}'.format(k));
            rout[k] = out[k];
        out=rout;
    if first_sort and not keep_edges:
        out = (out, argsort);
    return out;



def read_flds(
        file, header, var, vprint,
        vector=True,keep_edges=False,
        argsort=None,first_sort=False,
        keep_xs=False,
        mempattern='fast',
        return_array=False,
        loglvl=100,):
    if vector:
        size=3;
        readin = set();
        for i in var:#we assume none of the fields end in x
            if i[-1] == 'x' or i[-1] == 'y' or i[-1] == 'z':
                readin.add(i[:-1]);
            else:
                readin.add(i);
    else:
        size=1;
        readin = set(var);
    doms = [];
    qs = [i[0] for i in header['quantities']];
    vprint("reading quantities {}".format([q for q in qs if q in readin]));
    for i in range(header['domains']):
        iR, jR, kR = get_int(file, N=3);
        #getting grid parameters (real coordinates)
        nI = get_int(file); Ip = get_float(file,N=nI, forcearray=True);
        nJ = get_int(file); Jp = get_float(file,N=nJ, forcearray=True);
        nK = get_int(file); Kp = get_float(file,N=nK, forcearray=True);
        nAll = nI*nJ*nK;
        if loglvl < 2:
            vprint('reading domain {} with dimensions {}x{}x{}={}.'.format(
                i,nI,nJ,nK,nAll));
        elif (i+1)%loglvl==0:
            vprint('reading domain {:04}...'.format(i+1));
        d={}
        d['xs'], d['ys'], d['zs'] = Ip, Jp, Kp;
        d['z'], d['y'], d['x'] = np.meshgrid(Kp,Jp,Ip,indexing='ij')
        d['z'], d['y'], d['x'] = d['z'].ravel(), d['y'].ravel(), d['x'].ravel();
        for quantity in qs:
            if quantity not in readin:
                file.seek(nAll*4*size,1);
            else:
                d[quantity] = get_float(file,N=nAll*size);
                if size==3:
                    data=d[quantity].reshape(nAll,3).T;
                    d[quantity+'x'],d[quantity+'y'],d[quantity+'z']= data;
                    del data, d[quantity];
        doms.append(d);
    if not keep_edges:
        vprint("removing minimum edges in domains");
        doms = flds_shave_doms(doms);
    vprint('stringing domains together');
    vprint('mempattern used is {}'.format(mempattern));
    out=flds_concat_doms(doms,vprint,mempattern=mempattern);
    del doms;
    for k in out:
        out[k] = out[k].astype('=f4');
    if not argsort or first_sort:
        vprint('sorting rows...');
        argsort = flds_firstsort(out)
    out = flds_sort(out,argsort);
    if not keep_xs:
        del out['xs'],out['ys'],out['zs']
        if return_array:
            vprint('stuffing into array'.format(k));
            keys = sorted(out.keys());
            dt = list(zip(keys,['f4']*len(out)));
            rout = np.zeros(out['x'].shape,dtype=dt);
            for k in keys:
                vprint('saving {}'.format(k));
                rout[k] = out[k];
            out=rout;
    if first_sort and not keep_edges:
        out = (out, argsort);
    return out;

def iseof(file):
    c = file.tell();
    file.read(1);
    if file.tell() == c:
        return True;
    file.seek(c);
    
def read_movie(file, header):
    params,_  = zip(*header['params']);
    nparams = len(params);
    pbytes = (nparams+1)*4;
    frames=[];
    pos0 = file.tell(); 
    while not iseof(file):
        d=get_dict(file, 'fii',['t','step','pnum']);
        d['pos']=file.tell();
        file.seek(d['pnum']*pbytes,1);
        frames.append(d);
    for i,d in enumerate(frames):
        N = d['pnum'];
        dt = [('ip','>i4')]+list(zip(params,['>f4']*nparams));
        ndt= [('ip','=i4')]+list(zip(params,['=f4']*nparams));
        file.seek(d['pos']);
        arr = np.fromfile(file,dtype=dt,count=N).astype(ndt,copy=False);
        frames[i].update({'data':arr});
        del frames[i]['pos'];
    return frames;

def read_particles(file, header):
    params,_  = zip(*header['params']);
    dt = list(zip(('ip',)+params, ['>i4']+['>f4']*len(params)));
    ndt= [(i[0], re.sub(">","=",i[1])) for i in dt ];
    out = np.fromfile(file,dtype=dt,count=-1).astype(ndt,copy=False);
    return out;

def read_pext(file, header):
    nparams = len(header['quantities']);
    params = ['t','q','x','y','z','ux','uy','uz'];
    if nparams == 9:
        params+=['E'];
    elif nparams == 11:
        params+=['xi','yi','zi'];
    elif nparams == 12:
        params+=['E','xi','yi','zi'];
    #it's just floats here on out
    dt = list(zip(params, ['>f4']*len(params)));
    ndt= [ (i[0],'=f4') for  i in dt ];
    out = np.fromfile(file,dtype=dt,count=-1).astype(ndt,copy=False);
    return out;

def read(fname,**kw):
    '''
    Reads an lsp output file and returns a raw dump of data,
    sectioned into quantities either as an dictionary or a typed numpy array.

    Parameters:
    -----------

    fname -- filename of thing to read
    
    Keyword Arguments:
    ------------------

    vprint   --  Verbose printer. Used in scripts
    override --  (type, start) => A tuple of a dump type and a place to start
                 in the passed file, useful to attempting to read semicorrupted
                 files.
    gzip     --  Read as a gzip file.
    nobuffer --  Turn off file buffering. Default is on. This will not work with gzip
                 of course.

    flds/sclr Specific Arguments:
    -----------------------------
    var          -- list of quantities to be read. For fields, this can consist
                    of strings that include vector components, e.g., 'Ex'. If 
                    None (default), read all quantities.
    keep_edges   -- If set to truthy, then don't remove the edges from domains before
                    concatenation and don't reshape the flds data.
    argsort      -- If not None, sort using these indices, useful for avoiding
                    resorting.
    first_sort   -- If truthy, sort, and return the sort data for future flds
                    that should have the same shape.
    keep_xs      -- Keep the xs's, that is, the grid information. Usually redundant
                    with x,y,z returned.
    return_array -- If set to truthy, then try to return a numpy array with a dtype.
                    Requires of course that the quantities have the same shape.
    mempattern   -- Change the memory pattern used in order to try to save on memory.
                    Values can be "memsave_1" or "memsave_2"
    new_reader   -- Try the new field reader.
    restrict     -- Set coordinate restrictions as a 6-tuple. You must specify all 
                    dimension if you do this. This is an experimental reader.
    '''
    if test(kw,'gzip') and kw['gzip'] == 'guess':
        kw['gzip'] = re.search(r'\.gz$', fname) is not None;
    if test(kw,'gzip'):
        openf = gzip.open;
    else:
        if test(kw,'nobuffer'):
            print("not buffering");
            openf = lambda fname,mode: open(fname,mode,buffering=0)
        else:
            openf=open;
    with openf(fname,'rb') as file:
        if test(kw,'override'):
            dump, start = kw['override'];
            file.seek(start);
            header = {'dump_type': dump};
            if not test(kw, 'var') and 2 <= header['dump_type'] <= 3 :
                raise ValueError(
                    "If you want to force to read as a scalar, you need to supply the quantities"
                );
        else:
            header = get_header(file);
        vprint = kw['vprint'] if test(kw, 'vprint') else lambda s: None;
        if 2 <= header['dump_type'] <= 3 :
            fldscall = read_flds;
            if not test(kw, 'var'):
                var=[i[0] for i in header['quantities']];
            else:
                var=kw['var'];
            keep_edges = test(kw, 'keep_edges');
            first_sort = test(kw, 'first_sort');
            if test(kw,'argsort'):
                argsort = kw['argsort']
            else:
                argsort = None;
            keep_xs = test(kw, 'keep_xs');
            return_array = test(kw, 'return_array');
            mempattern='fast';
            if test(kw,'mempattern'):
                mempattern = kw['mempattern'];
                if mempattern not in [None, 'memsave_1', 'memsave_2'] or re.match("^chunk_",mempattern):
                    print("warning: unrecognized mempattern {}, using default".format(
                        mempattern));
                if mempattern is None:
                    mempattern = 'fast';
            if test(kw,'new_reader'):
                fldscall = read_flds_new;
            elif test(kw, 'restrict'):
                fldscall = lambda *arg, **kw2: read_flds_restricted(*arg,lims=kw['restrict'],**kw2)
        readers = {
            1: lambda: read_particles(file, header),
            2: lambda: fldscall(
                file,header,var,vprint,
                keep_edges=keep_edges,
                first_sort=first_sort,
                argsort=argsort,
                keep_xs=keep_xs,
                return_array=return_array,
                mempattern=mempattern,),
            3: lambda: fldscall(
                file,header,var, vprint,
                keep_edges=keep_edges,
                first_sort=first_sort,
                argsort=argsort,
                keep_xs=keep_xs,
                return_array=return_array,
                mempattern=mempattern,
                vector=False),
            6: lambda: read_movie(file, header),
            10:lambda: read_pext(file,header)
        };
        if header['dump_type'] not in readers:
            raise NotImplementedError("Other file types not implemented yet!");
        d = readers[header['dump_type']]();
    return d;
