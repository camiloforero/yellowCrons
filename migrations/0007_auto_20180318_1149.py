# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-03-18 11:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yellowCrons', '0006_countrypartner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Office',
            fields=[
                ('name', models.CharField(help_text='The name of the office', max_length=32)),
                ('expa_id', models.PositiveIntegerField(help_text='The EXPA ID of the country partner. It can be found in EXPA by visiting the eneity page', primary_key=True, serialize=False, verbose_name='EXPA ID')),
                ('is_partner', models.BooleanField(default=False, verbose_name='Is a country partner?')),
                ('is_blacklisted', models.BooleanField(default=False, verbose_name='Is blacklisted?')),
            ],
        ),
        migrations.DeleteModel(
            name='CountryPartner',
        ),
    ]