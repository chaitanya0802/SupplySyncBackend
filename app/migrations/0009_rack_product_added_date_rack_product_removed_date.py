# Generated by Django 5.0.4 on 2024-08-15 03:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_rack_product_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='product_added_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rack',
            name='product_removed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
