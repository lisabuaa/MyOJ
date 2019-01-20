from test_repair_ly import *
from test_repair_ly_python import *

f = open('/home/admin/OJGitLab/OnlineJudge/submission/views/w_code_python.py','r')
w_code = f.read()
f.close()

p=open('/home/admin/OJGitLab/OnlineJudge/submission/views/proid.txt','r')
pid=p.read()
p.close()

if pid==230:
    list=test_repair_ly.my_repair(w_code, 230)
else:
    list=test_repair_ly_python.my_repair(w_code,97)

c=open('/home/admin/OJGitLab/OnlineJudge/submission/views/feedback.txt','w')
c.write(list[0])
c.close()

h=open('/home/admin/OJGitLab/OnlineJudge/submission/views/repair_info.txt','w')
h.write(list[1])
h.close()

