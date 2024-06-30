#
# UltraDict
#
# A sychronized, streaming Python dictionary that uses shared memory as a backend
#
# Copyright [2022] [Ronny Rentner] [ultradict.code@ronny-rentner.de]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#from .shms import sgnDict,sgnQueue,Locker,cleanup_resources,remove_shm_from_resource_tracker
#from .ipcdict import IPCdict as sgnDict,IPClist as sgnQueue#,Locker,cleanup_resources,remove_shm_from_resource_tracker
#from .sgnIPC import sgnIPC,subscribe

#from .sgnService import sgnService

import os,sys

def clearPathSymbols(paths, keepers=None):
	"""
	Removes path symbols from the environment.

	This means I can unload my tools from the current process and re-import them
	rather than dealing with the always finicky reload()

	I use directory paths rather than module names because it gives me more control
	over what is unloaded

	*Make sure to close any UI's you're clearing before using this function*

	Parameters
	----------
	paths : list
		List of directory paths that will have their modules removed
	keepers : list, optional
		List of module names that will not be removed
	"""

	## TODO ## Possibly emit a signal to close my custom UI's
	keepers = keepers or []
	paths = [os.path.normcase(os.path.normpath(p)) for p in paths]

	for key, value in sys.modules.items():
		if ('IPC' in key) or ('extman' in key):
			print('%s=%s'%(key,value))
		protected = False

		# Used by multiprocessing library, don't remove this.
		if key == '__parents_main__':
			protected = True

		# Protect submodules of protected packages
		if key in keepers:
			protected = True

		ckey = key
		while not protected and '.' in ckey:
			ckey = ckey.rsplit('.', 1)[0]
			if ckey in keepers:
				protected = True

		if protected:
			continue

		try:
			packPath = value.__file__
		except AttributeError:
			continue

		try:
			packPath = os.path.normcase(os.path.normpath(packPath))

			isEnvPackage = any(packPath.startswith(p) for p in paths)
		except:
			isEnvPackage = False

		if isEnvPackage:
			print('UNLOAD module: %s'%key)
			sys.modules.pop(key)

clearPathSymbols('IPC')

from IPC.extman import subscribe, sgnService

from .Exceptions import *

def cleanup_resources():
	pass

