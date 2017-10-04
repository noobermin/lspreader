import numpy as np;
minE=0.5;
def f(frame):
    data=frame['data'];
    E   = (np.sqrt(data['ux']**2+data['uy']**2+data['uz']**2+1)-1)*0.511;
    return E>minE;
