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

from IPC.extman import subscribe, sgnService

from .Exceptions import *

def cleanup_resources():
	pass
