import MySQLdb 
import sys
class DB_doing():
    def __init__(self):
        self.conn=MySQLdb.connect(
        host = 'localhost',
        port = 3306,
        user='root',
        passwd='xidian320',
        db = 'qlearning'
        )
        self.cur=self.conn.cursor()

    def getq(self,cpu,mem,a):
        sql= "select Q from Qappx where cpu = "+"'"+str(cpu)+"'"+" and mem = "+"'"+str(mem)+"'"+" and a = "+str(a)
        print sql 
        self.cur.execute(sql)
        data=self.cur.fetchone()
        return data

    def getvalue(self,cpu,mem):
        sql= "select Q from Qappx where cpu = "+"'"+str(cpu)+"'"+" and mem = "+str(mem)
        print sql 
        self.cur.execute(sql)
        data=self.cur.fetchall()
        print data
        return data

    def getaction(self,cpu,mem,Q):
        sql= "select a from Qappx where cpu = "+"'"+str(cpu)+"'"+" and mem = "+"'"+str(mem)+"'"+" and Q = "+str(Q)
        print sql 
        self.cur.execute(sql)
        data=self.cur.fetchone()
        print data[0]
        return data[0]

    def updateq(self,cpu,mem,a,Q):
        sql="update Qappx set Q="+"'"+str(Q)+"'"+" where cpu= "+"'"+str(cpu)+"'"+" and mem = "+"'"+str(mem)+"'"+" and a = "+str(a)
        print sql
        self.cur.execute(sql)
        self.conn.commit()

    def insert_state(self,cpu,mem,a):
        sql="insert into  Qappx  values(NULL,'"+str(cpu)+"','"+str(mem)+"','"+str(a)+"',0)"
        print sql
        self.cur.execute(sql)
        self.conn.commit()

    def __del__(self):
        self.cur.close()
        self.conn.close()

