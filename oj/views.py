# coding=utf-8
import json
import urllib
import csv
import datetime
import pytz
import operator
import os
import traceback
import zipfile

from time import strftime, localtime

import datetime
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import transaction, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse, \
    StreamingHttpResponse
from django.shortcuts import render, render_to_response
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods



from codeAnalysis.models import CodeInfo,TreeLevel,CodeSrc
def code_tree2(request):
    problem_id = request.GET['problem']
    level=TreeLevel.objects.get(pro_id = problem_id).all_level
    if level:
        return HttpResponse('success')
    else:
        return HttpResponse('error')

def code_tree(request, template="code_tree.html"):
    problem_id = request.GET['problem']
    data = {}
    stu_info = {}
    try:
        level = TreeLevel.objects.get(pro_id = problem_id).all_level
        item = CodeInfo.objects.filter(pro_id = problem_id).filter(level = 0)[0]
        gen_id = item.code_id
        gen_stu_id = item.stu_id
        gen_children_num = item.children_num
        need_gen_id = str(gen_stu_id)+':'+str(gen_children_num)
        try:
            problem_content = CodeSrc.objects.get(code_id=gen_id).src
        except:
            problem_content = ''
        i = level - 1
        data_temp = {}
        while i > 0:
            items = CodeInfo.objects.filter(pro_id = problem_id).filter(level = i)
            code_ids = items.values('parent_id').distinct()
            code_ids_without_sort = [x['parent_id'] for x in code_ids]  #all parent_id
            for parent_id in code_ids_without_sort:
                item_parent = CodeInfo.objects.get(code_id=parent_id)
                parent_stu_id = item_parent.stu_id
                parent_children_num = item_parent.children_num
                need_parent_id = str(parent_stu_id)+':'+str(parent_children_num)
                items2 = CodeInfo.objects.filter(parent_id=parent_id)
                temps = []
                for item in items2:
                    code_id = item.code_id
                    stu_id = item.stu_id
                    children_num = item.children_num
                    stu_info[stu_id] = code_id
                    code_temp = {}
                    need_id = str(stu_id)+':'+str(children_num)
                    if need_id in data_temp :
                        code_temp['children'] = data_temp[need_id]
                    code_temp['name'] = need_id
                    temps.append(code_temp)
                    #print temps
                    #temps.sort(key=lambda x: int(x['name'].split(':')[-1]))
                    #print temps
                data_temp[need_parent_id] = temps
            i = i - 1
        data['name'] = need_gen_id
        data_temp[need_gen_id].sort(reverse=True,key=lambda x: int(x['name'].split(':')[-1]))
        data['children'] = data_temp[need_gen_id]

    except Exception as e:
        error_message = e.message
        print (error_message)
    #print (data)
    
    problem_content= '<pre  id="code" class="ace_editor" style="min-height:400px"><textarea class="ace_text-input">'+problem_content+'</textarea></pre>'
    

    return render(request, template,{"gen_id":gen_id,"data":json.dumps(data),"problem_id":problem_id,"problem_content":problem_content,"stu_info":json.dumps(stu_info)})

@require_http_methods(["POST"])
def code_tree_content(request):
    code_id = request.POST.get("code_id", '')
    print (code_id)
    if code_id:
        try:
            code_id = int(code_id)
            item = CodeSrc.objects.get(code_id = code_id)
            src = item.src
        except:
            src ='int main(){\n    int n,m;\n    scanf("%d %d",&n,&m);\n    printf("%d",n+m);\n    return 0;\n}'
    src= '<pre  id="code" class="ace_editor" style="min-height:400px"><textarea class="ace_text-input">'+src+'</textarea></pre>'
    #src = src.replace('\n','</br>')
    return JsonResponse(src, safe=False)



#add by code_analysis end