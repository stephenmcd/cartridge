import mezzanine.core.managers
import mezzanine.pages.managers
from django.db import migrations, models

import cartridge.shop.managers


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0002_auto_20141227_1331"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="billing_detail_email",
            field=models.EmailField(max_length=254, verbose_name="Email"),
        ),
    ]
