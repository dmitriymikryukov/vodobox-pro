import multiprocessing
import time,sys

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
		try:
			try:
				try:
					#p.join()
					while True:
						time.sleep(10)
				except KeyboardInterrupt:
					print("CTRL-C")
					try:
						d.critical('CTRL-C Interrupt')
						time.sleep(1)
						d['shutdown']=True
						time.sleep(1)
					except:
						pass
			finally:
				try:
					p.shutdown()
				except:
					pass
		except:
			pass

if __name__ == '__main__':
	multiprocessing.freeze_support()
	mprun()

	#p=multiprocessing.Process(target=mprun)
	#p.start()
	#try:
	#	p.join()
	#finally:
	#	p.shutdown()
	#	time.sleep(1.0)
