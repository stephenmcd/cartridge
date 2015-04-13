# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mezzanine.pages.managers
import mezzanine.core.managers
import cartridge.shop.managers


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_auto_20141227_1331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='billing_detail_email',
            field=models.EmailField(max_length=254, verbose_name='Email'),
        ),
    ]
