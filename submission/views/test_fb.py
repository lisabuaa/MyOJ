from test_repair_ly import *

f = open('/home/admin/OJGitLab/OnlineJudge/submission/views/w_code.c','r')
w_code = f.read()
f.close()

list=my_repair(w_code, 230)

c=open('/home/admin/OJGitLab/OnlineJudge/submission/views/cost.txt','w')
c.write(list[0])
c.close()

h=open('/home/admin/OJGitLab/OnlineJudge/submission/views/hint.txt','w')
h.write(list[1])
h.close()

#print list
