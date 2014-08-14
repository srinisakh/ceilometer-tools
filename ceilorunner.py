#!/usr/bin/env python
from ceilometerclient.shell import CeilometerShell
from ceilometerclient import client as ceiloclient
from ceilometerclient.v2 import options
import threading
import argparse
import sys
import os
import time
import pdb

"""
Replace functions will call the non-printing version of functions
Add to prevent seeing ton of out put on cm shell functions
Name them as same as the shell functions
"""

def do_meter_list(client, args):
    return client.meters.list(q=options.cli_to_array(args.query))

def do_resource_list(client, args):
    return client.resources.list(q=options.cli_to_array(args.query))

def do_resource_show(client, args):
    return client.resources.get(args.resource_id)

def do_alarm_list(client, args):
    return client.alarms.list(q=options.cli_to_array(args.query))

def do_statistics(client, args):
    '''List the statistics for a meter.'''
    aggregates = []
    for a in args.aggregate:
        aggregates.append(dict(zip(('func', 'param'), a.split("<-"))))
    api_args = {'meter_name': args.meter,
                'q': options.cli_to_array(args.query),
                'period': args.period,
                'groupby': args.groupby,
                'aggregates': aggregates}
    statistics = client.statistics.list(**api_args)

"""
Uses the env if no authentication args are given
"""
def get_ceilometer_api_client(args):
    s = CeilometerShell()
    api_version, parsed_args = s.parse_args(args)

    return parsed_args, ceiloclient.get_client(api_version, **(parsed_args.__dict__))

def parse_args(args):
    arg_parser = argparse.ArgumentParser(
        prog='ceilometer',
    )

    arg_parser.add_argument('--num-threads', type=int, default=1)
    arg_parser.add_argument('--num-iterations', type=int, default=1)
    #arg_parser.add_argument('--input-file', default="~/.inputceilorunner")

    return arg_parser.parse_known_args()

def enable_output(self):
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

def disable_output(self):
    sys.stdout = os.devnull
    sys.stderr = os.devnull

class CeiloCommandThread(threading.Thread):
    def __init__(self, num_iterations, client, func, args):
        threading.Thread.__init__(self, name=func.__name__)
        self.num_iterations = num_iterations
        self.client = client
        self.func = self.get_function_to_call(func)
        self.args = args
        self.run_times = []
        self.error_flag = False
        self.error_str = ''

    @property
    def avg(self):
        if self.run_times:
            return sum(self.run_times) / len(self.run_times)
        else:
            return 0.0

    @property
    def sum(self):
        if self.run_times:
            return sum(self.run_times)
        else:
            return 0.0

    @property
    def min(self):
        if self.run_times:
            return min(self.run_times)
        else:
            return 0.0

    @property
    def max(self):
        if self.run_times:
            return max(self.run_times)
        else:
            return 0.0

    @property
    def error(self):
        return self.error_str if self.error_flag else ''


    def print_stats(self):
        print "Function %s took %f sec (avg=%f, min=%f, max=%f) for %d iterations (%s)" \
              % (self.name, self.sum, self.avg, self.min, self.max, self.num_iterations, self.error)


    def get_function_to_call(self, shell_func):
        replace_function = globals().get(shell_func.__name__, None)
        return replace_function if replace_function else shell_func


    def run(self):
        try:
            self.run_times = []
            for _ in range(self.num_iterations):
                t0 = time.time()
                try:
                    self.func(self.client, self.args)
                finally:
                    t1 = time.time()
                    self.run_times.append(t1 - t0)
        except Exception as e:
            self.error_flag = True
            self.error_str = "error occured in thread %s" % str(e)


def main(args=None):
    try:
        if args is None:
            args = sys.argv[1:]

        local_args, ceilo_args = parse_args(args)
        ceilo_client_args, client = get_ceilometer_api_client(ceilo_args)

        threads = []
        for _ in range(local_args.num_threads):
            t = CeiloCommandThread(local_args.num_iterations,
                                   client, ceilo_client_args.func, ceilo_client_args)
            threads.append(t)
            t.start()

        total_runtimes = []
        for i, t in enumerate(threads):
            t.join()
            #t.print_stats()
            if t.error_flag:
                t.print_stats()
            total_runtimes = total_runtimes + t.run_times

        gt_60 = sum(1 for t in threads if t.max > 60.0)
        print "Threads that are greater than 60 secs %d", gt_60

        print "num iter / thread, numthreads, ave, min, max = %d\t%d\t%f\t%f\t%f" % \
              (local_args.num_iterations, len(threads),
               sum(total_runtimes)/len(total_runtimes), min(total_runtimes), max(total_runtimes))

    except Exception as e:
        print "CeiloRunner: Unknown error ", str(e)

if __name__ == "__main__":
    main()

