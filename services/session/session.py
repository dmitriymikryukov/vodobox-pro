import sys,os,time
sys.path.insert(0, '../..')

from IPC import *

import time

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

class SgnSession(sgnService):
	def __init__(self):
		super().__init__()
		self.session_init()

	def session_init(self):
		self['session']=dict(
			session_type=False,
			cash_balance=0,
			escrow_balance=0,
			e_balance=0,
			client_balance=0,
			liter_balance=0,
			is_dispensing=False,
			)

	def doExit(self):
		print("Exiting SESSION,exit")
		if (self.session_type):
			self.EndSession()
		super().doExit()

	@subscribe
	def StartSession(self,session_type):
		if self['session']:
			self.EndSession()
		self.session_init()
		self['session']['session_type']=session_type

	@subscribe
	def ChangeSession(self,session_type):
		if self['session']:
			self['session']['session_type']=session_type
		else:
			self.StartSession(session_type)

	@subscribe
	def EventPayoutFinished(self,group,name,amount,required):
		self.debug('Сессия: %s %s Выдача сдачи завершена, выдано %s из %s'%(group,name,amount,required))
		self['session']['is_dispensing']=False
		self['session']['cash_balance']-=amount

	@subscribe
	def EventMoneyStacked(self,amount,mtype):
		log.debug('Сессия: Пополение баланса на %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))
		if mtype in ['CASH']:
			self['session']['cash_balance']+=amount

	@subscribe
	def EndSession(self):
		if self['session']['cash_balance']:
			self['session']['is_dispensing']=True
			self.PayoutCash(self['session']['cash_balance'])
			#наверное нужно запустить в отдельном процессе
			ts=time.time()
			while (ts+65)<time.time():
				if not self['session']['is_dispensing']:
					break
				time.sleep(0.5)

try:
	l=SgnSession()
	l.warning('SGN SESSION STARTED')
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
