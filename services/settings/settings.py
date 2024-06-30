import sys,os
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

class SgnSettings(sgnService):
	def __init__(self):
		super().__init__()
		#self['payment_method']=self.gdict._manager.dict()

	def do_init(self):
		self['payment_method']=dict(CASH=dict(),CASHLESS=dict())
		self['mdb']=dict(port='/dev/ttyAMA0')
		self['currency']='RUR'
		self['currency_decimals']=2
		self['accept']=dict(
			coin=False,
			bill=False,
			client_card=False,
			bank_card=False,
			sbp=False,
			qr_reader=False,
			)
		self['dispense']=dict(
			coin=False,
			bill=False,
			bank_full=False,
			bank_partial=False,
			sbp=False,
			)
		self['dispense_amount']=dict(
			coin=0,
			bill=0,
			)
		self['disabled_nominals']=dict(
			coin=[],
			bill=[]
			)

try:
	l=SgnSettings()
	l.warning('SGN SETTINGS STARTED')
	l.do_init()
	l.join()
finally:
	print("FINALLY!")
	#cleanup_resources()
