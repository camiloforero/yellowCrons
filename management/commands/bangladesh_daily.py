# coding:utf-8
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
from yellowCrons import bangladesh_scripts

class Command(BaseCommand):
    help = "Runs the daily PODIO notifications for AIESEC in Bangladesh" 

    def handle(self, *args, **options):
        bangladesh_scripts.bangladesh_daily_load()
