from ipcdict import IPCdict
from multiprocessing import current_process
import time
import random

def main():
    sharable_dict=IPCdict()
    try:
        pid = current_process().pid
        time.sleep(random.randint(0,1000)*0.001)
        print('My pic =', pid)
        sharable_dict[pid] = True
        sharable_dict['xyu%s'%pid] = True
        del sharable_dict['xyu%s'%pid]
        sharable_dict['x']['sub%s'%pid]=False
        sharable_dict['x']['n']+=1
        sharable_dict['x']['z'][0]+=1
        sharable_dict['x']['z'][3][0]+=1
        sharable_dict['x']['z'][3][3]['a']+=1
        sharable_dict['x']['z'][3][3]['c'][0]+=1
        time.sleep(random.randint(0,1000)*0.001)
        print ("%s dict: %s"%(pid,sharable_dict))
        sharable_dict[pid]=False
        time.sleep(random.randint(0,1000)*0.001)
        print ("%s dict: %s"%(pid,sharable_dict))    
        sharable_dict['add'].append('pid:%s'%pid)
        print("pop:%s"%sharable_dict['pop'].pop(-2))
        sharable_dict['ins'].insert(0,'pid:%s'%pid)
    except Exception as e:
        print (sharable_dict.dict)
        raise e

if __name__ == '__main__':
    main()
    print ("CHILD DONE")
