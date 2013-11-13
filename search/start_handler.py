from argparse import ArgumentParser
from configparser import ConfigParser
import worker.worker as worker
from search.utils import logUtils

def start_handler(config, handler_name):

    logUtils.setup_logging(config)
    logger = logUtils.get_logger(__name__)
    logger.info('starting handler ' + handler_name)
    worker.run(config, handler_name)

if __name__ == '__main__':
    # parse command line args
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", help="Complete path of the fillup configuration file.")
    parser.add_argument("-r", "--resource", help="Name of the handler.")
    args = parser.parse_args()
    # parse the config file supplied in the command line args
    config = ConfigParser()
    config.read(args.file)
    start_handler(config, args.resource)