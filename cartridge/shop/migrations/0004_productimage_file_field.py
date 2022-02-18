import mezzanine.core.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0003_emailfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productimage",
            name="file",
            field=mezzanine.core.fields.FileField(verbose_name="Image", max_length=255),
        ),
    ]
