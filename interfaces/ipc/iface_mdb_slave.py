from interfaces.iface import InterfaceCommon
import threading
from IPC import *

class ifaceMDBslave(InterfaceCommon):
	
	def __init__(self,addr=1):
		self.addr=addr
		self.rxEv=threading.Event()
		self.rxRes=None
		InterfaceCommon.__init__(self)
		self.process=threading.Thread(target=self.process,daemon=True)
		self.process.start()

	"""
	@subscribe
	def mdb_slave_receive(self,addr,data):
		print("MDB slave receive: %s %s"%(addr,data))
		if addr!=self.addr:
			self.error("MDB slave receive alien: %s %s"%(addr,data))
			self.rxRes=None
		else:
			self.rxRes=data
		self.rxEv.set()
	"""

	def cmd(self,data):
		self.rxEv.clear()
		x=self.mdb_command(self.addr,data)
		print('RES:%s'(x,))
		if (x is tuple) and len(x)>0:
			return x[0]
		"""
			self.critical('MDB service not answers')
			return False
		self.rxEv.wait(1.0)
		if not self.rxEv.is_set():
			return None
		else:
			return self.rxRes
		"""

	def process(self):
		raise NotImplementedError('Process is abstract')

	def reset(self):
		raise NotImplementedError('Reset is abstract')		

	def setup(self):
		raise NotImplementedError('setup is abstract')		