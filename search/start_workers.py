from argparse import ArgumentParser
from configparser import ConfigParser
from multiprocessing import Process
import worker.worker as worker
from search.utils import logUtils

import signal
import sys

_PROCESSES = []
_LOGGER = None

def start_workers(config):
    '''
    Picks up all the external system configuration from the config file and starts up as many processes as non-default sections in the config.
    The following elements are required from the default configuration section :
    - solr_url : base url of the solr server.
    - nova_db_server : IP or hostname of the nova controller.
    - nova_db_port : Port of the nova db to which the workers should connect.For nova+mysql this would be 3306.
    - nova_db_creds : credentials in the format user:password
    - amqp_server : IP or hostname of the amqp server. Usually, this is same as the nova controller.
    - amqp_port : Port of the AMQP server. If using RMQ this should be 5672.
    - amqp_creds : credentials in the format user:password
    
    Each non-default section of the config should represent a resource type that this system monitors. Each individual worker corresponds to
    a resource type and is run in a separate python process.
    '''
 
    logUtils.setup_logging(config)
    global _LOGGER
    _LOGGER = logUtils.get_logger(__name__)
    for section in config.sections():
        process = Process(target=worker.run, args=(config, section,))
        process.daemon = True
        process.start()
        _LOGGER.info('Started worker process - ' + str(process.pid))
        _PROCESSES.append(process)
    
def kill_subprocesses(signal, frame):
    '''
    Kills all the processes forked off and tracked via start_workers.
    '''
    for process in _PROCESSES:
        _LOGGER.info('terminating process - ' + str(process.pid))
        process.terminate()
    for process in _PROCESSES:
        _LOGGER.info('waiting for termination of - ' + str(process.pid))
        process.join()
    _LOGGER.info('Main process dying.')
    sys.exit(0)
    

if __name__ == '__main__':
    # parse command line args
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", help="Complete path of the fillup configuration file.")
    args = parser.parse_args()
    # parse the config file supplied in the command line args
    config = ConfigParser()
    config.read(args.file)
    start_workers(config)
    # ctrl+c
    signal.signal(signal.SIGINT, kill_subprocesses)
    # un-ignorable termination
    signal.signal(signal.SIGTERM, kill_subprocesses)
    signal.pause()