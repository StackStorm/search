from argparse import ArgumentParser
from mock import MagicMock
from multiprocessing import Process
from search.datasource.session import DBInfo
from search.worker.computenode import ComputeNodeHandler
from search.worker.instance import InstanceHandler
from tests import scale_gen
from tests import faker
import subprocess
import time
import os
import random

#config = ConfigParser()
#config.read('../config/config.ini')
#logUtils.setup_logging(config)

# class ScaleTest(unittest.TestCase):
#         
#     def test_load_scale_data(self):
#         self.instance.engine = scale_gen.ScaleDataProvider(InstanceHandlerScaleTest.data_files)
#         self.instance.on_start()

SOLR_START_WAIT = 5

def _gen_random_memory(_):
    return { 'used': random.randint(1, 32768) }

def _is_script_available(script, pass_exception = False):
    try:
        with open(script):
            return True
    except:
        if pass_exception:
            print '%s not found.' % script
        else:
            raise
    return False

def _start_solr(solr_scripts_location):
    # kill old solr instance
    kill_script = '%s/%s' % (solr_scripts_location, 'kill.sh')
    if _is_script_available(kill_script):
        subprocess.call(kill_script, shell=True)
    # start a clean solr instance
    dropindex_script = '%s/%s' % (solr_scripts_location, 'dropindex.sh')
    if _is_script_available(dropindex_script):
        subprocess.call(dropindex_script, shell=True)
    # start a new instance of solr
    run_script = '%s/%s' % (solr_scripts_location, 'run.sh')
    if _is_script_available(run_script, True):
        dev_null = open(os.devnull, 'w')
        subprocess.Popen(run_script, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
        #subprocess.Popen(run_script, shell=True)

def _run_computenode_test(computenode_files):
    print 'Adding computenodes to Solr.'
    start_time = time.time()
    solr_url = 'http://localhost:8983/solr/'
    db_info =  DBInfo(host='fake', port='123', creds='foo:bar')
    ampq_info = None
    libvirt_info = {'user':'fake'}
    computenode_handler = ComputeNodeHandler(solr_url, db_info, ampq_info, libvirt_info)
    computenode_handler.engine = scale_gen.ScaleDataProvider(computenode_files)
    computenode_handler._get_host_memory = MagicMock(side_effect=_gen_random_memory)
    computenode_handler.on_start()
    print 'computenodes added in %f.' % (time.time() - start_time)

def _run_instance_test(instance_files):
    print 'Adding instances to Solr.'
    start_time = time.time()
    solr_url = 'http://localhost:8983/solr/'
    db_info =  DBInfo(host='fake', port='123', creds='foo:bar')
    ampq_info = None
    libvirt_info = {'user':'fake'}
    instance_handler = InstanceHandler(solr_url, db_info, ampq_info, libvirt_info)
    instance_handler._get_users = MagicMock(return_value = dict(zip(['u'+str(i) for i in range(0, 10)], faker.username(10))))
    instance_handler._get_projects = MagicMock(return_value = dict(zip(['p'+str(i) for i in range(0, 10)], faker.projectname(10))))
    instance_handler._get_images = MagicMock(return_value = dict(zip(['i'+str(i) for i in range(0, 10)], faker.imagename(10))))
    instance_handler.engine = scale_gen.ScaleDataProvider(instance_files)
    instance_handler.on_start()
    print 'instances added in %f.' % (time.time() - start_time)

def main():
    parser = ArgumentParser()
    parser.add_argument('-l', '--location', help='location of the file.')
    parser.add_argument('-n', '--number', help='number of resources.')
    parser.add_argument('-s', '--solr', help='location of solr scripts like kill & run.')
    args = parser.parse_args()
    # generate scale data
    computenode_files, instance_files = scale_gen.generate_data(args.location, int(args.number))
    _start_solr(args.solr)
    # give solr sometime to start.
    # TODO(manask) - Implement a deterministic way.
    time.sleep(SOLR_START_WAIT)
    processes = []
    p = Process(target=_run_computenode_test, args=(computenode_files,)) # without the trailing , a list with 1 element is not passed down as a list
    p.start()
    processes.append(p)
    p = Process(target=_run_instance_test, args=(instance_files,))
    p.start()
    processes.append(p)
    while len(processes) > 0:
        processes.pop().join()
    print 'Exit.'

if __name__ == '__main__':
    main()