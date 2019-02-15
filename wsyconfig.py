#!/usr/bin/env python
# coding=utf-8
from xmlrpclib import ServerProxy
from xml.dom.minidom import parseString
import os,sys
import DealDB
import numpy as np
import time as stime


vm_list={'ubuntu-desktop-770':'192.168.12.169'}

#possible actions
ACTION_INC_CPU_1 = 1
ACTION_DEC_CPU_1 = 2
ACTION_INC_MEM_1 = 3
ACTION_DEC_MEM_1 = 4
ACTION_INC_CPU_2 = 5
ACTION_DEC_CPU_2 = 6
ACTION_INC_MEM_2 = 7
ACTION_DEC_MEM_2 = 8
#equal shouldn't live
#ACTION_EQU = 0
#ACTION_ZERO=0

#probability for exploration
EPSILON = 0.1

#learn rate
ALPHA = 0.1

#reword rate in future 
GAMA = 0.9

#value function converge 
CONVERGE=0.05

#state=[vcpu,mem]
START=[1,1]

db=DealDB.DB_doing()

ACTIONS=[ACTION_INC_CPU_1,ACTION_DEC_CPU_1,ACTION_INC_CPU_2,ACTION_DEC_CPU_2,ACTION_INC_MEM_1,ACTION_DEC_MEM_1,ACTION_INC_MEM_2,ACTION_DEC_MEM_2]

def step(state,action):
    i,j=state
    if action == ACTION_INC_CPU_1:
        return [i+1,j]
    elif action == ACTION_DEC_CPU_1 and i-1>=1:
        return [i-1,j]
    elif action == ACTION_INC_CPU_2:
        return [i+2,j]
    elif action == ACTION_DEC_CPU_2 and i-2>=1:
        return [i-2,j]
    elif action == ACTION_INC_MEM_1:
        return [i,j+1]
    elif action == ACTION_INC_MEM_2:
        return [i,j+2]
    elif action == ACTION_DEC_MEM_2 and j-2>=1:
        return [i,j-2]
    elif action == ACTION_DEC_MEM_1 and j-1>=1:
        return [i,j-1]
    #elif action == ACTION_EQU:
    #    return [i,j]
    else:
        print ".......dec too fast........."
        return [i,j]
        #assert False

def getQappx(cpu,mem,a):
    db=DealDB.DB_doing()
    q=db.getq(cpu,mem,a)
    return q

def correct(vm_label,vcpus,memorys):
    new_xml='/etc/libvirt/qemu/'+vm_label+'_new.xml'
    shell='virsh dumpxml '+vm_label+' > '+new_xml
    os.system(shell)
    print 'new xml created'
    shell = 'virsh destroy '+vm_label
    os.system(shell)

    shell_xml = 'virsh undefine '+vm_label
    os.system(shell_xml)
    print 'undefine success'

    mv_shell='mv /etc/libvirt/qemu/'+vm_label+'_new.xml /etc/libvirt/qemu/'+vm_label+'.xml'
    try:
        os.system(mv_shell)
        print mv_shell
    except Exception:
        print 'mv failure'

    vm_xml='/etc/libvirt/qemu/'+vm_label+'.xml'
    #correct xml
    xml = open (vm_xml,'r').read()
    doc = parseString(xml)

    #change cpu
    VCPU=doc.getElementsByTagName('vcpu')[0]
    VCPU.childNodes[0].data =vcpus

     #change Memory,GB
    memorys=int(memorys)
    memorys = memorys*1024*1024
    Memory=doc.getElementsByTagName('memory')[0]
    Memory.childNodes[0].data = memorys
    CM=doc.getElementsByTagName('currentMemory')[0]
    CM.childNodes[0].data = memorys


    f = open(vm_xml,'w')
    doc.writexml(f)
    f.close()

    print'correct success'

    #define
    df_shell='virsh define /etc/libvirt/qemu/'+vm_label+'.xml'
    print df_shell
    os.system(df_shell)

    os.system('virsh start '+vm_label)

def reword(thr,res):
    #the value should be considered
    SLA = 800.000
    ref_thrpt = 1200.000
    float(thr)
    print 'throughtput is '+ str(thr)
    print 'responsetime is '+str(res)
    if(res<=SLA):
	penalty = 0
    else:
	penalty = float(res)/float(SLA);
    score = float(thr)/ref_thrpt-penalty
    #reword is n VM score
    if score<=0:
        reward=-1
    else:
        reward = score
    print 'reward is '+str(reward)
    return float(reward)

def gettpcm(serverip):
    #serverip="192.168.12.169"
    svr = ServerProxy("http://"+serverip+":8888")
    throughput,restime=svr.getresult()
    return throughput,restime

#update the Q approximator
def episode():
    #track the total time steps in this episode
    time=0
    
    #initialize state
    state=START
    db=DealDB.DB_doing()

    #wsy 10.19
    serverip="192.168.12.169"
    serverlabel="ubuntu-desktop-770"

    print '----need recorrect----'
    correct(serverlabel,state[0],state[1])
    stime.sleep(15)
    throughput,restime=gettpcm(serverip)
    rt=reword(throughput,restime)
  
    #wsy 11.17
    #until value function converages
    #to get one or all vms' performance?tpcm can represent performanace
    print 'converge value is '+str(np.std(float(rt)))
    while restime>500:
    #while np.std(float(throughput))>CONVERGE:
        print 'begin episode:'+str(time+1)
        #e-greedy choose an action
        if np.random.binomial(1,EPSILON)==1:
            action = np.random.choice(ACTIONS)
        else:
            #values_ represent all q_value where vcpu=state[0] and memory=state[1]
            db=DealDB.DB_doing()
            values_=db.getvalue(state[0],state[1])
            print "value is "+str(values_)
            if values_==() or max(values_[0])== -10000:
                action = np.random.choice(ACTIONS)
                #db.insert_state(state[0],state[1],action)
            else:
                action=db.getaction(state[0],state[1],max(values_)[0])
        print 'choose action end'+str(action)
        #wsy 11.19 
        next_state = step(state,action)
       
        values_=db.getvalue(state[0],state[1])
        print "value is "+str(values_)
        if values_==():
            db.insert_state(state[0],state[1],action)

        #if too fast continue  
        if next_state==state:   
            q = -10000
            db.updateq(state[0],state[1],action,q)
            continue
        
        #perform action
        correct(serverlabel,next_state[0],next_state[1])
      
        next_values = db.getvalue(next_state[0],next_state[1])
        if next_values==():
            next_action=np.random.choice(ACTIONS)
            db.insert_state(next_state[0],next_state[1],next_action)
        else:
            next_action = db.getaction(next_state[0],next_state[1],max(next_values)[0])

        stime.sleep(15)
 
        #measure reward
        throughput,restime=gettpcm(serverip)
        REWARD=reword(throughput,restime)

        #update Qmax
        q=db.getq(state[0],state[1],action)
        q_next=db.getq(next_state[0],next_state[1],next_action)
        if q==None:
            db.insert_state(state[0],state[1],action)
        q=db.getq(state[0],state[1],action)
        print q[0]
        q=q[0]
        if q_next==None:
            q_next=0
        else:
            q_next=q_next[0]
        q+=ALPHA*(REWARD+GAMA*q_next-q)
        print q
        db.updateq(state[0],state[1],action,q)
        state=next_state

        #record
        tmp =open('./record.txt','a+')
        tmp.write('state,'+str(state[0])+','+str(state[1]))
        tmp.write(',action,'+str(action))
        tmp.write(',reward,'+str(REWARD))
        tmp.write(',response,'+str(restime))
        tmp.write(',tpcm,'+str(throughput))
        tmp.write(',q_value,'+str(q))
        tmp.write('\r')
        tmp.close()    

        print time
        time+=1
    return time         
    
def q_learning_init():
    #q_value
    episode_limit=500
    ep=0
    steps = []
    print 'begin qlearning init'
    while ep<episode_limit:
        steps.append(episode())
        ep+=1
   
    #draw 
    #plt.plot(steps, np.arange(1, len(steps) + 1))
    #plt.xlabel('Time steps')
    #plt.ylabel('Episodes')
    #plt.savefig('./q-learning.png')
    #plt.close()
 
def q_learning():
    #2.initilize t
    time=0
    vcpu=START[0]
    mem=START[1]   
    state=START 
    #wsy 11.29
    serverip="192.168.12.169"
    serverlabel="ubuntu-desktop-770"
    thr,res=gettpcm(serverip)
    rt=reword(thr,res)

    #until value function converages
    #to get one or all vms' performance?tpcm can represent performanace
    while thr>3400:
    #while res>600:
    #while np.std(float(thr))>CONVERGE:
        print '----vm allocation '+str(time+1)
        #4.get current state
        #state=[vcpu,mem]
        print 'state is '+str(state[0])+' '+str(state[1]) 
        #5.greedy choose an action
        db=DealDB.DB_doing()
        values_=db.getvalue(state[0],state[1])
        action=db.getaction(state[0],state[1],max(values_)[0])
        #6.get state st+1
        next_state = step(state,action)
        print 'next state is '+str(next_state[0])+' '+str(next_state[1])
        #perform action
        correct(serverlabel,next_state[0],next_state[1])
        next_values=db.getvalue(next_state[0],next_state[1])   
        stime.sleep(15) 
        #7.measure reward
        thr,res=gettpcm(serverip)
        REWARD=reword(thr,res)
        
        #8.get next actions
        next_action = db.getaction(next_state[0],next_state[1],max(next_values)[0])
        #9.update Qmax
        q=db.getq(state[0],state[1],action)
        q=q[0]
        q_next=db.getq(next_state[0],next_state[1],next_action)
        if q_next==None:
            q_next=0
        else:
            q_next=q_next[0]
        q+=ALPHA*(REWARD+GAMA*q_next-q)
        print q
        db.updateq(state[0],state[1],action,q)
        state=next_state

        #record
        tmp =open('./record_online.txt','a+')
        tmp.write('state,'+str(state[0])+','+str(state[1]))
        tmp.write(',action,'+str(action))
        tmp.write(',reward,'+str(REWARD))
        tmp.write(',response,'+str(res))
        tmp.write(',tpcm,'+str(thr))
        tmp.write(',q_value,'+str(q))
        tmp.write('\r')
        tmp.close() 
        time+=1       
    return time         
    
#consider all vm!!!
#def vconf_core():
if __name__=='__main__':    
    #q_learning_init()
    q_learning() 
 


