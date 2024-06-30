import multiprocessing

def mprun():	
	import IPC
	from IPC.multiboot import sgnMpReg,sgnMpWorker

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

if __name__ == '__main__':
	multiprocessing.freeze_support()

	p=multiprocessing.Process(target=mprun)
	p.start()
	p.join()
