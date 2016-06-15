'''
For parsing .lsp files.
'''
import re;
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
