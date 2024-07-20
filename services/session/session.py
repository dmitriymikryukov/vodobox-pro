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
			query_amount=False,
			complete=False,
			)
		self.esc_ack=False

	def nominal_to_text(self,n):
		#return '%.2f'%n
		if n is False:
			return n
		x='0000%s'%n
		d0=int(x[:-self['currency_decimals']])
		d1=x[-self['currency_decimals']:]
		return "%s.%s"%(d0,d1)

	def nominal_to_text_with_currency(self,n):
		if n is False:
			return n
		return self.nominal_to_text(n)+self['currency']

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
		self.debug('Сессия: %s %s Выдача сдачи завершена, выдано %s из %s'%(group,name,
			self.nominal_to_text_with_currency(amount),self.nominal_to_text_with_currency(required)))
		self['session']['is_dispensing']=False
		self['session']['cash_balance']-=amount
		self.EventBalanceChanged()

	@subscribe
	def EventMoneyStacked(self,amount,mtype):
		self.debug('Сессия: Пополение баланса на %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))
		if mtype in ['CASH']:
			self['session']['cash_balance']+=amount
			self.EventBalanceChanged()
			if self.esc_ack:
				self.esc_ack=False
				self.DepositACK()

	@subscribe
	def EventMoneyRejected(self,amount,mtype):
		self.debug('Сессия: Возврат номинала %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))
		if mtype in ['CASH']:
			self.EventBalanceChanged()
			if self.esc_ack:
				self.esc_ack=False
				self.DepositNCK('REJECTED')			

	@subscribe
	def EventMoneyEscrow(self,amount,mtype):
		self.debug('Сессия: На удержании %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))
		if mtype in ['CASH']:
			self.esc_ack=False
			if self['session']['escrow_balance']!=0:
				self.critical('Повторное внесение наличных при удержании')
			else:
				self['session']['escrow_balance']+=amount
			self.EventBalanceChanged()

	@subscribe
	def EndSession(self):
		self.esc_ack=False
		self['session']['query_amount']=False
		self['session']['complete']=True
		self.DeactivateAllPayments()
		if self['session']['escrow_balance']!=0:
			self.RejectEscrow()
		if self['session']['cash_balance']:
			self['session']['is_dispensing']=True
			self.PayoutCash(self['session']['cash_balance'])
			#наверное нужно запустить в отдельном процессе
			ts=time.time()
			while (ts+65)<time.time():
				if not self['session']['is_dispensing']:
					break
				time.sleep(0.5)

	def _getBalance(self):
		return self['session']['cash_balance']+self['session']['escrow_balance']

	@subscribe
	def EventPaymentComplete(self):
		self.info('Сессия: Оплата завершена. Получено %s из %s'%(self.nominal_to_text_with_currency(self._getBalance()),self.nominal_to_text_with_currency(self['session']['query_amount'])))
		self.DeactivateAllPayments()

	@subscribe
	def EventBalanceChanged(self):
		self.info('Сессия: Изменение баланса: %s из %s'%(self.nominal_to_text_with_currency(self._getBalance()),self.nominal_to_text_with_currency(self['session']['query_amount']),))
		if self['session']['query_amount']:
			bal=self._getBalance()
			if bal>=self['session']['query_amount']:
				self.EventPaymentComplete()

	@subscribe
	def DepositAmount(self,amount):
		self.esc_ack=False
		bal=self._getBalance()
		if bal<amount:
			self.DepositNCK('INSUFFICIENT_BALANCE')
		elif self['session']['escrow_balance']>0 and (bal-self['session']['escrow_balance'])<amount:
			self.esc_ack=amount
			self.AcceptEscrow()
		else:
			self.DepositACK()

	@subscribe
	def AcknowlegeAmount(self,amount):
		self['cash_balance']-=amount


try:
	l=SgnSession()
	l.warning('SGN SESSION STARTED')
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
