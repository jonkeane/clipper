import sys, re, os, time, subprocess, errno
from pipes import quote
from datetime import datetime #both datetime imports needed?
from datetime import timedelta #both datetime imports needed?

# from http://stackoverflow.com/questions/273192
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

class clipper:
    """Generates the actually ffmpeg clipping"""
    def __init__(self, annos, outPath, inFile, audio, videoFilters, videoCodec, videoQuality, otherOptions):
        tstart = float(annos[0])/1000. # convert milliseconds to seconds
        tend = float(annos[1])/1000. # convert milliseconds to seconds
        make_sure_path_exists(os.path.dirname(outPath))
        outFile = outPath+'.mp4' # This works with spaces again, but why did I use quote() before?

        # allow logging doesn't work currently
        logfile = quote(''.join([outPath,".log"]))

        proc = self.clipFunc(infile=inFile, outfile=outFile, tstart=tstart, tend=tend, audio=audio, videoFilters=videoFilters, videoCodec=videoCodec, videoQuality=videoQuality, otherOptions=otherOptions, log=None, verbose=True)
        self.subProc = proc
    
    def clipFunc(self, infile, outfile, tstart, tend, audio='', videoFilters='', videoCodec='', videoQuality='', otherOptions= [], log=None, verbose=False):
        ''' clips video with no options '''
        #deinterlace+crop+scale '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [o2]; [o2] scale=852:480 [out]"'
        #deinterlace+crop '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [out]"'
        #deinterlace '-vf "[in] yadif=1 [out]"'
        dur = tend-tstart
        cmd = ['../Resources/ffmpeg'] # for including in package
        cmd = ['ffmpeg']

        opts = []

        ## # specify a prejump to seek to a little while before the clipping should begin. doesn't work for some clips?
        ## preJump = tstart-30
        ## if preJump > 0:
        ##    opts.extend(['-ss', str(timedelta(seconds=preJump))])

        opts.extend(['-i', infile])

        if videoFilters != '':
            opts.extend(['-vf', videoFilters])
            
        opts.extend(['-ss', str(timedelta(seconds=tstart)), '-t', str(timedelta(seconds=dur))])

        if videoQuality != '':
            opts.extend(['-qscale', videoQuality])
               
        if audio == False:
             opts.extend(['-an'])

        if videoCodec != '':
            opts.extend(['-vcodec', videoCodec])

        if otherOptions != ['']:
            opts.extend(otherOptions)

        opts.extend(['-y', outfile])
        cmd.extend(opts)
        if verbose: print(cmd)
        # logging currently doesn't work?
        if log: logFile = open(log, 'w') 
        p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout = subprocess.PIPE, bufsize=1, universal_newlines=True)
        return p



def  determineNumberOfCPUs():
    """ Number of virtual or physical CPUs on this system, i.e.
    user/real as output by time(1) when called with an optimally scaling
    userspace-only program
    from http://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-in-python"""

    # Python 2.6+
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError,NotImplementedError):
        pass

    # POSIX
    try:
        res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

        if res > 0:
            return res
    except (AttributeError,ValueError):
        pass

    # Windows
    try:
        res = int(os.environ['NUMBER_OF_PROCESSORS'])

        if res > 0:
            return res
    except (KeyError, ValueError):
        pass

    # jython
    try:
        from java.lang import Runtime
        runtime = Runtime.getRuntime()
        res = runtime.availableProcessors()
        if res > 0:
            return res
    except ImportError:
        pass

    # BSD
    try:
        sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'],
                                      stdout=subprocess.PIPE)
        scStdout = sysctl.communicate()[0]
        res = int(scStdout)

        if res > 0:
            return res
    except (OSError, ValueError):
        pass

    # Linux
    try:
        res = open('/proc/cpuinfo').read().count('processor\t:')

        if res > 0:
            return res
    except IOError:
        pass

    # Solaris
    try:
        pseudoDevices = os.listdir('/devices/pseudo/')
        expr = re.compile('^cpuid@[0-9]+$')

        res = 0
        for pd in pseudoDevices:
            if expr.match(pd) != None:
                res += 1

        if res > 0:
            return res
    except OSError:
        pass

    # Other UNIXes (heuristic)
    try:
        try:
            dmesg = open('/var/run/dmesg.boot').read()
        except IOError:
            dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
            dmesg = dmesgProcess.communicate()[0]

        res = 0
        while '\ncpu' + str(res) + ':' in dmesg:
            res += 1

        if res > 0:
            return res
    except OSError:
        pass

    raise Exception('Can not determine number of CPUs on this system')
