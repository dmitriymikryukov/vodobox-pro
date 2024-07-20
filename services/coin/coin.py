import sys,os
sys.path.insert(0, '../..')
from IPC import *

from interfaces.ipc.iface_mdb_coin import ifaceMDBcoin
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

class SgnMDBcoin(ifaceMDBcoin):
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
	def CoinActivateNominals(self,nominals):
		self.enabled_nominals=nominals

	@subscribe
	def CoinPayout(self,amount):
		self.enabled_nominals=[]
		self.payout_amount=amount

	def readManufacturers(self):
		rmd = [
			dict(code=0x6E, name="mgmt", code3=False),
			dict(code=0x6B, name="cash_float", yy=[65, 66, 67], code3=True, code3yy=[0], zz=[0, 0, 0, 0, 0, 0]),
			dict(code=0x74, name="casette_type", code3=True),
			dict(code=0x7C, name="reserved_coin", code3=False),
			dict(code=0x87, name="error_report", code3=False),
			dict(code=0x88, name="payout_method", code3=False),
			dict(code=0x8F, name="tube_detection", code3=False),
			dict(code=0x92, name="resend_credit", code3=False)]
		if self.able['extra_customer_commands']:
			rmd += [
				dict(code=0x7F, name="residual_credit", code3=False),
				dict(code=0xA2, name="set_quantity", code3=True),
			]
		for rr in rmd:
			if ('code3' in rr) and rr['code3']:
				x=self.manufacturer(rr['code'], 0x03, 0x00 if not ('code3yy' in rr) else rr['code3yy'][0],
								  zz=rr['zz'] if 'zz' in rr else [])
			else:
				x=self.manufacturer(rr['code'], 0x01, 0x00 if not ('yy' in rr) else rr['yy'][0],
									  zz=rr['zz'] if 'zz' in rr else [])
			self.debug('manufacturer result: %s'%(x,))

	def writeManufacturers(self):
		wmd = [
			# dict(code=0x6E,name="mgmt",code3=False),
			# dict(code=0x6B,name="cash_float",yy=[65,66,67],code3=True,code3yy=[0],zz=[0,0,0,0,0,0]),
			# dict(code=0x74,name="casette_type",code3=True),
			dict(code=0x7C, name="reserved_coin", yy=[0x0F]),
			dict(code=0x87, name="error_report", yy=[0x01]),
			dict(code=0x88, name="payout_method", yy=[0x00]),
			dict(code=0x8F, name="tube_detection", yy=[0x01]),
			dict(code=0x92, name="resend_credit", yy=[0x01])]
		if self.able['extra_customer_commands']:
			wmd += [
				dict(code=0x7F, name="residual_credit", yy=[0x02]), # настройка транзакции + отправляеться удаленно только для версий прошивки >=3,56 coin
				# dict(code=0xA2, name="set_quantity", code3=True),
			]
		for rr in wmd:
			x=self.manufacturer(rr['code'], 0x02, rr['yy'][0])
			self.debug('manufacturer result: %s'%(x,))


	def process(self):
		self.info('COIN process started')
		try:
			while True:
				try:
					self.able['extra_customer_commands']=False
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
					self.info("устройство приема монет сброшено")
					if self.able['setup']['level']<3:
						self.able['status']='UNSUPPORTED'
						self.critical('COIN ACCEPTOR LEVEL UNSUPPORTED LESS THAN 3')
						time.sleep(60.0)
						continue
					self.able['status']='CONNECTED'
					self['currency']=self.able['setup']['country_code']
					self.decimal_places=self.able['setup']['decimal_places']
					self.scaling_factor=self.able['setup']['scaling_factor']
					while True:
						x=self.identification()
						if x:
							self.able['ident']=x
							break
						time.sleep(0.1)
					self.able['status']='CONFIGURING'
					self.info('Обнаружено устройство приема монет Level %s: %s'%(self.able['setup']['level'],self.able['ident']))
					while True:
						x=self.featuresEnable(self.able['ident']['features'])
						if x:
							break
						time.sleep(0.1)
					if (self.able['ident']['model'] in ['CCM6-RUR MDB']) and self.able['ident']['software'] >= 1334:
						self.able['extra_customer_commands']=False
						self.info('Поддерживаются команды для настройки сдачи')
						#self.readManufacturers()
						self.writeManufacturers()
					else:
						self.info('Команды для настройки сдачи не поддерживаются устройством')

					self.info("Валюта монет: %s"%self['currency'])
					coin_type_credit=self.able['setup']['coin_type_credit']
					x=[]
					for nom in coin_type_credit:
						if nom:
							x.append('%s'%self.internalToCents(nom))
					self.info("Поддерживаемые номиналы монет: %s"%(', '.join(x)))

					while True:
						x=self.tubeStatus()
						if x:
							coin_type_credit=self.able['setup']['coin_type_credit']
							coin_tube_routing_msk=self.able['setup']['coin_tube_routing_msk']
							i=0
							xn=dict()
							for nom in coin_type_credit:
								if nom:
									v=dict(
										nominal=self.internalToCents(nom),
										can_route_to_stack=True if coin_tube_routing_msk&(1<<i) else False,
										is_bill=False,
										is_stack_full=True if x['tube_full_msk']&(1<<i) else False,
										stack_nominal_count=x['coin_count'][i],
										stack_number=i
										)
									xn[v['nominal']]=v
								i+=1
							self.able['setup']['fixed_nominals']=xn
							self.able['setup']['enabled_nominals']=[]
							self.dispenseAmount()
							break
						time.sleep(0.1 if self.able['status']!='READY' else 0.01)
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
				self.payoutProcessing()
				time.sleep(0.1)
		finally:
			self.able['can_be_used']=False
			self.able['is_ready']=False
			self.able['is_enabled']=False
			self.info('COIN process finished')

	def polling(self):
		is_r=self.able['is_ready']
		if not self.pts or (self.pts+1.0)<time.time():
			x=self.diagnostic()
			if x:
				self.pts=time.time()
				try:
					self.diagEvent(x)
				except Exception as e:
					self.exception(e)
		x=self.poll()
		if x is True:
			#self.able['is_ready']=True
			self.pollEvent([0])
		elif x:
			try:
				_dp=[]
				while len(x):
					dl=self.pollEvent(x)
					if (x[0]&0xE0)==0:
						_dp+=x[:dl]
					x=x[dl:]
				_jdp=json.dumps(_dp)
				if self.ppol!=_jdp:
					self.ppol=_jdp
			except Exception as e:
				self.exception(e)
		if is_r!=self.able['is_ready']:
			self.info('READY %s->%s'%(is_r,self.able['is_ready']))
		_jx=json.dumps(self.enabled_nominals)
		_jd=json.dumps(list(self['disabled_nominals']['coin']))
		if not self.penabled_nominals or self.penabled_nominals!=_jx or not self.pdisabled_nominals or self.pdisabled_nominals!=_jd:
			if self.enableNominals(self.enabled_nominals):
				self.penabled_nominals=_jx
				self.pdisabled_nominals=_jd			

	def enableNominals(self,nominals):
		noms=[]
		nn=[]
		print('coin enableNominals: %s'%(nominals,))
		print('coin disabled_nominals: %s'%(self['disabled_nominals']['coin'],))
		for x in nominals:
			if not (x in self['disabled_nominals']['coin']):
				#t=self.getTubeNominal(x)
				#if t:
				if x in self.able['setup']['fixed_nominals'].keys():
					nn.append(x)
					noms.append(self.able['setup']['fixed_nominals'][x]['stack_number'])
		self.able['setup']['enabled_nominals']=nn
		return self.cmdEnableNominals(noms)


	def getTubeNominal(self,n):
		for nom in self.able['setup']['fixed_nominals'].keys():
			if self.able['setup']['fixed_nominals'][nom]['stack_number']==n:
				return self.able['setup']['fixed_nominals'][nom]
		self.error('NOMINAL tube %s is not found in %s'%(n,self.able['setup']['fixed_nominals']))
		return False

	def dispenseAmount(self):
		amo=0
		dpc=int(10**self['currency_decimals'])
		for nom in self.able['setup']['fixed_nominals'].keys():
			t=self.able['setup']['fixed_nominals'][nom]
			amo+=int(nom)*t['stack_nominal_count']
		amo*=dpc
		self['dispense_amount']['coin']=amo
		return amo


	def tubeStatusUpdate(self):
		ts=time.time()
		while True:#(ts+3.0)<time.time():
			x=self.tubeStatus()
			if x:
				for nom in self.able['setup']['fixed_nominals'].keys():
					t=self.able['setup']['fixed_nominals'][nom]
					t['is_stack_full']=True if x['tube_full_msk']&(1<<t['stack_number']) else False
					t['stack_nominal_count']=x['coin_count'][t['stack_number']]
				break
		return self.dispenseAmount()

	def pollEvent(self,aEvent):
		#we return byte count of event
		try:
			if 0x80==(aEvent[0]&0x80):
				count=(aEvent[0]>>4)&7
				coin_type=aEvent[0]&15
				coins_in_tube=aEvent[1]
				t=self.getTubeNominal(coin_type)
				if not t:
					self.critical('INVALID TUBE NUMBER WHILE MANUAL DISPENSE')
				else:
					self.tubeStatusUpdate()
					self.warning("Coins Dispensed Manually type:%d count: %d InTubeCount: %d"%(coin_type,count,coins_in_tube))
					self.EventPaymentManualDispense(self.able['group'],self.able['name'],t['nominal'],count)					
				return 2
			elif 0x40==(aEvent[0]&0xC0):
				route=(aEvent[0]>>4)&3
				coin_type=aEvent[0]&15
				coins_in_tube=aEvent[1]
				t=self.getTubeNominal(coin_type)
				if not t:
					self.critical('INVALID TUBE NUMBER WHILE ROUTING')
				else:
					self.tubeStatusUpdate()
					t=self.getTubeNominal(coin_type)
					if 0==route:
						route_txt="CASH_BOX"
						ru_txt=u'В ЯЩИК'
						self.EventPaymentNominalStacked(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					elif 1==route:
						route_txt="TUBES"
						ru_txt=u'В ТУБЫ'
						self.EventPaymentNominalStacked(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					elif 2==route:
						route_txt="NOT_USED"
						ru_txt=u'НИКУДА'
						self.EventPaymentNominalStacked(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					else:
						route_txt="REJECT"
						ru_txt=u'И ВОЗВРАЩЕНА КЛИЕНТУ'
						self.EventPaymentNominalRejected(self.able['group'],self.able['name'],
							self.nominal_to_cents(t['nominal']),route_txt,t['is_bill'],t['is_stack_full'])	
					self.info('Получена монета номиналом %s %s %s'%(t['nominal'],self['currency'],ru_txt))
				return 2
			elif 0x20==(aEvent[0]&0xE0):
				slugs=aEvent[0]&0x1F
				self.EventPaymentSlugs(self.able['group'],self.able['name'],slugs)
			elif 0x01==aEvent[0]:
				self.EventPaymentEscrowLever(self.able['group'],self.able['name'],"[Escrow request] - An escrow lever activation has been detected.")
			elif 0x02==aEvent[0]:
				self.able['status']='BUSY'
				self.able['is_ready']=False
				self.EventPaymentDeviceBusy(self.able['group'],self.able['name'],"[Changer Payout Busy] - The changer is busy activating payout devices.")
			elif 0x03==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"[No Credit] - A coin was validated but did not get to the place in the system when credit is given.")
			elif 0x04==aEvent[0]:
				self.able['status']='FAULT'
				self.able['is_ready']=False
				self.EventPaymentFault(self.able['group'],self.able['name'],aEvent[0],"[Defective Tube Sensor] - The changer has detected one of the tube sensors behaving abnormally.")
			elif 0x05==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"[Double Arrival] - Two coins were detected too close together to validate either one.")
			elif 0x06==aEvent[0]:
				self.able['status']='FAULT'
				self.able['is_ready']=False
				self.EventPaymentFault(self.able['group'],self.able['name'],aEvent[0],"[Acceptor Unplugged] - The changer has detected that the acceptor has been removed.")
			elif 0x07==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"[Tube Jam] - A tube payout attempt has resulted in jammed condition.")
			elif 0x08==aEvent[0]:
				self.able['status']='FAULT'
				self.able['is_ready']=False
				self.EventPaymentFault(self.able['group'],self.able['name'],aEvent[0],"[ROM checksum error] - The changers internal checksum does not match the calculated checksum.")
			elif 0x09==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"Not Used now [Coin Routing Error] - A coin has been validated, but did not follow the intended routing.")
			elif 0x0A==aEvent[0]:
				self.able['status']='BUSY'
				self.able['is_ready']=False
				self.EventPaymentDeviceBusy(self.able['group'],self.able['name'],"[Changer Payout Busy] - The changer is busy activating payout devices.")
			elif 0x0B==aEvent[0]:
				self.able['status']='RESETED'
				self.able['is_ready']=False				
				self.warning("JUST RESET")
			elif 0x0C==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"[Coin Jam] - A coin(s) has jammed in the acceptance path.")
			elif 0x0D==aEvent[0]:
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"[Possible Credited Coin Removal] – There has been an attempt to remove a credited coin.")
			elif 0x00==aEvent[0]:
				self.able['status']='READY'
				self.able['is_ready']=True
				self['accept']['coin']=True
				self['dispense']['coin']=True
			else:
				self.error("COIN UNKNOWN STATUS:%02X"%aEvent[0])
				self.able['status']='ERROR'
				self.EventPaymentError(self.able['group'],self.able['name'],aEvent[0],"COIN UNKNOWN STATUS:%02X"%aEvent[0])

		except Exception as e:
			self.exception('ERROR IN POLL PARSER, EVENT: {e}: {err}',e='%s'%aEvent,err='%s'%format_exc())
		return 1

	def diagEvent(self,response):
		_epl=[]
		for i in range(0,len(response),2):
			st=(response[i]<<8)|response[i+1]
			_epl+=[st]
			if 0x0300==st:
				self.able['is_ready']=True
				self['accept']['coin']=True
				self['dispense']['coin']=True
				if self.able['status']!='READY':
					self.able['status']='READY'
					self.EventPaymentReady(self.able['group'],self.able['name'])
			else:
				if 0x0600!=st:
					self['dispense']['coin']=False
					self['accept']['coin']=False
					self.able['is_ready']=False
				if 0x0100==st:
					self.info("Changer powering up / initialization")
				elif 0x0200==st:
					self.info("Changer powering down")
				elif 0x0400==st:
					self.info("Действия с клавиатурой")
				elif 0x0510==st:
					self.debug("Manual Fill / Payout active")
				elif 0x0520==st:
					self.debug("New Inventory Information Available")
				elif 0x0600==st:
					#log.debug("Inhibited by VMC")
					self.able['status']='DISABLED'
				elif 0x1000==st:
					self.able['status']='FAULT'
					self.able['is_ready']=False
					self.EventPaymentFault(self.able['group'],self.able['name'],st,"NON-SPECIFIC ERROR")
				elif 0x1003==st:
					self.able['status']='FAULT'
					self.able['is_ready']=False
					self.EventPaymentFault(self.able['group'],self.able['name'],st,"ПИТАНИЕ НЕСТАБИЛЬНО!!!")
				elif 0x1000==(st&0xFF00):
					self.able['status']='FAULT'
					self.able['is_ready']=False
					self.EventPaymentFault(self.able['group'],self.able['name'],st,"КРИТИЧЕСКАЯ ОШИБКА")
				elif 0x1100==(st&0xFF00):
					self.able['status']='ERROR'
					self.EventPaymentError(self.able['group'],self.able['name'],st,"Discriminator module error:%d"%(st&255))
				elif 0x1200==(st&0xFF00):
					self.able['status']='ERROR'
					self.EventPaymentError(self.able['group'],self.able['name'],st,"Accept gate module error:%d"%(st&255))
				elif 0x1300==(st&0xFF00):
					self.able['status']='ERROR'
					self.EventPaymentError(self.able['group'],self.able['name'],st,"Separator module error:%d"%(st&255))
				elif 0x1400==(st&0xFF00):
					self.able['status']='ERROR'
					self.EventPaymentError(self.able['group'],self.able['name'],st,"Dispenser module error:%d"%(st&255))
				elif 0x1500==(st&0xFF00):
					self.able['status']='ERROR'
					self.EventPaymentError(self.able['group'],self.able['name'],st,"Coin Cassette / tube module error:%d"%(st&255))
				else:
					self.able['status']='FAULT'
					self.able['is_ready']=False
					self.EventPaymentFault(self.able['group'],self.able['name'],st,"UNKNOWN STATUS: %04X"%st)
		_jdp=json.dumps(_epl)
		if self.pepol!=_jdp:
			self.pepol=_jdp					

	def payoutProcessing(self):
		if self.payout_amount:
			amount=self.payout_amount
			self.payout_amount=False
			if amount and amount>0:
				was_amo=self['dispense_amount']['coin']
				self.info('Монет на начало выдачи сдачи: %s'%self.nominal_to_text_with_currency(self['dispense_amount']['coin']))
				dpc=int(10**self['currency_decimals'])
				amount=int(amount/dpc)
				self.debug('Payout request %s'%(amount))
				#Округление в пользу клиента
				xamo=self.centsToInternal(amount)
				damo=self.internalToCents(amount)
				if (damo<amount):
					xamo+=1
				amount=xamo
				res_amo=0
				try:
					self.EventPayoutStarted(self.able['group'],self.able['name'],self.internalToCents(amount)*dpc)
					try:
						while amount>0:
							amo=amount if amount<255 else 255
							ts=time.time()
							succ=False
							ft=True
							while (ts+5.0)>time.time():
								x=self.alternativePayout(amo)
								if ft:
									ft=False
									if x is False:
										break
								if not (x is True):
									x=self.payoutReport()
									if x is True:
										succ=True
										break
								else:
									succ=True
									break
								self.polling()
								if self.able['status'] in ['BUSY']:
									succ=True
									break
								time.sleep(0.1)
							if not succ:
								break
							ts=time.time()
							amo=0
							while (ts+60.0)>time.time():
								v=self.payoutPoll()
								if v is True:
									break
								elif v:
									po_am=0
									for i in range(len(v)):
										t=self.getTubeNominal(i)
										po_am+=self.centsToInternal(t['nominal'])*v[i]
									amo+=po_am
									if po_am>0:
										self.EventPayoutProgress(self.able['group'],self.able['name'],self.internalToCents(po_am)*dpc)
							if amo<=0:
								break
							ts=time.time()
							summ=0
							xuc=False
							while (ts+5.0)>time.time():
								v=self.payoutReport()
								if (v is True) or (v is False):
									self.critical('Не удалось получить отчет о выдече сдачи, устройство занято')
								elif v:
									for i in range(len(v)):
										if (v[i])>0:
											t=self.getTubeNominal(i)
											if t:
												summ+=self.centsToInternal(t['nominal'])*v[i]
									xuc=True
									break
							if summ!=amo:
								self.critical("Расхождение в отчете выдачи сдачи %s!=%s"%(amo,summ))
								if xuc:
									amo=summ
								xuc=False

							res_amo+=amo
							amount-=amo

							if not xuc:
								break
					except Exception as eee:
						self.exception(eee)
				finally:
					res_amo=int(self.internalToCents(res_amo)*dpc);					
					xamo=int(self.internalToCents(xamo)*dpc);					
					self.EventPayoutFinished(self.able['group'],self.able['name'],res_amo,xamo)
					self.tubeStatusUpdate()
					self.info('Монет на конец выдачи сдачи: %s'%self.nominal_to_text_with_currency(self['dispense_amount']['coin']))
					if (self['dispense_amount']['coin']+res_amo)!=was_amo:
						self.critical('Расхождение количества монет в тубах после выдачи сдачи. Было: %s Выдано+Стало: %s'%(
							self.nominal_to_text(was_amo),self.nominal_to_text(self['dispense_amount']['coin']+res_amo)))



try:
	l=SgnMDBcoin()
	l.warning('SGN COIN STARTED')
	#l.warning('SgnMDBcoin Base Classes: %s'%(SgnMDBcoin.__bases__,))
	#l.warning('SgnMDBcoin MRO: %s'%(type.mro(SgnMDBcoin)))
	l.join()
finally:
	print("FINALLY!")
	cleanup_resources()
