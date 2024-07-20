import sys,os
sys.path.insert(0, '../..')
from IPC import *

from interfaces.ipc.iface_mdb_bill import ifaceMDBbill

from traceback import format_exc

import time
import json
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

class SgnMDBbill(ifaceMDBbill):
	def __init__(self):
		super().__init__()
		self.pts=False
		self.ppol=False
		self.pepol=False
		self.enabled_nominals=[]
		self.penabled_nominals=False
		self.pdisabled_nominals=False
		self.payout_amount=False

	def nominal_to_text(self,n):
		x='0000%s'%n
		d0=int(x[:-self['currency_decimals']])
		d1=x[-self['currency_decimals']:]
		return "%s.%s"%(d0,d1)

	def nominal_to_text_with_currency(self,n):
		return self.nominal_to_text(n)+self['currency']

	def nominal_to_cents(self,n):
		x=int(n)*(10**self['currency_decimals'])
		return round(x,self['currency_decimals'])

	@subscribe
	def BillActivateNominals(self,nominals):
		self.enabled_nominals=nominals

	def process(self):
		self.info('BILL process started')
		try:
			while True:
				try:
					self.able['escrow']=False
					self.able['is_enabled']=False
					self.able['can_be_used']=False
					self.able['is_ready']=False
					self.able['status']='DISCONNECTED'
					while not self.setup():
						time.sleep(0.5)
					self.able['status']='RESETTING'
					self.reset()
					time.sleep(0.3)
					while True:
						x=self.setup()
						if x:
							self.able['setup']=x
							break
						time.sleep(0.1)
					self.info("устройство приема купюр сброшено")
					#if self.able['setup']['level']<2:
					#	self.able['status']='UNSUPPORTED'
					#	self.critical('BILL ACCEPTOR LEVEL UNSUPPORTED LESS THAN 2 %s'%(self.able['setup']))
					#	time.sleep(60.0)
					#	continue
					self.able['status']='CONNECTED'
					self['currency']=self.able['setup']['country_code']
					while True:
						x=self.identification(self.able['setup']['level'])
						if x:
							self.able['ident']=x
							break
						time.sleep(0.1)
					self.able['status']='CONFIGURING'
					self.info('Обнаружено устройство приема купюр Level: %s: %s'%(self.able['setup']['level'],self.able['ident']))
					while True:
						x=self.featuresEnable(self.able['ident']['features'])
						if x or self.able['setup']['level']<2:
							break
						time.sleep(0.1)

					self.info("Валюта купюр: %s"%self['currency'])
					bill_type_credit=self.able['setup']['bill_type_credit']
					x=[]
					for nom in bill_type_credit:
						if nom:
							x.append('%s'%self.internalToCents(nom))
					self.info("Поддерживаемые номиналы купюр: %s"%(', '.join(x)))

					while True:
						x=self.tubeStatus()
						if x:
							bill_type_credit=self.able['setup']['bill_type_credit']
							i=0
							xn=dict()
							for nom in bill_type_credit:
								if nom:
									v=dict(
										nominal=self.internalToCents(nom),
										can_route_to_stack=x['is_stack_full'],# if coin_tube_routing_msk&(1<<i) else False,
										is_bill=True,
										is_stack_full=False,#True if x['tube_full_msk']&(1<<i) else False,
										#stack_nominal_count=x['coin_count'][i],
										stack_number=i
										)
									xn[v['nominal']]=v
								i+=1
							self.able['setup']['fixed_nominals']=xn
							self.able['setup']['enabled_nominals']=[]
							break
						time.sleep(0.1)
				except Exception as e:
					self.exception(e)
					time.sleep(15.0)
				else:
					break

			self.able['can_be_used']=True
			self.able['is_ready']=False
			self.able['is_enabled']=False
			self.ppol=False
			while True:
				self.polling()
				self.escrowProcessing()
				time.sleep(0.1)
		finally:
			self.able['can_be_used']=False
			self.able['is_ready']=False
			self.able['is_enabled']=False
			self.info('BILL process finished')

	def polling(self):
		is_r=self.able['is_ready']
		x=self.poll()
		if x is True:
			self.pollEvent([0])
		elif x:
			try:
				el=len(x)
				_dp=[]
				while len(x):
					if el!=1 or x[0]!=9:
						dl=self.pollEvent(x)
						if (x[0]&0xE0)==0:
							_dp+=x[:dl]
					else:
						if el==1 or x[0]!=9:
							dl=self.pollEvent(x)
							self.able['is_ready']=True
							self['accept']['bill']=True
						else:
							dl=1
					x=x[dl:]
				_jdp=json.dumps(_dp)
				if self.ppol!=_jdp:
					self.ppol=_jdp
			except Exception as e:
				self.exception(e)
		if is_r!=self.able['is_ready']:
			self.info('READY %s->%s'%(is_r,self.able['is_ready']))
		_jx=json.dumps(self.enabled_nominals)
		_jd=json.dumps(list(self['disabled_nominals']['bill']))
		if not self.penabled_nominals or self.penabled_nominals!=_jx or not self.pdisabled_nominals or self.pdisabled_nominals!=_jd:
			if self.enableNominals(self.enabled_nominals):
				self.penabled_nominals=_jx
				self.pdisabled_nominals=_jd			

	def enableNominals(self,nominals):
		noms=[]
		nn=[]
		#escr=[]
		print('bill enableNominals: %s'%(nominals,))
		print('bill disabled_nominals: %s'%(self['disabled_nominals']['bill'],))
		for x in nominals:
			if not (x in self['disabled_nominals']['bill']):
				#t=self.getTubeNominal(x)
				#if t:
				if x in self.able['setup']['fixed_nominals'].keys():
					nn.append(x)
					snn=self.able['setup']['fixed_nominals'][x]['stack_number']
					noms.append(snn)
					#if self['session']['query_amount'] and self.nominal_to_cents(x)>=(self['session']['query_amount']-self['session']['cash_balance']):
					#	escr.append(snn)
		self.able['setup']['enabled_nominals']=nn
		#print('bill escrowNominals: %s'%(escr,))
		return self.cmdEnableNominals(noms,noms)


	def getTubeNominal(self,n):
		for nom in self.able['setup']['fixed_nominals'].keys():
			if self.able['setup']['fixed_nominals'][nom]['stack_number']==n:
				return self.able['setup']['fixed_nominals'][nom]
		self.error('NOMINAL in tube %s is not found in %s'%(n,self.able['setup']['fixed_nominals']))
		return False


	def tubeStatusUpdate(self):
		ts=time.time()
		while (ts+3.0)<time.time():
			x=self.tubeStatus()
			if x:
				for nom in self.able['setup']['fixed_nominals'].keys():
					t=self.able['setup']['fixed_nominals'][nom]
					t['is_stack_full']=x['is_stack_full']#True if x['tube_full_msk']&(1<<t['stack_number']) else False
					t['stack_nominal_count']=x['bills_in_stack']
				break

	def pollEvent(self,aEvent):
		#we return byte count of event
		try:
			if 0x80==(aEvent[0]&0x80):
				route=(aEvent[0]>>4)&7
				bill_type=aEvent[0]&15
				t=self.getTubeNominal(bill_type)
				if not t:
					self.critical('INVALID NOMINAL %s'%(bill_type))
				else:
					self.tubeStatusUpdate()
					if 0==route:
						self.able['escrow']=False
						route_txt="CASH_BOX"
						ru_txt=u'В СТЕКЕР'
						self.EventPaymentNominalStacked(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					elif 1==route:
						self.able['escrow']=t
						route_txt="ESCROW"
						ru_txt='НА УДЕРЖАНИЕ'
						po=self['dispense_amount']['coin']
						n2c=self.nominal_to_cents(t['nominal'])
						if self['session']['query_amount']!=0:
							qelse=(self['session']['query_amount']-self['session']['cash_balance'])
							if n2c>=qelse or qelse<(po/2):
								self.EventPaymentNominalEscrow(self.able['group'],self.able['name'],
									n2c,route_txt,t['is_bill'],t['is_stack_full'])
								if qelse<(po/2):
									self.EventNominalIsHigh(self.able['group'],self.able['name'],
										n2c,route_txt,t['is_bill'],po-qelse)									
							elif qelse<=0:
								self.cmdEscrow(0)								
							else:
								self.cmdEscrow(1)
						elif n2c>(po/2):
							self.EventPaymentNominalEscrow(self.able['group'],self.able['name'],
								n2c,route_txt,t['is_bill'],t['is_stack_full'])
							self.EventNominalIsHigh(self.able['group'],self.able['name'],
								n2c,route_txt,t['is_bill'],po-n2c)	
						else:
							self.cmdEscrow(1)
					elif 2==route:
						self.able['escrow']=False
						route_txt="REJECT"
						ru_txt='ВОЗВРАЩЕНА КЛИЕНТУ'
						self.EventPaymentNominalRejected(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					elif 3==route or 5==route:
						self.able['escrow']=False
						route_txt="RECYCLER"
						ru_txt='В RECYCLER'
						self.EventPaymentNominalStacked(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					elif 4==route:
						self.able['escrow']=False
						route_txt="REJECT"
						ru_txt='И ВОЗВРАЩЕНА КЛИЕНТУ (ПРИЕМ НОМИНАЛА ЗАПРЕЩЕН)'
						self.EventPaymentNominalRejected(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					elif 6==route:
						self.able['escrow']=False
						route_txt="MANUAL_DISPENSE"
						ru_txt='МАНUAL DISPENSE'
					elif 7==route:
						self.able['escrow']=False
						route_txt="CASH_BOX"
						ru_txt='RECYCLER->STACKER'
					if 2==route and self['session']['escrow_balance']>0:
						self.info('Купюра номиналом %s %s'%(t['nominal'],ru_txt))
					else:
						self.info('Получена купюра номиналом %s %s'%(t['nominal'],ru_txt))
				return 1
			elif 0x40==(aEvent[0]&0xE0):
				self.EventPaymentSlugs(self.able['group'],self.able['name'],aEvent[0]&0x1F)
			elif aEvent[0] in [0x01,0x26]:
				self.able['status']='FAULT'
				self.able['is_ready']=False
				self.EventPaymentFault(self.able['group'],self.able['name'],aEvent[0],"Defective Motor")
			elif aEvent[0] in [0x02,0x24]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"Sensor Problem")
			elif aEvent[0] in [0x03,0x22,0x23]:
				self.able['status']='BUSY'
				self.able['is_ready']=False
				self.EventPaymentDeviceBusy(self.able['group'],self.able['name'],"Bill vaildator busy")
			elif aEvent[0] in [0x04,0x28]:
				self.able['status']='FAULT'
				self.able['is_ready']=False
				self.EventPaymentFault(self.able['group'],self.able['name'],aEvent[0],"ROM Checksum Error")
			elif aEvent[0] in [0x05,0x27]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"Bill Jammed")
			elif 0x06==aEvent[0]:
				self.able['status']='RESETED'
				self.able['is_ready']=False				
				self.warning("Just Reset")
			elif 0x07==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"Bill Removed!")
			elif 0x08==aEvent[0]:
				self.able['status']='FAULT'
				self.able['is_ready']=False
				self.EventPaymentFault(self.able['group'],self.able['name'],aEvent[0],"Stacker is removed")
			elif 0x09==aEvent[0]:
				self.able['status']='DISABLED'
				#self.able['is_ready']=True
				#self['accept']['bill']=True
			elif 0x0A==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"Cannot Escrow! No Bill At Escrow position")
			elif 0x0B==aEvent[0]:
				self.EventPaymentSlugs(self.able['group'],self.able['name'],1)
			elif 0x0C==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"Possible Credited Coin Removal")
			elif 0x21==aEvent[0]:
				self.EventPaymentEscrowLever(self.able['group'],self.able['name'],"[Escrow request] - An escrow lever activation has been detected.")
			elif 0x00==aEvent[0]:
				self.able['status']='READY'
				self.able['is_ready']=True				
				self['accept']['bill']=True
			else:
				self.error("BILL UNKNOWN STATUS:%02X"%aEvent[0])
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"COIN UNKNOWN STATUS:%02X"%aEvent[0])

		except Exception as e:
			self.exception('ERROR IN POLL PARSER, EVENT: {e}: {err}',e=aEvent,err=format_exc())
		return 1

	def escrowProcessing(self):
		pass

	#@subscribe
	#def EventBalanceChanged(self):
	#	if self.enabled_nominals and len(self.enabled_nominals)>0:
	#		self.penabled_nominals='xyu'

	@subscribe
	def RejectEscrow(self):
		self.cmdEscrow(0)

	@subscribe
	def AcceptEscrow(self):
		self.cmdEscrow(1)

try:
	l=SgnMDBbill()
	l.warning('SGN BILL STARTED')
	#l.warning('SgnMDBcoin Base Classes: %s'%(SgnMDBcoin.__bases__,))
	#l.warning('SgnMDBcoin MRO: %s'%(type.mro(SgnMDBcoin)))
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
