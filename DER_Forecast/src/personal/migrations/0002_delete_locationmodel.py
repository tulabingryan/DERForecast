# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-18 00:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LocationModel',
        ),
    ]