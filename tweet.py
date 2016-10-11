#
# Copyright 2013 IBM Corp
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

import logging
import logging.handlers

from oslo_log import log
from six.moves.urllib import parse as urlparse
from twython import Twython

import ceilometer
from ceilometer.i18n import _
from ceilometer import publisher

LOG = log.getLogger(__name__)


"""
{'user_id': u'16b4a66fd1f44373a89a2ac398934523', 'name': 'volume.size', 'resource_id': u'a07b6240-bc2e-428d-b897-f062636bac77', 'timestamp': u'2016-09-29 15:01:47.935435', 'resource_metadata': {u'status': u'deleting', 'event_type': u'volume.delete.end', u'availability_zone': u'proxmox11-9', u'volume_id': u'a07b6240-bc2e-428d-b897-f062636bac77', u'host': u'volume.cinder-volume-1.paslab011009.mc.metacloud.in@nfs-default', u'replication_status': u'disabled', u'snapshot_id': None, u'replication_extended_status': None, u'display_name': u'VCO_mcp2.paslab011009_2477740_20160929-150110', u'size': 5, u'user_id': u'16b4a66fd1f44373a89a2ac398934523', u'volume_attachment': [], u'tenant_id': u'626f6a926d444b7892742c11ef6b179a', u'created_at': u'2016-09-29T15:01:11', u'volume_type': None, u'replication_driver_data': None, u'launched_at': u'2016-09-29T15:01:12', u'metadata': []}, 'volume': 5, 'source': 'openstack', 'project_id': u'626f6a926d444b7892742c11ef6b179a', 'type': 'gauge', 'id': 'a4f957c8-8655-11e6-9888-3a3766353637', 'unit': 'GB'}
"""
class TwitterPublisher(publisher.PublisherBase):
    def __init__(self, parsed_url):
        super(TwitterPublisher, self).__init__(parsed_url)
        self.twitter = Twython("xIpbyvwmQK4YMwXaO2z9NR2NV",
                          "fOFKEl0U64f7no8JDoEZZZZvesgWcHDC5Y0c2EKiVTAWBeRat0",
                          "781505281377218560-tWW00zVr7RN9YrCMQAfsC1djTPLwUhX",
                          "EwPNbO62G1dfbVbNUbMQnfM0w2HpUx1K9T4kqClTCzo5J")

    def publish_samples(self, context, samples):
        """Send a metering message for publishing

        :param context: Execution context from the service or RPC call
        :param samples: Samples from pipeline after transformation
        """
        if self.twitter:
            for sample in samples:
                d = sample.as_dict()
                event = d.get("resource_metadata", {}).get("event_type")
                status = d.get("resource_metadata", {}).get("status")
                timestamp = d.get("timestamp")
                id = d.get("resource_id")
                msg = "Event: %s status: %s timestamp: %s id: %s" % (event, status, timestamp, id)
                self.twitter.update_status(status=msg)

    def publish_events(self, context, events):
        """Send an event message for publishing

        :param context: Execution context from the service or RPC call
        :param events: events from pipeline after transformation
        """
        raise ceilometer.NotImplementedError
