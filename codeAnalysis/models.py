# coding=utf-8
from __future__ import unicode_literals
from utils.models import JSONField

from account.models import User
from contest.models import Contest
from utils.models import RichTextField
from utils.constants import Choices
from django.db import models

class CodeInfo(models.Model):
    #code_id=models.IntegerField(primary_key=True, db_column='FId')  #自增的字段
    code_id=models.AutoField(primary_key=True,db_column='FId')
    pro_id=models.CharField(max_length=20)
    stu_id=models.CharField(max_length=20)
    level=models.IntegerField(default=0) #在树中的层次，根节点为0
    parent_id=models.IntegerField(default=0)  #父节点的code_id
    children_num =models.IntegerField(default=0)  #父节点的code_id
    def __unicode__(self):
        return u'%d %s %s %d %d' % (self.code_id,self.pro_id,self.stu_id,self.level,self.parent_id)


class CodeSrc(models.Model):
    code_id=models.IntegerField(primary_key=True)
    #src=models.CharField(max_length=1000,default='')   #代码
    src=RichTextField(default='')
    def __unicode__(self):
        return u'%d %s' % (self.code_id,self.src)

class TreeLevel(models.Model):
    pro_id=models.CharField(max_length=20)
    pro_name=models.CharField(max_length=100,default='')
    all_level=models.IntegerField(default=0)   #每个问题构成树的层数
    def __unicode__(self):
        return u'%s %d' % (self.pro_id,self.all_level)

