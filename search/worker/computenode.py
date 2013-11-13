from search.datasource import session, amqp_client
from search.inventory import Inventory
from search.utils import logUtils

LOG = logUtils.get_logger(__name__)

class ComputeNodeHandler():
    '''
    All ComputeNode/Host related handling. Associated with the host core in solr.
    '''

    def __init__(self, solr_url, db_info, amqp_info, interval=60):
        self.db_info = db_info
        self.amqp_info = amqp_info
        self.interval = interval
        self.hosts = []
        self.inventory = Inventory(solr_url + 'host')
        self.engine = session.get_engine(self.db_info)

    def setup_amqp(self):
        queue_info = amqp_client.QueueInfo('osh_computenode_q', 'nova', 'notifications.info', 'topic')
        client = amqp_client.NotificationClient(self.amqp_info, queue_info, self.on_event)
        client.start()

    def on_start(self):
        LOG.debug("running on_start")
        compute_query = ("SELECT id, hypervisor_hostname, hypervisor_type, cpu_info, running_vms, "
                         "vcpus, vcpus_used, memory_mb, memory_mb_used, free_ram_mb, "
                         "local_gb, local_gb_used, free_disk_gb "
                         "FROM compute_nodes "
                         "WHERE deleted = 0")
        result = self.engine.execute(compute_query)
        data = [self._to_compute_node_data(row) for row in result]
        # Save the hosts around
        self.hosts = [{'id':row['id'], 'name':row['name']} for row in data]
        LOG.info("Adding {0} compute nodes.".format(str(len(data))))
        #FIXME(DZ): Move check for empty data can be inside inventory
        if len(data) > 0:
            self.inventory.post(data)

    def on_event(self, body, message):
        try:
            event_type = body.get('event_type')
            handler_func = self._get_event_handler(event_type)
            if not hasattr(handler_func, '__call__'):
                LOG.debug('Ignoring ' + event_type + ' : ' + body['timestamp'])
            else:
                handler_func(body['payload'])
        except:
            LOG.exception('Failed to handle event')
        finally:
            message.ack()

    def on_interval(self):
        """
            Periodic checks for the resource go here...
        """
        LOG.debug('Running on_interval')

    def _get_event_handler(self, event_type):
        """
        matches event_type with a handler method.
        """
        if event_type is None:
            return None
        # Assume 
        if event_type.startswith('compute.instance') and event_type.endswith(".end"):
            return self._handle_modify_event
        else:
            return None
    
    def _handle_modify_event(self, event_payload):
        # retrieve the ComputeNode associated with this instance.
        instance_id = event_payload['instance_id']
        compute_query = ("SELECT cn.id, cn.hypervisor_hostname, cn.hypervisor_type, cn.cpu_info, cn.running_vms, cn.vcpus, cn.vcpus_used, cn.memory_mb, cn.memory_mb_used, cn.free_ram_mb, cn.local_gb, cn.local_gb_used, cn.free_disk_gb "
                         "FROM compute_nodes as cn "
                         "INNER JOIN instances as i on i.host = cn.hypervisor_hostname "
                         "WHERE cn.deleted = 0 and i.uuid = '%s'" % instance_id)
        result = self.engine.execute(compute_query)
        data = [self._to_compute_node_data(row) for row in result]
        if len(data) < 1 :
            LOG.warn('No host found for instance ' + instance_id)
            return
        # By defn 1 instance maps to a single host
        row = data[0]
        # update if know host else add new one.
        if self._is_known_host(row['name']):
            # generate update set
            host_update_data = [{'id':row['id'], 
                                    'fields':[{'name' : 'vm_count', 'value' : row['vm_count'], 'command':'set'},
                                              {'name' : 'vcpus', 'value' : row['vcpus'], 'command':'set'},
                                              {'name' : 'vcpus_assigned', 'value' : row['vcpus_assigned'], 'command':'set'},
                                              {'name' : 'memory_assigned', 'value' : row['memory_assigned'], 'command':'set'},
                                              {'name' : 'memory_available_for_vms', 'value' : row['memory_available_for_vms'], 'command':'set'},
                                              {'name' : 'storage_used', 'value' : row['storage_used'], 'command':'set'},
                                              {'name' : 'storage_free', 'value' : row['storage_free'], 'command':'set'}
                                              ]
                                 }]
            self.inventory.put(host_update_data)
        else:
            # update self.hosts
            if self.hosts is None:
                self.hosts = []
            self.hosts.append({'id':row['id'], 'name':row['name']})
            # add new compute_node to solr. memory_used will be update during the next on_interval cycle.
            self.inventory.post(row)
    
    def _is_known_host(self, hostname):
        '''
        checks if a host with the supplied hostname is available in the set of known hosts
        '''
        if self.hosts:
            for host in self.hosts:
                if host['name'] == hostname:
                    return True
        return False

    def _to_compute_node_data(self, row):
        '''
        solr schema formatted row representation.
        '''
        return {'id':row['id'], 
                 'name':row['hypervisor_hostname'], 
                 'ip':row['hypervisor_hostname'], # Get from libvirt?
                 'vcpus':row['vcpus'],
                 'memory':row['memory_mb'],
                 'storage':row['local_gb'],
                 'vm_count':row['running_vms'], # In nova, running_vms include suspended/paused
                 'hypervisor':row['hypervisor_type'],
                 'cpu_info':row['cpu_info'],
                 'vcpus_assigned':row['vcpus_used'],
                 'memory_assigned':row['memory_mb_used'],
                 'memory_available_for_vms':row['free_ram_mb'], # in nova, =total-assigned
                 'memory_used': -1, # True free/used not available in OpenStack, get later...
                 'storage_used':row['local_gb_used'],
                 'storage_free':row['free_disk_gb']}