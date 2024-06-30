import multiprocessing


if __name__ == '__main__':
	multiprocessing.freeze_support()
	
	import IPC
	from IPC.multiboot import *

	with sgnMpReg().manager as manager:
		d = manager.dict()
		maindict=d
		d['control']=manager.dict({'shutdown':False})
		d['service_container']=manager.dict()
		d['events']=manager.dict()
		d['lock']=manager.RLock()

		p = sgnMpWorker('boot',d,'./bootmgr.py')

		p.start()
		p.join()
		p.shutdown()

