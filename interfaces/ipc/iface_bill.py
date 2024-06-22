from IPC import *
from .iface_ipc import ifaceIPC
import threading

class ifaceBILLipc(sgnService,ifaceIPC):
	
	def __init__(self):
		sgnService.__init__(self)
		ifaceIPC.__init__(self)

