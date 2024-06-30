from interfaces.iface import InterfaceCommon
import threading
from IPC import *

class ifacePAYMENTslave(InterfaceCommon):
	
	def __init__(self,name,group,cashless=False,remote=False,coupon=False,bank=False,without_known_price=False):

		self.able=dict(
				name=name,
				group=group,
				cashless=cashless,
				remote=remote,
				coupon=coupon,
				bank=bank,
				without_known_price=without_known_price,
				status='DISCONNECTED',
				can_be_used=False,
				is_ready=False,
				is_enabled=False,
				fixed_nominals=False,
			)


		"""		
		#print ('PS: %s'%self['payment_method'])

		#with self.lock:
		if not (group in self['payment_method']):
			self['payment_method'][group]=dict()
		if not (name in self['payment_method'][group]):
			self['payment_method'][group][name]=dict(
					name=name,
					group=group,
					cashless=cashless,
					remote=remote,
					coupon=coupon,
					bank=bank,
					without_known_price=without_known_price,
					status='DISCONNECTED',
					can_be_used=False,
					is_ready=False,
					is_enabled=False,
					fixed_nominals=False,
				)
		else:
			raise AlreadyExists('%s-%s payment_method alreary registered, %s'%(group,name,self['payment_method']))

		self.able=self['payment_method'][group][name]
		"""

	def ps_reg(self):
		group=self.able['group']
		name=self.able['name']
		if not (group in self['payment_method'].keys()):
			self['payment_method'][group]={name:self.able}
		elif not (name in self['payment_method'][group].keys()):
			self['payment_method'][group][name]=self.able
		else:
			raise AlreadyExists('%s-%s payment_method alreary registered, %s'%(group,name,self['payment_method']))
		self.able=self['payment_method'][group][name]

