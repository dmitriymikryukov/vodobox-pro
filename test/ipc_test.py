import sys
sys.path.insert(0, '..')


from IPC import *


import time

try:

	class MyClass(sgnIPC):
		link_name = 'shared-class'

		def __init__(self):
			super().__init__()

		@subscribe
		def test_event(self):
			self.info("test event")
			aaa

	first = MyClass()
	second = MyClass()

	first['something'] = 'some value'

	first.info('%s%s%s'%(first['something'], ' == ', second['something']))


	first.test_event()
	second.test_event()

	first.debug("DEBUG")
	second.info("INFO")
	second.error("ERROR")
	first.critical("CRITICAL")

	"""
	first.warning("\n\n!!!1 done !!!!")

	try:
		a=b
	except:
		second.exception("HELLO")
	"""

	time.sleep(3.0)

	first.close()
	second.close()

finally:
	"""
	try:
		sgnDict.unlink_by_name('sgnipcbroker',ignore_errors=True)
	except:
		pass
	try:
		sgnDict.unlink_by_name('sgnipc',ignore_errors=True)
	except:
		pass
	"""
	pass
