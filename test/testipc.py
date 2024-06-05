from ipcdict import IPCdict
from subprocess import Popen

def main():
    sharable_dict=IPCdict(is_server=True)
    sharable_dict['x']=dict(hello=True,n=0,z=[1,2,3,[5,6,7,dict(a=1,b=2,c=[1,2,3])]])
    sharable_dict['add']=[]
    sharable_dict['pop']=[1,2,3,4,5,6,7,8,[1,dict(a=0)]]
    sharable_dict['ins']=[{'c':'ccc'}]
    try:
        processes = [Popen(['python3', 'testipc2.py']) for _ in range(3)]
        for process in processes:
            process.communicate()
        print(sharable_dict)
        print(sharable_dict.keys())
        print(sharable_dict.values())
        print(sharable_dict.toDict())

        sharable_dict['x']['z'][3][3]=dict(hello='opa')
        sharable_dict['x']['z'][3][2]=['a','b','c']

        sharable_dict['x']['z'][3]='xyu'
        print(sharable_dict)

        print("pop_dict:%s"%sharable_dict['pop'].pop(-1))


        print(sharable_dict.dict)

    finally:
        sharable_dict.connection.shutdown()

if __name__ == '__main__':
    main()
    print ("MAIN DONE")