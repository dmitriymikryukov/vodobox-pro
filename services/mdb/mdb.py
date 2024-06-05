import sys,os
sys.path.insert(0, '../..')
from IPC import *

from interfaces.ipc.iface_mdb import ifaceMDBipc

import signal
l=None

def_handTERM=signal.getsignal(signal.SIGTERM)
def signal_thandler(num, stack):
	print("TERM STOP SIGNAL!")
	if l:
		l.exiting=True
	signal.signal(signal.SIGTERM, def_handTERM)
	sys.exit(1)
signal.signal(signal.SIGTERM, signal_thandler)

def_handINT=signal.getsignal(signal.SIGTERM)
def signal_ihandler(num, stack):
	print("INT STOP SIGNAL!")
	if l:
		l.exiting=True
	signal.signal(signal.SIGINT, def_handINT)
	sys.exit(1)
signal.signal(signal.SIGINT, signal_ihandler)

def classlookup(cls):
	c = list(cls.__bases__)
	for base in c:
		c.extend(classlookup(base))
	return c

class SgnMDB(ifaceMDBipc):
	def __init__(self):
		super().__init__()

try:
	l=SgnMDB()
	l.warning('SGN MDB STARTED')
	#l.warning('SgnMDB Base Classes: %s'%(SgnMDB.__bases__,))
	#l.warning('SgnMDB MRO: %s'%(type.mro(SgnMDB)))
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
