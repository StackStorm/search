from search.utils import logUtils
from search.datasource import session, amqp_client

def get_class( kls ):
    '''
    Given a fully qualified class name will return the class so that it can be instantiated.
    '''
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

def run(config, section_name):
    import eventlet
    # Apply monkey_patch at the earliest
    eventlet.monkey_patch(thread=False)
    '''
    Sets up logging for the entire process and then starts the corresponding handler.
    - config : Configuration of the application.
    - section_name : Name of the section in the config.
    '''
    logUtils.setup_logging(config)
    logger = logUtils.get_logger(__name__)
    solr_url = config['DEFAULT']['solr_url']
    db_info = session.DBInfo(config['DEFAULT']['nova_db_server'], config['DEFAULT']['nova_db_port'], config['DEFAULT']['nova_db_creds'])
    amqp_info = amqp_client.AmqpInfo(config['DEFAULT']['amqp_server'], config['DEFAULT']['amqp_port'], config['DEFAULT']['amqp_creds'])

    # pull out name of the handler for the specific core
    section = config[section_name]
    handlerName = section["handlerName"]
    interval = int(section["interval"])
    
    try :
        # instantiate the handler
        handlerKls = get_class(handlerName)
        handler = handlerKls(solr_url, db_info, amqp_info, interval)
        logger.info(str(handler) + ' instantiated to perform work.')
        # handler is expected to have an on_start & setup_amqp() method to do the real work.
        # run on_start on a green thread.
        eventlet.spawn_n(handler.on_start)
        # call setup_amqp on the main thread so that it keeps the main thread busy.
        handler.setup_amqp()
        return handler
    except Exception as inst:
        logger.exception(inst)