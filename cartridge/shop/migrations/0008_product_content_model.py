# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_auto_20150921_2323'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='content_model',
            field=models.CharField(editable=False, max_length=50, null=True),
        ),
    ]
