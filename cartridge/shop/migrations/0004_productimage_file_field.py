# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mezzanine.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_emailfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='file',
            field=mezzanine.core.fields.FileField(verbose_name='Image', max_length=255),
        ),
    ]
