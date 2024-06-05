from IPC import *
from .iface_hw import ifaceHardware
from serial import Serial as pySerial
import serial
import time

class ifaceSERIAL(ifaceHardware):
	
	def __init__(self):
		ifaceHardware.__init__(self)
		self.sp=None	

	def serial_connect(self,port):
		if self.sp:
			try:
				self.sp.close()
			except:
				pass
		self.sp = pySerial(port,
		              timeout=0.01,
		              xonxoff=False,
		              rtscts=False,
		              baudrate=57600,
		              parity=serial.PARITY_NONE,
		              stopbits=serial.STOPBITS_ONE,
		              bytesize=serial.EIGHTBITS)
		self.sp.flushInput()
		self.sp.flushOutput()
		self.sp.write(b'MM\n')
		self.sp.flush()
		time.sleep(0.2)
		try:
			x=self.sp.readline()
		except:
			self.error('CANNOT READ reset')
		self.sp.flushInput()
		self.sp.flushOutput()
		self.info('MDB reset done')		


	def serial_tx(self,data):
		self.sp.flushInput()
		self.sp.flushOutput()		
		try:
			self.sp.write(data)
			self.sp.flush()
		except:
			self.serial_connection_lost()

	def serial_rx(self):
		try:
			return self.sp.read(128)
		except Exception as e:
			self.exception(e)
			self.serial_connection_lost()
		return None

	def serial_connection_lost(self):
		raise NotImplementedError()
