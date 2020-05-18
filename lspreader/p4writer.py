'''
Writer for LSP output xdr files (.p4's)

'''
import xdrlib as xdr;
import re;
import numpy as np;
import gzip;
from pys import test;
import pys;
import sys;
import struct;
if sys.version_info >= (3,0):
    strenc = lambda b: b.decode('latin1');
else:
    strenc = lambda b: b;

def dump_string(f,s):
    sz = len(s)
    f.write(struct.pack('>ii',sz,sz));
    bs = s.encode('ascii') + (b'\0' * (4 - sz % 4) if (sz % 4 > 0) else b'');
    f.write(bs);

def dump_strlist(f,l):
    if type(l) == str: raise ValueError("expected list to dump_strlist");
    for s in l:
        dump_string(f,s);
    pass

def dump_intlist(f,l):
    if type(l) == str: raise ValueError("expected list to dump_intlist");
    for i in l:
        dump_int32(f,i);
    pass;

def dump_int32(f,i): f.write(struct.pack('>i',i));
def dump_float32(f,i): f.write(struct.pack('>f',i));

def dump_spec(f,fmt,*a):
    dumps = dict(
        s=dump_string,
        f=dump_float32,
        i=dump_int32);
    for s,i in zip(fmt,a):
        dumps[s](f,i);
    
        
def dump_header(f,header,**kw):
    hd = header;
    dmtype = hd['dump_type']
    dump_spec(f,'iiss',
              dmtype,
              hd['dversion'],
              hd['title'],
              hd['revision']);
    if dmtype == 1:
        dump_spec(f,'fiiiiii',
                  *destr(hd,
                         'timestamp','geometry','sflagsx','sflagsy','sflagsz',
                         'num_species','num_particles'));
        dump_int32(f,len(hd['params']));
        for _,unit in hd['params']:
            dump_string(f,unit);
        pass;
    elif dmtype == 2 or dmtype == 3:
        dump_spec(f, 'fii', *destr(hd,'timestamp','geometry','domains'));
        dump_int32(f,len(hd['quantities']));
        names,units = zip(*hd['quantities']);
        dump_strlist(f,names);
        dump_strlist(f,units);
    elif dmtype == 6:
        dump_spec(f,'iiii',*destr(hd,'geometry','sflagsx','sflagsy','sflagsz'));
        if not test(hd,'n_params'):
            print("warning: n_params not present, assuming n_params=11, may not be");
            print("         correct based on lsp compiler flags. Please use a");
            print("         newer version of lspreader to read the files!");
            dump_int32(f, 11);
            dump_intlist(f, [1]*11);
            dump_strlist(f, ['unit']*11);
        else:
            dump_int32(f, hd['n_params']);
            dump_intlist(f, hd['flags']);
            dump_strlist(f, hd['units']);
    elif dmtype == 10:
        dump_spec(f, 'ii', hd['geometry'], len(hd['quantities']));
        dump_strlist(f, hd['quantities']);
    else:
        raise ValueError("Unknown dump type {}".format(dmtype));

def dump_pext(f, pext):
    #amazing
    pextp = pext.byteswap();
    f.write(memoryview(pextp));
    
