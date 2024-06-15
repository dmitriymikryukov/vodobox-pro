import IPC
from IPC.multiboot import *
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    with sgnMpReg().manager as manager:
        d = manager.dict()
        maindict=d
        d['control']=manager.dict({'shutdown':False})
        d['service_container']=manager.dict()
        d['events']=manager.dict()
        d['lock']=manager.RLock()

        p1 = sgnMpWorker('logger',d,'logger/logger.py')
        p2 = sgnMpWorker('settings',d,'settings/settings.py')
        p1.start()
        p2.start()
        time.sleep(10)
        p1.shutdown()
        #d['service_container']['logger']['methods']['stop']()
        p1.join()
        p2.join()

