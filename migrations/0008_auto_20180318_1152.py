# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-03-18 11:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yellowCrons', '0007_auto_20180318_1149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='office',
            name='is_partner',
            field=models.BooleanField(default=True, verbose_name='Is a country partner?'),
        ),
    ]