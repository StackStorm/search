from mock import MagicMock
from search.datasource.session import DBInfo
from search.worker.instance import InstanceHandler
import unittest
import datetime

FAKE_NODES = [{'uuid':1,
               'display_name':'v1', 
               'host':'h1',
               'power_state':1,
               'vm_state':'active',
               'vcpus':2,
               'memory_mb':10,
               'disk_gb':1,
               'key_name':'key1',
               'launched_at':datetime.datetime.strptime("2013-04-01T00:27:06.000000",'%Y-%m-%dT%H:%M:%S.%f'),
               'user_id':'u1',
               'project_id':'p1',
               'image_ref':'i1',
               'flavor_name':'flavor1'
              },
              {'uuid':2,
               'display_name':'v2', 
               'host':'h1',
               'power_state':3,
               'vm_state':'active',
               'vcpus':2,
               'memory_mb':10,
               'disk_gb':1,
               'key_name':'key2',
               'launched_at':datetime.datetime.strptime("2013-04-01T00:27:06.000000",'%Y-%m-%dT%H:%M:%S.%f'),
               'user_id':'u2',
               'project_id':'p2',
               'image_ref':'i2',
               'flavor_name':'flavor2'
               }]

#config = ConfigParser()
#config.read("../config/config.ini")
#logUtils.setup_logging(config)

class InstanceHandlerTest(unittest.TestCase):

    def setUp(self):

        solr_url = 'https://fake/solr/url'
        db_info =  DBInfo(host='fake', port='123', creds='foo:bar')
        ampq_info = None
        libvirt_info = {'user':'fake'}
        self.instance = InstanceHandler(solr_url, db_info, ampq_info, libvirt_info)
        self.instance.inventory = MagicMock()
        self.instance.users = {'u1':'user1', 'u2':'user2'}
        self.instance.projects = {'p1':'project1', 'p2':'project2'}
        self.instance.images = {'i1':'image1', 'i2':'image2'}
    
    def test_on_create_event(self):
        '''
        tests the compute.instance.create.end event
        '''
        self.instance.engine.execute = MagicMock(return_value=[FAKE_NODES[0]])
        create_event = {}
        create_event['event_type'] = 'compute.instance.create.end'
        create_event['payload'] = {'instance_id':'1'}
        create_event['timestamp'] = str(datetime.datetime.now())
        message = MagicMock()
        self.instance.on_event(create_event, message)
        self.assertEqual(self.instance.engine.execute.call_count, 1)
        rows = self._computed_row_data(self.instance.inventory.post.call_args, FAKE_NODES[0])
        self.instance.inventory.post.assert_called_with(rows)
        message.ack.assert_called_once_with()

    def test_on_delete_event(self):
        '''
        tests the compute.instance.delete.end event
        '''
        self.instance.engine.execute = MagicMock(return_value=[FAKE_NODES[0]])
        delete_event = {}
        delete_event['event_type'] = 'compute.instance.delete.end'
        delete_event['payload'] = {'instance_id':'1'}
        delete_event['timestamp'] = str(datetime.datetime.now())
        message = MagicMock()
        self.instance.on_event(delete_event, message)
        self.instance.inventory.delete.assert_called_with(delete_event['payload']['instance_id'])
        message.ack.assert_called_once_with()
    
    def test_update_event(self):
        '''
        tests the compute.instance.update event
        '''
        self._run_update_test('compute.instance.update')
        
    def test_rebuild_event(self):
        '''
        tests the compute.instance.rebuild.end event
        '''
        self._run_update_test('compute.instance.rebuild.end')
    
    def test_resize_prep_event(self):
        '''
        tests the compute.instance.rebuild.end event
        '''
        self._run_update_test('compute.instance.resize.prep.end')
    
    def test_resize_confirm_event(self):
        '''
        tests the compute.instance.rebuild.end event
        '''
        self._run_update_test('compute.instance.resize.confirm.end')
    
    def test_resize_revert_event(self):
        '''
        tests the compute.instance.rebuild.end event
        '''
        self._run_update_test('compute.instance.resize.revert.end')
        
    def test_resize_event(self):
        '''
        tests the compute.instance.resize event
        '''
        self._run_update_test('compute.instance.resize.end')
    
    def test_finish_resize_event(self):
        '''
        tests the compute.instance.finish_resize.end event
        '''
        self._run_update_test('compute.instance.finish_resize.end')
    
    def test_shutdown_event(self):
        '''
        tests the compute.instance.shutdown.end event
        '''
        self._run_update_test('compute.instance.shutdown.end')
    
    def test_power_off_event(self):
        '''
        tests the compute.instance.power_off.end event
        '''
        self._run_update_test('compute.instance.power_off.end')
    
    def test_power_on_event(self):
        '''
        tests the compute.instance.power_on.end event
        '''
        self._run_update_test('compute.instance.power_on.end')
    
    def test_reboot_on_event(self):
        '''
        tests the compute.instance.reboot.end event
        '''
        self._run_update_test('compute.instance.reboot.end')
    
    def test_suspend_event(self):
        '''
        tests the compute.instance.suspend event
        '''
        self._run_update_test('compute.instance.suspend')
    
    def test_resume_event(self):
        '''
        tests the compute.instance.resume event
        '''
        self._run_update_test('compute.instance.resume')
    
    def test_snapshot_event(self):
        '''
        tests the compute.instance.snapshot.end event
        '''
        self._run_update_test('compute.instance.snapshot.end')
    
    def test_invalid_event(self):
        '''
        tests an invalid event
        '''
        invalid_event = {}
        invalid_event['event_type'] = 'unhandled.event'
        invalid_event['timestamp'] = str(datetime.datetime.now())
        message = MagicMock()
        self.instance.on_event(invalid_event, message)
        message.ack.assert_called_once_with()
    
    def test_user_name_cache_hit(self):
        user_name = self.instance._get_user_name('u1')
        self.assertEqual('user1', user_name, 'User name match failed.')
    
    def test_user_name_cache_miss(self):
        users = {'u1':'user1','u2':'user2','u3':'user3'}
        self.instance._get_users = MagicMock(return_value=users)
        user_name = self.instance._get_user_name('u3')
        self.assertEqual(self.instance._get_users.call_count, 1)
        self.assertEqual(self.instance.users, users, 'self.instance.users value is unexpected.')
        self.assertEqual(users['u3'], user_name, 'User name match failed.')
        
    def test_user_name_cache_double_miss(self):
        users = {'u1':'user1','u2':'user2','u3':'user3'}
        self.instance._get_users = MagicMock(return_value=users)
        user_name = self.instance._get_user_name('u4')
        self.assertEqual(self.instance._get_users.call_count, 1)
        self.assertEqual(self.instance.users, users, 'self.instance.users value is unexpected.')
        self.assertEqual('', user_name, 'User name match failed.')
    
    def test_project_name_cache_hit(self):
        project_name = self.instance._get_project_name('p1')
        self.assertEqual('project1', project_name, 'project name match failed.')
    
    def test_project_name_cache_miss(self):
        projects = {'p1':'project1', 'p2':'project2', 'p3':'project3'}
        self.instance._get_projects = MagicMock(return_value=projects)
        project_name = self.instance._get_project_name('p3')
        self.assertEqual(self.instance._get_projects.call_count, 1)
        self.assertEqual(self.instance.projects, projects, 'self.instance.projects value is unexpected.')
        self.assertEqual(projects['p3'], project_name, 'project name match failed.')
    
    def test_project_name_cache_double_miss(self):
        projects = {'p1':'project1', 'p2':'project2', 'p3':'project3'}
        self.instance._get_projects = MagicMock(return_value=projects)
        project_name = self.instance._get_project_name('p4')
        self.assertEqual(self.instance._get_projects.call_count, 1)
        self.assertEqual(self.instance.projects, projects, 'self.instance.projects value is unexpected.')
        self.assertEqual('', project_name, 'project name match failed.')
    
    def test_image_name_cache_hit(self):
        image_name = self.instance._get_image_name('i1')
        self.assertEqual('image1', image_name, 'image name match failed.')
    
    def test_image_name_cache_miss(self):
        images = {'i1':'image1', 'i2':'image2', 'i3':'image3'}
        self.instance._get_images = MagicMock(return_value=images)
        image_name = self.instance._get_image_name('i3')
        self.assertEqual(self.instance._get_images.call_count, 1)
        self.assertEqual(self.instance.images, images, 'self.instance.images value is unexpected.')
        self.assertEqual(images['i3'], image_name, 'image name match failed.')
    
    def test_image_name_cache_double_miss(self):
        images = {'i1':'image1', 'i2':'image2', 'i3':'image3'}
        self.instance._get_images = MagicMock(return_value=images)
        image_name = self.instance._get_image_name('i4')
        self.assertEqual(self.instance._get_images.call_count, 1)
        self.assertEqual(self.instance.images, images, 'self.instance.images value is unexpected.')
        self.assertEqual('', image_name, 'image name match failed.')
    
    def _run_update_test(self, update_event_id):
        update_event = {}
        update_event['event_type'] = update_event_id
        update_event['payload'] = {'instance_id':'1'}
        update_event['timestamp'] = str(datetime.datetime.now())
        self.instance.engine.execute = MagicMock(return_value=[FAKE_NODES[0]])
        message = MagicMock()
        self.instance.on_event(update_event, message)
        self.assertEqual(self.instance.engine.execute.call_count, 1)
        rows = self._computed_row_data(self.instance.inventory.post.call_args, FAKE_NODES[0])
        self.instance.inventory.post.assert_called_with(rows)
        message.ack.assert_called_once_with()
    
    def _computed_row_data(self, call_args, source_node):
        # hack to pull out uptime
        uptime = call_args[0][0][0]['uptime']
        # todo (manas) : validate uptime is a timedelta
        row = self.instance._to_instance_data(source_node)
        row['uptime'] = uptime
        return [row]

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(InstanceHandlerTest)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())