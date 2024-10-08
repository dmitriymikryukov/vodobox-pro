import subprocess,signal,os,time,threading

def detach_processGroup():
    os.setpgrp()

def merge_pipes(**named_pipes):
    import threading
    from queue import Queue as queue
    # Constants. Could also be placed outside of the method. I just put them here
    # so the method is fully self-contained
    PIPE_OPENED = 1
    PIPE_OUTPUT = 2
    PIPE_CLOSED = 3

    # Create a queue where the pipes will be read into
    output = queue()

    # This method is the run body for the threads that are instatiated below
    # This could be easily rewritten to be outside of the merge_pipes method,
    # but to make it fully self-contained I put it here
    def pipe_reader(name, pipe):
        try:
            output.put((PIPE_OPENED, name,))
            try:
                for line in iter(pipe.readline, ''):
                    output.put((PIPE_OUTPUT, name, line.rstrip(),))
            finally:
                output.put((PIPE_CLOSED, name,))
        except:
            logging.exception('Ошибка считывания pipe')

    # Start a reader for each pipe
    for name, pipe in named_pipes.items():
        t = threading.Thread(target=pipe_reader, args=(name, pipe,))
        t.daemon = True
        t.start()

    # Use a counter to determine how many pipes are left open.
    # If all are closed, we can return
    pipe_count = 0

    # Read the queue in order, blocking if there's no data
    for data in iter(output.get, ''):
        code = data[0]
        if code == PIPE_OPENED:
            pipe_count += 1
        elif code == PIPE_CLOSED:
            pipe_count -= 1
        elif code == PIPE_OUTPUT:
            yield data[1:]
        if pipe_count == 0:
            return
procc=None
def flow(vol,pls):
    cmd = './flow %d %.5f' % (vol,pls)
    def xyu(cmd):
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                             universal_newlines=True, preexec_fn=detach_processGroup)
        global procc
        procc=p
        print("CHILD PID: %s"%p.pid)
        try:
            trans = dict()
            ow = False
            for name, line in merge_pipes(out=p.stdout, err=p.stderr):
                print("FLOW SAYS: %s:%s"%(name,line))

        finally:
            try:
                #p.send_signal(signal.SIGINT)
                os.kill(p.pid,signal.SIGINT)
            except:
                os.kill(p.pid,signal.SIGKILL)
                #p.send_signal(signal.SIGKILL)            
            status = p.wait()
            print("DONE: STATUS: %s"%status)
    ppp=threading.Thread(target=xyu,args=[cmd],daemon=False)
    ppp.start()
    time.sleep(5)
    print("DEMO KILL")
    #procc.send_signal(signal.SIGINT)
    os.system("killall -2 flow")
    ppp.join()
    #os.kill(p.pid,signal.SIGINT)
    #os.system("kill -SIGINT %s &"%p.pid)

flow(5000,12.075)
