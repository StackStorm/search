from search.worker import worker
import time
import unittest
from mock import patch

TEST_CONFIG = {'DEFAULT':{ 'solr_url':'http://localhost:8983/solr/',
                              'nova_db_server':'172.16.80.200', 
                              'nova_db_port':3306, 
                              'nova_db_creds':'root:openstack', 
                              'amqp_server':'172.16.80.200', 
                              'amqp_port':5672,
                              'amqp_creds':'guest:guest', 
                              'logConfig':'./tests/logging.conf'},
                'testHandler' : {'handlerName':'workertest.FakeHandler', 
                              'interval':60 }
                }


class WorkerTest(unittest.TestCase):
    
    @patch('search.worker.worker.get_class')
    def test_run(self, get_klass):
        '''
        Test if the config is read correctly by the config handler,
        and the proper handler instantiated and called in right order
        '''
        worker.run(TEST_CONFIG, 'testHandler')

        self.assertEqual(get_klass.call_args[0][0], 
                TEST_CONFIG['testHandler']['handlerName'])

        # Obtain a handler via mock chain
        handlerKls = get_klass.return_value
        handler = handlerKls.return_value
        
        # Validate configuration parsing. We are happy if handler instantiated
        # with parameters we wanted.
        solr_url = handlerKls.call_args[0][0]
        self.assertEqual(solr_url, TEST_CONFIG['DEFAULT']['solr_url'])
        db_info = handlerKls.call_args[0][1]
        self.assertEqual(db_info.host, TEST_CONFIG['DEFAULT']['nova_db_server'])
        self.assertEqual(db_info.port, TEST_CONFIG['DEFAULT']['nova_db_port'])
        self.assertEqual(db_info.creds, TEST_CONFIG['DEFAULT']['nova_db_creds'])

        amqp_info = handlerKls.call_args[0][2]
        self.assertEqual(amqp_info.host, TEST_CONFIG['DEFAULT']['amqp_server'])
        self.assertEqual(amqp_info.port, TEST_CONFIG['DEFAULT']['amqp_port'])
        self.assertEqual(amqp_info.creds, TEST_CONFIG['DEFAULT']['amqp_creds'])

        self.assertEqual(handlerKls.call_args[0][3], 
                TEST_CONFIG['testHandler']['interval'])

        if len(handler.method_calls)!=2:
            # picking a value that does not affect the test performance much
            time.sleep(0.001)
        h = get_klass.return_value.return_value
        # Aassert the methods and the order. There is likely an easier way.
        self.assertTrue( h.method_calls[0][0] == 'setup_amqp' )
        self.assertTrue( h.method_calls[1][0] == 'on_start' )


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(WorkerTest)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())