import sys,os,time
sys.path.insert(0, '../..')

from IPC import *

#import signal
l=None
"""
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
"""

class SgnHwDriver(sgnService):
	def __init__(self):
		super().__init__()

	def doExit(self):
		print("Exiting HWDRIVER,exit")
		super().doExit()

try:
	l=SgnHwDriver()
	l.warning('SGN HWDRIVER STARTED')
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
