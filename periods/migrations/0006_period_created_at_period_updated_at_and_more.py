# Generated by Django 5.2.2 on 2025-07-09 22:09

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('periods', '0005_alter_period_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='period',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='period',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='period',
            name='period',
            field=models.CharField(choices=[('1st', '1st Period'), ('2nd', '2nd Period'), ('3rd', '3rd Period'), ('1exam', '1st Semester Exam'), ('4th', '4th Period'), ('5th', '5th Period'), ('6th', '6th Period'), ('2exam', '2nd Semester Exam')], default='1st', max_length=9),
        ),
    ]
