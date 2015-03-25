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
