from search.datasource import session, amqp_client
from search.inventory import Inventory
from search.utils import logUtils
import datetime
        
LOG = logUtils.get_logger(__name__)

INSTANCE_CREATE_EVENTS= ['compute.instance.create.end']
INSTANCE_DELETE_EVENTS = ['compute.instance.delete.end']
INSTANCE_MODIFY_EVENTS = ['compute.instance.update',
                          'compute.instance.rebuild.end',
                          'compute.instance.resize.prep.end',
                          'compute.instance.resize.confirm.end',
                          'compute.instance.resize.revert.end',
                          'compute.instance.resize.end',
                          'compute.instance.finish_resize.end',
                          'compute.instance.shutdown.end',
                          'compute.instance.power_off.end',
                          'compute.instance.power_on.end',
                          'compute.instance.reboot.end',
                          'compute.instance.suspend', 
                          'compute.instance.resume',
                          'compute.instance.snapshot.end']

class InstanceHandler():
    '''
    All instance/vm related handling. Associated with the vm core of solr.
    '''    
    def __init__(self, solr_url, db_info, amqp_info, interval=60):
        self.solr_url = solr_url+'vm'
        self.db_info = db_info
        self.amqp_info = amqp_info
        self.interval = interval
        self.inventory = Inventory(solr_url+'vm')
        self.engine = session.get_engine(self.db_info)
    
    def setup_amqp(self):
        queue_info = amqp_client.QueueInfo('osh_instance_q', 'nova', 'notifications.info', 'topic')
        client = amqp_client.NotificationClient(self.amqp_info, queue_info, self.on_event)
        client.start()

    def on_start(self):
        # user, projects and images are from 
        self.users = self._get_users(self.db_info)
        self.projects = self._get_projects(self.db_info)
        self.images = self._get_images(self.db_info)
        instances_query = ("SELECT i.uuid, i.display_name, i.host, i.power_state, i.vm_state, i.vcpus, i.memory_mb, i.root_gb + i.ephemeral_gb as disk_gb, i.key_name, i.launched_at, i.user_id, i.project_id, i.image_ref, t.name as flavor_name "
                          "FROM instances as i INNER JOIN instance_types as t ON i.instance_type_id = t.id "
                          "WHERE i.deleted = 0")
        result = self.engine.execute(instances_query)
        # Ok for small inventory but will not work for large inventories
        data = [self._to_instance_data(row) for row in result]
        if len(data) > 0:
            LOG.info("Adding %d instances." % len(data))
            self.inventory.post(data)
   
    def on_event(self, body, message):
        try :
            event_type = body.get('event_type')
            handler_func = self._get_event_handler(event_type)
            if not hasattr(handler_func, '__call__'):
                LOG.debug('Ignoring ' + event_type + ' : ' + body['timestamp'])
            else:
                LOG.debug('Handling ' + event_type + ' : ' + body['timestamp'])
                handler_func(body['payload'])
        except:
            LOG.exception('Failed to handle event ' + event_type)
        finally:
            message.ack()

    def on_interval(self):
        '''
            Periodic checks for the resource go here...
        '''
        LOG.debug('Running on_interval')


    def _get_event_handler(self, event_type):
        """
        matches event_type with a handler method.
        """
        if event_type is None:
            return None
        elif event_type in INSTANCE_CREATE_EVENTS:
            return self._handle_create_event
        elif event_type in INSTANCE_DELETE_EVENTS:
            return self._handle_delete_event
        elif event_type in INSTANCE_MODIFY_EVENTS:
            return self._handle_modify_event
        return None
        
    def _handle_create_event(self, event_payload):
        instance_id = event_payload['instance_id']
        instance_query = ("SELECT i.uuid, i.display_name, i.host, i.power_state, i.vm_state, i.vcpus, i.memory_mb, i.root_gb + i.ephemeral_gb as disk_gb, i.key_name, i.launched_at, i.user_id, i.project_id, i.image_ref, t.name as flavor_name "
                          "FROM instances as i INNER JOIN instance_types as t ON i.instance_type_id = t.id "
                          "WHERE i.deleted = 0 AND i.uuid = '" + instance_id + "'")
        result = self.engine.execute(instance_query)
        data = [self._to_instance_data(row) for row in result]
        if len(data) > 0 :
            self.inventory.post(data)
    
    def _handle_delete_event(self, event_payload):
        instance_id = event_payload['instance_id']
        self.inventory.delete(instance_id)
    
    def _handle_modify_event(self, event_payload):
        # for now same handling as create
        self._handle_create_event(event_payload)
    
    def _to_instance_data(self, row):
        '''
        solr schema formatted row representation.
        '''
        def map_powerstate(power_state):
            # DZ: We map nova power state to a simpler model
            if power_state == 0x01 :
                return 'on'
            elif power_state == 0x03 :
                return 'paused'
            elif power_state in [0x04, 0x07] :
                return 'off'
            return 'none'

        return {'id':row['uuid'],
                 'name':row['display_name'], 
                 'host':row['host'],
                 'ip':dict(row).get('ip'),
                 'power':map_powerstate(row['power_state']),
                 'state':row['vm_state'],
                 'flavor':row['flavor_name'],
                 'vcpus':row['vcpus'],
                 'memory':row['memory_mb'],
                 'storage':row['disk_gb'],
                 'user':self._get_user_name(row['user_id']),
                 'project':self._get_project_name(row['project_id']),
                 'image':self._get_image_name(row['image_ref']),
                 'ssh_key':row['key_name'],
                 'launched_at':str(row['launched_at']),
                 'uptime':str(datetime.datetime.now() - row['launched_at']) if row['launched_at'] is not None else ''}

    def _get_users(self, db_info):
        """
        Returns user name by user id per keystone.
        """
        engine = session.get_keystone_engine(db_info)
        result = engine.execute("select id, name from user")
        users = {row['id'] : row['name'] for row in result}
        return users
    
    def _get_user_name(self, user_id):
        """
        Name of the user identified by user_id. If not found returns an empty string.
        """
        if user_id not in self.users:
            self.users =  self._get_users(self.db_info)
        if user_id in self.users:
            return self.users[user_id]
        return ""
    
    def _get_projects(self, db_info):
        """
        Returns project name by project id per keystone.
        """
        engine = session.get_keystone_engine(db_info)
        result = engine.execute("select id, name from project")
        projects = {row['id'] : row['name'] for row in result}
        return projects
    
    def _get_project_name(self, project_id):
        """
        Name of the project identified by project_id. If not found returns an empty string.
        """
        if project_id not in self.projects:
            self.projects =  self._get_projects(self.db_info)
        if project_id in self.projects:
            return self.projects[project_id]
        return ""
    
    def _get_images(self, db_info):
        """
        Returns image name by image id per keystone.
        """
        engine = session.get_glance_engine(db_info)
        result = engine.execute("select id, name from images")
        images = {row['id'] : row['name'] for row in result}
        return images

    def _get_image_name(self, image_id):
        """
        Name of the image identified by image_id. If not found returns an empty string.
        """
        if image_id not in self.images:
            self.images =  self._get_images(self.db_info)
        if image_id in self.images:
            return self.images[image_id]
        return ""