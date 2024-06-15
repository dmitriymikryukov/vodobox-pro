from IPC import *
from .iface_ipc import ifaceIPC
from interfaces.hardware.mdb import ifaceMDBonboard
import threading

class ifaceMDBipc(sgnService,ifaceMDBonboard,ifaceIPC):
	
	def __init__(self):
		self.mdbRL=threading.RLock()
		self.mdbEV=threading.Event()
		self.timeout=True
		self.ans=None
		ifaceMDBonboard.__init__(self)
		ifaceIPC.__init__(self)
		sgnService.__init__(self)

	@subscribe
	def mdb_command(self,addr,data):
		return self.mdb_command_handler(addr,data)
	"""
		return None
		if not self:
			print("PIZDA!")
		#print('%s'%(type(self)))
		#print('%s'%self.mdb_command_handler)
		try:
			m=self._doCall(callback_event)
		except Exception as e:
			self.exception('CALLBACK METHOD %s is not found'%callback_event)
		else:
			z=threading.Thread(target=self.mdb_command_handlerX,daemon=True,args=(addr,data,m))
			z.start()

	def mdb_command_handlerX(self,addr,data,m):
		with self.mdbRL:
			ans=self.mdb_command_handler(addr,data)
			m(ans[0],ans[1])
	"""

	def mdb_command_handler(self,addr,data):
		with self.mdbRL:
			self.mdbEV.clear()
			self.timeout=False
			self.mdb_send_command_bytes(addr,data)
			self.mdbEV.wait(1.0)
			if self.mdbEV.is_set():
				print("mdb_hdl0: %s,%s"%(addr,self.ans,))
				if self.ans[0]==addr:
					return (addr,self.ans[1])
				else:
					return (addr,None)
			else:
				print("mdb_hdl1: %s,%s"%(addr,self.ans,))
				self.timeout=True
				return (addr,None)

	"""
	@subscribe
	def mdb_receive(self,addr,ans):
		print("mdb_receive: %s,%s"%(addr,ans,))
		if not self.timeout:
			print("rx success")
			self.ans=(addr,ans)
			self.mdbEV.set()
	"""
