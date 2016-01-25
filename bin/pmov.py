#!/usr/bin/env python2
'''
Read a pmovie. In the absense of an output name, output
the name based on the frame step. With an output name, and
when not outputting directly to hdf, output using dump_pickle.

Usage:
    pmov.py [options] <input> [<output>]
    pmov.py [options] [--hdf | -H ] <input> <output>

Options:
    --help -h         Output this help.
    --sort -s         Sort the pmovies by IPP.
    --hdf -H          Output to hdf5 instead of to a pickle file.
                      The group will be based on the step.
    --zip -c          Use compression for hdf5.
    --verbose -v      Be verbose.
    --lock=L -l L     Specify a lock file for synchronized output for hdf5.
    --hash=HFILE      Hashing. It might work only for uniform
                      grids. Specify specification file used to generate hash
                      as HASHFILE.
    --firsthash=HFILE Specify first hashing, see above. Use this file as the
                      first file to generate the hash specification from and
                      output to DFILE.
    --dir=D -D D      Output to this directory if given not <output> name.
    --X -x            Use X as a spatial dimension. Similar options below are
                      for Y and Z. If none are passed, assume 3D cartesian.
    --Y -y            See above.
    --Z -z            See above.
'''
from lspreader import lspreader as rd;
from lspreader.pmovie import firsthash, genhash, addhash, sortframe
from lspreader.misc import dump_pickle, h5w, mkvprint,  readfile;
from docopt import docopt;
import h5py as h5;
import numpy as np;

def hdfoutput(outname, frames, dozip=False):
    '''Outputs the frames to an hdf file.'''
    with h5.File(outname,'a') as f:
        for frame in frames:
            group=str(frame['step']);
            h5w(f, frame, group=group,
                compression='lzf' if dozip else None);

if __name__=='__main__':
    opts = docopt(__doc__,help=True);
    vprint = mkvprint(opts);
    dims=[]
    if opts['--X']: dims.append('xi');
    if opts['--Y']: dims.append('yi');
    if opts['--Z']: dims.append('zi');
    if len(dims)==0:
        dims=['xi','yi','zi'];
    #reading in using the reader.
    frames=rd.read(opts['<input>']);
    
    if opts['--sort']:
        vprint("sorting...");
        frames[:] = [sortframe(frame) for frame in frames];
        vprint("done");
    #experimental hashing
    if opts['--firsthash']:
        d=firsthash(frames[0],dims, removedupes=True);
        dump_pickle(opts['--firsthash'], d);
        frames[:] = [addhash(frame,d,removedupes=True) for frame in frames];
    elif opts['--hash']:
        d = readfile(opts['--hash'],dumpfull=True);
        frames[:] = [addhash(frame,d,removedupes=True) for frame in frames];
    #outputting.
    if opts['--hdf']:
        import fasteners;
        output = lambda :hdfoutput(opts['<output>'], frames, opts['--zip']);
        if opts['--lock']:
            output = fasteners.interprocess_locked(opts['--lock'])(output);
        output();
    elif not opts['<output>']:
        for frame in frames:
            outname = "{}.{}".format(opts['<input>'],frame['step']);
            if opts['--dir']:
                outname = '{}/{}'.format(opts['--dir'], outname);
            np.savez(outname, **frame);
    else:
        dump_pickle(opts['<output>'], frames);
