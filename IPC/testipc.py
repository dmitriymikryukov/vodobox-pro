from extman import *
import os
#_registry=dict()


print ("LOADIUNG TEST MODULE %a"%os.getpid())

class test(sgnIPC):

    def __init__(self):
        sgnIPC.__init__(self)

    @subscribe
    def opa(self,a):
        print("OPA %s"%os.getpid())
        print(a)
        return 123

    @subscribe
    def zopa(self,a):
        print("ZOPA %s"%os.getpid())
        print(('%s'%a)+(' %s'%self.gdict['service_container']['settings']['ipc'].call('opa','hello')))
        print(self.opa('sass'))
        return 123

