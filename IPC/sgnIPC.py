from . import sgnDict,sgnQueue#,remove_shm_from_resource_tracker
import hashlib
import os,sys
import threading
import signal

import traceback 

import sys,os,time

ipcsRL=threading.RLock()
ipcs=dict()

from traceback import format_exc

from .Exceptions import *

from queue import Empty

def signal_handler(num, stack):
	print("SIGNAL! %s"%([ipcs[ipcn].getName() for ipcn in ipcs],))
	try:
		while True:
			b=False
			bt=False
			bi=False
			with ipcsRL:
				for ipcn in ipcs:				
					ipc=ipcs[ipcn]
					print("IPC: %s %s"%(ipc._objId,ipc.getName()))
					for x in ipc['broker']['queues']:
						if x==ipcn:						
							q=ipc['broker']['queues'][x]
							b=q
							bi=ipc
							#zt=time.time()#q.timeofitem()
							#if zt and (not b or zt<bt):
							#	b=q
							#	bt=zt
							#	bi=ipc
			print (b)
			if not b:
				break
			with ipc.lock:
				try:
					x=b.pop()
				except:
					print (traceback.format_exc())
					x=False
					break
			print('evvvv:%s'%(x,))
			if x:
				with ipcsRL:
					with bi._callRL:
						bi._callQueue.append(x)
						bi._callEv.set()
	except:
		print (traceback.format_exc())
	print (ipc)
	return 0


subscribers=dict()

class subscribe:
	def __init__(self, fn):
		self.fn = fn

	def __set_name__(self, owner, name):
		#print("Subscribe to %s.%s"%(owner.__name__,name))
		#owner._event_methods.append(self.fn)
		n=owner.__name__
		if not (n in subscribers):
			subscribers[n]=dict()
		m=sys.modules[owner.__module__].__file__
		if not (m in subscribers[n]):
			subscribers[n][m]=dict()
		subscribers[n][m][name]=self.fn

		#owner._event_methods[name]=self.fn
		self.fn.class_name = owner.__name__
		# then replace ourself with the original method
		setattr(owner, 'event_'+name, self.fn)
		delattr(owner, name)

def extract_subscribers(cls):
	res=dict()
	mro=[x.__name__ for x in type.mro(cls.__class__)]
	for s in subscribers:
		if s in mro:
			for f in subscribers[s]:
				for m in subscribers[s][f]:
					res[m]=subscribers[s][f][m]
	return res

_sgn_scal_idx=0

class sgnCall():
	def __init__(self,ipc,name):
		self.name=name
		self.ipc=ipc

	def __call__(self,*args, **kwargs):
		global _sgn_scal_idx
		with self.ipc.lock:
			x='%s:%s'%(self.ipc._objId,_sgn_scal_idx)
			_sgn_scal_idx+=1
		self.ipc.connection.eventqueue.put(dict(caller_id=x,name=self.name,args=args,kwargs=kwargs))
		r=0
		while not (x in self.ipc.connection.resdict):
			time.sleep(0.001)
		r=self.ipc.connection.resdict[x]
		del self.ipc.connection.resdict[x]
		return r
		"""
		pids=dict()
		wks=0
		try:
			#print("\n*****CALL: %s"%self.name)
			for oid in self.ipc['broker']['events'][self.name]['items']:
				#print("loop oid: %s"%oid)
				with self.ipc.lock:
					q=self.ipc['broker']['queues']
					#print ("%s in q:%s"%(oid,oid in q))
					clo=q[oid]
					#print(clo)
					if True:#clo:					
						clo.push(dict(ev=self.name,args=args,kwargs=kwargs))
						c=self.ipc['broker']['events'][self.name]['items'][oid]
						try:
							pids[c['pid']]=c['sig']
						except Exception as e:
							print(format_exc(e))
						wks+=1
					else:
						#print (q)
						#print('CURRENT QUEUES: %s'%self.ipc['broker']['queues'])
						#print("NULL!!!")
						raise AlreadyClosed('Queue "%s" is Null'%oid)
			#print("END CALL: %s"%self.name)
			ee=False
			suc=False
			for x in pids:
				try:
					os.kill(x,pids[x])
				except Exception as e:
					ee=e
				else:
					suc=True
			#if (ee and not suc):
			#	raise AlreadyClosed('Call "%s" on disconnected subscribers'%self.name)
		except:
			if not self.ipc.closed:
				raise
		return wks
		"""


class sgnIPC(sgnDict):
	#remove_shm_from_resource_tracker()

	RL=threading.RLock()
	_event_methods={}
	_calls={}
	_t=None
	def_signal=signal.SIGUSR1

	"""
	_instances = dict()

	def __new__(class_, *args, **kwargs):
		ln=kwargs['link_name'] if 'link_name' in kwargs else 'sgnipc'
		if not (ln in class_._instances) or not class_._instances[ln]:
			#print("NOT EXISTING")
			class_._instances[ln] = sgnDict.__new__(class_, *args, **kwargs)
		#else:
		#	print("EXISTING")
		return class_._instances[ln]
	"""

	def __init__(self,link_name='sgnipc',init=False,is_server=False):
		#print("sgnIPC.init:%s"%link_name)
		"""
		try:
			self._main
		except:
			pass
		else:
			#print("sgnIPC.init-duplicate")
			return
		"""

		print ("IS_SERVER:%s"%is_server)

		self.lock=threading.RLock()

		self._link_name=link_name
		#super().__init__(name=link_name,init=init,is_server=is_server)
		sgnDict.__init__(self,is_server=is_server)
		print("sgnIPC.init-after parent init")

		with self.lock:
			if init or not ('broker' in self):
				self['broker']={}#sgnDict(name=self._path+'-broker',init=True)
			#print("sgnIPC.init-after broker init")
			if init or not ('events' in self['broker']):
				self['broker']['events']={}#sgnDict(name=self._path+'-broker-events',init=True)
			#print("sgnIPC.init-after broker.events init")
			#if init or not ('queues' in self['broker']):
			#	self['broker']['queues']={}#sgnDict(name=self.name+'-broker-queues',init=True)
			#print("sgnIPC.init-after broker.queues init")
		self._main=sys.argv[0]
		self._callRL=threading.RLock()
		self._callQueue=[]
		self._callEv=threading.Event()
		self._main=sys.argv[0]
		self.autoclose=0
		self.exiting=False
		self._event_methods=extract_subscribers(self)
		self._doSubscribe()
		self._t=threading.Thread(target=self._run_broker,daemon=True)
		self._t.start()
		with ipcsRL:
			ipcs[self._objId]=self
		signal.signal(signal.SIGUSR1, signal_handler)


	def join(self):
		self._t.join()

	def close(self):
		try:
			sgnIPC._instances[self._link_name]=False
		except:
			pass
		super().close()


	def __getattr__ (self, name):
		with self.lock:
			if name in self['broker']['events']:
				return self._doCall(name)
			#return self.__dict__[name]

	#def __setattr__ (self, name, value):
	#	self.__dict__[name] = value	

	def getName(self):
		return self._main

	def _doSubscribe(self):
		with self.RL:
			with self.lock:
				fname=os.path.abspath(sys.modules[type(self).__module__].__file__)
				self._objId=hashlib.md5(('%s%s%s'%(fname,self.__class__,os.path.dirname(os.path.abspath(sys.argv[0])))).encode()).hexdigest()
				#print("Real Subcribing for OBJ ID: %s"%self._objId)
				for ev in self._event_methods:
					#print ("Real subscribe to: %s"%ev)
					if not (ev in self['broker']['events']):
						#print("NEW BR EVS")
						self['broker']['events'][ev]=dict()					
					if not ('items' in self['broker']['events'][ev]):
						#print("NEW BR EV %s"%ev)
						self['broker']['events'][ev]['items']=dict()
					if not (self._objId in self['broker']['events'][ev]['items']):
						#print("NEW BR EV %s items"%ev)
						self['broker']['events'][ev]['items'][self._objId]=dict()
					a=self['broker']['events'][ev]['items'][self._objId]
					a['pid']=os.getpid()
					a['sig']=self.def_signal
					#if not (self._objId in self['broker']['queues']):
					#	n='sgn%s-callq'%(self._objId)
					#	self['broker']['queues'][self._objId]=[]#sgnQueue(name=n)

	def _doCall(self,name):
		with self.lock:
			if not (name in self._calls):
				self._calls[name]=sgnCall(self,name)
			return self._calls[name]

	def has_subscribers(self,name):
		if self.exiting:
			return False
		try:
			with self.lock:
				return name in self['broker']['events']
		except:
			return False

	def suca_form(self,t,txt):
		ta=[]
		mn='[%s]'%os.path.basename(self.getName())+'                '
		mn=mn[:16]
		t=t+':               '
		t=t[:10]
		for x in txt.split('\n'):
			if len(x):
				ta.append('%s %s %s'%(mn,t,x))
		return '\n'.join(ta)

	def exception(self,e):
		try:
			if isinstance(e, Exception):
				txt=''.join(traceback.format_exception(e,sys.exc_info()[1],sys.exc_info()[2])) 
			else:
				txt=e+'\n'
				txt+=traceback.format_exc()
			if self.has_subscribers('exception_handler'):
				self.exception_handler(self.getName(),txt)
			else:
				print(self.suca_form('EXCEPTION',"EXEPTION HANDLER has no subscribers:"))
				print(self.suca_form('EXCEPTION',txt))
				print("")
		except:
			print(self.suca_form('EXCEPTION',traceback.format_exc()))
			print("")

	def failure(self,e):
		self.exception(e)

	def debug(self,txt):
		try:
			if self.has_subscribers('debug_handler'):
				self.debug_handler(self.getName(),txt)
		except:
			self.exception("DEBUG EXEPTION")

	def info(self,txt):
		try:
			if self.has_subscribers('info_handler'):
				self.info_handler(self.getName(),txt)
			else:
				print(self.suca_form('INFO',"INFO HANDLER has no subscribers:"))
				print(self.suca_form('INFO',txt))
		except:
			self.exception("INFO EXEPTION")

	def warning(self,txt):
		try:
			if self.has_subscribers('warning_handler'):
				self.warning_handler(self.getName(),txt)
			else:
				print(self.suca_form('WARNING',"WARNING HANDLER has no subscribers:"))
				print(self.suca_form('WARNING',txt))
		except:
			self.exception("WARNING EXEPTION")

	def warn(self,txt):
		self.warning(txt)

	def error(self,txt):
		try:
			if self.has_subscribers('error_handler'):
				self.error_handler(self.getName(),txt)
			else:
				print(self.suca_form('ERROR',"ERROR HANDLER has no subscribers:"))
				print(self.suca_form('ERROR',txt))
		except:
			self.exception("ERROR EXEPTION")

	def critical(self,txt):
		try:
			if self.has_subscribers('critical_handler'):
				self.critical_handler(self.getName(),txt)
			else:
				print(self.suca_form('CRITICAL',"CRITICAL HANDLER has no subscribers:"))
				print(self.suca_form('CRITICAL',txt))
		except:
			self.exception("CRITICAL EXEPTION")


	def __enter__(self):
		self.autoclose+=1
		self.autounreg=True

	def __exit__(self,type, value, traceback):
		print("EXIT IPC")
		self.autoclose-=1
		if self.autoclose<=0:
			self.close()


	def will_call(self,f):
		pass

	def doBegin(self):
		pass

	def doEnd(self):
		pass

	def _run_broker(self):
		self.doBegin()
		try:
			while not self.closed and not self.exiting:
				try:
					x=self.connection.callqueue.get(timeout=0.5)
				except Empty:
					x=None
				if x is None:					
					f=False
					self.will_call(None)
				else:
					f=dict(ev=x['name'],args=x['args'],kwargs=x['kwargs'])
					#print("Exec: %s(%s,%s)"%(f['ev'],f['args'],f['kwargs']))
					self.will_call(f)
				if f:
					try:
						#print ("%s CALL:%s"%(self.getName(),f))
						ccc=self._event_methods[f['ev']]
						#print(ccc)
						ccc(self,*f['args'],**f['kwargs'])
					except Exception as e:
						try:
							self.error('CALL_METHOD FAILED:"%s"'%f)
							self.error('METHOD:"%s"'%ccc)
						except:
							pass
						try:
							self.exception(e)
						except:
							print(self.suca_form('EXCEPTION',traceback.format_exc()))
					#self.connection.callqueue.task_done()
		finally:
			self.doEnd()


