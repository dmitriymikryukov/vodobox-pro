from IPC import *
from interfaces.hardware.iface_serial import ifaceSERIAL
import time

class ifaceMDB(ifaceSERIAL):

	def __init__(self):
		ifaceSERIAL.__init__(self)
		self.buf=bytes()
			
	def mdb_send_command_bytes(self,addr,data):
		self.buf=bytes()		
		x=b'M'+bytes([addr|data[0]]).hex().upper().encode()+bytes(data[1:]).hex().upper().encode()+b'\n'
		self.debug('raw tx: %s'%(x,))
		try:
			self.serial_tx(x)
		except:
			self.mdb_receive(addr,None)			
			self.serial_connect(self['mdb']['port'])
		else:
			xt=time.time()
			while (xt+0.5)>time.time():
				x=self.serial_rx()
				if (x is None):
					self.buf=bytes()
					break
				else:
					if len(x)>0:
						xt=time.time()
						self.buf+=x
						while (len(self.buf) and self.buf[0]!=ord('R')):
							self.buf=self.buf[1:]
						if 10 in self.buf:
							x=self.buf.split(b'\n')
							self.buf=x[0]
							break
			self.sp.flushInput()

			self.debug('raw rx:%s'%(self.buf,))

			if not self.buf or len(self.buf)<1:
				res=None
			elif b'N' in self.buf:
				res=False
			elif b'R' == self.buf:
				res=True
			else:
				try:
					res=bytes.fromhex(self.buf[1:].decode())
					if len(res)==1:
						if res[0]==0:
							res=True
						elif res[0]==255:
							res=False
				except Exception as e:
					self.exception(e) 
					res=None

			self.mdb_receive(addr,res)


