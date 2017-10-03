#!/usr/bin/env python
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
    --gzip -Z         File is gzipped.
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
    --x -x            Use X as a spatial dimension. Similar options below are
                      for Y and Z. If none are passed, guess based on .lsp file
                      in the directory of input.
    --y -y            See above.
    --z -z            See above.
'''
from lspreader import lspreader as rd;
from lspreader.pmovie import firsthash, genhash, addhash, sortframe
from lspreader.misc import h5w;
from pys import dump_pickle, load_pickle, mkvprint;
from docopt import docopt;
import h5py as h5;
import numpy as np;
import re;

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
    #reading in using the reader.
    frames=rd.read(opts['<input>'], gzip='guess');
    if opts['--sort']:
        vprint("sorting...");
        frames[:] = [sortframe(frame) for frame in frames];
        vprint("done");
    #experimental hashing
    if opts['--firsthash'] or opts['--hash']:
        if opts['--firsthash']:
            d=firsthash(frames[0], removedupes=True);
            dump_pickle(opts['--firsthash'], d);
        else:
            d = load_pickle(opts['--hash']);
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
