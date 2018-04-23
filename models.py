#coding:utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Member(models.Model):
    expa_id = models.PositiveIntegerField("EXPA ID", primary_key=True, help_text="The EXPA ID of this person")
    name = models.CharField(max_length=64, help_text="THe name of this person")
    team_name = models.CharField(max_length=64, help_text="The name of this person's team", blank=True, null=True)
    podio_id = models.PositiveIntegerField("PODIO ID", help_text="The PODIO ID of this person")
    email = models.EmailField("Email")
    is_active = models.BooleanField("Is EP Manager?", help_text="Mark if this person is active inside the LC currently, and should be assigned EPs")
    is_lcvp = models.BooleanField("Is LCVP?", help_text="Mark if this person should be automatically assigned at the top level as an EP Manager in EXPA during the daily load", default=False)
    team_leader = models.ForeignKey('self', models.SET_NULL, blank=True, null=True, related_name='team_members', default=None)
    team_picture = models.ImageField(blank=True, null=True)
    extra_points = models.PositiveSmallIntegerField(default=0)
    def __str__(self):
        return "%s - %s" % (self.name, self.expa_id)


@python_2_unicode_compatible
class Role(models.Model):
    role = models.CharField(max_length=32, help_text="The name of the role. Follow the manual to see what each role does")
    member = models.ForeignKey(Member, models.CASCADE)
    def __str__(self):
        return "%s - %s" % (self.member, self.role)


@python_2_unicode_compatible
class Office(models.Model):
    name = models.CharField(max_length=32, help_text="The name of the office")
    expa_id = models.PositiveIntegerField("EXPA ID", help_text="The EXPA ID of the country partner. It can be found in EXPA by visiting the eneity page", primary_key=True)
    is_partner = models.BooleanField("Is a country partner?", default=True)
    is_blacklisted = models.BooleanField("Is blacklisted?", default=False)
    def __str__(self):
        return "%s - %s" % (self.name, self.expa_id)
# Create your models here.
