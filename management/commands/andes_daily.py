# coding:utf-8
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
from yellowCrons import andes_scripts

class Command(BaseCommand):
    help = "Reloads all local and national offices' stats in measures such as opens, applied, accepted, realized and completed experiencies"

    def handle(self, *args, **options):
        andes_scripts.andes_daily_load()
