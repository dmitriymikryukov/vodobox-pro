import multiprocessing
from multiprocessing.managers import DictProxy, ListProxy
import threading
import sys,time,os
from traceback import format_exc

class sgnMpDict(DictProxy):
    #def __init__(self,*args,**kwargs):
    #    DictProxy.__init__(self,*args,**kwargs)

    def __repr__(self):
        dv=''
        res='{'
        items=list(self.items())
        for n,v in items:
            res+=("%s%s:*%s"%(dv,n.__repr__(),v.__repr__()))
            dv=', '
        res+='}'
        return res

    def __setitem__(self,k,v):
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
        return super().__setitem__(k,v)

    def __str__(self):
        return self.__repr__()


class sgnMpList(ListProxy):
    #def __init__(self,*args,**kwargs):
    #    ListProxy.__init__(self,*args,**kwargs)

    def __repr__(self):
        dv=''
        res='['
        items=list(self)
        for v in items:
            res+=("%s*%s"%(dv,v.__repr__()))
            dv=', '
        res+=']'
        return res

    def __setitem__(self,k,v):
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
        return super().__setitem__(k,v)

    def __str__(self):
        return self.__repr__()


class sgnMpReg(object):
    def __init__(self,*args,**kwargs):
        self.manager=multiprocessing.Manager()
        self.manager.register('dict',sgnMpDict, sgnMpDict)
        self.manager.register('list',sgnMpList, sgnMpList)


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
                })            
            self.gdict['service_container'][self.name]=container
            try:
                sys.path.insert(0, self.service_base)
                sys.path.insert(0, self.base_path)
                try:
                    x='import %s'%(os.path.basename(self.path[:-3]))
                    print (x)
                    exec(x)
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
        time.sleep(1)
        print(d)
        p.shutdown()
        #d['service_container']['logger']['methods']['stop']()
        p.join()

