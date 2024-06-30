import sys,os,time
sys.path.insert(0, '../..')

from IPC import *

#from guiservice.main import run_gui

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

class SgnGUI(sgnService):
	def __init__(self):
		super().__init__()
		self.min_coin_dispense_amount=1800
		self.min_bill_dispense_amount=0

	def doExit(self):
		print("Exiting GUI,exit")
		super().doExit()

	def can_accept_coins(self):
		return self['accept']['coin']

	def can_accept_bills(self):
		return self['accept']['bill']

	def can_dispense_coins(self):
		return self['dispense']['coin'] and (self['dispense_amount']['coin']>=self.min_coin_dispense_amount)

	def can_dispense_bills(self):
		return self['dispense']['bill'] and (self['dispense_amount']['bill']>=self.min_bill_dispense_amount)

	def can_accept_cash(self):
		return self.can_accept_coins() or self.can_accept_bills()

	def can_dispense_cash(self):
		return self.can_dispense_coins() or self.can_dispense_bills()

	def nominal_to_text(self,n):
		x='0000%s'%n
		d0=int(x[:self['currency_decimals']])
		d1=x[-self['currency_decimals']:]
		return "%s.%s"%(d0,d1)

	def nominal_to_text_with_currency(self,n):
		return self.nominal_to_text(n)+self['currency']

	@subscribe
	def EventMoneyStacked(self,amount,mtype):
		log.info('Пополение баланса на %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))

	@subscribe
	def EventPayoutStarted(self,group,name,amount):
		self.info('%s %s Начинаем выдачу сдачи %s'%(group,name,self.nominal_to_text_with_currency(amount)))

	@subscribe
	def EventPayoutProgress(self,group,name,amount):
		self.info('%s %s Выдача часть сдачи %s'%(group,name,self.nominal_to_text_with_currency(amount)))

	@subscribe
	def EventPayoutFinished(self,group,name,amount,required):
		self.info('%s %s Выдача сдачи завершена, выдано %s из %s'%(group,name,self.nominal_to_text_with_currency(amount),self.nominal_to_text_with_currency(required)))


try:
	l=SgnGUI()
	l.warning('SGN GUI STARTED')
	#os.chdir('./guiservice')
	#run_gui(l)
	
	print("DEAC")
	l.info('Deactivating')
	l.DeactivateAllPayments()
	print("SESS")
	l.info('session')
	l.StartSession('CASH')
	print("LOOP")
	l.info('loop')
	try:
		try:
			#put your code here
			while True:
				print("aaa")
				if l.can_accept_cash():				
					print("act")
					l.ActivateCash()
					time.sleep(60)
					break
				else:
					time.sleep(0.5)
					print('%s'%l['accept'])
		except Exception as e:
			l.exception(e)
	finally:
		l.EndSession()
		l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
