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


        d['xyu']=manager.dict()
        d['xyu']['pizda']=123
        d['a']=dict(a=1,b=2,c=dict(x=[1,2,3,[4,5,6],{'c':'d'}]))
        p1 = sgnMpWorker('logger',d,'logger/logger.py')
        p2 = sgnMpWorker('settings',d,'settings/settings.py')
        p1.start()
        p2.start()
        time.sleep(1)
        print(d)
        print(d['service_container']['logger']['ipc'].get())
        print(d['service_container']['settings']['ipc'].get())
        d['service_container']['logger']['ipc'].set(1)
        d['service_container']['settings']['ipc'].set(2)
        print(d['service_container']['logger']['ipc'].get())
        print(d['service_container']['settings']['ipc'].get())
        print(d['service_container']['settings']['ipc'].call('opa','hello'))
        print(d['service_container']['settings']['ipc'].call('zopa','hello'))
        time.sleep(1)
        p1.shutdown()
        #d['service_container']['logger']['methods']['stop']()
        p1.join()
        p2.join()

