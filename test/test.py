from multiprocessing.managers import BaseManager
from multiprocessing import current_process
import time
import random

address = "127.0.0.1"
port = 50000
password = "secret"

def connect_to_manager():
    BaseManager.register('sharable_dict')
    manager = BaseManager(address=(address, port), authkey=password.encode('utf-8'))
    manager.connect()
    return manager.sharable_dict()

if __name__ == '__main__':
    pid = current_process().pid
    time.sleep(random.randint(0,1000)*0.001)
    sharable_dict = connect_to_manager()
    print('My pic =', pid)
    sharable_dict[pid] = True
    sharable_dict['xyu%s'%pid] = True
    del sharable_dict['xyu%s'%pid]
    sharable_dict['x'][pid]=False
    sharable_dict['x']['n']+=1
    sharable_dict['x']['z'][0]+=1
    time.sleep(random.randint(0,1000)*0.001)
    print ("%s dict: %s"%(pid,sharable_dict))
    sharable_dict[pid]=False
    time.sleep(random.randint(0,1000)*0.001)
    print ("%s dict: %s"%(pid,sharable_dict))

