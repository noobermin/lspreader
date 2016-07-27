'''
For parsing .lsp files.
'''
import re;
import numpy as np;
getrx = lambda rx:float(re.search(rx,lines,flags=re.MULTILINE).group(1));

def getdim(lsp):
    '''
    Obtain the dimensionality of a .lsp file

    Parameters:
    -----------
       lsp      : .lsp string

    Returns a list of dimensions.
    '''
    dims= ['x','y', 'z'];
    rxs = ['{}-cells *([0-9]+)'.format(x) for x in ['x','y','z']];
    return [
        x for x,rx in zip(dims,rxs)
        if re.search(rx,lsp) and int(re.search(rx,lsp).group(1)) > 0 ];

def getpexts(lsp):
    '''
    Get information from pext planes.

    Parameters:
    -----------

      lsp       : .lsp string

    Returns a list of dicts with information for all pext planes
    '''
    lines=lsp.split('\n');
    #unfortunately regex doesn't work here
    lns,planens = zip(
        *[ (i,int(re.search('^ *extract *([0-9]+)',line).group(1)))
           for i,line in enumerate(lines)
           if re.search('^ *extract *[0-9]+', line)]);
    if len(lns) == 0: return [];
    end = lns[-1];
    
    for i,line in enumerate(lines[end+1:]):
        if re.match(' *\[',line): break;
    end += i;
    lineranges = zip(lns,(lns+(end,))[1:]);
    planes=dict()
    for (i,end),plane in zip(lineranges,planens):
        d=dict();
        labels = [
            'species',
            'direction',
            'position',];
        datarx = [
            '^ *species *([0-9]+)',
            '^ *direction *([xXyYzZ])',
            '^ *at *(.*)',];
        convs  = [
            lambda s: int(s),
            lambda i: i,
            lambda s: np.array(
                map(float,s.split(' '))),
        ];
        for line in lines[i:end]:
            for label,rx,conv in zip(labels,datarx,convs):
                if re.match(rx,line):
                    d[label]=conv(re.match(rx,line).group(1));
                pass
            pass
        planes[plane] = d;
    return planes;
    
    
