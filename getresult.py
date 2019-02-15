#!/usr/bin/env python
import os,sys,re
import time as stime
import log
import numpy as np
from SimpleXMLRPCServer import SimpleXMLRPCServer
def getresult():
    ret=os.system("/home/ubuntu/tpcc-mysql/tpcc_start -h 127.0.0.1 -P 3306 -dtpcc1000 -u root -pxidian320 -w 20 -c 32 -r 300 -l 300 ->/home/ubuntu/tpcc-mysql/tpcc-output-log")
  
    time=[] 
    stime.sleep(150)    
    if ret==0:
        try:
            f=open('/home/ubuntu/tpcc-mysql/tpcc-output-log','r')
        except Exception,e:
            log.MyLog(str(e)) 
    else:
        assert False
        #with open("out.txt","r") as file:
       
    for line in f.readlines():
        #matchre=re.match(r"(.*)TpmC",f)
        matchre=line.split('TpmC')
        s=matchre[0].strip()
        try:
            matchtime=line.split('99%:')[1].split(',')
            t=matchtime[0].strip()
            time.append(float(t))
            print(t)
        except:
            pass
    print(s)
    ti=int(np.mean(time))
    os.system("rm /home/ubuntu/tpcc-mysql/tpcc-output-log")
    print(ti)
    return s,ti
#getresult()
svr=SimpleXMLRPCServer(("",8888),allow_none=True)
#while(1):
#    time.sleep(20)
svr.register_function(getresult)

svr.serve_forever()
