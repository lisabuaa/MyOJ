#!/usr/bin/python
# coding=UTF-8

import sys
import json
import urllib
import psycopg2
import git
import itertools
import os
import datetime
import time
import re
import  urllib.request
student_amount = 200   #学生代码
db = psycopg2.connect(database="onlinejudge2", user="onlinejudge", password="onlinejudge", host="10.2.26.127", port="5432")
cursor = db.cursor()
code_copy=""

class Shixun(object):
    
    def __init__(self,id,name,identifier):
        self.id = id
        self.name = name
        self.identifier = identifier
        self.user_ids = []
        
    def get_shixun(self):
        url = 'https://www.educoder.net/api/v1/sources/%s/shixun_detail?private_token=hriEn3UwXfJs3PmyXnSG' %self.identifier
        req = urllib.request.Request(url)
        res_data = urllib.request.urlopen(req)
        res = json.loads(res_data.read())
        
        self.myshixuns_count = res.get("myshixuns_count",0)
        #print 'myshixuns_count',self.myshixuns_count


    def get_myshixun(self,date='20190102'):
        length = 1
        pages = 0
        this_amount = 0
        while length != 0 and this_amount <= student_amount:   #选500个学生
            pages += 1
            url = 'https://www.educoder.net/api/v1/sources/myshixuns_index?time=%s&private_token=hriEn3UwXfJs3PmyXnSG&page=%s' %(date,str(pages))
            req = urllib.request.Request(url)
            res_data = urllib.request.urlopen(req)
            res = json.loads(res_data.read())

            length = len(res)

            for item in res:
                item = item["myshixun"]
                id = item.get("id","")
                shixun_id = item.get("shixun_id","")
                if shixun_id != self.id:
                    continue
                user_id = item.get("user_id","")
                
                ####得到git_url######
                url = 'https://www.educoder.net/api/v1/sources/search_myshixun?user_id=%s&shixun_id=%s&private_token=hriEn3UwXfJs3PmyXnSG' %(user_id,self.id)
                reqq = urllib.request.Request(url)
                res_dataa = urllib.request.urlopen(reqq)
                ress = json.loads(res_dataa.read())
                git_url = ress.get("git_url","")
                #print 'git_url',git_url
                
                ###得到identity#####
                for cha in self.challenge:
                    cha_id = cha.id
                    url = 'https://www.educoder.net/api/v1/sources/search_game?user_id=%s&challenge_id=%s&private_token=hriEn3UwXfJs3PmyXnSG' %(str(user_id),str(cha_id))
                    req = urllib.request.Request(url)
                    res_data = urllib.request.urlopen(req)
                    res = json.loads(res_data.read())
                    identifier = res.get("identifier","")
                    #print 'identifier',identifier
                 ####用identifier来做submission_id#####                       
                ####code###########
                    path = cha.path
                    self.get_code(identifier,user_id,path)
                              
                    this_amount += 1

#         #print self.user_ids
            
    def git_clone(self,dir_name,git_url):   #从git 下载到本地 code目录下
        #print git_url
        os.chdir(dir_name)
        git.Git().clone(git_url)
    
    
    def add_dir(self,dir_name):    #创建目录
        isExists=os.path.exists(dir_name)
        if not isExists:
            os.makedirs(dir_name)
    
    
    def get_code(self,identifier,user_id,path):   #代码下载到本地
        
        url = 'https://www.educoder.net/api/v1/sources/%s/game_detail?private_token=hriEn3UwXfJs3PmyXnSG' %identifier
        req = urllib.request.Request(url)
        res_data = urllib.request.urlopen(req)
        res = json.loads(res_data.read())
        
        code_info = res
    
        #print (res)
        id = res.get("id","")
        cid = res.get("challenge_id","")
        commit_count = res.get("commit_count",0)
        right = res.get("right","False")
        final_score = res.get("final_score",0)
        git_url = res.get("git_url","")
        commit_status = res.get("commit_status",[])
        status = '0'
        
        if commit_count == 0 :
            return 
        #print 'right:',right
        
        #print 'commmit_count',commit_count
        dir_name = '/home/nlsde/educoder/code/%s/%s' %(self.id,user_id)
        
        if git_url:
            self.add_dir(dir_name)
            try:
                self.git_clone(dir_name,git_url)
            except:
                pass
            
            git_name = '%s/%s'   %(dir_name,git_url.split('/')[-1].replace('.git',''))
            os.chdir(git_name)
            #print 'git_name',git_name
            
            ######传数据库1#################
            
            submission_id = '%s-0' %identifier
            code_dir = '%s/%s' %(git_name,path)
            #time.sleep(1)
            code_content = open(code_dir,'r',encoding='UTF-8').read()
            code_r = chuli(code_content)
            shixun_id = self.id
            user_id = user_id
            commit_count = commit_count
            commit_number = 0   ###第几次
            
            insert_info_root = "INSERT INTO \"submission_submission_python\" (shixun_id, challenge_id, student_id, submission_time, submission_count,submission_id,code,result,w_code,code_r) VALUES (%s,%s, %s, %s, %s,%s,%s,%s,'0',%s)"
            list_tmp = [shixun_id, cid, user_id,commit_number,commit_count,submission_id,code_content,right,code_r]
            cursor.execute(insert_info_root, list_tmp)
            db.commit()

            #print submission_id
            #print code_dir
            #print code_content
            
            ######如果只有一次提交##########
            if commit_count == 1:
                return
            
            #####得到git log中的提交时间######
            os.system('git log > log')
            git_log = open('log','r', encoding='UTF-8').readlines()
            p1 = r'Date.*800'
            pattern = re.compile(p1)
            date_all = []
            for line in git_log:
                this = pattern.findall(line)
                if this:
                    date_str = this[0]
                    date_str = date_str.replace('Date:','').replace('+0800','').strip()
                    date = datetime.datetime.strptime(date_str,"%a %b %d %H:%M:%S %Y")
                    date_all.append(date)
            ###### 得到commit_id###########
            #commit_id_final = 'git log head -n 1 > now.txt'
            for i,item in enumerate(commit_status):
                if i == 0:
                    continue
                submission_id2 = "%s-%s" %(identifier,str(i)) 
                commit_time = item.get("commit_time","")
                
                #print commit_time
                #"2018-10-18T18:33:41+08:00",
                commit_id = ''
                if commit_time:
                    this_time = commit_time.strip().split('+')[0]
                    now = datetime.datetime.strptime(this_time,"%Y-%m-%dT%H:%M:%S")
                    last_date = date_all[0]  
                    this_date = datetime.datetime.strftime(last_date,"%a %b %d %H:%M:%S %Y")
                            
                    for git_date in date_all:
                        if last_date > now and git_date < now:
                            this_date = datetime.datetime.strftime(last_date,"%a %b %d %H:%M:%S %Y")
                            break
                        if last_date < now:
                            this_date = datetime.datetime.strftime(last_date,"%a %b %d %H:%M:%S %Y")
                        last_date = git_date
                    
                    #print date_all[0]
                    mingling = 'git log | grep -B 2 "%s" | head -n 1 > now.txt' %this_date
                    #print mingling   
                
                    return_mingling  = os.system(mingling)
                    all_strs = open('now.txt','r').read()
                    if all_strs:
                        commit_id = all_strs.replace("\n","").split(" ")[-1]
                        #print 'commit_id',commit_id
                
                    
                    #### 传数据库2########################

                    
                    if commit_id:
                        mingling2 = 'git show %s:%s >code.txt' %(commit_id,path)
                        #print mingling2
                        os.system(mingling2)
                        #code_dir2 = '%s/%s' %(git_name,path)
                        code_content2 = open('code.txt','r',encoding='UTF-8').read()
                    
                        if code_content2 == code_content:
                            #print '一样'
                            continue
                        #print submission_id2
                        #print code_dir
                        #print code_content2
                        shixun_id2 = self.id
                        user_id2 = user_id
                        commit_count2 = commit_count
                        commit_number2 = i   ###第几次
                        code_content=code_content2
                        code_r = chuli(code_content)
                        right = 'false'        #中间结果为false
                        insert_info_root2 = "INSERT INTO \"submission_submission_python\" (shixun_id, challenge_id, student_id, submission_time, submission_count,submission_id,code,result,w_code,code_r) VALUES (%s, %s, %s, %s, %s,%s,%s,%s,'0',%s)"
                        list_tmp2 = [shixun_id2, cid,user_id2,commit_number2,commit_count2,submission_id2,code_content,right,code_r]
                        cursor.execute(insert_info_root2, list_tmp2)
                        db.commit()

                    ######################################

    
    def get_challenge(self,):   #得到该实训下所有的关卡
        url = 'https://www.educoder.net/api/v1/sources/%s/shixun_challenges?private_token=hriEn3UwXfJs3PmyXnSG' %self.identifier
    #具体例子 查看https://www.educoder.net/api/v1/sources/zlg2nmcf/shixun_challenges?private_token=hriEn3UwXfJs3PmyXnSG
        req = urllib.request.Request(url)
        res_data = urllib.request.urlopen(req)
        res = json.loads(res_data.read())
        self.challenge = []
        
        
        for item in res:
            id = item.get("id","")
            name = item.get("name","")
            path = item.get("path","")
            ins = item.get("sets",[])    ####测试样例 格式[{"input":"","output":""}]
            answer = item.get("answer","") 
            answer = chuli(answer)
            content = item.get("task_pass","") ######题目内容
            #######################chanlleng存入数据库#################################
            #print(content.encode('utf-8'))
            try:
                entryfun = content.split('def')[1].split('(')[0].strip()
                if len(entryfun)>10:
                    entryfun = 'main_none'
            except Exception:
                entryfun = 'main_none'

            insert_info_root = "INSERT INTO \"submission_challenge\" (challenge_id, challenge_name, path, ins, answer,content,entryfun,children_num,level,parent_id,shixun_id,identifier) VALUES (%s, %s, %s, %s,%s,%s,%s,'0','0','0',%s,%s)"
            list_tmp = [id, name,path,str(ins),answer,content,entryfun,self.id,self.identifier]
            #print(str(ins))
            cursor.execute(insert_info_root, list_tmp)
            db.commit()
            if id:
                s_c = Challenge(id,self.id,name,path)
                #s_c.get_student_challenge()     #得到学生完成challenge
                #print s_c.id
                #print s_c.name
                self.challenge.append(s_c)
                print(s_c)
            
            #break
    
    def __str__(self,):
        result = [self.id,self.name,self.identifier]
        result = [str(i).encode("ascii") for i in result]
        return str(result)



class Challenge(object):
    
    def __init__(self,id,shixun_id,name,path):
        self.id = id
        self.shixun_id = shixun_id
        self.name = name
        self.path = path
        self.submission = {}
    
    
    def git_clone(self,dir_name,git_url):   #从git 下载到本地 code目录下
        #print git_url
        os.chdir(dir_name)
        git.Git().clone(git_url)

    
    def get_code(self,identifier,result):   #代码下载到本地
        user_id = result["user_id"]
        url = 'https://www.educoder.net/api/v1/sources/%s/game_detail?private_token=hriEn3UwXfJs3PmyXnSG' %identifier
        req = urllib.request.Request(url)
        res_data = urllib.request.urlopen(req)
        res = json.loads(res_data.read())
        
        code_info = res
    
        ##print res
        id = res.get("id","")
        commit_count = res.get("commit_count",0)
        right = res.get("right","false")
        final_score = res.get("final_score",0)
        git_url = res.get("git_url","")
        commit_status = res.get("commit_status",[])
        
        if right  == "false":
            return
        #print 'right',right
        #print 'commmit_count',commit_count
        if right == 'true':
            status = '1'
        dir_name = '/home/nlsde/educoder/code/%s/%s' %(self.id,user_id)
        
        if git_url:
            self.add_dir(dir_name)
            try:
                self.git_clone(dir_name,git_url)
            except:
                pass

            for i,item in enumerate(commit_status):
                submission_id = "%s%s" %(id,str(i))
                ##print item
            
            
    def add_dir(self,dir_name):    #创建目录
        isExists=os.path.exists(dir_name)
        if not isExists:
            os.makedirs(dir_name)
            
                
    def get_student_challenge(self,date='20190102'):    
        #url = 'https://www.educoder.net/api/v1/sources/lrmbky4hjp9a/game_detail?private_token=hriEn3UwXfJs3PmyXnSG' 
        url = 'https://www.educoder.net/api/v1/sources/games?time=%s&private_token=hriEn3UwXfJs3PmyXnSG' %date
        req = urllib.request.Request(url)
        res_data = urllib.request.urlopen(req)
        res = json.loads(res_data.read())
        
        self.student_challenge = {}
        
        for item in res:
            item = item['game']
            user_id = item.get("user_id","")
            identifier = item.get("identifier","")
            myshixun_id = item.get("myshixun_id","")
            
            if user_id:
                result = {}
                result["user_id"] = user_id
                result["myshixun_id"] = myshixun_id
                self.student_challenge[identifier] = result
                code_info = self.get_code(identifier,result)
                #result["code"] = code_info
                ##print result
            

####从这里开始################
def chuli(code):
    code = code.replace("'",'"')
    date_all = re.findall(r"[(]((.|\n)*?)[)]", code)
    for item in date_all:
        item = item[0]
        item2 = item.replace("\n","").replace("\t","")
        code = code.replace(item,item2)
    
    #code = code.decode("utf8")
    start = '    '
    name = 'main_none'
    try:
        entryfun = code.split('def')[1].split('(')[0].strip()
        if len(entryfun) > 10:
            entryfun = 'main_none'
    except:
        entryfun = 'main_none'
    if entryfun == 'main_none' or entryfun == 'print_':
        result_code = ''
        lines = code.split('\n')
        hanshu = 'def %s():\n' %name
        end = '%s()\n' %name
        tag = -1
        if 'import' not in code and 'coding' not in code:
            tag = 1

        for line in lines:
            if line == "'''python":
                continue
            regex = u"[\u4e00-\u9fa5]+"
            res = re.findall(regex, line)
            
            for item in res:
                
                line = line.replace(item,'#')   #中m~V~Gm~[0m~M0m~H~P#
            if line.strip().startswith('#'):  #m~H| m~Ym~G~J
                continue
            if line.startswith('import') or line.startswith('#coding') or line.startswith('from'):
                line = line + '\n'
                tag = 1
            elif tag == 1:
                result_code += hanshu
                line = start + line + '\n'
                tag = 0
            elif tag == -1:
                continue
            elif tag == 0:
                line = start + line + '\n'
            result_code += line
        result_code += end
    else:
        result_code = ''
        lines = code.split('\n')
        for line in lines:
            regex = u"[\u4e00-\u9fa5]+"
            res = re.findall(regex, line)
            for item in res:
                line = line.replace(item,'#')   #中m~V~Gm~[0m~M0m~H~P#
            if line.startswith('#'):
                continue
            result_code += line+'\n'
    return result_code

identifiers = ['q4ixftoz']
def download_shixun(date):
    url = 'https://www.educoder.net/api/v1/sources/shixun_index?time=%s&private_token=hriEn3UwXfJs3PmyXnSG' %date
    req = urllib.request.Request(url)
    res_data = urllib.request.urlopen(req)
    res = json.loads(res_data.read())
    ##print len(res)
    for item in res:
        item = item['shixun']
        name = item.get("name","")
        id = item.get("id","")
        identifier = item.get("identifier","")
        
        if id and 'Python' in name:
            shixun = Shixun(id,name,identifier)
            shixun.get_shixun()
            #print shixun.name
            #print shixun.identifier
            
            for identifier in identifiers:
                shixun.get_challenge()
                shixun.get_myshixun()

    


download_shixun('20190102')    
db.close()







