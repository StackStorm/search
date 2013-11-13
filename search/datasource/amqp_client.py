from kombu import Exchange, Queue, BrokerConnection
from kombu.mixins import ConsumerMixin
from search.utils import logUtils
import eventlet

class AmqpInfo:
    '''
    AMQP server information.
        host : IP or hostname of the AMQP server.
        port : Listening port of the AMQP server.
        creds : Login credentials of the AMQP server.
    '''
    def __init__(self, host, port, creds):
        self.host = host
        self.port = port
        self.creds = creds

class QueueInfo:
    '''
    Queue information of the AMQP server.
        name : name of the queue
        exchange_name : name of the exchnge on which to create the queue.
        routing_key : the routing key used to bind queue with exchange.
    '''
    def __init__(self, name, exchange_name, routing_key, exchange_type='topic'):
        self.name = name
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.routing_key = routing_key
        pass
    
class NotificationClient(ConsumerMixin):
    '''
    AMQP client abstraction that is assocaited with a specific queue and provides generic handling for all messages
    sent to the queue.
    '''
    
    logger = logUtils.get_logger(__name__)
    
    def __init__(self, amqp_info, queue_info, callback):
        '''
        Constructor.
            amqp_info : info of the amqp server.
            queue_info : info of the queue to create. See QueueInfo.
            callback : Method to execute on receipt of any message on the supplied queue.
        '''
        self.__queue = Queue(name = queue_info.name,
                           exchange=Exchange(name=queue_info.exchange_name,
                                             type=queue_info.exchange_type,
                                             durable=False,
                                             auto_delete=False),
                           routing_key='notifications.info',
                           durable=False,
                           auto_delete=False)
        self.__callback = callback
        self.__connection_str = 'amqp://' + amqp_info.creds + '@' + amqp_info.host + ':' + amqp_info.port

    def on_consume_ready(self, *args, **kwds):
        pass

    def on_consume_end(self, *args, **kwds):
        pass

    def on_iteration(self, *args, **kwds):
        pass

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[self.__queue],
                         callbacks=[self.process_event])]

    def process_event(self, body, message):
        eventlet.spawn_n(self.__callback, body, message)
    
    def start(self):
        NotificationClient.logger.info('Using connection_str - ' + self.__connection_str)
        with BrokerConnection(self.__connection_str) as connection:
            self.connection = connection
            try:
                self.run()
            except Exception:
                # TODO(manask) - Perhaps can retry on certain exceptions.
                NotificationClient.logger.exception('Exception while waiting on amqp messages.')
        NotificationClient.logger.info('Exit.')
    
    def on_connection_error(self, exc, interval):
        '''
        Overrides ConsumerMixin.on_connection_error to log. The base method also does the same thing but somehow it does not
        end up in the logs so logging here.
        '''
        NotificationClient.logger.warn('Broker connection error: %r. '
             'Trying again in %s seconds.', exc, interval)