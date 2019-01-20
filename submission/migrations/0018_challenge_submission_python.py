# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-01-19 13:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0017_auto_20190119_1335'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('challenge_id', models.TextField(default='')),
                ('challenge_name', models.TextField(default='')),
                ('path', models.TextField(default='')),
                ('ins', models.TextField(default='')),
                ('answer', models.TextField(default='')),
                ('content', models.TextField(default='')),
                ('entryfun', models.TextField(default='')),
                ('level', models.TextField(default='')),
                ('parent_id', models.TextField(default='')),
                ('children_num', models.TextField(default='')),
                ('shixun_id', models.TextField(default='')),
                ('identifier', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='Submission_python',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('shixun_id', models.TextField(default='')),
                ('challenge_id', models.TextField(default='')),
                ('student_id', models.TextField(default='')),
                ('submission_time', models.IntegerField()),
                ('submission_count', models.IntegerField()),
                ('submission_id', models.TextField(default='')),
                ('code', models.TextField(default='')),
                ('code_r', models.TextField(default='')),
                ('result', models.TextField(default='')),
                ('w_code', models.TextField(default='')),
            ],
        ),
    ]
