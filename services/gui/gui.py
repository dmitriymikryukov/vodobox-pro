import sys,os,time
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'guiservice'))

from IPC import *


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
		self.current_window=None
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
		#return '%.2f'%n
		x='0000%s'%n
		d0=int(x[:-self['currency_decimals']])
		d1=x[-self['currency_decimals']:]
		return "%s.%s"%(d0,d1)

	def nominal_to_text_with_currency(self,n):
		return self.nominal_to_text(n)+self['currency']

	@subscribe
	def EventMoneyStacked(self,amount,mtype):
		self.info('Пополение баланса на %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))

	@subscribe
	def EventPayoutStarted(self,group,name,amount):
		self.info('%s %s Начинаем выдачу сдачи %s'%(group,name,self.nominal_to_text_with_currency(amount)))

	@subscribe
	def EventPayoutProgress(self,group,name,amount):
		self.info('%s %s Выдача часть сдачи %s'%(group,name,self.nominal_to_text_with_currency(amount)))

	@subscribe
	def EventPayoutFinished(self,group,name,amount,required):
		self.info('%s %s Выдача сдачи завершена, выдано %s из %s'%(group,name,self.nominal_to_text_with_currency(amount),self.nominal_to_text_with_currency(required)))

	@subscribe
	def EventNominalIsHigh(self, group, name, nominal, route_txt, is_bill, payout_amount_after):
		self.current_window.no_money_left_to_change.emit()

	# @subscribe
	# def EventPaymentComplete(self):
	# 	self.current_window.payment_succeed.emit()

	@subscribe
	def EventBalanceChanged(self):
		self.current_window.deposit_balance_changed.emit()

try:
	sgn_gui = SgnGUI()
	sgn_gui.warning('SGN GUI STARTED')
	os.chdir(os.path.join(os.path.dirname(__file__),'guiservice'))

	from guiservice.main import run_gui

	try:
		run_gui(sgn_gui)
	except KeyboardInterrupt:
		print('CTRL-C')
		sgn_gui.critical('CTRL-C Interrupt')
		time.sleep(1)
		sgn_gui['shutdown'] = True
	except Exception as e:
		sgn_gui.exception(e)
		time.sleep(1)
		sgn_gui['shutdown'] = True

finally:
	print("FINALLY!")
	try:
		sgn_gui['shutdown'] = True
	except:
		pass
	time.sleep(1)	
	cleanup_resources()

"""
	пример работы:

	sgn_gui.DeactivateAllPayments()
	sgn_gui.StartSession('CASH')
	sgn_gui['session']['query_amount']=15000
	try:
		try:
			#put your code here
			while True:
				if sgn_gui.can_accept_cash():
					time.sleep(5)				
					sgn_gui.ActivateCash()
					time.sleep(60)
					break
				else:
					time.sleep(0.5)
		except Exception as e:
			sgn_gui.exception(e)
	finally:
		sgn_gui.EndSession()
		sgn_gui.join()
"""
