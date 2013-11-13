from configparser import ConfigParser
from mock import MagicMock
from search.datasource.session import DBInfo
from search.utils import logUtils
from search.worker.computenode import ComputeNodeHandler
import unittest


FAKE_NODES = [{ 'id':1,
        'local_gb': 259,
        'vcpus_used': 0,
        'deleted': 0,
        'hypervisor_type': 'powervm',
        'created_at': '2013-04-01T00:27:06.000000',
        'local_gb_used': 0,
        'updated_at': '2013-04-03T00:35:41.000000',
        'hypervisor_hostname': 'fake_phyp1',
        'memory_mb_used': 512,
        'memory_mb': 131072,
        'current_workload': 0,
        'vcpus': 16,
        'cpu_info': 'ppc64,powervm,3940',
        'running_vms': 0,
        'free_disk_gb': 259,
        'service_id': 7,
        'hypervisor_version': 7,
        'disk_available_least': 265856,
        'deleted_at': None,
        'free_ram_mb': 130560
        },
        { 'id':2,
        'local_gb': 259,
        'vcpus_used': 0,
        'deleted': 0,
        'hypervisor_type': 'powervm',
        'created_at': '2013-04-01T00:27:06.000000',
        'local_gb_used': 0,
        'updated_at': '2013-04-03T00:35:41.000000',
        'hypervisor_hostname': 'fake_phyp2',
        'memory_mb_used': 512,
        'memory_mb': 131072,
        'current_workload': 0,
        'vcpus': 16,
        'cpu_info': 'ppc64,powervm,3940',
        'running_vms': 0,
        'free_disk_gb': 259,
        'service_id': 7,
        'hypervisor_version': 7,
        'disk_available_least': 265856,
        'deleted_at': None,
        'free_ram_mb':12202
        }
    ]

#TODO: Figure why tests don't work...
config = ConfigParser()
config.read("./tests/config.ini")
logUtils.setup_logging(config)

# Both elements of array the same, to simplify mocking

class ComputeNodeHandlerTest(unittest.TestCase):

    def setUp(self):

        solr_url = 'https://fake/solr/url'
        db_info =  DBInfo(host='fake', port='123', creds='foo:bar')
        ampq_info = None
        libvirt_info = {'user':'fake'}
        self.c = ComputeNodeHandler(solr_url, db_info, ampq_info, libvirt_info)
        self.c.inventory = MagicMock()

    def test_on_start_success(self):

        def execute(self, query):
            if query == None or len(query) == 0:
                raise Exception("Empty query!")
            return FAKE_NODES
        self.c.engine.execute = MagicMock(return_value=FAKE_NODES)

        self.c.on_start()
        post_expects = [self.c._to_compute_node_data(d) for d in FAKE_NODES]
        self.c.inventory.post.assert_called_with(post_expects)
    
    def test_on_event_success(self):
        self.c.engine.execute = MagicMock(return_value=[FAKE_NODES[0]])
        fake_event = {}
        fake_event['event_type'] = 'compute.instance.Suspend.end'
        fake_event['payload'] = {'instance_id':1}

        message = MagicMock()
        self.c.on_event(fake_event, message)

        self.assertEqual(self.c.engine.execute.call_count, 1)
        self.c.inventory.post.assert_called_with(
                self.c._to_compute_node_data(FAKE_NODES[0]))
        message.ack.assert_called_once_with()

    def test_handle_modify_event_new_host(self):
        self.assertEqual(self.c.hosts, [])
        self.c.engine.execute = MagicMock(return_value=[FAKE_NODES[0]])
        self.c._handle_modify_event({'instance_id':1})
        self.assertTrue(self.c.inventory.post.called)

    def test_handle_modify_event_old_host(self):
        self.assertEqual(self.c.hosts, [])
        self.c.hosts.append(dict(name=FAKE_NODES[0]['hypervisor_hostname']))
        self.c.engine.execute = MagicMock(return_value=[FAKE_NODES[0]])
        self.c._handle_modify_event({'instance_id':1})
        self.assertTrue(self.c.inventory.put.called) 

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ComputeNodeHandlerTest)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())


