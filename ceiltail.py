#!/usr/bin/python -u

# Debug
#  1 - print interesting stuff
#  2 - print counters as written to stats file
#  4 - print lines as read from log
#  8 - cat vs tail logfile and when done exist, sleeping 0.01 secs
#      between samples

# source /opt/stack/venvs/openstack/bin/activate

# the api log is an apache log and only contains countable records, BUT...
# Ceilometer log record counting must contain (after making sure DEBUG record)
# one of the following patterns:
#     agent-notification:    pipeline
#     alarm-notifier:        alarm.service 
#     alarm-evaluator:       alarm.service 
#     collector:             dispatcher.database (plus details on type)

import os
import re
import sys
import shlex
import signal
import socket
import subprocess
import time
from optparse import OptionParser, OptionGroup

counters = {}
lastsize = 0
counted = False
taildone = False

parser = OptionParser()
parser.add_option('-d',   dest='debug', default='0')
parser.add_option('-D',   dest='daemon', help='run as daemon', action='store_true')
parser.add_option('-t',   dest='type', default='')
try:
    (options, args) = parser.parse_args(sys.argv[1:])
except:
    print 'invalid option'
    sys.exit(1)
debug = int(options.debug)

type = options.type
if type == '':
    print 'required: -l'
    sys.exit(1)

logdir = '/var/log/ceilometer'
if type == 'agent-notification':
    match = 'pipeline'
    logtype = 1
    logname = '/var/log/ceilometer/ceilometer-agent-notification.log'
    extract = 0
elif type == 'alarm-notifier':
    match = 'alarm.service'
    logtype = 1
    logname = '/var/log/ceilometer/ceilometer-alarm-notifier.log'
    extract = 0
elif type == 'alarm-evaluator':
    match = 'alarm.service'
    logtype = 1
    logname = '/var/log/ceilometer/ceilometer-alarm-evaluator.log'
    extract = 0
elif type == 'collector':
    match = 'dispatcher'
    logtype = 1
    logname = '/var/log/ceilometer/ceilometer-collector.log'
    extract = 8 
elif type == 'api':
    match = ''
    logtype = 2
    logname = '/var/log/apache2/ceilometer_access.log'
    extract = 5
else:
    print "Unknownm type:", type
    sys.exit(1)

if debug & 1:
    print "LogFile: %s  Match: %s" % (logname, match)


# stolen from swift-statstee
def logmsg(severity, text):

    timestamp = time.strftime("%Y%m", time.gmtime())
    logfile = '%s/%s-%s-ceiltail.log' % \
        (logdir, time.strftime("%Y%m", time.gmtime()),
         socket.gethostname().split('.')[0])
    msg = '%s %s %s' % \
        (time.strftime("%Y%m%d-%H:%M:%S", time.gmtime()), severity, text)
    if debug or re.match('[EF]', severity) and not options.daemon:
        print text

    try:
        log = open(logfile, 'a+')
        log.write('%s\n' % msg)
        log.close()
    except:
        print "Couldn't open", logfile
        syslog.syslog("couldn't open %s for appending" % logfile)
        sys.exit()

    if re.match('E|F', severity):
        syslog.syslog(text)
        if severity == 'F':
            sys.exit()


def error(text):
    print text
    sys.exit(1)


def run_as_daemon():

    if debug != 0:
        error("No debugging in daemon mode")

    myname = os.path.basename(__file__)
    runlog = '/var/run/ceiltail-%s.pid' % type
    if os.path.exists(runlog):
        f = open(runlog, 'r')
        pid = f.read()[:-1]
        f.close()

        # cmdline contains the command that started us BUT spaces have been
        # changed to nulls.  Since the command should contain -t type,
        # we can just see if our command line contains that string
        proc_path = '/proc/%s/cmdline' % pid
        if os.path.exists(proc_path):
            f = open('/proc/%s/cmdline' % pid)
            pname = f.read()[:-1]
            f.close()
            if re.search('%s' % type, pname):
                error("a daemonized %s already running" % myname)

    # there seems to be some differing opinions of whether or
    # not to disable I/O right before we fork/exit, but it
    # certainly can't hurt.  I also discovered I need to use
    # dup2() as 3 opens cause hangs over ssh?!?  no explantion
    # was ever found
    sys.stdin = open('/dev/null', 'r+')
    os.dup2(0, 1)    # standard output (1)
    os.dup2(0, 2)    # standard error (2)

    # for a new copy and exit the parent
    pid = os.fork()
    if pid > 0:
        sys.exit()

    # decouple from parent environent
    os.chdir('/')
    os.setsid()
    os.umask(0)

    # and disable all I/O
    sys.stdin = open('/dev/null', 'r+')
    os.dup2(0, 1)    # standard output (1)
    os.dup2(0, 2)    # standard error (2)

    # finally write our new PID to the run file
    f = open(runlog, 'w')
    f.write('%s\n' % os.getpid())
    f.close()


def alarm(signum, frame):
    global counted, lastsize, taildone

    size = os.path.getsize(logname)
    if size < lastsize:
        taildone = True
	logmsg('W', 'Log rolled: %s' % logname)
        os.kill(tail.pid, signal.SIGTERM)
    lastsize = size

    if counted:
	if debug & 2:
            print "Counters:", counters
	statslog.seek(0)
	statslog.write('%s\n' % counters)
	statslog.flush()
        counted = False

if options.daemon:
    if debug & 1:
        print "Starting daemon..."
    run_as_daemon()
    logmsg('I', "ceiltail beginning execution: %s" % type)

statsfile = '/var/log/ceilometer/stats-%s' % type

# NOTE - using this mechanism if file rolls and size doesn't change
# (most unlikely), we won't know it.
devnull = open(os.devnull, 'w')
command = 'tail -n1 -f %s' % logname
if debug & 8:
    command = 'cat %s' % logname

if os.path.exists(statsfile) and os.path.getsize(statsfile) > 0:
    statslog = open(statsfile, 'r+')
    line = statslog.readline()
    line = re.sub('{|}', '', line)
    for stat in re.split(', ', line):
	name, value = stat.split(':')
	name = re.sub("'", '', name)
	counters[name] = int(value)
else:
    statslog = open(statsfile, 'w')

secs = interval = 1
signal.signal(signal.SIGALRM, alarm)
signal.setitimer(signal.ITIMER_REAL, secs, interval)

while 1:
    if debug & 1:
        print "Command:", command

    tail = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=devnull)
    taildone = False
    while not taildone:
        line = tail.stdout.readline()[:-1]

	# ignore blank records unless we're doing a cat in which case
	# we just want to quit
	if line == '':
	    if debug & 8:
	        sys.exit()
	    continue

	fields = line.split(' ')

	# ceilometer logs contain a lot we don't care about
	if logtype == 1:
  	    try:
	        if fields[3] != 'DEBUG' or fields[3] == 'ERROR':
	            continue
	    except:
	        logmsg('E', 'Malformed Record [%s]: >%s<' % (type, line))
	        continue

	    if not re.search(match, fields[4]):
                continue

	if debug & 4:
	    print line

	# if a field to extract, do so we can count it by name,
        # otherwise use generic name 'count'
        if extract:
	    ltype = fields[extract]
	    ltype = re.sub('"', '', ltype)
        else:
	    ltype = 'count'

	if debug & 8:
	    time.sleep(0.01)

	counted = True
	if ltype not in counters:
	    counters[ltype] = 0	
        counters[ltype] += 1

