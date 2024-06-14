import multiprocessing
from multiprocessing.managers import DictProxy, ListProxy, BaseProxy, SyncManager
import threading
import sys,time,os
from traceback import format_exc

_lsi=ListProxy.__setitem__
_dsi=DictProxy.__setitem__


def list__repr__(self):
        dv=''
        res='['
        items=list(self)
        for v in items:
            res+=("%s*%s"%(dv,v.__repr__()))
            dv=', '
        res+=']'
        return res

def dict__repr__(self):
        dv=''
        res='{'
        items=list(self.items())
        for n,v in items:
            res+=("%s%s:*%s"%(dv,n.__repr__(),v.__repr__()))
            dv=', '
        res+='}'
        return res


def list__setitem__(self,k,v):
        if isinstance(v,dict):
            _v=v
            v=self._manager.dict()
            for x in _v:
                v[x]=_v[x]
        elif isinstance(v,list):
            _v=v
            v=self._manager.list()
            for x in _v:
                v.append(x)
        return _lsi(self,k,v)

def dict__setitem__(self,k,v):
        if isinstance(v,dict):
            _v=v
            v=self._manager.dict()
            for x in _v:
                v[x]=_v[x]
        elif isinstance(v,list):
            _v=v
            v=self._manager.list()
            for x in _v:
                v.append(x)
        return _dsi(self,k,v)


_registry=dict()

class sgnMpShareClass(BaseProxy):
    def __init__(self):
        self.var = 0
        print("INIT %s"%os.getpid())

    def set(self, value):
        print("SET %s"%os.getpid())
        self.var = value

    def get(self):
        print("GET %s"%os.getpid())
        return self.var

    def call(self,f,*args,**kwargs):
        #print("CALL %s"%os.getpid())
        #print(args)
        #print(_registry)
        if (f in _registry):
            return _registry[f]['fn'](_registry[f]['owner'],*args,**kwargs)

class subscribe:
    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        #print("Subscribe to %s.%s"%(owner.__name__,name))
        #owner._event_methods.append(self.fn)
        n=owner.__name__
        m=sys.modules[owner.__module__].__file__
        _registry[name]=dict(owner=owner,module=m,fn=self.fn)
        #owner._event_methods[name]=self.fn
        self.fn.class_name = m
        # then replace ourself with the original method
        setattr(owner, 'event_'+name, self.fn)
        delattr(owner, name)


class sgnSyncManager(SyncManager):
    pass

sgnSyncManager.register('sgnMpShareClass',sgnMpShareClass)



class sgnMpReg(object):
    def __init__(self,*args,**kwargs):
        self.manager=sgnSyncManager()#multiprocessing.Manager()
        print(type(self.manager))
        #self.manager.register('dict',sgnMpDict, sgnMpDict)
        #self.manager.register('list',sgnMpList, sgnMpList)
        DictProxy.__repr__=DictProxy.__str__=dict__repr__
        ListProxy.__repr__=ListProxy.__str__=list__repr__
        DictProxy.__setitem__=dict__setitem__
        ListProxy.__setitem__=list__setitem__
        #self.manager.sh=self.manager.ShareClass()
        print (self.manager._registry)


class sgnMpWorker(multiprocessing.Process):
    
    def __init__(self,name,gdict,path):
        super().__init__()
        self.name=name
        self.gdict=gdict
        self.path=path
        self.stopping=False

    def shutdown(self):
        self.gdict['control']['shutdown']=True
        
    def stop(self):
        self.stopping=True

    def run(self):
        print('Hello %s'%self.name)
        self.service_base=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
        self.services_dir=os.path.join(self.service_base,'services')
        p=os.path.abspath(os.path.join(self.services_dir,self.path))
        self.base_path=os.path.dirname(p)
        with sgnMpReg().manager as manager:
            container=manager.dict({
                'name':self.name,
                'pid':os.getpid(),
                'status':'STARTING',
                'main':p,
                'basepath':self.base_path,
                'ipc':manager.sgnMpShareClass()
                })            
            self.gdict['service_container'][self.name]=container
            container['ipc'].set(os.getpid())
            try:
                sys.path.insert(0, self.service_base)
                sys.path.insert(0, self.base_path)
                try:
                    x='import %s'%(os.path.basename(self.path[:-3]))
                    print (x)
                    #exec(x)
                except Exception as e:
                    print(format_exc())
                    print(sys.path)
                    container['status']='DIED'
                else:
                    container['status']='STARTED'
                print(self.gdict)
                print(self.gdict['xyu'])
                self.gdict['zhopa']=manager.dict({'a':1})
                print(self.gdict)
                while not self.gdict['control']['shutdown'] and not self.stopping:
                    time.sleep(0.5)
                container['status']='STOPPING'
            finally:
                try:
                    container['status']='DIED'
                except:
                    pass
                try:
                    del self.gdict['service_container'][self.name]
                except:
                    pass


class test(object):

    @subscribe
    def opa(self,a):
        print("OPA %s"%os.getpid())
        print(a)
        return 123

if __name__ == '__main__':
    multiprocessing.freeze_support()
    with sgnMpReg().manager as manager:
        d = manager.dict()
        d['control']=manager.dict({'shutdown':False})
        d['service_container']=manager.dict()
        d['xyu']=manager.dict()
        d['xyu']['pizda']=123
        d['a']=dict(a=1,b=2,c=dict(x=[1,2,3,[4,5,6],{'c':'d'}]))
        p = sgnMpWorker('logger',d,'logger/logger.py')
        p.start()
        p = sgnMpWorker('settings',d,'settings/settings.py')
        p.start()
        time.sleep(1)
        print(d)
        print(d['service_container']['logger']['ipc'].get())
        print(d['service_container']['settings']['ipc'].get())
        d['service_container']['logger']['ipc'].set(1)
        d['service_container']['settings']['ipc'].set(2)
        print(d['service_container']['logger']['ipc'].get())
        print(d['service_container']['settings']['ipc'].get())
        print(d['service_container']['settings']['ipc'].call('opa','hello'))
        time.sleep(1)
        p.shutdown()
        #d['service_container']['logger']['methods']['stop']()
        p.join()

