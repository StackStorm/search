from argparse import ArgumentParser
from multiprocessing import Pool, Manager
from tests import faker

import datetime
import json
import time
import uuid
import sys
import random

INSTANCE_TEMPLATE = { 'uuid':'uuid_replace',
               'display_name':'display_name_replace', 
               'host':'h1',
               'power_state':1,
               'vm_state':'active',
               'vcpus':2,
               'memory_mb':10,
               'disk_gb':1,
               'key_name':'key1',
               'launched_at':'replace',
               'user_id':'u1',
               'project_id':'p1',
               'image_ref':'i1',
               'flavor_name':'flavor1',
               'ip':'0.0.0.0' }

COMPUTENODE_TEMPLATE = { 'id':-1, #replace
        'local_gb': 259,
        'vcpus_used': 0,
        'deleted': 0,
        'hypervisor_type': 'powervm',
        'created_at': '2013-04-01T00:27:06.000000',
        'local_gb_used': 0,
        'updated_at': '2013-04-03T00:35:41.000000',
        'hypervisor_hostname': 'hostname_replace',
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
        'free_ram_mb': 130560 }

STATE_MAP = {
    0: 'pending',
    1: 'active',
    3: 'paused',
    4: 'shutdown',
    6: 'crashed',
    7: 'suspended',
    9: 'building',
}

DATA_BATCH = 1000
MAX_PROCESSES = 10
HOST_TO_VM_RATIO = 20

class ScaleDataProvider():
    
    def __init__(self, file_names):
        self.file_names = file_names
    
    def execute(self, query):
        def datetime_hook(data):
            if 'launched_at' in data:
                # expensive translation that causes a 4x multiple in data read time. Necessary to keep InstanceHandler happy.
                data['launched_at'] = datetime.datetime.strptime(data['launched_at'],'%Y-%m-%d %H:%M:%S.%f') if '.' in data['launched_at'] else datetime.datetime.strptime(data['launched_at'],'%Y-%m-%d %H:%M:%S')
            return data
        data = []
        for file_name in self.file_names :
            with open(file_name, "r") as data_file :
                file_data = json.load(data_file, object_hook= datetime_hook)
                data.extend(file_data)
        return data

def ensure_dir(dirname):
    import os
    if not os.path.exists(dirname):
        print 'Creating %s.' % dirname
        os.makedirs(dirname)

def _generate_instance_batch(file_name, data_range, host_names):
    #start_time = time.time()
    #print 'Writing to %s range[%d, %d] in proc %d.' % (file_name, data_range[0], data_range[0] + len(data_range), os.getpid())
    sys.stdout.write('.')
    host_names_index = 0
    projects = faker.firstname(10)
    with open(file_name, 'w') as data_file:
        add_separator = False
        data_file.write('[')
        for index in data_range:
            INSTANCE_TEMPLATE['uuid'] = str(uuid.uuid4())
            INSTANCE_TEMPLATE['display_name'] = 'i-%d.' % index + faker.domain()
            INSTANCE_TEMPLATE['launched_at'] = str(datetime.datetime.now())
            INSTANCE_TEMPLATE['host'] = host_names[host_names_index]
            INSTANCE_TEMPLATE['flavor_name'] = random.sample(("m1.tiny", "m1.small", "m1.medium", "m1.large", "m1.xlarge"), 1)[0]
            INSTANCE_TEMPLATE['power_state'] = random.sample((1,1,1,3,7), 1)[0]
            INSTANCE_TEMPLATE['vm_state'] = STATE_MAP[INSTANCE_TEMPLATE['power_state']]
            INSTANCE_TEMPLATE['vcpus'] = random.randint(1, 4)
            INSTANCE_TEMPLATE['memory_mb'] = random.randint(1, 2048)
            INSTANCE_TEMPLATE['disk_gb'] = random.randint(1, 256)
            INSTANCE_TEMPLATE['project_id'] = 'p' + str(random.randint(0, 9))
            INSTANCE_TEMPLATE['user_id'] = 'u' + str(random.randint(0, 9))
            INSTANCE_TEMPLATE['image_ref'] = 'i' + str(random.randint(0, 9))
            INSTANCE_TEMPLATE['ip'] = faker.ip()
            
            if add_separator:
                data_file.write(',\n')
            else :
                add_separator = True
            json.dump(INSTANCE_TEMPLATE, data_file)
            # even host distribution
            host_names_index = host_names_index + 1
            host_names_index = 0 if host_names_index == len(host_names) else host_names_index
        data_file.write(']')
    #print 'Process %d done writing to %s in %f.' % (os.getpid(), file_name, time.time() - start_time)

def _generate_instance_data(location, size, host_names):
    instance_location = '%s/%s' % (location, 'instance')
    ensure_dir(instance_location)
    sys.stdout.write('generating instance data')
    file_names = []
    num_file = size / DATA_BATCH
    if (size % DATA_BATCH) :
        num_file = num_file + 1
    HOST_BATCH = DATA_BATCH / HOST_TO_VM_RATIO
    pp = Pool(processes=MAX_PROCESSES)
    for file_index in range(num_file):
        file_name = '%s/data_%d.dat' % (instance_location, file_index)
        file_names.append(file_name)
        data_start_index = file_index * DATA_BATCH
        is_last_page = (size - data_start_index) <= DATA_BATCH
        data_end_index = size if is_last_page else data_start_index + DATA_BATCH
        # Even batch distribution
        pp.apply_async(_generate_instance_batch, 
                       args=(file_name, range(data_start_index, data_end_index), 
                       host_names[file_index*HOST_BATCH:file_index*HOST_BATCH + HOST_BATCH]))
    pp.close()
    pp.join()
    sys.stdout.write('\n')
    return file_names

def _generate_computenode_batch(file_name, data_range, host_names):
    #start_time = time.time()
    #print 'Writing to %s range[%d, %d] in proc %d.' % (file_name, data_range[0], data_range[0] + len(data_range), os.getpid())
    sys.stdout.write('.')
    with open(file_name, 'w') as data_file:
        add_separator = False
        data_file.write('[')
        for index in data_range:
            COMPUTENODE_TEMPLATE['id'] = index
            host_name = faker.domain()
            COMPUTENODE_TEMPLATE['hypervisor_hostname'] = host_name
            vcpus = random.randint(8, 24)
            COMPUTENODE_TEMPLATE['vcpus'] = vcpus
            COMPUTENODE_TEMPLATE['memory_mb'] = random.randint(32768, 98304)
            COMPUTENODE_TEMPLATE['local_gb'] = random.randint(1, 2048)
            # TODO: find a way to compute vcpus_used, vcpus_assignred, memory_active, 
            # memory_assigned, storage_used and storage_free. All of them should be calculated
            # after all vm's for the particular host are generated.
            COMPUTENODE_TEMPLATE['vcpus_used'] = random.randint(30, 5 * vcpus + 20)
            COMPUTENODE_TEMPLATE['memory_mb_used'] = random.randint(1, 3 * COMPUTENODE_TEMPLATE['memory_mb'])
            COMPUTENODE_TEMPLATE['local_gb_used'] = random.randint(1, COMPUTENODE_TEMPLATE['local_gb'])
            COMPUTENODE_TEMPLATE['free_disk_gb'] = COMPUTENODE_TEMPLATE['local_gb'] - COMPUTENODE_TEMPLATE['local_gb_used']
            
            host_names.append(host_name)
            if add_separator:
                data_file.write(',\n')
            else :
                add_separator = True
            json.dump(COMPUTENODE_TEMPLATE, data_file)
        data_file.write(']')
    #print 'Process %d done writing to %s in %f.' % (os.getpid(), file_name, time.time() - start_time)

def _generate_computenode_data(location, size):
    computenode_location = '%s/%s' % (location, 'computenode')
    ensure_dir(computenode_location)
    sys.stdout.write('generating computenode data')
    file_names = []
    num_file = size / DATA_BATCH
    if (size % DATA_BATCH) :
        num_file = num_file + 1
    # manager holds the host_names list and allows other process to manipulate this via proxy.
    # initial testing suggests this to be thread/process safe.
    manager = Manager()
    host_names = manager.list()
    pp = Pool(processes=MAX_PROCESSES)
    for file_index in range(num_file):
        file_name = '%s/data_%d.dat' % (computenode_location, file_index)
        file_names.append(file_name)
        data_start_index = file_index * DATA_BATCH
        is_last_page = (size - data_start_index) <= DATA_BATCH
        data_end_index = size if is_last_page else data_start_index + DATA_BATCH
        pp.apply_async(_generate_computenode_batch, args=(file_name, range(data_start_index, data_end_index), host_names))
    pp.close()
    pp.join()
    sys.stdout.write('\n')
    return (file_names, host_names)

def generate_data(location, size):
    # generate computenode data
    computenode_size = size / HOST_TO_VM_RATIO + (1 if size % HOST_TO_VM_RATIO > 0 else 0)
    start_time = time.time()
    computenodes_files, host_names = _generate_computenode_data(location, computenode_size)
    print 'generated %s compute_nodes in %f.' % (len(host_names), time.time() - start_time)
    #generate instance data
    start_time = time.time()
    instances_files = _generate_instance_data(location, size, host_names)
    print 'generated %s instance_nodes in %f.' % (size, time.time() - start_time)
    return (computenodes_files, instances_files)

def main():
    parser = ArgumentParser()
    parser.add_argument("-l", "--location", help="location of the file.")
    parser.add_argument("-n", "--number", help="number of resources.")
    args = parser.parse_args()
    
    computenodes_files, instances_files = generate_data(args.location, int(args.number))
    
#     if len(file_names) > 0:
#         #print file_names
#         print 'reading from %d file(s).' % len(file_names)
#         provider = ScaleDataProvider(file_names)
#         start_time = time.time()
#         data = provider.execute("")
#         print 'read %d(%d bytes) instance_nodes from all files in %f.' % (len(data), sys.getsizeof(data), time.time() - start_time)

if __name__ == '__main__':
    main()