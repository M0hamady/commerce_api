# Generated by Django 5.0.2 on 2024-08-18 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_alter_product_options_product_position'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='position',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
    ]
