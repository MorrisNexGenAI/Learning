import os
import django
import json
from django.db import transaction

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grade_system.settings")
django.setup()

from levels.models import Level
from enrollment.models import Enrollment
from students.models import Student
from subjects.models import Subject
from grades.models import Grade
from periods.models import Period
from academic_years.models import AcademicYear  # Correct import

@transaction.atomic
def load_data():
    with open('data_backup.json', 'r') as f:
        data = json.load(f)
    
    # Step 1: Create Period records
    period_mapping = {
        1: '1st',
        2: '2nd',  # period_id=1 maps to period='1st'
        3: '3rd',
        4:'1exam',
        5:'4th',
        6:'5th',
        7:'2exam'  # period_id=3 maps to period='3rd'
    }
    for period_id, period_value in period_mapping.items():
        period, created = Period.objects.get_or_create(
            id=period_id,
            defaults={'period': period_value}
        )
        print(f"{'Created' if created else 'Found'} Period: ID {period.id}, Period {period.period}")
    
    # Step 2: Create new levels
    level_mapping = {
        28: {'id': 7, 'name': '7'},
        29: {'id': 8, 'name': '8'},
        30: {'id': 9, 'name': '9'}
    }
    for old_id, new_data in level_mapping.items():
        level, created = Level.objects.get_or_create(
            id=new_data['id'],
            defaults={'name': new_data['name']}
        )
        print(f"{'Created' if created else 'Found'} Level: ID {level.id}, Name {level.name}")
    
    # Step 3: Load other models
    for item in data:
        model = item['model']
        fields = item['fields']
        
        if model == 'students.student':
            student, created = Student.objects.get_or_create(
                pk=item['pk'],
                defaults={
                    'firstName': fields['firstName'],
                    'lastName': fields['lastName'],
                    'gender': fields['gender'],
                    'dob': fields['dob'],
                    'created_at': fields['created_at']
                }
            )
            print(f"{'Created' if created else 'Found'} Student: ID {student.pk}, Name {student.firstName} {student.lastName}")
        
        elif model == 'academic_years.academicyear':
            ay, created = AcademicYear.objects.get_or_create(
                pk=item['pk'],
                defaults={
                    'name': fields['name'],
                    'start_date': fields['start_date'],
                    'end_date': fields['end_date']
                }
            )
            print(f"{'Created' if created else 'Found'} Academic Year: ID {ay.pk}, Name {ay.name}")
        
        elif model == 'subjects.subject':
            level_id = fields['level']
            if level_id in level_mapping:
                new_level = Level.objects.get(id=level_mapping[level_id]['id'])
                subject, created = Subject.objects.get_or_create(
                    subject=fields['subject'],
                    level=new_level,
                    defaults={'pk': item['pk']}
                )
                print(f"{'Created' if created else 'Found'} Subject: ID {subject.pk}, Name {subject.subject}, Level {subject.level.name}")
        
        elif model == 'enrollment.enrollment':
            level_id = fields['level']
            if level_id in level_mapping:
                new_level = Level.objects.get(id=level_mapping[level_id]['id'])
                enrollment, created = Enrollment.objects.get_or_create(
                    pk=item['pk'],
                    defaults={
                        'student_id': fields['student'],
                        'level': new_level,
                        'academic_year_id': fields['academic_year'],
                        'date_enrolled': fields['date_enrolled']
                    }
                )
                print(f"{'Created' if created else 'Found'} Enrollment: ID {enrollment.pk}, Student ID {enrollment.student_id}, Level {enrollment.level.name}")
        
        elif model == 'grades.grade':
            grade, created = Grade.objects.get_or_create(
                pk=item['pk'],
                defaults={
                    'enrollment_id': fields['enrollment'],
                    'subject_id': fields['subject'],
                    'period_id': fields['period'],
                    'score': fields['score']
                }
            )
            print(f"{'Created' if created else 'Found'} Grade: ID {grade.pk}, Enrollment ID {grade.enrollment_id}, Subject ID {grade.subject_id}")

# Run the script
load_data()

# Verify data
print("\nVerification:")
print("Periods:", Period.objects.count())
print("Levels:", Level.objects.count())
for l in Level.objects.all():
    print(f"Level: ID {l.id}, Name {l.name}")
print("Students:", Student.objects.count())
print("Academic Years:", AcademicYear.objects.count())
print("Subjects:", Subject.objects.count())
print("Enrollments:", Enrollment.objects.count())
print("Grades:", Grade.objects.count())
