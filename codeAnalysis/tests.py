
from django.test import TestCase
# coding=utf-8
import json
import urllib
import csv
import datetime
import pytz
import sys
import operator
import os
import traceback
import zipfile
sys.path.append('./problem')
sys.path.append('./codeAnalysis')
#from models import Problem
from models import CodeInfo,TreeLevel,CodeSrc

def fill_src(pid):
    cid=CodeInfo.objects.get(pro_id=pid,level=0).FId
    content=Problem.objects.get(id=pid).description
    src_update=CodeSrc.objects.get(code_id=cid)
    src_update.src=content
    src_update.save()
#print(sys.argv[1])
#pid=int(sys.argv[1])
#fill_src(pid)
print(1)
