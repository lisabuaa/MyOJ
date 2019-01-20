# coding=utf-8
import json
import os
import pprint
import sys
import traceback
import pstats

from ast import literal_eval

# clara imports
import clara
from clara.common import parseargs, debug
from clara.feedback import Feedback, FeedGen
from clara.feedback_repair import RepairFeedback
from clara.feedback_simple import SimpleFeedback
from clara.feedback_python import PythonFeedback
from clara.interpreter import getlanginter
from clara.matching import Matching
from clara.model import dict_to_expr
from clara.parser import getlangparser
from clara.repair import Repair

import cProfile

import psycopg2
from operator import itemgetter, attrgetter

# result:
result = []
result_tmp = []


class clara_repair(object):
    # global result_tmp
    # global result

    def __init__(self, ins, code_names, cmd):
        self.verbose = 0
        VERBOSE = self.verbose
        self.cmd = cmd
        self.sources = {}  # programs {'name':'code','name2':'code2'}
        for item in code_names:
            self.generate_sources(item)
        self.lang = 'py'
        self.timeout = 60
        self.ignoreio = 0
        self.ignoreret = 0
        self.bijective = 0
        self.cleanstrings = 0
        self.entryfnc = 'average'
        self.suboptimal = 1
        self.maxfeedcost = 0
        self.feedtype = 'simple'
        self.ins = None

        self.args = ins
        if self.lang is None:
            self.guess_lang()
        self.parser = getlangparser(self.lang)
        #        print self.parse
        self.inter = getlanginter(self.lang)

        self.process_sources()

        self.poolsize = 8

        if self.cmd == 'match':
            self.match()

        elif self.cmd == 'model':
            self.model()

        elif self.cmd == 'repair':
            self.repair()

        elif self.cmd == 'feedback':
            self.feedback()

        elif self.cmd == 'eval':
            self.eval()

        else:
            self.usage()
            self.error("Unknown command: '%s'", self.cmd)

    def error(self, msg, *args):
        '''
        Prints error message and exits
        '''

        if args:
            msg %= args
        print >> sys.stderr, 'Error: %s\n' % (msg,)
        sys.exit(1)

    def generate_sources(self, code_name):
        # generate models {}
        with open(code_name, 'r') as f:
            code = f.read().decode('utf-8')
            self.sources[code_name] = code

    def debug(self, msg, *args):
        '''
        Prints debug message if verbose mode on.
        '''

        if self.verbose:
            debug(msg, *args)

    def guess_lang(self):
        '''
        Sets lang options from the first source file extension.
        '''

        if not len(self.sources):
            self.error('Cannot guess the language - no source files!')
            return
        for item in self.sources:
            file_parts = item.rsplit('.', 1)
            break

        if len(file_parts) < 2:
            self.error('Cannot guess the language - no file extension!')

        self.lang = file_parts[1]
        self.debug('Guessed language: %s', self.lang)

    def process_sources(self):

        self.models = []

        for code_name in self.sources:
            self.debug("Reading and parsing source file '%s'", code_name)

            #            with open(src, 'r') as f:
            #            code = f.read().decode('utf-8')
            #            print self.parser
            model = self.parser.parse_code(self.sources[code_name])
            model.name = code_name
            self.extract_exprs(model)
            self.models.append(model)

    def model(self):

        if len(self.models) != 1:
            self.error('Model requires one program!')

        print self.models[0].tostring()

    def match(self):

        if len(self.models) < 2:
            self.error('Match requires two programs!')

        elif len(self.models) > 2:
            self.debug('Match requires two programs, ignoring the rest!')

        M = Matching(ignoreio=self.ignoreio, ignoreret=self.ignoreret,
                     verbose=self.verbose, bijective=self.bijective)

        m = M.match_programs(self.models[0], self.models[1], self.inter,
                             ins=self.ins, args=self.args,
                             entryfnc=self.entryfnc)
        print 'm', m
        if m:
            self.debug('Match: %s', pprint.pformat(m[1]))
            print 'Match!'
        else:
            print 'No match!'

    def eval(self):

        if len(self.models) != 1:
            self.error('Eval requires exactly one program!')

        print self.models[0]
        print

        inter = self.inter(entryfnc=self.entryfnc)
        trace = inter.run(self.models[0], args=self.args, ins=self.ins)

        print trace

    def repair(self):

        if len(self.models) < 2:
            self.error('Repair requires two programs!')

        elif len(self.models) > 2:
            self.debug('Repair requires two programs, ignoring the rest!')

        R = Repair(timeout=self.timeout, verbose=self.verbose,
                   allowsuboptimal=self.suboptimal,
                   cleanstrings=self.cleanstrings)

        # print (self.entryfnc)

        r = R.repair(self.models[0], self.models[1], self.inter,
                     ins=self.ins, args=self.args, ignoreio=self.ignoreio,
                     ignoreret=self.ignoreret, entryfnc=self.entryfnc)
        if r:
            # txt = RepairFeedback(self.models[1], self.models[0], r)
            txt = PythonFeedback(self.models[1], self.models[0], 3)

            print "pythonfeedback"
            print (txt)

            txt.genfeedback()

            # print 'Repairs:'
            # print '\n'.join(map(lambda x: '  * %s' % (x,), txt.feedback))

            global result_tmp

            result_tmp.append('\n'.join(map(lambda x: '  * %s' % (x,), txt.feedback)))

            # by liangyu

            totalcost = 0.0

            for i in txt.feedback:
                totalcost = totalcost + float(i.split('cost=')[1].split(')')[0])  # cost


            result_tmp.append(totalcost)


            print len(result)

            txt = SimpleFeedback(self.models[1], self.models[0], r)
            txt.genfeedback()

            result_tmp.append('\n'.join(map(lambda x: '  * %s' % (x,), txt.feedback)))

            result.append(result_tmp)
            result_tmp = []



        else:
            print 'No repair!'


    def feedback(self):

        if len(self.models) < 2:
            self.error('Feedback requires at least two programs!')

        F = FeedGen(verbose=self.verbose, timeout=self.timeout,
                    poolsize=self.poolsize, allowsuboptimal=self.suboptimal,
                    feedmod=self.feedtype)

        impl = self.models[-1]
        specs = self.models[:-1]

        feed = F.generate(
            impl, specs, self.inter, ins=self.ins, args=self.args,
            ignoreio=self.ignoreio, ignoreret=self.ignoreret,
            cleanstrings=self.cleanstrings,
            entryfnc=self.entryfnc)

        if feed.status == Feedback.STATUS_REPAIRED:
            if self.maxfeedcost > 0 and feed.cost > self.maxfeedcost:
                self.error('max cost exceeded (%d > %d)',
                           feed.cost, self.maxfeedcost)
            for f in feed.feedback:
                print '*', f

        elif feed.status == Feedback.STATUS_ERROR:
            self.error(feed.error)

        else:
            self.error(feed.statusstr())

    def extract_exprs(self, model):
        '''
        Loads additional expressions for the specification.
        '''
        ext = '.' + self.lang
        exprs_filename = model.name.replace(ext, '-exprs.json')
        if not os.path.isfile(exprs_filename): return

        with open(exprs_filename, 'r') as f:
            exprs = json.load(f)

        for expr_entry in exprs:
            fname = expr_entry['fnc']
            loc = expr_entry['loc']
            var = expr_entry['var']
            expr = dict_to_expr(expr_entry['expr'])

            fnc = model.fncs[fname]

            if not hasattr(fnc, 'repair_exprs'):
                fnc.repair_exprs = {}

            rex = fnc.repair_exprs

            if loc not in rex:
                rex[loc] = {}

            if var not in rex[loc]:
                rex[loc][var] = []

            rex[loc][var].append((expr, None))

    def process_sources(self):
        '''
        Reads and parses source files (sets models field).
        '''

        self.models = []

        for src in self.sources:
            self.debug("Reading and parsing source file '%s'", src)

            with open(src, 'r') as f:
                code = f.read().decode('utf-8')
                #                print self.parser
                model = self.parser.parse_code(code)
                model.name = src
                self.extract_exprs(model)
                self.models.append(model)


def my_repair(stu_code, pro_id):
    global result_tmp
    global result

    # remove comment /*...*/
    if stu_code.find("/*") != -1:
        stu_code = stu_code.split('/*')[0] + stu_code.split('*/')[1]

    stu_code = stu_code.replace("int main(int argc, char *argv[])",
                                "int main()")  # remove int argc, char *argv[]

    # establish wrong_code_file
    tmp_file_name = str(pro_id) + '.py'
    code_file = open(tmp_file_name, 'w')
    code_file.write(stu_code)
    code_file.close()

    # begin fetching templates
    db = psycopg2.connect(database="onlinejudge", user="onlinejudge", password="onlinejudge", host="10.2.26.122",
                          port="5432")
    cur_template = db.cursor()
    cur_template.execute(
        "SELECT * FROM \"codeAnalysis_codeinfo\" WHERE pro_id = '%s' AND level= 0" % str(pro_id))
    # level = 0 means the problem
    # template_ins = cur_template.fetchone()[6]

    cur_template.execute(
        "SELECT * FROM \"codeAnalysis_codeinfo\" WHERE pro_id = '%s' AND level= 1" % str(pro_id))
    # level = 1 means templates
    rows_template = cur_template.fetchall()

    for row_template in rows_template:
        cur_template.execute(
            "SELECT * from \"codeAnalysis_codesrc\" where code_id = '%s'" % str(row_template[0]))
        template_code = cur_template.fetchone()[1]

        tmp_template_name = str(row_template[0]) + '.py'
        template_file = open(tmp_template_name, 'w')

        template_file.write(template_code)
        template_file.close()

        result_tmp.append(tmp_file_name)
        result_tmp.append(tmp_template_name)

        clara_repair(ins=[[3.0, 3.0, 5.5]], code_names=[tmp_template_name, tmp_file_name], cmd='repair')
        # clara_repair(ins=[list(template_ins)], code_names=[tmp_template_name, tmp_file_name], cmd='feedback')

        os.remove(tmp_template_name)

    os.remove(tmp_file_name)

    final_result = sorted(result, key=itemgetter(0, 3))

    # output
    feedback_info = str(final_result[0][4])
    repair_info = str(final_result[0][2])

    return [feedback_info, repair_info]

    # print('wrong_code:' + str(final_result[0][0])
    #                       + '\ntemplate:' + str(final_result[0][1])
    #                       + '\ntotal_cost:' + str(final_result[0][3])
    #                       + '\nrepair:\n' + str(final_result[0][2])
    #                       + '\n\n')
    #


f = open('w_code_python.py','r')
w_code = f.read()

list1 = my_repair(w_code, 97)
print "feedback"
print list1[0]
print "repair"
print list1[1]

# my_repair("5066a47ca58b2a8614667ffa0b4d8df1.c", "test/18231146.c")


# cProfile.run("test()","result")
# p = pstats.Stats("result")
# print "p.strip_dirs().sort_stats(-1).print_stats()"
# p.strip_dirs().sort_stats(-1).print_stats()
# #strip_dirs():从所有模块名中去掉无关的路径信息
# #sort_stats():把打印信息按照标准的module/name/line字符串进行排序
# #print_stats():打印出所有分析信息
#
# #按照函数名排序
# #p.strip_dirs().sort_stats("name").print_stats()
#
# #按照在一个函数中累积的运行时间进行排序
# #print_stats(3):只打印前3行函数的信息,参数还可为小数,表示前百分之几的函数信息
# #p.strip_dirs().sort_stats("cumulative").print_stats(3)
#
#     #还有一种用法
# p.strip_dirs().sort_stats('time', 'cumulative').print_stats()
#     #先按time排序,再按cumulative时间排序,然后打倒出前50%中含有函数信息
#
#     #如果想知道有哪些函数调用了bar,可使用
# p.print_callers(0.5, "repair")
#
#     #同理,查看foo()函数中调用了哪些函数
# p.print_callees("test")
