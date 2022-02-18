from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0008_product_content_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Leave blank to have the URL auto-generated from the title.",
                max_length=2000,
                verbose_name="URL",
            ),
            preserve_default=False,
        ),
    ]
