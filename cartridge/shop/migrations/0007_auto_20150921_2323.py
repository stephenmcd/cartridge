# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cartridge.shop.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_auto_20150916_0459'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=cartridge.shop.fields.SKUField(max_length=20, null=True, verbose_name='SKU', blank=True),
        ),
        migrations.AlterField(
            model_name='productvariation',
            name='sku',
            field=cartridge.shop.fields.SKUField(max_length=20, null=True, verbose_name='SKU', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='product',
            unique_together=set([('sku', 'site')]),
        ),
    ]
