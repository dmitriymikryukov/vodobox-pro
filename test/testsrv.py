from multiprocessing.managers import BaseManager, DictProxy
from threading import Thread, Event
#from test2 import address, port, password, connect_to_manager
from subprocess import Popen

address = "127.0.0.1"
port = 50000
password = "secret"

the_dict = None

def get_dict():
    global the_dict
    print ("get_dict")
    if the_dict is None:
        the_dict = dict(x=dict(n=0,n2=0))
    the_dict['x']['n2']+=1
    print (the_dict)
    return the_dict

def connect_to_manager():
    BaseManager.register('sharable_dict')
    manager = BaseManager(address=(address, port), authkey=password.encode('utf-8'))
    manager.connect()
    return manager.sharable_dict()

def server(started_event, shutdown_event):
    net_manager = BaseManager(address=(address, port), authkey=password.encode('utf-8'))
    BaseManager.register('sharable_dict', get_dict, DictProxy)
    net_manager.start()
    started_event.set() # tell main thread that we have started
    shutdown_event.wait() # wait to be told to shutdown
    net_manager.shutdown()

def main():
    started_event = Event()
    shutdown_event = Event()
    server_thread = Thread(target=server, args=(started_event, shutdown_event,))
    server_thread.start()
    # wait for manager to start:
    started_event.wait()

    processes = [Popen(['python3', 'test.py']) for _ in range(3)]
    for process in processes:
        process.communicate()

    sharable_dict = connect_to_manager()
    print('sharable dictionary =', sharable_dict)

    # tell manager we are through:
    shutdown_event.set()
    server_thread.join()

if __name__ == '__main__':
    main()
