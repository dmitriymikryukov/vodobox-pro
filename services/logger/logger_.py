import sys,os
sys.path.insert(0, '../..')

from IPC import *

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


l=SgnLogger()
with l:
	print(l)
	l.warning('SGN LOGGER STARTED')
	l.join()
