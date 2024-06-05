from . import sgnIPC,subscribe
import sys,os,time

class sgnService(sgnIPC):
	def __init__(self,is_server=False):
		self.container=False
		self.started=False
		self.service_base=os.path.dirname(os.path.abspath(sys.argv[0]))
		self.servicename=os.path.basename(self.service_base)
		self.alive_ts=time.time()
		print("sgnService.init")
		sgnIPC.__init__(self,is_server=is_server)
		self.init_container()
		if is_server:
			self.connection.callback=self.callevents

	def callevents(self,svcs,method):
		i=0
		try:
			for x in self['service_container']:
				if self['service_container'][x]['objId'] in svcs:
					#print("SVC CALL PUT: %s:%s"%(x,method))
					self.connection.ccqueue[i].put(method)
				i+=1
		except:
			try:
				self.connection.shutdown()
			except:
				pass

	def init_container(self):
		with self.lock:
			if not ('service_container' in self):
				self['service_container']=dict()
			if not (self.servicename in self['service_container']):
				self['service_container'][self.servicename]=dict()
			self.container=self['service_container'][self.servicename]
			self.container['name']=self.servicename
			self.container['basepath']=self.service_base
			self.container['main']=self._main
			self.container['pid']=os.getpid()
			self.container['status']="STARTING"
			self.container['objId']=self._objId


	@subscribe
	def stopService(self,name):
		if name==self.servicename:
			self.doExit()

	def doEnd(self):
		self.warning('STOPPING...')
		self.serviceFinished()

	def serviceStarted(self):
		print("SERVICE %s STARING..."%self.servicename)
		while not self.container and not self.exiting:
			time.sleep(0.1)
		print("SERVICE %s STARTED"%self.servicename)
		self.started=True
		self.container['status']="ALIVE"

	def serviceFinished(self):
		try:
			if not self.closed:
				self.warning('STOPPED!')
		except:
			pass
		try:
			self.container['status']="DEAD"
		except:
			pass


	def close(self):
		try:
			self.serviceFinished()
		except:
			pass
		super().close()

	def getName(self):
		return self.servicename

	@subscribe
	def alive_watchdog(self):
		pass

	@subscribe
	def exit(self):
		self.doExit()

	def doExit(self):
		print("*** EXIT FUNCTION CALLED ***")
		try:
			self.critical("*** EXIT FUNCTION CALLED ***")
		except:
			pass			
		self.exiting=True
		sys.exit()

	def will_call(self,f):
		if not self.started:
			self.serviceStarted()
		if f:
			self.alive_ts=time.time()
			self.container['alive_ts']=self.alive_ts
		elif (time.time()-self.alive_ts)>5.0:
			self.alive_ts=time.time()
			try:
				self.alive_watchdog()
			except Exception as e:
				self.exception(e)
				time.sleep(1.0)
				raise e
