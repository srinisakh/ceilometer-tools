from kombu.mixins import ConsumerMixin
from kombu.log import get_logger
from kombu import Queue, Exchange

logger = get_logger(__name__)

'''
This script sets up a running subscription to a given queue on the local RabbitMQ bus.
It depends on the kombu library, which can be installed vi pypi and/or will be leveraged
from a Devstack install.

By default it's configured to listen on the "notifications.info" queue, which is a topic
type exchange, and subscribe to the "notifications" exchange.

IMPORTANT NOTE: If there are other subscribers to the same exchange, they may
supercede this reciever and remove messages before they reach this queue. This
receiver should not behave that way (i.e. it will leave messages on the queue)
due to message ack being turned off.
'''

class Worker(ConsumerMixin):
    task_queue = Queue('metering.info', Exchange('openstack', 'topic', durable=False), durable=False)
    #task_queue = Queue('metering.info', Exchange('openstack', 'topic'))

    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[self.task_queue],
                         accept=['json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        for k, v in body.items():
            if k == 'payload':
                print "First message in the payload: ", v[0]
                print "There are %d events more in this payload..." % (len(v) - 1)
            else:
                print "%s = %s" % (k, v)
        raw_input("Press Enter to continue...")
        print "\n"
        message.ack()

if __name__ == '__main__':
    from kombu import Connection
    from kombu.utils.debug import setup_logging
    # setup root logger
    setup_logging(loglevel='DEBUG', loggers=[''])

    #with Connection('amqp://guest:guest@localhost:5672/', virtual_host='/') as conn:
    with Connection('amqp://guest:guest@localhost:5672/') as conn:
        try:
            print(conn)
            worker = Worker(conn)
            worker.run()
        except KeyboardInterrupt:
            print('Terminating consumer:bye bye')

