#!/usr/bin/env python
import threading
import argparse
import sys
import os
import time
import pdb

class CeiloCommandThread(threading.Thread):
    def __init__(self, num_iterations, func, **args):
        threading.Thread.__init__(self, name=func.__name__)
        self.num_iterations = num_iterations
        self.args = args
        self.func = func
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
              % (self.name, self.sum, self.avg, self.min, self.max, len(self.run_times), self.error)


    def run(self):
        try:
            self.run_times = []
            for _ in range(self.num_iterations):
                t0 = time.time()
                try:
                    self.func(**self.args)
                finally:
                    t1 = time.time()
                    self.run_times.append(t1 - t0)
        except Exception as e:
            self.error_flag = True
            self.error_str = "error occured in thread %s" % str(e)
