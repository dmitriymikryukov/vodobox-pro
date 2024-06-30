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

class SgnPayment(sgnService):
	def __init__(self):
		super().__init__()

	def doExit(self):
		print("Exiting payment,exit")
		super().doExit()

	@subscribe
	def EventPaymentManualDispense(self,group,name,nominal,count):
		self.debug('EventPaymentManualDispense: %s %s %sx%s'%(group,name,nominal,count))

	@subscribe
	def EventPaymentNominalStacked(self,group,name,nominal,route_txt,is_bill,is_stack_full):
		self.debug('EventPaymentNominalStacked: %s %s %s to %s is_bill:%s full:%s'%(group,name,nominal,route_txt,is_bill,is_stack_full))
		self.EventMoneyStacked(nominal,group)

	@subscribe
	def EventPaymentNominalRejected(self,group,name,nominal,route_txt,is_bill,is_stack_full):
		self.debug('EventPaymentNominalRejected: %s %s %s to %s is_bill:%s full:%s'%(group,name,nominal,route_txt,is_bill,is_stack_full))

	@subscribe
	def EventPaymentSlugs(self,group,name,slugs):
		self.debug('EventPaymentSlugs: %s %s count: %s'%(group,name,slugs))

	@subscribe
	def EventPaymentEscrowLever(self,group,name,message):
		self.debug('EventPaymentEscrowLever: %s %s %s'%(group,name,message))

	@subscribe
	def EventPaymentDeviceBusy(self,group,name,message):
		self.debug('EventPaymentDeviceBusy: %s %s %s'%(group,name,message))

	@subscribe
	def EventPaymentError(self,group,name,code,message):
		self.debug('EventPaymentError: %s %s %s:%s'%(group,name,code,message))

	@subscribe
	def EventPaymentFault(self,group,name,code,message):
		self.debug('EventPaymentFault: %s %s %s:%s'%(group,name,code,message))

	@subscribe
	def EventPaymentReady(self,group,name):
		self.info('%s %s Готов к работе'%(group,name))

	@subscribe
	def EventPayoutStarted(self,group,name,amount):
		self.debug('%s %s Начинаем выдачу сдачи %s'%(group,name,amount))

	@subscribe
	def EventPayoutProgress(self,group,name,amount):
		self.debug('%s %s Выдача часть сдачи %s'%(group,name,amount))

	@subscribe
	def EventPayoutFinished(self,group,name,amount,required):
		self.debug('%s %s Выдача сдачи завершена, выдано %s из %s'%(group,name,amount,required))

	@subscribe
	def PayoutCash(self,amount):
		self.CoinPayout(amount)

	@subscribe
	def ActivateCoin(self,nominals):
		res=False
		if len(nominals)>0:
			if 'COIN' in self['payment_method']['CASH'].keys():
				m=self['payment_method']['CASH']['COIN']
				if m['is_ready']:
					self.info('Примимаются монеты номиналом %s'%(nominals,))
					self.CoinActivateNominals(nominals)
					res=True
				else:
					self.error('Устройство приема монет не готово')
			else:
				self.error('Нет устройства приема монет')
		else:
			self.info('Деактивация приема монет')			
			self.CoinActivateNominals(nominals)
			res=True
		return res

	def act_deact_cash(self,en):
		res=False
		try:
			if 'CASH' in self['payment_method'].keys():
				self.info('%s устрйств приема наличных'%("Активация" if en else "Деактивация"))
				for x in self['payment_method']['CASH'].keys():
					m=self['payment_method']['CASH'][x]
					if x in ['COIN']:
						if m['is_ready']:
							self.ActivateCoin(list(m['fixed_nominals']) if en else [])
							res=True
						else:
							self.error('%s Устройство приема монет не готово'%('DISABLING' if not en else'ENABLING'))
							self.info('%s'%(m,))						
					else:
						self.error('%s Устройство приема наличных %s не поддерживается'%(('DISABLING' if not en else 'ENABLING'),x,))
			else:
				if en:
					self.error('Невозможно активировать устройства приема наличных - нет устройств')
		except Exception as e:
			self.exception(e)
			res=False
		return res

	@subscribe
	def ActivateCash(self):
		self.act_deact_cash(True)

	@subscribe
	def DeactivateCash(self):
		self.act_deact_cash(False)

	@subscribe
	def DeactivateAllPayments(self):
		self.warning('Отключение всех видов приема денежных средств')
		try:
			self.DeactivateCash()
		except Exception as e:
			self.exception(e)


try:
	l=SgnPayment()
	l.warning('SGN PAYMENT STARTED')
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
