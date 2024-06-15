from .iface_coin import ifaceCOINipc
from .iface_mdb_slave import ifaceMDBslave
from .iface_payment_slave import ifacePAYMENTslave
import threading
from IPC import *

from interfaces.countrycode import getCCbcd

class ifaceMDBcoin(ifaceCOINipc,ifaceMDBslave,ifacePAYMENTslave):
	
	def __init__(self,addr=8):
		ifaceCOINipc.__init__(self)	
		ifacePAYMENTslave.__init__(self,'COIN','CASH',cashless=False,remote=False,coupon=False,bank=False,without_known_price=True)
		ifaceMDBslave.__init__(self,addr)
		self.decimal_places=2
		self.scaling_factor=1

	def started(self):
		self.ps_reg()

	def poll(self):
		return self.cmd([0x03])

	def reset(self):
		return self.cmd([0x00])

	def centsToInternal(self,v):
		dp=int(10**self.decimal_places)
		return v/dp/self.scaling_factor

	def internalToCents(self,v):
		dp=int(10**self.decimal_places)
		return v*dp*self.scaling_factor

	def setup(self):
		response=self.cmd([0x01])
		if response:
			r=dict(
				level=response[0],
				country_code=getCCbcd((int(response[1])<<8)|response[2]),
				scaling_factor=response[3],
				decimal_places=response[4],
				coin_tube_routing_msk=(int(response[5])<<8)|response[6],
				coin_type_credit=response[7:]
			)
			self.decimal_places=r['decimal_places']
			self.scaling_factor=r['scaling_factor']
			return r
		return response

	def identification(self):
		response=self.cmd([7,0])
		if response:
			try:
				return dict(
					manufacturer=''.join([chr(x) for x in response[0:3]]),
					serial=''.join([chr(x) for x in response[3:15]]),
					model=''.join([chr(x) for x in response[15:27]]),
					software=(response[27]<<8)|response[28],                    
					features=(response[29]<<24)|(response[30]<<16)|(response[31]<<8)|response[32]
				)
			except:
				self.exception('CANNOT PARSE: %s'%response)
				return None
		return response

	def tubeStatus(self):
		response=self.cmd([0x02])
		if response:
			try:
				return dict(
					tube_full_msk=(response[0]<<8)|response[1],
					coin_count=response[2:]
				)
			except:
				self.exception('CANNOT PARSE: %s'%response)
				return None
		return response

	def diagnostic(self):
		return self.cmd([0x07,0x05])

	def cmdEnableNominals(self,tubes):
		coin_enable_msk=0
		manual_dispense_enable_msk=0
		for x in tubes:
			coin_enable_msk|=1<<x
		return self.cmd([
				0x04, 
				(coin_enable_msk<<8)&255, coin_enable_msk&255, 
				(manual_dispense_enable_msk<<8)&255, manual_dispense_enable_msk&255
			])	#COIN ENABLE

	def featuresEnable(self,features):
		return self.cmd([0x07,0x01,(features>>24)&255,(features>>16)&255,(features>>8)&255,features&255])

	def alternativePayout(self,amount):
		return self.cmd([0x07,0x02,amount])

	def payoutReport(self):
		return self.cmd([0x07,0x03])

	def payoutPoll(self):
		return self.cmd([0x07,0x04])
