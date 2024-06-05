import sys
sys.path.insert(0, '..')


from IPC import *


import time

l=Locker('xyu')

with l:
	print('AAA')
	while True:
		pass

		