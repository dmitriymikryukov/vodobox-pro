from IPC import *
from .iface_ipc import ifaceIPC
import threading

class ifaceCOINipc(sgnService,ifaceIPC):
	
	def __init__(self):
		ifaceIPC.__init__(self)
		sgnService.__init__(self)

