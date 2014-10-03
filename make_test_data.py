#!/usr/bin/env python
#
# Copyright 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Command line tool for creating test data for Ceilometer.

Usage:

Generate testing data for e.g. for default time span

source .tox/py27/bin/activate
./tools/make_test_data.py --user 1 --project 1 1 cpu_util 20
"""
from __future__ import print_function

import argparse
import datetime
import logging
import random
import sys
import time
import threading

from oslo.config import cfg
from oslo.utils import timeutils

from ceilometer.publisher import utils
from ceilometer import sample
from ceilometer import storage
from sqlalchemy import func
from ceilometer.storage.sqlalchemy.models import Sample as DBSample
from ceilocommandthread import CeiloCommandThread

def make_test_data(conn, name, meter_type, unit, volume, random_min,
                   random_max, user_id, project_id, resource_id, start,
                   end, interval, resource_metadata={}, source='artificial',):

    # Compute start and end timestamps for the new data.
    if isinstance(start, datetime.datetime):
        timestamp = start
    else:
        timestamp = timeutils.parse_strtime(start)

    if not isinstance(end, datetime.datetime):
        end = timeutils.parse_strtime(end)

    increment = datetime.timedelta(minutes=interval)


    print('Adding new events for meter %s.' % (name))
    # Generate events
    n = 0
    total_volume = volume
    meter_names = ["meter" + name + str(i) for i in range(1, 50, 1)]
    resource_ids = ["resource" + resource_id + str(i) for i in range(1, 500, 1)]

    id = threading.current_thread().ident

    print("id, curr_sampl_count, avg, s")

    t0 = time.time()
    while timestamp <= end:
        if (random_min >= 0 and random_max >= 0):
            # If there is a random element defined, we will add it to
            # user given volume.
            if isinstance(random_min, int) and isinstance(random_max, int):
                total_volume += random.randint(random_min, random_max)
            else:
                total_volume += random.uniform(random_min, random_max)


        c = sample.Sample(name=random.choice(meter_names),
                          type=meter_type,
                          unit=unit,
                          volume=total_volume,
                          user_id=user_id,
                          project_id=project_id,
                          resource_id=random.choice(resource_ids),
                          timestamp=timestamp,
                          resource_metadata=resource_metadata,
                          source=source,
                          )
        data = utils.meter_message_from_counter(
            c,
            cfg.CONF.publisher.metering_secret)
        conn.record_metering_data(data)
        n += 1
        timestamp = timestamp + increment
        t1 = time.time()
        if not n % 1000:
            print ("%d, %d, %f, %f" % (id, get_current_sample_count(conn), (n / (t1 - t0)), t1))

        if (meter_type == 'gauge' or meter_type == 'delta'):
            # For delta and gauge, we don't want to increase the value
            # in time by random element. So we always set it back to
            # volume.
            total_volume = volume

    t1 = time.time()
    totaltime = t1 - t0
    print ("%d, %d, %f, %f" % (id, get_current_sample_count(conn), (n / (t1 - t0)), t1))

    print('Id %d Added %d samples total time %f sec avg: %f samples/sec ts: %f' % (id, n, totaltime, (n / totaltime), t1))

def get_current_sample_count(conn):
    session = conn._engine_facade.get_session()
    return session.query(func.count(DBSample.id)).scalar()

def main():
    cfg.CONF([], project='ceilometer')

    parser = argparse.ArgumentParser(
        description='generate metering data',
    )
    parser.add_argument(
        '--interval',
        default=10,
        type=int,
        help='The period between events, in minutes.',
    )
    parser.add_argument(
        '--start',
        default=31,
        type=int,
        help='The number of days in the past to start timestamps.',
    )
    parser.add_argument(
        '--end',
        default=2,
        type=int,
        help='The number of days into the future to continue timestamps.',
    )
    parser.add_argument(
        '--type',
        choices=('gauge', 'cumulative'),
        default='gauge',
        help='Counter type.',
    )
    parser.add_argument(
        '--unit',
        default=None,
        help='Counter unit.',
    )
    parser.add_argument(
        '--project',
        help='Project id of owner.',
    )
    parser.add_argument(
        '--user',
        help='User id of owner.',
    )
    parser.add_argument(
        '--random_min',
        help='The random min border of amount for added to given volume.',
        type=int,
        default=0,
    )
    parser.add_argument(
        '--random_max',
        help='The random max border of amount for added to given volume.',
        type=int,
        default=0,
    )
    parser.add_argument(
        '--num-threads',
        help='Number of parallel threads',
        type=int,
        default=1,
    )
    parser.add_argument(
        'resource',
        help='The resource id for the meter data.',
    )
    parser.add_argument(
        'counter',
        help='The counter name for the meter data.',
    )
    parser.add_argument(
        'volume',
        help='The amount to attach to the meter.',
        type=int,
        default=1,
    )
    args = parser.parse_args()

    # Set up logging to use the console
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    root_logger = logging.getLogger('')
    root_logger.addHandler(console)
    root_logger.setLevel(logging.DEBUG)

    # Connect to the metering database
    conn = storage.get_connection_from_config(cfg.CONF)
    start_sample_rows = get_current_sample_count(conn)

    # Find the user and/or project for a real resource
    if not (args.user or args.project):
        for r in conn.get_resources():
            if r.resource_id == args.resource:
                args.user = r.user_id
                args.project = r.project_id
                break

    # Compute the correct time span
    start = datetime.datetime.utcnow() - datetime.timedelta(days=args.start)
    end = datetime.datetime.utcnow() + datetime.timedelta(days=args.end)

    kwargs = dict(conn=conn,
                  name=args.counter,
                  meter_type=args.type,
                  unit=args.unit,
                  volume=args.volume,
                  random_min=args.random_min,
                  random_max=args.random_max,
                  user_id=args.user,
                  project_id=args.project,
                  resource_id=args.resource,
                  start=start,
                  end=end,
                  interval=args.interval,
                  resource_metadata={},
                  source='artificial')

    threads = []
    for _ in range(args.num_threads):
        #New connection for each thread
        kwargs['conn'] = storage.get_connection_from_config(cfg.CONF)
        t = CeiloCommandThread(1, make_test_data, **kwargs)
        threads.append(t)
        t.start()

    total_runtimes = []
    for i, t in enumerate(threads):
        t.join()
        total_runtimes = total_runtimes + t.run_times

    end_sample_rows = get_current_sample_count(conn)
    print ("Samples count in DB beginning: %d end: %d" % (start_sample_rows, end_sample_rows))

    #print ("numthreads, ave, min, max = %d\t%f\t%f\t%f" % \
    #          (len(threads), sum(total_runtimes)/len(total_runtimes), 
    #          min(total_runtimes), max(total_runtimes)))

    return 0

if __name__ == '__main__':
    main()
