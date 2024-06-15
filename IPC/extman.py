import multiprocessing
from multiprocessing.managers import DictProxy, ListProxy, BaseProxy, SyncManager, AutoProxy
import threading
import sys,time,os
from traceback import format_exc

_registry=dict()

class subscribe:
    subscribers=dict()

    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        #print("Subscribe to %s.%s %s"%(owner.__name__,name,os.getpid()))
        #owner._event_methods.append(self.fn)
        n=owner.__name__
        if not (n in subscribe.subscribers):
            subscribe.subscribers[n]=dict()
        m=sys.modules[owner.__module__].__file__
        if not (m in subscribe.subscribers[n]):
            subscribe.subscribers[n][m]=dict()
        subscribe.subscribers[n][m][name]=self.fn

        #owner._event_methods[name]=self.fn
        self.fn.class_name = owner.__name__
        # then replace ourself with the original method
        setattr(owner, 'event_'+name, self.fn)
        delattr(owner, name)

def extract_subscribers(cls):
    res=dict()
    mro=[x.__name__ for x in type.mro(cls.__class__)]
    for s in subscribe.subscribers:
        if s in mro:
            for f in subscribe.subscribers[s]:
                for m in subscribe.subscribers[s][f]:
                    res[m]=subscribe.subscribers[s][f][m]
    return res


class sgnIPC(object):

    def __init__(self):
        self.name=ipc_name
        self.gdict=ipc_gdict
        self.container=self.gdict['service_container'][self.name]
        t=threading.Thread(target=self._doSubscribe)
        t.start()

    def _doSubscribe(self):
        self.container['w_init'].wait()        
        try:
            global _registry
            #print(self.__class__.__name__)
            self._events=extract_subscribers(self)
            for x in self._events:
                _registry[x]=dict(owner=self,fn=self._events[x])
                #print("REG: %s.%s"%(self.name,x))
                #with self.gdict['lock']:
                if not (x in self.gdict['events']): 
                    self.gdict['events'][x]=1
                else:
                    self.gdict['events'][x]+=1
                self.container['events'][x]=True
            #print ("REGS!")
            self.container['status']='ALIVE'
        finally:
            self.container['w_start'].set()

    def __getattr__ (self, name):
        #print("GETATTR %s"%(name))
        if (name in self.gdict['events']):
            v=self.gdict['events'][name]
            if v==1 and (name in self._events):
                def sicall(*args,**kwargs):
                    return (getattr(self,'event_%s'%name)(*args,**kwargs),)
                return sicall
            else:
                def sucall(*args,**kwargs):
                    svc=[]
                    with self.gdict['lock']:
                        for x in self.gdict['service_container'].keys():
                            if name in self.gdict['service_container'][x]['events']:
                                svc.append(x)
                                if (len(svc)>=v):
                                    break
                    resl=[]
                    for x in svc:
                        try:
                            r=self.gdict['service_container'][x]['ipc'].call(name,*args,**kwargs)
                            resl.append(r)
                        except Exception as e:
                            print(format_exc(e))
                    return tuple(resl)
            return sucall
        else:
            raise NotImplementedError('%s is not subscibed'%name)

    def __getitem__ (self, name):
        return self.gdict['name']

    def __setitem__ (self, name,value):
        self.gdict['name']=value

    #def __getattribute__ (self, name):
    #    print("GETATTRIBUTE %s"%(name))
    #    return self.event_opa

