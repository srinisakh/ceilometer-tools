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
from sqlalchemy.exc import OperationalError as DbOpError
from retrying import retry
from ceilometer.openstack.common import log
from ceilometer.openstack.common.gettextutils import _

LOG = log.getLogger(__name__)

def _db_error_filter(exc):
    if isinstance(exc, DbOpError):
        LOG.warn(_("Error connecting to database. Retrying..."))
        return True

    return False


#@retry(retry_on_exception=_db_error_filter, wait_fixed=500, stop_max_attempt_number=50) 
#@retry(wait_fixed=500, stop_max_attempt_number=50) 
#def get_connection():

def main():
    # Connect to the metering database
    cfg.CONF([], project='ceilometer')
    conn = storage.get_connection_from_config(cfg.CONF)
    print("Connection succeeded trying get_meters")
    res = conn.get_meters()
    print("1 Number of meters: %d" % sum(1 for i in res))
    res = conn.get_meters()
    print("2 Number of meters: %d" % sum(1 for i in res))
    res = conn.get_meters()
    print("3 Number of meters: %d" % sum(1 for i in res))
    

if __name__ == '__main__':
    main()
