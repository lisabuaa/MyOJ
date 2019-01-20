import os
from django.core.management.base import BaseCommand

from account.models import AdminType, ProblemPermission, User, UserProfile
from contest.models import Contest
from utils.models import RichTextField
from problem.models import ProblemTag,ProblemDifficulty,Problem
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views



class Command(BaseCommand):
    def handle(self, *args, **options):
        print ("ok")
        self.alter_difficulty('入门训练','Low')
        #self.alter_difficulty('算法提高','High')
        
        
    
    
    def alter_difficulty(self,strs,diff):
        problems = Problem.objects.filter( title__contains = strs)
        for problem in problems:
            problem.difficulty = diff
            print (problem.id)
            #problem.save()