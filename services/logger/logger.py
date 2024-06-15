import sys,os,time
sys.path.insert(0, '../..')

from IPC import *
l=None
"""
import signal

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

class SgnLogger(sgnService):
	def __init__(self):
		super().__init__()

	def buca_form(self,m,t,txt):
		ta=[]
		mn='[%s]'%os.path.basename(m)+'                '
		mn=mn[:16]
		t=t+':               '
		t=t[:10]
		for x in txt.split('\n'):
			if len(x):
				ta.append('%s %s %s'%(mn,t,x))
		return '\n'.join(ta)

	def doExit(self):
		print("Exiting logger,exit")
		super().doExit()

	@subscribe
	def exception_handler(self,m,txt):
		print(self.buca_form(m,"EXCEPTION",txt))

	@subscribe
	def debug_handler(self,m,txt):
		print(self.buca_form(m,"debug",txt))

	@subscribe
	def info_handler(self,m,txt):
		print(self.buca_form(m,"INFO",txt))

	@subscribe
	def error_handler(self,m,txt):
		print(self.buca_form(m,"ERROR",txt))

	@subscribe
	def warning_handler(self,m,txt):
		print(self.buca_form(m,"WARNING",txt))

	@subscribe
	def critical_handler(self,m,txt):
		print(self.buca_form(m,"CRITICAL",txt))

try:
	l=SgnLogger()
	l.warning('SGN LOGGER STARTED')
	l.join()
finally:
	print("FINALLY!")
	#cleanup_resources()
