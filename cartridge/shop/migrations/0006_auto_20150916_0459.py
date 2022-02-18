from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0005_auto_20150527_1127"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="key",
            field=models.CharField(max_length=40, db_index=True),
        ),
    ]
