#!/usr/bin/env python2
'''
Generate a monolithic pbs script for a reading pmovies.

Usage: 
    ./pmovie-prep.py [options] <workdir>

Options:
    --help -h                  Print this help.
    --nodes=N -n N             Number of utilized nodes. [default: 1]
    --server=SERVER            Tune for this server. [default: ramses]
    --scanner=SCANSCRIPT       Use this scan script. [default: Escan.py]
    --conv-opts=OPTS           Add these opts to pmov.py. [default: ]
    --scan-opts=OPTS           Add these opts to the chosen scanner. [default: ]
    --outdir=OUT -o OUT        Specify an output directory for pbsscripts [default: .]
    --ramses-node=NODE         Submit to a specific ramses node.
    --filelist=LS -l LS        Supply a directory listing if the directory is
                               unreachable for this script.
    --dotlsp=DOT -. DOT        Supply a .lsp file if it is unreachable for this
                               script.
'''
import subprocess;
import numpy as np;
import re;
from docopt import docopt;

opts = docopt(__doc__,help=True);
workdir = opts['<workdir>'];

def call(cmd):
    return subprocess.check_output(cmd).split('\n');

def filelines(fname,strip=False):
    with open(fname,'r') as f:
        lines = f.readlines();
    if strip:
        lines[:] = [line.strip() for line in lines]
    return lines;

if not opts['--filelist']:
    ls = call(('ls',workdir))
else:
    ls = filelines(opts['--filelist'],strip=True);
# filtering for pmovies
pmovierx=re.compile(r"pmovie([0-9]+).p4$");
lspmovies = [(s, int(pmovierx.match(s).group(1)))
             for s in ls if pmovierx.match(s)];
lspmovies.sort(key=lambda i: i[1]);
if len(ls) == 0:
    raise ValueError("I see no pmovies in {}.".format(workdir));
sortedmovies = [i[0] for i in lspmovies];
#reading .lsp file to find information
if not opts['--dotlsp']:
    dotlsprx = re.compile(r".*\.lsp");
    dotlsp = [s for s in ls if dotlsprx.match(s)][0];
else:
    dotlsp = opts['--dotlsp'];
dotlsp = filelines(dotlsp,strip=True);

#Figure out the dimensionality of the simulation.
#Another possiblity is to read the output dir which
#has compiler flags. This will work for now as long
#as the .lsp file is cleanish. Basically search for the
#Grid and look for the *-cells entries
cellrxs=[re.compile(r"^{}-cells +[0-9]+".format(dim))
         for dim in ['x','y','z']]
dims =  [ np.array([rx.match(line) for line in dotlsp]).max()
          for rx in cellrxs ]
dims = [dim for dim,isdim in zip(['x','y','z'],dims) if isdim];
dims_flag = ' -{} '.format(''.join(dims));

#providing for different settings which varies
#by server.
server_settings = {
    #          maxproc ppn  hours  mins
    'ramses': [23,     48,   999,      0],
    'glenn':  [8,       8,    48,      0]
};
try:
    maxproc,ppn,hours,mins = server_settings[opts['--server']];
except KeyError as k:
    print('Invalid server "{}"'.format(k));
    exit(1);

#template for PBS script output
headert='''
#PBS -l walltime={hours}:{mins}:00
#PBS -l nodes=1:ppn={ppn}{ramsesnode}
#PBS -S /bin/bash
#PBS -j oe
#PBS -N pmovie-conv-{post}

source $HOME/.bashrc
source $HOME/conda
LOGFILE=$PBS_O_WORKDIR/pmovie-conv-{post}.log
MAXPROC={maxproc}
WORKDIR={workdir}
cd $WORKDIR
>$LOGFILE
'''
#what follows are different sections of the pbscript


#conversion
#convert first file
convertt_first='''
PMOVDIR=$WORKDIR/pmovie-conv
[ ! -d $PMOVDIR ] && mkdir $PMOVDIR;

FIRSTPMOV={firstfile}
./pmov.py {convopts} -D $PMOVDIR --exp-first=./hash.d $FIRSTPMOV
#get first file in case first file has multiple frames

FIRSTNPZ=$(ls $PMOVDIR | grep '{firstfile}.*\.npz$' | head -n 1)
./orig.py $PMOVDIR/$FIRSTNPZ orig
'''

convertt='''
echo "starting mass conversion at $(date)">>$LOGFILE
#these are files other than the first
FILES=$(ls $WORKDIR | grep -v $FIRSTPMOV )
for i in $FILES; do
    while [ $(pgrep -f pmov.py  |  wc -l ) -ge $MAXPROC ]; do sleep 5; done; 
    echo "convert: running $i">>$LOGFILE
    sleep 0.2;
    ./pmov.py {convopts} -D pmovie-conv  --exp-d=./hash.d $i &
done

while [ $(pgrep -f pmov.py | wc -l) -gt 0 ]; do
    echo "waiting for $(pgrep -f pmov.py | wc -l) process(es)">>$LOGFILE
    echo "call deq to end">>$LOGFILE
    sleep 5;
done
'''

#global scans
scant='''
FILES="$(ls $PMOVDIR | grep .npz);"
SCANSCRIPT={scanscript}
SCANDIR=pmovie-scan
[ ! -d $PMOVDIR ] && mkdir $SCANDIR;

echo "scanning files at $(date)">>$LOGFILE
for i in $FILES; do
    while [ $(pgrep -f $SCANSCRIPT  |  wc -l ) -ge $MAXPROC ]; do sleep 5; done;
    OUTNAME="found$(echo $i | sed 's/^.*p4\.\([0-9]\+\).npz$/\1/')"
    echo "scan: running $i into $OUTNAME">>$LOGFILE
    sleep 0.2;
    ./$SCANSCRIPT {scanopts} $PMOVDIR/$i $SCANDIR/$OUTNAME &
done
while [ $(pgrep -f $SCANSCRIPT | wc -l) -gt 0 ]; do
    echo "waiting for $(pgrep -f Escan.py | wc -l) process(es)">>$LOGFILE
    echo "call deq to end">>$LOGFILE
    sleep 5;
done
'''

gathert='''
#now, gather the matches
echo "gathering searches at $(date)">>$LOGFILE
./gather.py -ui ./orig.npy $SCANDIR'found.*.npy' $SCANDIR/selected.npy &>>$LOGFILE
rm "$SCANDIR/found*.npy
'''
#trajectory finding
searcht='''
FILES=$(ls $PMOVDIR | grep .npz);
#now, we search
echo "searching for files at $(date)">>$LOGFILE
for i in $FILES; do
    while [ $(pgrep -f search.py  |  wc -l ) -ge $MAXPROC ]; do sleep 5; done;
    OUTNAME="traj$(echo $i | sed 's/^.*p4\.\([0-9]\+\).npz$/\1/')"
    echo "search: searching $i into $OUTNAME">>$LOGFILE
    sleep 0.2;
    ./search.py $PMOVDIR/$i $SCANDIR/selected.npy $SCANDIR/$OUTNAME &
done
while [ $(pgrep -f search.py | wc -l) -gt 0 ]; do
    echo "waiting for $(pgrep -f search.py | wc -l) process(es)">>$LOGFILE
    echo "call deq to end">>$LOGFILE
    sleep 5;
done
'''
trajt='''
echo "gathering for trajectories $(date)">>$LOGFILE
#finally, we gather trajectories
./traj.py $SCANDIR/'traj.*.npz' trajectories >>$LOGFILE
rm  $SCANDIR/*.npz $SCANDIR/selected.npy
echo "done at $(date)">>$LOGFILE
if [ -f tranjectories.npz ]; then
    echo "file is available at $HOSTNAME:$PWD/trajectories.npz"
else
    echo "trajectories is not found, check the log for errors."
fi;
'''
post = '0';
xopts=''+dims_flag; #for copy so we don't write to dims_flag
#ramses hack
if opts['--server'] and opts['--ramses-node']:
    ramsesnode=':'+opts['--ramses-node'];
else:
    ramsesnode='';
convopts=xopts+opts['--conv-opts'];
scanopts = opts['--scan-opts'];
scanscript=opts['--scanner'];

#header
header = headert.format(
    hours=hours,mins=mins,ppn=ppn,
    ramsesnode=ramsesnode,post=post,
    workdir=workdir,
    maxproc=maxproc);
#conversion
#creating pbs script.
convert_first = convertt_first.format(
    convopts = convopts,
    firstfile=sortedmovies[0])

convert = convertt.format(
    convopts=convopts);

#scanning
scan = scant.format(
    scanscript=scanscript,
    scanopts=scanopts);
#no format needed for the following.
gather=gathert;
search=searcht;
traj =trajt;
out = ''.join([header,convert_first,convert,scan,gather,search,traj]);

with open(opts['--outdir']+'/pmovie-conv-'+post+'.pbs','w') as f:
    f.write(out);
