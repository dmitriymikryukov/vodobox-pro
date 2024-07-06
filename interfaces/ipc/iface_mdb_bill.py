from .iface_bill import ifaceBILLipc
from .iface_mdb_slave import ifaceMDBslave
from .iface_payment_slave import ifacePAYMENTslave
import threading
from IPC import *

from interfaces.countrycode import getCCbcd

class ifaceMDBbill(ifaceBILLipc,ifaceMDBslave,ifacePAYMENTslave):
	
	def __init__(self,addr=0x30):
		ifaceBILLipc.__init__(self)	
		ifacePAYMENTslave.__init__(self,'BILL','CASH',cashless=False,remote=False,coupon=False,bank=False,without_known_price=True)
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
                country_code=getCCbcd((response[1] << 8) | response[2]),
                scaling_factor=(response[3] << 8) | response[4],
                decimal_places=response[5],
                stacker_capacity=(response[6] << 8) | response[7],
                bill_security_levels=(response[8] << 8) | response[9],
                escrow_capability=response[10],
                bill_type_credit=response[11:]
			)
			self.decimal_places=r['decimal_places']
			self.scaling_factor=r['scaling_factor']
			return r
		return response

	def identification(self,level=2):
		if level>1:			
			try:
				response=self.cmd([7,2])
				if response:
					return dict(
	                    manufacturer=''.join([chr(x) for x in response[0:3]]),
	                    serial=''.join([chr(x) for x in response[3:15]]),
	                    model=''.join([chr(x) for x in response[15:27]]),
	                    software=(response[27] << 8) | response[28],
						features=(response[29]<<24)|(response[30]<<16)|(response[31]<<8)|response[32],
					)
			except:
				flt=True
		else:
			flt=True
		if flt:
			response=self.cmd([7,0])
			if response:
				try:
					return dict(
	                    manufacturer=''.join([chr(x) for x in response[0:3]]),
	                    serial=''.join([chr(x) for x in response[3:15]]),
	                    model=''.join([chr(x) for x in response[15:27]]),
	                    software=(response[27] << 8) | response[28],
	                    features=0,
					)
				except:
					self.exception('CANNOT PARSE: %s'%response)
					return None
		return response

	def tubeStatus(self):
		response=self.cmd([0x06])		
		if response:
			return dict(
				is_stack_full=True if response[0]&128 else False,
				bills_in_stack=response[1]|(int(response[0])&127<<8)
				)
		return response

	def diagnostic(self):
		pass

	def cmdEnableNominals(self,tubes,escrow):
		for x in tubes:
			bill_enable_msk|=1<<x
		for x in wscrow:
			escrow_enable_msk|=1<<x
		return self.cmd([0x04,(bill_enable_msk>>8&255),bill_enable_msk&255,(escrow_enable_msk>>8&255),escrow_enable_msk&255])		

	def featuresEnable(self,features):
		pass
