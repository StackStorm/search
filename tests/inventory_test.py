import unittest
from configparser import ConfigParser
from search.utils import logUtils
from search.inventory import Inventory
from pysolr import Solr


# Attempting Integration test,
# a 'wise' to run solr client in isolation from the rest

VMDATA = [
    {
      "name" :  "My Cool VM",
      "id":  "550e8400-e29b-41d4-a716-446655440000",
      "power": "running",
      "state": "running",
      "image":"CentOS",
      "flavor": "m1.tiny",
      "vcpus": 1,
      "memory": 512,
      "storage":0
    },
    {
      "name" :  "Manas",
      "id":  "550e8400-e29b-41d4-a716-446655440001",
      "power": "on",
      "state": "running",
      "image": "Ubuntu 12.04",
      "flavor": "m1.medium",
      "vcpus": 2,
      "memory": 1024,
      "storage":1
    }
]

class InventoryTest(unittest.TestCase):
    '''
        testing solr, using VM core
    '''
    @classmethod
    def setUpClass(cls):
        #TODO: all config parsing - to module level setup
        config = ConfigParser()
        config.read("config/config.ini")
        cls.solr_url = config['DEFAULT']['solr_url'] + 'vm'
        #TODO: figure why 
        logUtils.setup_logging(config)

    
    def setUp(self):

        self.solr = Solr(InventoryTest.solr_url, timeout=2)
        self.solr.delete(q='*:*')
        self.inventory = Inventory(InventoryTest.solr_url);

        super(InventoryTest, self).tearDown()
    

    def testAdd(self):
        self.assertEqual(len(self.solr.search('*:*')), 0)
        self.inventory.post(VMDATA)
        self.assertEqual(len(self.solr.search('*:*')), 2)
        self.assertEqual(len(self.solr.search(VMDATA[0]['name'])), 1)

    def testVmUpdate(self):
        self.inventory.post(VMDATA)
        self.assertEqual(len(self.solr.search('memory:513')), 0)

        vm_update_data = [{'id':VMDATA[0]['id'], 'fields':
                            [
                                {'name':'power', 'value':'off', 'command':'set'},
                                {'name':'memory', 'value':513, 'command':'set'}
                            ]
                          }];
        self.inventory.put(vm_update_data);
        self.assertEqual(len(self.solr.search('memory:513')), 1)

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(InventoryTest)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())



