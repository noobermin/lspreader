import numpy as np;
minE=0.5;
maxX=-15e-4;
def f(frame):
    data=frame['data'];
    E   = (np.sqrt(data['ux']**2+data['uy']**2+data['uz']**2+1)-1)*0.511;
    return np.logical_and(E>minE, data['x'] < maxX);
