import os,django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")# project_name 项目名称
django.setup()
from django.test import TestCase
# coding=utf-8
import json
import urllib
import csv
import datetime
import pytz
import sys
import re
import operator
import os
import traceback
import zipfile
from problem.models import Problem
from codeAnalysis.models import CodeInfo,TreeLevel,CodeSrc

def fill_src(pid):
    cid=CodeInfo.objects.get(pro_id=pid,level=0).code_id
    content=Problem.objects.get(id=pid).description
    cont=re.sub(r'<.+?>','',content)
    cont2=re.sub(r'【','\n【',cont)
    src_update=CodeSrc.objects.get(code_id=cid)
    src_update.src=cont2
    src_update.save()
#print(sys.argv[1])
pid=int(sys.argv[1])
fill_src(pid)
