# Generated by Django 5.2.1 on 2025-05-21 15:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grade_sheets', '0002_alter_gradesheet_level_alter_gradesheet_period_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GradeSheet',
        ),
    ]
