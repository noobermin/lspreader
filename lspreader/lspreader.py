'''
Reader for LSP output xdr files (.p4's)

'''
import xdrlib as xdr;
import re;
import numpy as np;
import gzip;
from pys import test;

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
    return xdr.Unpacker(file.read(size)).unpack_fstring(l1);

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
            with gzip.open(file,'r') as f:
                return get_header(f,**kw);
        else:
            with open(file,'r') as f:
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
        
        ns = get_int(file);
        n = get_int(file);
        header['units'] = [get_str(file) for i in range(n)];
        labels = ['q', 'x', 'y', 'z', 'ux', 'uy', 'uz']
        if n == 7:
            pass;
        elif n == 8 or n == 11:
            labels += ['H']
        elif n == 10 or n == 11:
            labels += ['xi', 'yi', 'zi'];
        else:
            raise NotImplementedError(
                'Not implemented for these number of parameters:{}.'.format(n));
        header['params'] = list(zip(labels,header['units']));
    if header['dump_type'] == 2 or header['dump_type'] == 3:
        #this is a fields file or a scalars file.
        d = get_dict(file,'fii',['timestamp','geometry','domains']);
        header.update(d);
        #reading quantities
        n = get_int(file);
        names=[get_str(file) for i in range(n)];
        units=[get_str(file) for i in range(n)];
        header['quantities'] = zip(names,units);
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


def flds_firstsort(d):
    '''
    Perform a lexsort and return the sort indices and shape as a tuple.
    '''
    shape = [ len( np.unique(d[l]) )
              for l in ['xs', 'ys', 'zs'] ];
    si = np.lexsort((d['z'],d['y'],d['x']));
    return si,shape;
def flds_sort(d,s):
    '''
    Sort based on position. Sort with s as a tuple of the sort
    indices and shape from first sort.

    Parameters:
    -----------

    d   -- the flds/sclr data
    s   -- (si, shape) sorting and shaping data from firstsort.
    '''
    labels = [ key for key in d.keys()
               if key not in ['t', 'xs', 'ys', 'zs', 'fd', 'sd'] ];
    si,shape = s;
    for l in labels:
        d[l] = d[l][si].reshape(shape);
        d[l] = np.squeeze(d[l]);
    return d;
def read_flds(file, header, var, vprint,
              vector=True,keep_edges=False,
              sort=None,first_sort=False):
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
        vprint('reading domain with dimensions {}x{}x{}={}.'.format(nI,nJ,nK,nAll));
        d={}
        d['xs'], d['ys'], d['zs'] = Ip, Jp, Kp;
        d['z'], d['y'], d['x'] = np.meshgrid(Kp,Jp,Ip,indexing='ij')
        d['z'], d['y'], d['x'] = d['z'].ravel(), d['y'].ravel(), d['x'].ravel();
        for quantity in qs:
            if quantity not in readin:
                vprint('skipping {}'.format(quantity));
                file.seek(nAll*4*size,1);
            else:
                vprint('reading {}'.format(quantity));
                d[quantity] = get_float(file,N=nAll*size);
                if size==3:
                    data=d[quantity].reshape(nAll,3).T;
                    d[quantity+'x'],d[quantity+'y'],d[quantity+'z']= data;
                    del data, d[quantity];
        doms.append(d);
    if not keep_edges:
        vprint("removing edges");
        dims = ['xs','ys','zs'];
        readqs = [k for k in doms[0].keys()
                  if k not in dims ] if len(doms) > 0 else None;
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
        doms[:] = [cutdom(d) for d in doms];
    vprint('Stringing domains together.');
    out = { k : np.concatenate([d[k] for d in doms]) for k in doms[0] };
    for k in out:
        out[k] = out[k].astype('f4');
    if not keep_edges:
        vprint('sorting....');
        sort = flds_firstsort(out)
        out = flds_sort(out,sort);
        if first_sort:
            out = (out, sort);
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
        lt=[('ip','>i4')]+zip(params,['>f4']*nparams);
        file.seek(d['pos']);
        arr=np.frombuffer(file.read(N*4*len(lt)),dtype=np.dtype(lt),count=N);
        arr.flags.writeable = True;
        frames[i].update({'data':arr});
        del frames[i]['pos'];
    return frames;

def read_particles(file, header):
    params,_  = zip(*header['params']);
    dt = list(zip(params, ['>i4']+['>f4']*len(params)));
    out = np.fromfile(file, dtype=dt,count=-1);
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
    out = np.fromfile(file,dtype=dt,count=-1);
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

    flds/sclr Specific Arguments:
    -----------------------------
    var          -- list of quantities to be read. For fields, this can consist
                    of strings that include vector components, e.g., 'Ex'. If 
                    None (default), read all quantities.
    keep_edges   -- If set to truthy, then don't remove the edges from domains before
                    concatenation and don't reshape the flds data.
    sort         -- If not None, sort using these indices, useful for avoiding
                    resorting. If True and not an ndarray, just sort.
    first_sort   -- If truthy, sort, and return the sort data for future flds
                    that should have the same shape.
    '''
    if test(kw,'gzip') and kw['gzip'] == 'guess':
        kw['gzip'] = re.search(r'\.gz$', fname) is not None;
    openf = gzip.open if test(kw, 'gzip') else open;
    with openf(fname,'rb') as file:
        if test(kw,'override'):
            dump, start = kw['override'];
            file.seek(start);
            header = {'dump_type': dump};
            if not test(kw, 'var') and 2 <= header['dump_type'] <= 3 :
                raise ValueError("If you want to force to read as a scalar, you need to supply the quantities")
        else:
            header = get_header(file);
        
        vprint = kw['vprint'] if test(kw, 'vprint') else lambda s: None;
        if 2 <= header['dump_type'] <= 3 :
            if not test(kw, 'var'):
                var=[i[0] for i in header['quantities']];
            else:
                var=kw['var'];
            keep_edges = test(kw, 'keep_edges');
            first_sort = test(kw, 'first_sort');
            if test(kw,'sort'):
                sort = kw['sort']
            else:
                sort = None;
        readers = {
            1: lambda: read_particles(file, header),
            2: lambda: read_flds(
                file,header,var,vprint,
                keep_edges=keep_edges,
                first_sort=first_sort,
                sort=sort),
            3: lambda: read_flds(
                file,header,var, vprint,
                keep_edges=keep_edges,
                first_sort=first_sort,
                sort=sort,
                vector=False),
            6: lambda: read_movie(file, header),
            10:lambda: read_pext(file,header)
        };
        
        try:
            d = readers[header['dump_type']]();
        except KeyError:
            raise NotImplementedError("Other file types not implemented yet!");
    return d;
