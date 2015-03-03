from kombu import BrokerConnection, Exchange
from kombu.utils.debug import setup_logging
import argparse
import traceback

#Taken from https://wiki.openstack.org/wiki/NotificationEventExamples
SAMPLE_NOTIFICATION_PAYLOAD = \
    {
        "event_type": "compute.instance.resize.confirm.start",
        "timestamp": "2012-03-12 17:01:29.899834",
        "message_id": "1234653e-ce46-4a82-979f-a9286cac5258",
        "priority": "error",
        "publisher_id": "compute.compute-1-2-3-4",
        "payload": {
            "state_description": "",
            "display_name": "testserver",
            "memory_mb": 512,
            "disk_gb": 20,
            "tenant_id": "12345",
            "created_at": "2012-03-12 16:55:17",
            "instance_type_id": 2,
            "instance_id": "abcbd165-fd41-4fd7-96ac-d70639a042c1",
            "instance_type": "512MB instance",
            "state": "active",
            "user_id": "67890",
            "launched_at": "2012-03-12 16:57:29",
            "image_ref_url": "http://127.0.0.1:9292/images/a1b2c3b4/home/jaiswaro-575f-4381-9c6d-fcd3b7d07d17"
            }
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Utility to send messages to RMQ..')

    parser.add_argument("exchange_name", type=str, help="name of the exchange to publish message to")
    parser.add_argument("routing_key", type=str, help="routing key used to route message to appropriate queue")

    args = parser.parse_args()

    setup_logging(loglevel='DEBUG', loggers=[''])

    topic_exchange = Exchange(name=args.exchange_name, type='topic', durable=False)

    with BrokerConnection('amqp://guest:password@localhost:5672//') as connection:
        with connection.Producer(exchange=topic_exchange,routing_key=args.routing_key, serializer='json') as producer:
            try:
                print "\nMessage format taken from https://wiki.openstack.org/wiki/NotificationEventExamples..\n"
                print "Message to be published: " + str(SAMPLE_NOTIFICATION_PAYLOAD)
                print "\nPublishing message to exchange %s with routing key %s" % (args.exchange_name, args.routing_key)
                producer.publish(SAMPLE_NOTIFICATION_PAYLOAD)
            except Exception as ex:
                print str(ex)
    print "\nMessage sent."




