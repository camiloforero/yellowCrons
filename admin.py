#coding:utf-8
from django.contrib import admin
from .models import Member, Role, Office 

# Register your models here.o

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display= ('name', 'is_active', 'is_lcvp', 'team_leader')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role', 'member')

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'expa_id', 'is_partner', 'is_blacklisted')
