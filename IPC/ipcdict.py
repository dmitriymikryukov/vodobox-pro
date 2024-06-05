from multiprocessing.managers import BaseManager, DictProxy
from threading import Thread, Event
from multiprocessing import Queue
from traceback import format_exc

class IPCconnectionException(Exception):
	pass

_server_started_event = Event()
_server_shutdown_event = Event()
_server_server_thread = None
_server_event_thread = None

class sgnSharedQueue:
	def __init__(self):
		self._queue=Queue()

	def __call__(self):
		return self._queue

class IPCdictConnection(object):
	address = "127.0.0.1"
	port = 50000
	password = "secret"
	maxqueues = 16

	def __init__(self,is_server=False):
		self.is_server=is_server
		if is_server:
			self.the_dict = None
			self.res_dict = None
			self.callback = None
			print("WAITING SERVER TO BECOME READY")
			_server_server_thread=Thread(target=self.server)
			_server_server_thread.start()
			# wait for manager to start:			
			_server_started_event.wait()
			print("SERVER IS READY, CONNECTING")

		BaseManager.register('eventqueue')
		BaseManager.register('sharable_dict')
		BaseManager.register('res_dict')
		for i in range(self.maxqueues):
			BaseManager.register('callqueue%s'%i)			

		self.manager = BaseManager(address=(self.address, self.port), authkey=self.password.encode('utf-8'))
		self.manager.connect()
		self.dict=self.manager.sharable_dict()	
		self.resdict=self.manager.res_dict()	
		self.eventqueue=self.manager.eventqueue()
		s=IPCdict.separator
		sk='%s%ssvcs'%(s,s)
		if is_server:
			self.qidx=0
			self.dict[sk]=0
			self.ccqueue=[]
			for i in range(self.maxqueues):
				self.ccqueue.append(eval('self.manager.callqueue%s()'%i))
			self.callqueue=self.ccqueue[self.qidx]
			_server_event_thread=Thread(target=self.eventthread)
			_server_event_thread.start()
		else:
			self.dict[sk]+=1
			self.qidx=self.dict[sk]
			self.callqueue=eval('self.manager.callqueue%s()'%self.qidx)



	def shutdown(self):
		# tell manager we are through:
		try:
			_server_shutdown_event.set()
			print("Shutting down server...")
			_server_server_thread.join()
			print("Server is shutted down")
		except:
			pass

	def eventthread(self):
		print("Event Broker started")
		try:
			while not _server_shutdown_event.is_set():
				try:
					x=self.eventqueue.get()
				except:
					print("*** CONNECTION TO EVENT QUEUE LOST! SHUTTING DOWN! ***")
					_server_shutdown_event.set()
					break
				else:
					#print("RX EVENT: %s"%(x,))
					n=0
					try:
						s=IPCdict.separator
						eqk='%s%sbroker%sevents%s%s%sitems%s'%(s,s,s,s,x['name'],s,s)
						svcs=[]
						for k in self.dict.keys():
							if k.startswith(eqk):
								z=k[len(eqk):]
								if not (s in z):
									#pid=self.dict['%s%s%spid'%(eqk,z,s)]
									#sig=self.dict['%s%s%ssig'%(eqk,z,s)]
									#print("pid: %s sig: %s"%(pid,sig))
									svcs.append(z)
						#print("scvs:%s"%svcs)
						if self.callback:
							self.callback(svcs,x)
						else:
							print("NO REGISTERED CALLBACK")
					except:
						print(format_exc())
					try:
						self.resdict[x['caller_id']]=n
					except:
						_server_shutdown_event.set()
		except:
			print(format_exc())
			_server_shutdown_event.set()


	def server(self):
		print("*STARTING IPC SERVER*")
		self.net_manager = BaseManager(address=(self.address, self.port), authkey=self.password.encode('utf-8'))
		BaseManager.register('sharable_dict', self.srv_get_dict, DictProxy)
		BaseManager.register('res_dict', self.srv_get_resdict, DictProxy)
		self._ev_queue=sgnSharedQueue()
		BaseManager.register('eventqueue', self._ev_queue)
		for i in range(self.maxqueues):
			BaseManager.register('callqueue%s'%i, sgnSharedQueue())			
		self.net_manager.start()
		print("*STARTED IPC SERVER*")
		_server_started_event.set() # tell main thread that we have started
		print("*WAITING END OF IPC SERVER*")
		_server_shutdown_event.wait() # wait to be told to shutdown
		self.net_manager.shutdown()

	def srv_get_dict(self):
		if self.the_dict is None:
			self.the_dict = {}
		return self.the_dict

	def srv_get_resdict(self):
		if self.res_dict is None:
			self.res_dict = {}
		return self.res_dict

from collections.abc import MutableSequence

class IPClist(MutableSequence):

	def __new__(class_,*args,**kwargs):
		path=kwargs['path']
		if not (path in IPCdict.paths):
			IPCdict.paths[path]=super().__new__(class_)
		return IPCdict.paths[path]


	def __init__(self, initlist=None, path=None):
		try:
			self._path
		except:
			self._path=path
			super().__init__()
			self.data=[]
			#IPCdict.connection.dict[self._path]=self.data			
		if initlist is not None:
			data=[]
			if isinstance(initlist, list):
				data[:] = initlist

			elif isinstance(initlist, IPCList):
				data[:] = initlist.data[:]

			else:
				data = list(initlist)
			for i in range(len(data)):
				if i>=len(self):
					self.append(data[i])
				else:
					self[i]=data[i]
			while len(self)>len(data):
				del(self[-1])

	def __del__(self):
		del IPCdict.paths[self._path]

	def __enter__(self):
		pass

	def __exit__(self):
		pass


	def __repr__(self):
		self.data=IPCdict.connection.dict[self._path]
		return repr([x for x in self])

	def __lt__(self, other):		
		self.data=IPCdict.connection.dict[self._path]
		return self.data < self.__cast(other)

	def __le__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		return self.data <= self.__cast(other)

	def __eq__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		return self.data == self.__cast(other)

	def __gt__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		return self.data > self.__cast(other)

	def __ge__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		return self.data >= self.__cast(other)

	def __cast(self, other):
		return other.data if isinstance(other, MyList) else other

	def __contains__(self, value):
		self.data=IPCdict.connection.dict[self._path]
		return value in self.data

	def __len__(self):
		self.data=IPCdict.connection.dict[self._path]
		return len(self.data)

	def __getitem__(self, idx):
		idx=int(idx)
		self.data=IPCdict.connection.dict[self._path]
		try:
			v=self.data[idx]
		except IndexError:
			raise IndexError("Index %s is not found in %s"%(idx,self._path))
		if isinstance(v,dict):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			v=IPCdict(path=key)
		elif isinstance(v,list):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			v=IPClist(path=key)
		return v

	def __setitem__(self, idx, value):
		# optional: self._acl_check(val)
		idx=int(idx)
		self.data=IPCdict.connection.dict[self._path]
		if isinstance(value,dict):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			self.data[idx]={}
			IPCdict.connection.dict[self._path]=self.data
			IPCdict.connection.dict[key]={}
			v=IPCdict(path=key)
			for x in value:
				v[x]=value[x]
		elif isinstance(value,list):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			self.data[idx]=[]
			IPCdict.connection.dict[self._path]=self.data
			IPCdict.connection.dict[key]=[]
			v=IPClist(value,path=key)
		else:
			self.data[idx] = value
			IPCdict.connection.dict[self._path]=self.data

	def __delitem__(self, idx):
		"""
		idx=int(idx)
		v=self[idx]
		if isinstance(v,IPCdict):
			for x in v.keys():
				del v[x]
			del v
		elif isinstance(v,IPClist):
			while len(v):
				del v[-1]
			del v
		del self.data[idx]
		IPCdict.connection.dict[self._path]=self.data
		"""
		self.pop(idx)

	def __add__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		if isinstance(other, MyList):
			return self.__class__(self.data + other.data)

		elif isinstance(other, type(self.data)):
			return self.__class__(self.data + other)

		v=self.__class__(self.data + list(other))
		IPCdict.connection.dict[self._path]=self.data
		return v

	def __radd__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		if isinstance(other, MyList):
			v=self.__class__(other.data + self.data)

		elif isinstance(other, type(self.data)):
			v=self.__class__(other + self.data)

		v=self.__class__(list(other) + self.data)
		IPCdict.connection.dict[self._path]=self.data

	def __iadd__(self, other):
		self.data=IPCdict.connection.dict[self._path]
		if isinstance(other, MyList):
			self.data += other.data

		elif isinstance(other, type(self.data)):
			self.data += other

		else:
			self.data += list(other)

		IPCdict.connection.dict[self._path]=self.data
		return self

	def __mul__(self, nn):
		self.data=IPCdict.connection.dict[self._path]
		v=self.__class__(self.data * nn)
		IPCdict.connection.dict[self._path]=self.data
		return v

	__rmul__ = __mul__

	def __imul__(self, nn):
		self.data=IPCdict.connection.dict[self._path]
		self.data *= nn
		IPCdict.connection.dict[self._path]=self.data
		return self

	def __copy__(self):
		self.data=IPCdict.connection.dict[self._path]
		inst = self.__class__.__new__(self.__class__)
		inst.__dict__.update(self.__dict__)

		# Create a copy and avoid triggering descriptors
		inst.__dict__["data"] = self.__dict__["data"][:]
		IPCdict.connection.dict[self._path]=self.data

		return inst

	def append(self, value):
		try:
			self.data=IPCdict.connection.dict[self._path]
		except:
			self.data=[]
		l=len(self.data)
		self.data.append(None)
		IPCdict.connection.dict[self._path]=self.data
		self[l]=value

	def insert(self, idx, value):
		self.data=IPCdict.connection.dict[self._path]
		self.data.insert(idx, value)
		IPCdict.connection.dict[self._path]=self.data

	def pop(self, idx=-1):
		idx=int(idx)
		if idx<0:
			idx=len(self)+idx
		v=self[idx]
		if isinstance(v,IPCdict):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			res=v.toStdRecursive()
			for x in v.keys():
				del v[x]
			del v
			#del IPCdict.connection.dict[key]
		elif isinstance(v,IPClist):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			res=v.toStdRecursive()
			while len(v):
				del v[-1]
			del v
			#del IPCdict.connection.dict[key]
		else:
			res=v
		del self.data[idx]
		IPCdict.connection.dict[self._path]=self.data
		idx+=1
		while idx<(len(self)+1):
			key='%s%s%s'%(self._path,IPCdict.separator,idx)	
			for k in IPCdict.connection.dict.keys():
				if k.startswith(key):
					okey='%s%s%s%s'%(self._path,IPCdict.separator,idx-1,k[len(key):])
					IPCdict.connection.dict[okey]=IPCdict.connection.dict[k]
					del IPCdict.connection.dict[k]
			idx+=1

		return res

	def push(self,v):
		self.append(v)

	def remove(self, value):
		raise NotImplementedError('remove is not yet implemeted')
		self.data=IPCdict.connection.dict[self._path]
		self.data.remove(value)
		IPCdict.connection.dict[self._path]=self.data

	def clear(self):
		while len(self):
			del self[-1]

	def copy(self):
		#return self.__class__(self)
		return self.toStdRecursive()

	def count(self, value):
		self.data=IPCdict.connection.dict[self._path]
		return self.data.count(value)

	def index(self, idx, *args):
		raise NotImplementedError('index is not yet implemeted')
		self.data=IPCdict.connection.dict[self._path]
		return self.data.index(idx, *args)

	def reverse(self):
		raise NotImplementedError('reverse is not yet implemeted')
		self.data=IPCdict.connection.dict[self._path]
		self.data.reverse()
		IPCdict.connection.dict[self._path]=self.data

	def sort(self, /, *args, **kwds):
		raise NotImplementedError('sort is not yet implemeted')
		self.data=IPCdict.connection.dict[self._path]
		self.data.sort(*args, **kwds)
		IPCdict.connection.dict[self._path]=self.data

	def extend(self, other):
		raise NotImplementedError('extend is not yet implemeted')
		self.data=IPCdict.connection.dict[self._path]
		if isinstance(other, MyList):
			other.data=IPCdict.connection.dict[other.path]
			self.data.extend(other.data)
		else:
			self.data.extend(other)
		IPCdict.connection.dict[self._path]=self.data

	def toStdRecursive(self):
		res=[]
		for v in self:
			if isinstance(v,IPCdict) or isinstance(v,IPClist):
				res.append(v.toStdRecursive())
			else:
				res.append(v)
		return res



class IPCdict(dict):
	connection=None
	paths=dict()
	separator='/'

	def __new__(class_,*args,**kwargs):
		#print("IPCdict.new")
		if 'is_server' in kwargs:
			is_server=kwargs['is_server']
		else:
			is_server=False
		if 'path' in kwargs:
			path=kwargs['path']
		else:
			path=IPCdict.separator
		if IPCdict.connection is None:
			if is_server:
				print("THIS IS IPC SERVER")
			else:
				print("CONNECTING TO IPC SERVER")
			IPCdict.connection=IPCdictConnection(is_server=is_server)
		if not (path in IPCdict.paths):
			IPCdict.paths[path]=super().__new__(class_,*args,**kwargs)
		return IPCdict.paths[path]


	def __init__(self,*args,**kwargs):
		try:
			self._exists
		except:
			if 'is_server' in kwargs:
				self.is_server=kwargs['is_server']
				del kwargs['is_server']
			if 'path' in kwargs:
				self._path=kwargs['path']
				del kwargs['path']
			else:
				self._path=IPCdict.separator
			super().__init__(self,*args,**kwargs)

	def __del__(self):
		del IPCdict.paths[self._path]
		try:
			del IPCdict.connection.dict[self._path]
		except:
			pass
		if IPCdict.connection and IPCdict.connection.is_server and self._path==IPCdict.separator:
			IPCdict.connection.shutdown()
			IPCdict.connection=None

	def __enter__(self):
		pass

	def __exit__(self):
		pass

	def communication_error(self):
		self.exiting=True
		print("Connection Error")
		raise IPCconnectionException('Connecting to Server Error')


	def _dekey(self,key):
		if (key.startswith('i~')):
			return int(key[2:])
		else:
			return key

	def _cokey(self,key):
		if isinstance(key,int):
			key='i~%s'%key
		return '%s'%key

	def __setitem__(self, key, item):
		_key=key
		key=self._cokey(key)
		key='%s%s%s'%(self._path,IPCdict.separator,key)

		it={}
		ls=[]
		if isinstance(item,dict):
			it=item
			item={}
		elif isinstance(item,list):
			ls=item
			item=[]
		if key in IPCdict.connection.dict.keys():
			v=self[_key]
			if isinstance(v,IPCdict):
				for x in v.keys():
					del v[x]
				del v
			elif isinstance(v,IPClist):
				while len(v):
					del v[-1]
				del v
		try:
			IPCdict.connection.dict[key] = item
		except:
			self.communication_error()
		if len(it)>0:
			d=IPCdict(path=key)
			for v in it:
				d[v]=it[v]
		elif len(ls)>0:
			d=IPClist(ls,path=key)

	def __getitem__(self, key):
		key=self._cokey(key)
		key='%s%s%s'%(self._path,IPCdict.separator,key)
		try:
			haskey=key in IPCdict.connection.dict
		except:
			self.communication_error()
		else:
			if haskey:
				try:
					v=IPCdict.connection.dict[key]
					if isinstance(v,dict):
						v=IPCdict(path=key)
					elif isinstance(v,list):
						v=IPClist(path=key)
					return v
				except:
					self.communication_error()
			else:
				raise KeyError(key)

	def __delitem__(self, key):
		_key=key
		key=self._cokey(key)
		key='%s%s%s'%(self._path,IPCdict.separator,key)
		try:
			haskey=key in IPCdict.connection.dict
		except:
			self.communication_error()
		else:
			if haskey:
				try:
					v=self[_key]
					if isinstance(v,IPCdict):
						for x in v.keys():
							del v[x]
						del v
					elif isinstance(v,IPClist):
						while len(v):
							del v[-1]
						del v
					del IPCdict.connection.dict[key]
				except:
					self.communication_error()
			else:
				raise KeyError(key)

	def keys(self):
		res=[]
		pt="%s%s"%(self._path,IPCdict.separator)
		sl=len(pt)
		for x in IPCdict.connection.dict.keys():
			if x.startswith(pt):
				k=x[sl:]
				if not (IPCdict.separator in k):
					res.append(self._dekey(k))
		return res

	def values(self):
		ks=self.keys()
		res=[]
		for x in ks:
			res.append(self[x])
		return res

	def toDict(self):
		pt="%s%s"%(self._path,IPCdict.separator)
		ks=self.keys()
		res={}
		for x in ks:
			res[x]=self[x]
		return res

	def toStdRecursive(self):
		res={}
		for k in self.keys():
			v=self[k]
			if isinstance(v,IPCdict) or isinstance(v,IPClist):
				res[k]=v.toStdRecursive()
			else:
				res[k]=v
		return res


	def __eq__(self, other):
		return self.keys()==other.keys() and self.values()==other.values()

	def __contains__(self, key):
		key='%s%s%s'%(self._path,IPCdict.separator,key)
		try:
			return key in IPCdict.connection.dict
		except:
			self.communication_error()

	def __len__(self):
		return len(self.keys())

	def __iter__(self):
		return iter(self.keys())

	def __repr__(self):
		return '%s'%self.toDict()

