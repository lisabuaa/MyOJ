from django.db import models
from utils.models import JSONField
from problem.models import Problem
from contest.models import Contest

from utils.shortcuts import rand_str


class JudgeStatus:
    COMPILE_ERROR = -2
    WRONG_ANSWER = -1
    ACCEPTED = 0
    CPU_TIME_LIMIT_EXCEEDED = 1
    REAL_TIME_LIMIT_EXCEEDED = 2
    MEMORY_LIMIT_EXCEEDED = 3
    RUNTIME_ERROR = 4
    SYSTEM_ERROR = 5
    PENDING = 6
    JUDGING = 7
    PARTIALLY_ACCEPTED = 8


class Submission(models.Model):
    id = models.TextField(default=rand_str, primary_key=True, db_index=True)
    contest = models.ForeignKey(Contest, null=True)
    problem = models.ForeignKey(Problem)
    create_time = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField(db_index=True)
    username = models.TextField()
    code = models.TextField()
    result = models.IntegerField(db_index=True, default=JudgeStatus.PENDING)
    # 从JudgeServer返回的判题详情
    info = JSONField(default=dict)
    language = models.TextField()
    shared = models.BooleanField(default=False)
    # 存储该提交所用时间和内存值，方便提交列表显示
    # {time_cost: "", memory_cost: "", err_info: "", score: 0}
    statistic_info = JSONField(default=dict)
    ip = models.TextField(null=True)
    repair_info = models.TextField(default='')
    feedback_info = models.TextField(default='')
    wku_info = models.TextField(default='')

    def check_user_permission(self, user, check_share=True):
        return self.user_id == user.id or \
               (check_share and self.shared is True) or \
               user.is_super_admin() or \
               user.can_mgmt_all_problem() or \
               self.problem.created_by_id == user.id

    class Meta:
        db_table = "submission"
        ordering = ("-create_time",)

    def __str__(self):
        return self.id

class Submission_python(models.Model):
    
    id = models.AutoField(primary_key=True)
    shixun_id = models.TextField(default='')
    challenge_id = models.TextField(default='')
    student_id = models.TextField(default='')
    submission_time = models.IntegerField()
    submission_count = models.IntegerField()
    submission_id = models.TextField(default='')
    code = models.TextField(default='')
    code_r = models.TextField(default='')
    result = models.TextField(default='')
    w_code = models.TextField(default='')

class Challenge(models.Model):
    
    id = models.AutoField(primary_key=True)
    challenge_id = models.TextField(default='')
    challenge_name = models.TextField(default='')
    path = models.TextField(default='')
    ins = models.TextField(default='')    ####测试样例 格式[{"input":"","output":""}]
    answer = models.TextField(default='') 
    content = models.TextField(default='')#
    entryfun = models.TextField(default='')
    level = models.TextField(default='')
    parent_id = models.TextField(default='')
    children_num = models.TextField(default='')
    shixun_id = models.TextField(default='')
    identifier = models.TextField(default='')

