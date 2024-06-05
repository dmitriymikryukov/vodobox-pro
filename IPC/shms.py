from multiprocessing import shared_memory,resource_tracker
import collections, os, pickle, sys, time
import weakref
import fcntl

import hashlib,traceback

try:
	from .Exceptions import *
except:
	from Exceptions import *

import threading

resources={}

def _defile(name):
	s='sgn'+hashlib.md5(name.encode()).hexdigest()
	return s[:30]

def remove_shm_from_resource_tracker():
	"""Monkey-patch multiprocessing.resource_tracker so SharedMemory won't be tracked

	More details at: https://bugs.python.org/issue38119
	"""

	def fix_register(name, rtype):
		if rtype == "shared_memory":
			return
		return resource_tracker._resource_tracker.register(self, name, rtype)
	resource_tracker.register = fix_register

	def fix_unregister(name, rtype):
		if rtype == "shared_memory":
			return
		return resource_tracker._resource_tracker.unregister(self, name, rtype)
	resource_tracker.unregister = fix_unregister

	if "shared_memory" in resource_tracker._CLEANUP_FUNCS:
		del resource_tracker._CLEANUP_FUNCS["shared_memory"]

class Locker:
	def __init__(self,name,create=False):
		self.name='/tmp/'+name
		#print("opening lock: %s"%self.name)
		#print ("CALL STACK:")
		#for line in traceback.format_stack():
		#	print(line.strip())
		if not (self.name in resources):
			resources[self.name]=self
		elif resources[self.name].closed:
			resources[self.name]=self
			create=True
		else:
			raise AlreadyExists('Lock %s alreary open in this context'%self.name)
		if create:
			try:
				os.unlink(self.name)
			except:
				pass
		try:
			self.fp = open(self.name)
		except:
			self.fp = open(self.name,'wb')			
		self.lockedby=False
		self.lockcnt=0
		self.closed=False
		weakref.finalize(self,self._cleanup,self.fp)

	def close(self):
		self.closed=True
		try:
			del resources[self.name]
		except:
			pass
		try:
			self.fp.close()
		except:
			pass

	def unlink(self):
		try:
			self.close()
		except:
			pass
		try:
			os.unlink(self.name)
		except:
			pass

	def __enter__ (self):
		#print("%s Enter: %s %s"%(os.getpid(),self.name,self.lockcnt))
		if self.closed:
			return
		if self.lockedby==os.getpid():
			self.lockcnt+=1
		else:    	
			fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX)
			self.lockedby=os.getpid()
			self.lockcnt+=1

	def __exit__ (self, _type, value, tb):
		if self.closed:
			return
		self.lockcnt-=1
		if self.lockcnt<=0:
			self.lockedby=False
			fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
		#print("Exit: %s %s"%(self.name,self.lockcnt))

	@staticmethod
	def _cleanup(fp):
		fp.close()

class shmkeys(shared_memory.SharedMemory):	

	def __init__(self,name,init=False,*args,**kwargs):
		self.keysize=32
		self.numkeys=1000

		self.autounreg=False
		self.xclosed=False

		self.keyRL=threading.RLock()

		n=_defile(name)

		#print('Opening keys %s:%s'%(name,_defile(name)))
		if not (n in resources):
			resources[n]=self
		else:
			raise AlreadyExists('Keys %s alreary open in this context'%name)

		nopen=False
		ee=False
		try:
			if init:
				super().__init__(name=n,create=True,size=(self.keysize+5)*self.numkeys)
			else:
				super().__init__(name=n)				
		except Exception as e:
			#print(e)
			try:
				super().__init__(name=n,create=True,size=(self.keysize+5)*self.numkeys)
			except Exception as e:
				ee=e
				nopen=True
		if nopen:
			raise CannotAttachSharedMemory('%s %s:%s'%(ee,name,_defile(name)))

		self._lmod=dict()
		if init:
			self.init()
		else:
			for i in range(self.numkeys):
				n=self.keyAtIndex(i)
				if not (n is None):
					self._lmod[n]=-1

	def unregister(self):
		try:
			#print('unreg')
			resource_tracker.unregister(self._name, 'shared_memory')		
		except:
			pass

	def close(self):
		if not self.xclosed:
			self.xclosed=True
			#print('CLOSE KEYS: %s'%self.name)
			if self.name in resources:
				del resources[self.name]
			else:
				print('SHM is not in resources: %s/%s'%(self.name,self._name))
			super().close()
			if self.autounreg:
				self.unregister()


	def init(self):
		for i in range((self.keysize+5)*self.numkeys):
			self.buf[i]=0
			self._lmod=dict()


	def _getPos(self,n):
		return (self.keysize+5)*n

	def keyAtIndex(self,i):
		with self.keyRL:
			kp=self._getPos(i)
			sl=self.buf[kp]
			if sl<1:
				return None
			return bytes(self.buf[kp+5:kp+5+sl])
		
	def indexOfKey(self,name):
		with self.keyRL:
			nn=name.encode()
			sl=len(nn)
			for i in range(self.numkeys):
				kp=self._getPos(i)
				if (self.buf[kp]==sl):
					kn=self.keyAtIndex(i)
					if (kn==nn):
						return i
			return False

	def changeKey(self,name):
		#print("CHANGE KEY:%s"%name)
		with self.keyRL:
			i=self.indexOfKey(name)
			if i is False:
				self.addKey(name)
			else:
				kp=self._getPos(i)
				a=int.from_bytes(self.buf[kp+1:kp+5], "little")
				a+=1
				self.buf[kp+1:kp+5]=a.to_bytes(4,'little')
				self._lmod[name]=a

	def addKey(self,name):
		with self.keyRL:
			if not (name in self._lmod):
				i=self.indexOfKey(name)
				if i is False:
					nn=name.encode()
					sl=len(nn)
					for i in range(self.numkeys):
						kp=self._getPos(i)
						if self.buf[kp]==0:
							self.buf[kp+5:kp+5+sl]=nn
							a=0
							self._lmod[name]=a
							self.buf[kp+1:kp+5]=a.to_bytes(4,'little')
							self.buf[kp]=sl
							break
				else:
					self._lmod[name]=-1

	def items(self):
		with self.keyRL:
			x=[]
			for i in range(self.numkeys):
				kp=self._getPos(i)
				if self.buf[kp]!=0:
					a=int.from_bytes(self.buf[kp+1:kp+5], "little")
					kn=self.keyAtIndex(i)
					x.append(kn.decode())
			return x

	def dump_keys(self):
		with self.keyRL:
			for i in range(self.numkeys):
				kp=self._getPos(i)
				if self.buf[kp]!=0:
					a=int.from_bytes(self.buf[kp+1:kp+5], "little")
					kn=self.keyAtIndex(i)
					print('[%d]%s=%s'%(i, kn,a))


	def isChangedRemote(self,name):
		with self.keyRL:
			i=self.indexOfKey(name)
			if not (name in self._lmod) or i is False:
				return False
			kp=self._getPos(i)
			a=int.from_bytes(self.buf[kp+1:kp+5], "little")
			#print("CHANGED REMOTE:%s"%(a!=self._lmod[name]))
			return a!=self._lmod[name]

	def isAddedRemote(self,name):
		with self.keyRL:
			i=self.indexOfKey(name)
			return not (i is False) and not (name in self._lmod)

	def isDeletedRemote(self,name):
		with self.keyRL:
			i=self.indexOfKey(name)
			return (i is False) and (name in self._lmod)

	def delKey(self,name):
		with self.keyRL:
			try:
				del self._lmod[name]
			except:
				pass

	def acknowlege(self,name):
		with self.keyRL:
			#print("ACK KEY:%s"%name)
			i=self.indexOfKey(name)
			if not (name in self._lmod) or i is False:
				return False
			kp=self._getPos(i)
			self._lmod[name]=int.from_bytes(self.buf[kp+1:kp+5], "little")

	def __contains__(self, item):
		return item in self.items()

class shmvalue(shared_memory.SharedMemory):
	def __init__(self,name,size=10000,init=False):
		self.autounreg=False
		nopen=False
		ee=False
		n=_defile(name)
		self.xclosed=False
		#print('Opening value %s:%s'%(name,_defile(name)))
		if not (n in resources):
			resources[n]=self
		else:
			raise AlreadyExists('Value %s alreary open in this context'%name)
		try:
			if init:
				super().__init__(name=n,create=True,size=size)
			else:
				super().__init__(name=n)
		except:
			try:
				super().__init__(name=n,create=True,size=size)
			except Exception as e:
				ee=e
				nopen=True
		if nopen:
			raise CannotAttachSharedMemory('%s %s:%s'%(ee,name,_defile(name)))
		if init:
			for i in range(size):
				self.buf[i]=0

	def unregister(self):
		try:
			#print('unreg')
			resource_tracker.unregister(self._name, 'shared_memory')		
		except:
			pass

	def close(self):
		if not self.xclosed:
			self.xclosed=True
			#print('CLOSE VAL: %s'%self.name)
			if self.name in resources:
				del resources[self.name]
			else:
				print('SHM is not in resources: %s/%s'%(self.name,self._name))
			super().close()
			if self.autounreg:
				self.unregister()

	def get(self):
		a=int.from_bytes(self.buf[0:4], "little")
		if a<1:
			return None
		return pickle.loads(self.buf[4:4+a])

	def set(self,value):
		x=pickle.dumps(value)
		l=len(x)
		self.buf[0:4]=l.to_bytes(4,'little')
		self.buf[4:4+l]=x


class sgnQueue(object):
	def __init__(self,name,init=False):
		super().__init__()
		self.name=name
		self.autounreg=False
		#print ('create queue: %s'%self.name)
		self.lock = Locker(name=name+'$$lock-queue');
		with self.lock:
			self._values=shmvalue(name=name+'$$queue',init=init)
			if init or not self._values.get():
				self._values.set([])
		#weakref.finalize(self,self._cleanup,[self._values])

	def __repr__(self):
		with self.lock:
			return 'sgnQueue[%s]=%s'%(self.name,repr(self._values.get()))

	def __len__(self):
		with self.lock:			
			v=self._values.get()
			return len(v)


	def timeofitem(self):
		try:
			with self.lock:
				v=self._values.get()
			return v[0]
		except:
			return False

	def unregister(self):
		self._values.unregister()
		self.lock.close()

	def close(self):
		with self.lock:
			self._values.close()
		if self.autounreg:
			self.unregister()

	def unlink(self):
		#with self.lock:
		self._values.unlink()
		self.lock.close()
		self.lock.unlink()
			

	def push(self,value):
		if isinstance(value,sgnDict):
			value=value.toDict()
		with self.lock:			
			v=self._values.get()
			v.append((time.time(),value))
			self._values.set(v)

	def pop(self):
		with self.lock:
			v=self._values.get()
			r=v.pop(0)
			self._values.set(v)
		if isinstance(r,sgnDict):
			r=r.toDict()		
		return r[1]

	def toList(self):
		with self.lock:
			d=[]
			v=self._values.get()
			for x in v:
				if isinstance(x,sgnDict):
					d.append(x.toDict())
				else:
					d.append(x)
		return d


	@staticmethod
	def _cleanup(fp):
		for x in fp:
			try:
				x.close()
				x.unlink()
			except:
				pass



class sgnDict(collections.UserDict, dict):
	def __init__(self, *args, name=None, create=None, buffer_size=10_000, serializer=pickle, shared_lock=None, full_dump_size=None,
				auto_unlink=None, recurse=None, recurse_register=None, **kwargs):
		self.name=name
		#print ('create dict: %s'%self.name)
		self.lock = Locker(name=name+'$$lock-dict');
		self.closed=False
		self.autounreg=False
		with self.lock:
			self._vals=dict()
			self._keys=shmkeys(name+'$$keys')
			self._items=dict()
			self._sync_keys(init=create)
			if create:
				self._keys.init()
			self.data=self._items

	def __repr__(self):
		return 'sgnDict='+repr(self._items)


	def close(self):
		#print("CLOSE")
		if not self.closed:
			self.closed=True
			#print("CLOSING %s"%self.name)
			with self.lock:
				for n in self._vals:
					self._vals[n].autounreg=self.autounreg
					self._vals[n].close()
				self._keys.autounreg=self.autounreg
				self._keys.close()
				for x in self._items:
					try:
						self._items[x].autounreg=self.autounreg
						self._items[x].close()
					except:
						pass
			if self.autounreg:
				self.lock.close()

	def unregister(self):
		self.closed=True
		#print("UNREGING %s"%self.name)
		for n in self._vals:
			self._vals[n].unregister()
		self._keys.unregister()
		for x in self._items:
			try:
				self._items[x].unregister()
			except:
				pass
		self.lock.close()

	def unlink(self):
		#with self.lock:
		for n in self._vals:
			try:
				self._vals[n].unlink()
			except:
				pass
		try:
			self._keys.unlink()
		except:
			pass
		for x in self._items:
			try:
				self._items[x].unlink()
			except:
				pass
		self.lock.close()
		self.lock.unlink()


	def _sync_keys(self,init=False):
		for i in range(self._keys.numkeys):
			kn=self._keys.keyAtIndex(i)
			if not (kn is None):
				knd=kn.decode()
				#print("sync key: '%s'"%knd)
				if not (knd in self._vals):
					m=shmvalue(self.name+'$'+knd,init=init)
					if init:
						try:
							m.close()
						except:
							pass
						try:
							m.unlink()
						except:
							pass
						self._keys.delKey(knd)
						#print("key deleted")
					else:
						mv=m.get()
						if (isinstance(mv,str)) and (mv.startswith('SHM:') or mv.startswith('SHQ:')):
							kn=mv[4:]
							#print("adding %s as %s"%(mv,knd))
							self._items[knd]=sgnDict(name=kn) if mv.startswith('SHM:') else sgnQueue(name=kn)
						else:
							self._items[knd]=m.get()
							#print("adding %s"%knd)
						self._vals[knd]=m
						self._keys.addKey(knd)
				else:
					if self._keys.isChangedRemote(knd):						
						#print('sync:CHANGED REMOTE')					
						xk=self._vals[knd].get()
						if (isinstance(xk,str)) and (xk.startswith('SHM:') or xk.startswith('SHQ:')):
							pass
						else:
							self._items[knd]=self._vals[knd].get()
						self._keys.acknowlege(knd)
		#print (self._keys.items())
		#print (self._items.keys())

	def __getitem__(self, key):
		#print("get item: '%s'"%key)
		if not isinstance(key,str):
			print('key name should be string, %s instead in sgnDict %s'%(key,self.name))
			raise ValueError('key name should be string, %s instead in sgnDict %s'%(key,self.name))
		with self.lock:
			if self._keys.isChangedRemote(key):	
				#print('CHANGED REMOTE %s'%key)					
				v=self._vals[key].get()
				if (isinstance(v,str)) and (v.startswith('SHM:') or v.startswith('SHQ:')):
					kn=v[4:]
					if not (key in self._items):
						self._items[key]=sgnDict(name=kn) if v.startswith('SHM:') else sgnQueue(name=kn)
					else:
						#print("exisitng %s==%s?"%(self._items[key].name,kn))
						if isinstance(self._items[key],sgnDict) and self._items[key].name!=kn:
							#print("name mismatch")
							try:
								self._items[key].close()
							except:
								pass
							try:
								self._items[key].unlink()
							except:
								pass
							self._items[key]=sgnDict(name=kn)
						elif isinstance(self._items[key],sgnQueue) and self._items[key].name!=kn:
							#print("name mismatch")
							try:
								self._items[key].close()
							except:
								pass
							try:
								self._items[key].unlink()
							except:
								pass
							self._items[key]=sgnQueue(name=kn)
				else:
					self._items[key]=v
				self._keys.acknowlege(key)
			elif self._keys.isAddedRemote(key):
				#print("ADDED REMOTE:%s"%key)
				self._keys.addKey(key)
				m=shmvalue(self.name+'$'+key)
				mv=m.get()
				if (isinstance(mv,str)) and (mv.startswith('SHM:') or mv.startswith('SHQ:')):
					kn=mv[4:]
					self._items[key]=sgnDict(name=kn) if mv.startswith('SHM:') else sgnQueue(name=kn)
				else:
					self._items[key]=m.get()
				self._vals[key]=m
			elif self._keys.isDeletedRemote(key):
				self._keys.delKey(key)
				try:
					self._items[key].close()
				except:
					pass
				try:
					self._items[key].unlink()
				except:
					pass
				try:
					del self._items[key]
				except:
					pass
				try:
					self._vals[key].close()
				except:
					pass
				try:
					self._vals[key].unlink()
				except:
					pass
				try:
					del self._vals[key]
				except:
					pass

		#print ("get result:%s"%type(self._items[key]))
		return self._items[key]

	def __setitem__(self, key, value):
		if not isinstance(key,str):
			print('key name should be string, %s instead in sgnDict %s'%(key,self.name))
			raise ValueError('key name should be string, %s instead in sgnDict %s'%(key,self.name))
		#print("SET ITEM: %s value:%s"%(key,value))
		val=value
		if isinstance(value,sgnQueue):
			val=value
			value='SHQ:'+val.name
		elif isinstance(value,dict):
			if not isinstance(value,sgnDict):
				val=sgnDict(name=self.name+'.'+key)
				for x in value:
					val[x]=value[x]
				value=val
			value='SHM:'+value.name
		with self.lock:
			if not (key in self._vals):
				self._vals[key]=shmvalue(self.name+'$'+key)
			self._vals[key].set(value)
			self._items[key]=val
			self._keys.changeKey(key)			

	def __delitem__(self, key):
		if not isinstance(key,str):
			print('key name should be string, %s instead in sgnDict %s'%(key,self.name))
			raise ValueError('key name should be string, %s instead in sgnDict %s'%(key,self.name))
		self._keys.delKey(key)
		try:
			self._items[key].close()
		except:
			pass
		try:
			self._items[key].unlink()
		except:
			pass
		try:
			del self._items[key]
		except:
			pass
		try:
			self._vals[key].close()
		except:
			pass
		try:
			self._vals[key].unlink()
		except:
			pass
		try:
			del self._vals[key]
		except:
			pass

	def __contains__(self, item):		
		#print("CONTAINS: %s=%s"%(item,item in self._keys.items()))
		return item in self._keys.items()

	def has_key(self, k):
		#print ("HAS KEY")
		return item in self._keys.items()

	def toDict(self):
		d=dict()
		for x in self:
			if isinstance(self[x],sgnDict):
				d[x]=self[x].toDict()
			elif isinstance(self[x],sgnQueue):
				d[x]=self[x].toList()
			else:
				d[x]=self[x]
		return d

	def __iter__(self):
		#print("ITER: %s"%self._keys.items())
		return iter(self._keys.items())

	def keys(self):
		return self._keys.items()

	def itervalues(self):
		return (self[key] for key in self)

def cleanup_resources():
	print ("CLEANUP RESOURCES!")
	#print(resources)
	while len(resources)>0:
		try:
			for rn in resources:
				break
			try:
				resources[rn].close()
			except:
				pass
			try:
				del resources[rn]
			except:
				pass
		except:
			pass

"""
try:
	s=shmkeys('qwe',init=True)
	s.dump_keys()

	s.addKey('aaaa')
	print("isc %s"%s.isChangedRemote('aaaa'))

	s.changeKey('aaaa')

	s.dump_keys()

	print("isc %s"%s.isChangedRemote('aaaa'))

	print(s.indexOfKey('aaaa'))
	s.changeKey('bbbb')
	s.changeKey('aaaa')
	s.changeKey('aaaa')
	s.dump_keys()
	print(s.indexOfKey('aaaa'))
	print(s.indexOfKey('bbbb'))

	v=shmvalue('vvvqwe',init=True)
	v.set({'a':1,'b':2,'c':[1,2,'a'],'d':'hello'})
	print(v.get())

	q=sgnQueue('pizda')
	q.push(('hello',123))
	q.push('quwery')

	d=sgnDict(name='xyu')
	d['test']='hello'
	d['test2']={'a':1,'b':2,'c':[1,2,'a'],'d':'hello'}
	d['xyu']=q

	print(d['test'])
	print(d['test2'])

	print(d['xyu'].pop())
	print(d['xyu'].pop())

	os.system('ls /dev/shm')

finally:
	s.close()
	s.unlink()

	v.close()
	v.unlink()

	d.close()
	d.unlink()
"""
