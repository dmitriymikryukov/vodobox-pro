from IPC import *
import sys,os,time,signal
import glob
from traceback import format_exc

restarting=True

l=None

def_handTERM=signal.getsignal(signal.SIGTERM)
def signal_thandler(num, stack):
	print("TERM STOP SIGNAL!")
	if l and not l.exiting:
		l.stop()
	else:
		signal.signal(signal.SIGTERM, def_handTERM)
		sys.exit(1)
signal.signal(signal.SIGTERM, signal_thandler)

def_handINT=signal.getsignal(signal.SIGTERM)
def signal_ihandler(num, stack):
	print("INT STOP SIGNAL!")
	if l and not l.exiting:
		l.stop()
	else:
		signal.signal(signal.SIGINT, def_handINT)
		sys.exit(1)
signal.signal(signal.SIGINT, signal_ihandler)

from IPC.ipcdict import IPCdict

class mainService(sgnService):
	def __init__(self,*args,**kwargs):
		self.stopping=False
		self._services=dict()
		self.restarting=False
		print("mainService.init")
		sgnService.__init__(self,is_server=True)
		self.services_dir=os.path.join(self.service_base,'services')
		self.restart()

	def stop(self):
		print("*STOP*")
		self.exiting=True
		IPCdict.connection.shutdown()

	def serviceStarted(self):
		pass

	def doEnd(self):
		try:
			self.stopServices()
		finally:
			super().doEnd()

	def doExit(self):
		if not self.restarting:
			print("Main exiting, exiting")
			try:
				self.connection.shutdown()
			except:
				pass
			super().doExit()

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
		if len(services) and not self.exiting:
			succ=False
			try:
				self.info("\n*** STARTING SERIVCES AT LEVEL: %s"%level) if level!=0 else print("STARTING SERIVCES AT LEVEL: %s"%level)
				for s in services:
					try:
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
					except Exception as e:
						self.exception(e)
				ts=time.time()+15.0	
				succ=False		
				while time.time()<ts and not succ and not self.exiting:
					succ=True
					try:
						for s in services:
							if s in self['service_container']:
								if self['service_container'][s]['status']!='ALIVE':
									succ=False
							else:
								succ=False
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

	def stop(self):
		print('STOPPING SERVICES')
		try:
			self.stopServices()
		except Exception as e:
			self.exception(e)
		try:
			self.exit()
		except:
			pass
		self.exiting=True


	def restart(self):
		global restarting
		self.restarting=True
		try:
			self.exit()
		except:
			print("Not all services is active and can get exit signal")
		time.sleep(2.0)
		p=os.getpid()
		kills={}
		for s in self['service_container']:
			try:			
				pp=self['service_container'][s]['pid']
				if pp!=p:
						kills[pp]=True
			except Exception as ex:
				print (ex)														
		for e in self['broker']['events']:
			try:
				for itn in self['broker']['events'][e]['items']:
					try:
						pp=self['broker']['events'][e]['items'][itn]['pid']
						if pp!=p:
							kills[pp]=True
					except Exception as ex:
						print (ex)					
			except Exception as ex:
				print (ex)
		for k in kills:
			try:
				os.kill(k,signal.SIGTERM)
			except:
				print("TERMINATING %s - NO SUCH PROCESS"%k)
		time.sleep(1.0)
		for k in kills:
			try:
				os.kill(k,signal.SIGKILL)
			except:
				pass
		if len(kills):
			print("NEED TO RESTART MAIN AFTER KILLING")
			restarting=True
			self.exiting=True
		self.restarting=False

def main():
	global l,restarting
	try:
		l=mainService(is_server=True)
		#l.join()

		#raise OSError('hello')

		if not l.exiting:
			print("\n***** STARTING SGN IPC SYSTEM *****")
			print("basepath: %s"%l.service_base)
			print("APPLICATION: %s"%l.servicename)
			l.init_container()
			l.started=True
			l.container['status']="ALIVE"
			l.startServices()
		if not restarting:
			try:
				l.warning('STARTING %s SYSTEM'%l.getName())
			except:
				pass
		tx=[]
		tx.append('REGISTERED EVENTS:')
		for x in l['service_container']:
			tx.append('SERVICE: %s'%x)
			s=l['service_container'][x]
			for ev in l['broker']['events']:
				for itn in l['broker']['events'][ev]['items']:
					it=l['broker']['events'][ev]['items'][itn]
					if (it['pid']==s['pid']):
						it['main_acknowleged']=True
						tx.append(" - %s"%ev)
		for ev in l['broker']['events']:
			for itn in l['broker']['events'][ev]['items']:
				it=l['broker']['events'][ev]['items'][itn]
				if not ('main_acknowleged' in it):
					tx.append('UNACKNOWLEGED SUBSCRIBER: %s'%it)

		l.info('\n'.join(tx))
		#for x in l['broker']['event']['items']:

		l.join()
	except Exception as e:
		print(format_exc())
		l.stop()
		IPCdict.connection.shutdown()


if __name__ == '__main__':
	#freeze_support()

	main()
