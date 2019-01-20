import ipaddress
import json
from django.http import JsonResponse
from django.http import HttpResponse
from account.decorators import login_required, check_contest_permission
from judge.tasks import judge_task
from judge.dispatcher import JudgeDispatcher
import sys
import os
sys.path.append('/home/admin/OJGitLab/OnlineJudge/submission/views')
#import test_repair_ly
from problem.models import Problem, ProblemRuleType
from contest.models import Contest, ContestStatus, ContestRuleType
from options.options import SysOptions
from utils.api import APIView, validate_serializer
from utils.throttling import TokenBucket
from utils.captcha import Captcha
from utils.cache import cache
from ..models import Submission
from ..serializers import (CreateSubmissionSerializer, SubmissionModelSerializer,
                           ShareSubmissionSerializer)
from ..serializers import SubmissionSafeModelSerializer, SubmissionListSerializer

WRONG_CODES={
    'a':'常量',
    'b':'变量',
    'c':'表达式',
    'd':'输出语句',
    'e':'列表',
    'f':'字典',
    'g':'元祖',
    'h':'集合',
    'i':'字符串',
    'j':'一元运算符',
    'k':'二元运算符',
    'l':'If条件语句',
    'm':'循环语句',
    'n':'函数使用',
    'o':'函数Return语句'
}

class HintAPI(APIView):
    def get(self,request):
        submission_id = request.GET.get("id")
        pid=Submission.objects.get(id=submission_id).problem_id
        code=Submission.objects.get(id=submission_id).code
        rinfo=Submission.objects.get(id=submission_id).repair_info
        wkunits=''
        if len(rinfo)<1:
            file = open('/home/admin/OJGitLab/OnlineJudge/submission/views/proid.txt','w')
            file.write(str(pid))
            file.close()
            f0 = open('/home/admin/OJGitLab/OnlineJudge/submission/views/w_code.c','w')
            f0.write(code)
            f0.close()
            os.system('python /home/admin/OJGitLab/OnlineJudge/submission/views/test.py')
            f = open('/home/admin/OJGitLab/OnlineJudge/submission/views/feedback.txt','r')
            feedback = f.read()
            f.close()
            f1 = open('/home/admin/OJGitLab/OnlineJudge/submission/views/repair_info.txt','r')
            rinfo=f1.read()
            f1.close()
            f2 = open('/home/admin/OJGitLab/OnlineJudge/submission/views/wcodes.txt','r')
            wcode=f2.read()
            f2.close()
            for i in wcode:
                wkunits+=WRONG_CODES[i]+' '
            #wkunits=wkunits[:-1]
            item=Submission.objects.get(id=submission_id)
            item.repair_info=rinfo
            item.feedback_info=feedback
            item.wku_info=wkunits
            item.save()
            return JsonResponse({'repair_info': rinfo, 'feedback': feedback,'wcode':wkunits})
        else:
            feedback=Submission.objects.get(id=submission_id).feedback_info
            wkunits=Submission.objects.get(id=submission_id).wku_info
            return JsonResponse({'repair_info': rinfo, 'feedback': feedback,'wcode':wkunits})
            

class SubmissionAPI(APIView):
    def throttling(self, request):
        user_bucket = TokenBucket(key=str(request.user.id),
                                  redis_conn=cache, **SysOptions.throttling["user"])
        can_consume, wait = user_bucket.consume()
        if not can_consume:
            return "Please wait %d seconds" % (int(wait))

        ip_bucket = TokenBucket(key=request.session["ip"],
                                redis_conn=cache, **SysOptions.throttling["ip"])
        can_consume, wait = ip_bucket.consume()
        if not can_consume:
            return "Captcha is required"

    @validate_serializer(CreateSubmissionSerializer)
    @login_required
    def post(self, request):
        data = request.data
        hide_id = False
        if data.get("contest_id"):
            try:
                contest = Contest.objects.get(id=data["contest_id"], visible=True)
            except Contest.DoesNotExist:
                return self.error("Contest doesn't exist.")
            if contest.status == ContestStatus.CONTEST_ENDED:
                return self.error("The contest have ended")
            if not request.user.is_contest_admin(contest):
                if contest.status == ContestStatus.CONTEST_NOT_START:
                    return self.error("Contest have not started")
                user_ip = ipaddress.ip_address(request.session.get("ip"))
                if contest.allowed_ip_ranges:
                    if not any(user_ip in ipaddress.ip_network(cidr, strict=False) for cidr in contest.allowed_ip_ranges):
                        return self.error("Your IP is not allowed in this contest")

            if not contest.problem_details_permission(request.user):
                hide_id = True

        if data.get("captcha"):
            if not Captcha(request).check(data["captcha"]):
                return self.error("Invalid captcha")
        error = self.throttling(request)
        if error:
            return self.error(error)

        try:
            problem = Problem.objects.get(id=data["problem_id"], contest_id=data.get("contest_id"), visible=True)
        except Problem.DoesNotExist:
            return self.error("Problem not exist")
        if data["language"] not in problem.languages:
            return self.error(f"{data['language']} is now allowed in the problem")
        submission = Submission.objects.create(user_id=request.user.id,
                                               username=request.user.username,
                                               language=data["language"],
                                               code=data["code"],
                                               problem_id=problem.id,
                                               ip=request.session["ip"],
                                               contest_id=data.get("contest_id"))
        # use this for debug
        JudgeDispatcher(submission.id, problem.id).judge()
        judge_task.delay(submission.id, problem.id)
        if hide_id:
            return self.success()
        else:
            return self.success({"submission_id": submission.id})

    @login_required
    def get(self, request):
        submission_id = request.GET.get("id")
        if not submission_id:
            return self.error("Parameter id doesn't exist")
        try:
            submission = Submission.objects.select_related("problem").get(id=submission_id)
        except Submission.DoesNotExist:
            return self.error("Submission doesn't exist")
        if not submission.check_user_permission(request.user):
            return self.error("No permission for this submission")

        if submission.problem.rule_type == ProblemRuleType.OI or request.user.is_admin_role():
            submission_data = SubmissionModelSerializer(submission).data
        else:
            submission_data = SubmissionSafeModelSerializer(submission).data
        # 是否有权限取消共享
        submission_data["can_unshare"] = submission.check_user_permission(request.user, check_share=False)
        return self.success(submission_data)

    @validate_serializer(ShareSubmissionSerializer)
    @login_required
    def put(self, request):
        """
        share submission
        """
        try:
            submission = Submission.objects.select_related("problem").get(id=request.data["id"])
        except Submission.DoesNotExist:
            return self.error("Submission doesn't exist")
        if not submission.check_user_permission(request.user, check_share=False):
            return self.error("No permission to share the submission")
        if submission.contest and submission.contest.status == ContestStatus.CONTEST_UNDERWAY:
            return self.error("Can not share submission now")
        submission.shared = request.data["shared"]
        submission.save(update_fields=["shared"])
        return self.success()


class SubmissionListAPI(APIView):
    def get(self, request):
        if not request.GET.get("limit"):
            return self.error("Limit is needed")
        if request.GET.get("contest_id"):
            return self.error("Parameter error")

        submissions = Submission.objects.filter(contest_id__isnull=True).select_related("problem__created_by")
        problem_id = request.GET.get("problem_id")
        myself = request.GET.get("myself")
        result = request.GET.get("result")
        username = request.GET.get("username")
        if problem_id:
            try:
                problem = Problem.objects.get(_id=problem_id, contest_id__isnull=True, visible=True)
            except Problem.DoesNotExist:
                return self.error("Problem doesn't exist")
            submissions = submissions.filter(problem=problem)
        if (myself and myself == "1") or not SysOptions.submission_list_show_all:
            submissions = submissions.filter(user_id=request.user.id)
        elif username:
            submissions = submissions.filter(username__icontains=username)
        if result:
            submissions = submissions.filter(result=result)
        data = self.paginate_data(request, submissions)
        data["results"] = SubmissionListSerializer(data["results"], many=True, user=request.user).data
        return self.success(data)


class ContestSubmissionListAPI(APIView):
    @check_contest_permission(check_type="submissions")
    def get(self, request):
        if not request.GET.get("limit"):
            return self.error("Limit is needed")

        contest = self.contest
        submissions = Submission.objects.filter(contest_id=contest.id).select_related("problem__created_by")
        problem_id = request.GET.get("problem_id")
        myself = request.GET.get("myself")
        result = request.GET.get("result")
        username = request.GET.get("username")
        if problem_id:
            try:
                problem = Problem.objects.get(_id=problem_id, contest_id=contest.id, visible=True)
            except Problem.DoesNotExist:
                return self.error("Problem doesn't exist")
            submissions = submissions.filter(problem=problem)

        if myself and myself == "1":
            submissions = submissions.filter(user_id=request.user.id)
        elif username:
            submissions = submissions.filter(username__icontains=username)
        if result:
            submissions = submissions.filter(result=result)

        # filter the test submissions submitted before contest start
        if contest.status != ContestStatus.CONTEST_NOT_START:
            submissions = submissions.filter(create_time__gte=contest.start_time)

        # 封榜的时候只能看到自己的提交
        if contest.rule_type == ContestRuleType.ACM:
            if not contest.real_time_rank and not request.user.is_contest_admin(contest):
                submissions = submissions.filter(user_id=request.user.id)

        data = self.paginate_data(request, submissions)
        data["results"] = SubmissionListSerializer(data["results"], many=True, user=request.user).data
        return self.success(data)


class SubmissionExistsAPI(APIView):
    def get(self, request):
        if not request.GET.get("problem_id"):
            return self.error("Parameter error, problem_id is required")
        return self.success(request.user.is_authenticated() and
                            Submission.objects.filter(problem_id=request.GET["problem_id"],
                                                      user_id=request.user.id).exists())
