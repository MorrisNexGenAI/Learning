# Generated by Django 5.2.1 on 2025-06-18 08:54

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0008_grade_updated_at'),
        ('levels', '0012_alter_level_options_level_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grade',
            name='score',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0, message='Score must be at least 0'), django.core.validators.MaxValueValidator(100, message='Score cannot exceed 100')]),
        ),
        migrations.CreateModel(
            name='GradePolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_weight', models.FloatField(default=0.5)),
                ('exam_weight', models.FloatField(default=0.5)),
                ('required_grades', models.IntegerField(default=8)),
                ('passing_threshold', models.IntegerField(default=50, validators=[django.core.validators.MinValueValidator(0, message='Threshold must be at least 0'), django.core.validators.MaxValueValidator(100, message='Threshold cannot exceed 100')])),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='levels.level')),
            ],
            options={
                'unique_together': {('level',)},
            },
        ),
    ]
