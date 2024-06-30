import multiprocessing
from multiprocessing.managers import DictProxy, ListProxy, BaseProxy, SyncManager, AutoProxy
import threading
import sys,time,os
from traceback import format_exc

from IPC import extman
import threading

_lsi=ListProxy.__setitem__
_dsi=DictProxy.__setitem__


def set_proc_name(newname):
    try:
        newname=newname.encode()
        from ctypes import cdll, byref, create_string_buffer
        libc = cdll.LoadLibrary('libc.so.6')
        buff = create_string_buffer(len(newname)+1)
        buff.value = newname
        libc.prctl(15, byref(buff), 0, 0, 0)
    except:
        pass


def list__repr__(self):
        dv=''
        res='['
        try:
            items=list(self)
            for v in items:
                res+=("%s*%s"%(dv,v.__repr__()))
                dv=', '
        except:
            res+='Exception'
        res+=']'
        return res

def dict__repr__(self):
        dv=''
        res='{'
        try:
            items=list(self.items())
            for n,v in items:
                res+=("%s%s:*%s"%(dv,n.__repr__(),v.__repr__()))
                dv=', '
        except:
            res+='Exception'
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


def sgnMpAutoProxy(*args,**kwargs):
    return AutoProxy(*args,**kwargs)
    

def _xxcall(path,name,gdict):
    container=gdict['service_container'][name]
    try:
        set_proc_name('sgn:%s'%name)    
        service_base=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
        services_dir=os.path.join(service_base,'services')
        p=os.path.abspath(os.path.join(services_dir,path))
        base_path=os.path.dirname(p)
        sys.path.insert(0, service_base)
        sys.path.insert(0, base_path)
        container['status']='STARTED'
        extman.ipc_name=name
        extman.ipc_gdict=gdict
        #print(gdict._manager)
        if not gdict._manager:
            gdict._manager=sgnSyncManager()
            gdict._manager.start()
        try:
            x='import %s'%(os.path.basename(path[:-3]))
            print (x)
            exec(x)
            #import testipc
            #tmp=testipc.test()


            while not gdict['control']['shutdown'] and (container['status'] in ['STARTED','ALIVE']):
                time.sleep(0.5)
            container['status']='STOPPING'
        except Exception as e:
            print(format_exc())
            print(sys.path)
    finally:
        try:
            container['status']='DIED'
            container['w_start'].set()
            container['w_init'].set()        
        except:
            pass


class sgnMpShareClass(object):

    def __init__(self,gdict,path,name):
        self.gdict=gdict
        self.var = 0
        self.name=name
        set_proc_name('sgn:%s'%name)    
        #self._reg=dict()
        #print("INIT MP SHARE %s"%os.getpid())
        t=threading.Thread(target=_xxcall,args=(path,name,self.gdict))
        t.start()

    def set(self, value):
        print("SET %s"%os.getpid())
        self.var = value
        self.gdict['service_container'][self.name]['w_init'].set()        

    def get(self):
        #print("GET %s"%os.getpid())
        return self.var

    def call(self,f,*args,**kwargs):
        #_registry=extman._registry#self._reg
        #print("CALL %s"%os.getpid())
        #print(args)
        #print(extman._registry)
        #print(extman.subscribe.subscribers)
        if (f in extman._registry):
            extman._registry[f]['owner'].name=self.name
            extman._registry[f]['owner'].gdict=self.gdict
            return extman._registry[f]['fn'](extman._registry[f]['owner'],*args,**kwargs)



class sgnSyncManager(SyncManager):
    pass

sgnSyncManager.register('sgnMpShareClass',sgnMpShareClass,sgnMpAutoProxy)



class sgnMpReg(object):
    def __init__(self,*args,**kwargs):
        self.manager=sgnSyncManager()#multiprocessing.Manager()
        #print(type(self.manager))
        #self.manager.register('dict',sgnMpDict, sgnMpDict)
        #self.manager.register('list',sgnMpList, sgnMpList)
        DictProxy.__repr__=DictProxy.__str__=dict__repr__
        ListProxy.__repr__=ListProxy.__str__=list__repr__
        DictProxy.__setitem__=dict__setitem__
        ListProxy.__setitem__=list__setitem__
        #self.manager.sh=self.manager.ShareClass()
        #print (self.manager._registry)

class sgnMpWorker(multiprocessing.Process):
    
    def __init__(self,name,gdict,path):
        super().__init__()
        self.name=name
        self.gdict=gdict
        self.path=path
        self.stopping=False
        self.w_start=multiprocessing.Event()

    def shutdown(self):
        self.gdict['control']['shutdown']=True
        
    def stop(self):
        self.stopping=True

    def start(self):
        super().start()
        self.w_start.wait()

    def run(self):
        set_proc_name('sgn:%s'%self.name)    
        print('Hello %s'%self.name)
        self.service_base=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
        self.services_dir=os.path.join(self.service_base,'services')
        p=os.path.abspath(os.path.join(self.services_dir,self.path))
        self.base_path=os.path.dirname(p)
        with sgnMpReg().manager as manager:
            self._manager=manager
            with self.gdict['lock']:
                container=manager.dict({
                    'name':self.name,
                    'pid':os.getpid(),
                    'status':'STARTING',
                    'main':p,
                    'basepath':self.base_path,
                    'lock':manager.RLock(),
                    'events':manager.dict(),
                    'w_start':manager.Event(),
                    'w_init':manager.Event()
                    })            
                self.gdict['service_container'][self.name]=container
                container['ipc']=manager.sgnMpShareClass(self.gdict,self.path,self.name)
                container['ipc'].set(os.getpid())
                container['w_start'].wait()                
                self.w_start.set()
            try:
                """
                sys.path.insert(0, self.service_base)
                sys.path.insert(0, self.base_path)
                try:
                    x='import %s'%(os.path.basename(self.path[:-3]))
                    print (x)
                    #exec(x)
                    import testipc
                    tmp=testipc.test()

                except Exception as e:
                    print(format_exc())
                    print(sys.path)
                    container['status']='DIED'
                else:
                    container['status']='STARTED'
                """
                while not self.gdict['control']['shutdown'] and not self.stopping and (container['status'] in ['STARTED','ALIVE']):
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



if __name__ == '__main__':
    multiprocessing.freeze_support()
    with sgnMpReg().manager as manager:
        d = manager.dict()
        maindict=d
        d['control']=manager.dict({'shutdown':False})
        d['service_container']=manager.dict()
        d['events']=manager.dict()
        d['lock']=manager.RLock()


        d['xyu']=manager.dict()
        d['xyu']['pizda']=123
        d['a']=dict(a=1,b=2,c=dict(x=[1,2,3,[4,5,6],{'c':'d'}]))
        p1 = sgnMpWorker('logger',d,'logger/logger.py')
        p2 = sgnMpWorker('settings',d,'settings/settings.py')
        p1.start()
        p2.start()
        time.sleep(1)
        print(d)
        print(d['service_container']['logger']['ipc'].get())
        print(d['service_container']['settings']['ipc'].get())
        d['service_container']['logger']['ipc'].set(1)
        d['service_container']['settings']['ipc'].set(2)
        print(d['service_container']['logger']['ipc'].get())
        print(d['service_container']['settings']['ipc'].get())
        print(d['service_container']['settings']['ipc'].call('opa','hello'))
        print(d['service_container']['settings']['ipc'].call('zopa','hello'))
        time.sleep(1)
        p1.shutdown()
        #d['service_container']['logger']['methods']['stop']()
        p1.join()
        p2.join()

