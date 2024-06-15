import IPC
from IPC.multiboot import *
import multiprocessing
import sys,os,time
import glob

class sgnBoot(IPC.sgnService):
	
	def __init__(self):
		super().__init__()
		self.services_dir=os.path.abspath(os.path.join(os.path.dirname(__file__),'services'))

	def getServices(self):
		dirs=[f for f in os.listdir(self.services_dir) if os.path.isdir(os.path.join(self.services_dir, f))]
		srv=dict()
		for d in dirs:
			lvf=os.path.join(self.services_dir, d)
			lvl=glob.glob(os.path.join(lvf,'level.*'))
			if not len(lvl):
				lvl=-1
			elif len(lvl)>1:
				self.exception('MULTIPLE LEVELS IN SERVICE: %s'%d)
				lvl=0
			else:
				try:
					z=lvl[0].split('.')
					lvl=int(z[-1])
				except:
					self.exception('INVALID LEVEL IN SERVICE: %s'%d)
					lvl=-1
			if not (lvl in srv):
				srv[lvl]=[]
			srv[lvl].append(d)
		return srv


	def startLevel(self,level,services):
		if len(services) and not self['control']['shutdown']:
			succ=False
			try:
				self.info("\n*** STARTING SERIVCES AT LEVEL: %s"%level) if level!=0 else print("STARTING SERIVCES AT LEVEL: %s"%level)
				for s in services:
					try:
						path='%s/%s.py'%(s,s)
						p = sgnMpWorker(s,self.gdict,path)
						p.start()

						"""
						f=os.path.join(self.services_dir, s, 'run.sh')
						if os.path.isfile(f):
							pd=os.getcwd()
							try:
								os.chdir(os.path.join(self.services_dir, s))
								if 0==os.system('"%s" &'%f):
									self.info("%d: STARTING %s.service"%(level,s)) if level!=0 else print("%d: STARTING %s.service"%(level,s))
									time.sleep(1.5)
								else:
									self.critical("%d: CANNOT %s.service, failed execute run.sh"%(level,s)) if level!=0 else print("%d: CANNOT %s.service, no run.sh"%(level,s)) 
							finally:
								os.chdir(pd)
						else:
							self.critical("%d: CANNOT %s.service, no run.sh"%(level,s)) if level!=0 else print("%d: CANNOT %s.service, no run.sh"%(level,s)) 
						"""
					except Exception as e:
						self.exception(e)
				ts=time.time()+15.0	
				succ=False		
				while time.time()<ts and not succ and not self['control']['shutdown']:
					succ=True
					try:
						for s in services:
							if s in self['service_container'].keys():
								if self['service_container'][s]['status']!='ALIVE':
									succ=False
							else:
								succ=False
							time.sleep(0.1)
					except Exception as e:
						print(e)
						time.sleep(2.0)
						succ=False
					time.sleep(0.1)
				self.info("*** LEVEL: %s COMPLETE\n"%level)
				if not succ:
					for s in services:
						if s in self['service_container']:
							self.info("%s status: %s"%(s,self['service_container'][s]['status']))
			finally:
				if not succ:
					self.critical('STARTING LEVEL FAILED, TIMED OUT!')
					self.exiting=True

	def startServices(self):
		srv=self.getServices()
		kl=list(srv.keys())
		kl.sort()
		for l in kl:
			if l>=0:
				self.startLevel(l,srv[l])
				#break
		#return
		for l in kl:
			if l<0:
				self.startLevel(l,srv[l])
		self._services=srv

	def stopLevel(self,level,services):
		if len(services):
			print('STOPPING LEVEL: %s'%level)
			for s in services:
				print('\tSTOPPING SERVICE: %s'%s)
				try:
					self.stopService(s)
				except:
					print("\n FAILED TO STOP %s"%s)
			ts=time.time()+3.0	
			succ=False		
			while time.time()<ts and not succ:
				succ=True
				try:
					for s in services:
						if s in self['service_container']:
							if self['service_container'][s]['status']=='ALIVE':
								succ=False
						else:
							succ=False
				except Exception as e:
					print(e)
					time.sleep(0.5)
					succ=False
				time.sleep(0.1)

			print('LEVEL %s STOPPED'%level)

	def stopServices(self):
		if not self.stopping:
			self.stopping=True
			srv=self._services
			kl=list(srv.keys())
			kl.sort()
			for l in reversed(kl):
				if l>=0:
					self.stopLevel(l,srv[l])
			for l in reversed(kl):
				if l<0:
					self.stopLevel(l,srv[l])

	def boot(self):
		try:
			print("BOOTING UP SYSTEM")
			self.startServices()
			self.join()
		finally:
			self['control']['shutdown']=True

b=sgnBoot()
b.boot()

