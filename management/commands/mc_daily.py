# coding:utf-8
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
from yellowCrons import malaysia_scripts

class Command(BaseCommand):
    help = "Runs the daily cronjobs of AIESEC in Malaysia" 

    def handle(self, *args, **options):
        malaysia_scripts.malaysia_daily_load()
