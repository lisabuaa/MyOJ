from django.db import models
from utils.models import JSONField

from account.models import User
from contest.models import Contest
from utils.models import RichTextField
from utils.constants import Choices
from problem.models import Problem
from submission.models import Submission

from utils.shortcuts import rand_str


class ProblemClarify(models.Model):
    id = models.TextField(default=rand_str, primary_key=True, db_index=True)
    problem = models.ForeignKey(Problem)
    submission = models.ForeignKey(Submission)
    amount = models.BigIntegerField(default=0)


    class Meta:
        db_table = "problemClarify"
        unique_together = (("problem", "submission"),)
        ordering = ("-amount",)

    def add_amount(self):
        self.amount = models.F("amount") + 1
        self.save(update_fields=["amount"])
