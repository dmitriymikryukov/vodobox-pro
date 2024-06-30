import multiprocessing
from multiprocessing.managers import DictProxy, ListProxy, BaseProxy, SyncManager, AutoProxy
import threading
import sys,time,os
import traceback
from traceback import format_exc

_registry=dict()

print ("LOADING EXTMAN %a"%os.getpid())

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

    def started(self):
        pass

    def _doSubscribe(self):
        print('Waiting init...')
        self.container['w_init'].wait()        
        print('Init wait done')
        try:
            global _registry
            #print(self.__class__.__name__)
            self._events=extract_subscribers(self)
            for x in self._events:
                _registry[x]=dict(owner=self,fn=self._events[x])
                print("REG%s: %s.%s"%(os.getpid(),self.name,x))
                #with self.gdict['lock']:
                if not (x in self.gdict['events']): 
                    self.gdict['events'][x]=1
                else:
                    self.gdict['events'][x]+=1
                self.container['events'][x]=True
            #print ("REGS!")
            self.container['status']='ALIVE'
            self.started()
        finally:
            self.container['w_start'].set()

    def __getattr__ (self, name):
        #print("GETATTR %s"%(name))
        self.container['w_start'].wait()
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
        return self.gdict[name]

    def __setitem__ (self, name,value):
        self.gdict[name]=value

    #def __getattribute__ (self, name):
    #    print("GETATTRIBUTE %s"%(name))
    #    return self.event_opa

class sgnService(sgnIPC):

    def join(self):
        while (self.container['status'] in ['ALIVE','STARTED']):
            time.sleep(0.5)

    def getName(self):
        return self.name

    def has_subscribers(self,name):
        try:
            if not (self.container['status'] in ['ALIVE','STARTED']):
                return False
        except:
            return False
        else:
            return True

    def suca_form(self,t,txt):
        ta=[]
        mn='[%s]'%os.path.basename(self.getName())+'                '
        mn=mn[:16]
        t=t+':               '
        t=t[:10]
        for x in txt.split('\n'):
            if len(x):
                ta.append('%s %s %s'%(mn,t,x))
        return '\n'.join(ta)

    def exception(self,e):
        try:
            if isinstance(e, Exception):
                txt=''.join(traceback.format_exception(e,sys.exc_info()[1],sys.exc_info()[2])) 
            else:
                txt=e+'\n'
                txt+=traceback.format_exc()
            if self.has_subscribers('exception_handler'):
                self.exception_handler(self.getName(),txt)
            else:
                print(self.suca_form('EXCEPTION',"EXEPTION HANDLER has no subscribers:"))
                print(self.suca_form('EXCEPTION',txt))
                print("")
        except:
            print(self.suca_form('EXCEPTION',traceback.format_exc()))
            print("")

    def failure(self,e):
        self.exception(e)

    def debug(self,txt):
        try:
            if self.has_subscribers('debug_handler'):
                self.debug_handler(self.getName(),txt)
        except:
            self.exception("DEBUG EXEPTION")

    def info(self,txt):
        try:
            if self.has_subscribers('info_handler'):
                self.info_handler(self.getName(),txt)
            else:
                print(self.suca_form('INFO',"INFO HANDLER has no subscribers:"))
                print(self.suca_form('INFO',txt))
        except:
            self.exception("INFO EXEPTION")

    def warning(self,txt):
        try:
            if self.has_subscribers('warning_handler'):
                self.warning_handler(self.getName(),txt)
            else:
                print(self.suca_form('WARNING',"WARNING HANDLER has no subscribers:"))
                print(self.suca_form('WARNING',txt))
        except:
            self.exception("WARNING EXEPTION")

    def warn(self,txt):
        self.warning(txt)

    def error(self,txt):
        try:
            if self.has_subscribers('error_handler'):
                self.error_handler(self.getName(),txt)
            else:
                print(self.suca_form('ERROR',"ERROR HANDLER has no subscribers:"))
                print(self.suca_form('ERROR',txt))
        except:
            self.exception("ERROR EXEPTION")

    def critical(self,txt):
        try:
            if self.has_subscribers('critical_handler'):
                self.critical_handler(self.getName(),txt)
            else:
                print(self.suca_form('CRITICAL',"CRITICAL HANDLER has no subscribers:"))
                print(self.suca_form('CRITICAL',txt))
        except:
            self.exception("CRITICAL EXEPTION")

