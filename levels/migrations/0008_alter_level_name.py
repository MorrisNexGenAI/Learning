# Generated by Django 5.2.1 on 2025-05-31 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('levels', '0007_rename_levels_level_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='level',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
