import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grade_system.settings")
django.setup()

from subjects.models import Subject
from levels.models import Level
from django.db import transaction

with transaction.atomic():
    Subject.objects.all().delete()
    print("Deleted all existing subjects.")
    Level.objects.all().delete()
    print("Deleted all existing levels.")

    # Create levels 7-9 and store them
    levels = []
    for i in range(7, 10):  # Changed from range(1, 10) to range(7, 10)
        level = Level.objects.create(name=f"Level {i}")
        levels.append(level)
        print(f"Created Level {i} (ID: {level.id})")

    subjects = [
        "Mathematics", "English", "Science", "Civics", "History",
        "Geography", "RME", "Vocabulary", "Agriculture"
    ]

    # Create subjects for each level
    for level in levels:
        for subject_name in subjects:
            subject = Subject.objects.create(subject=subject_name, level=level)
            print(f"Created subject: {subject_name} (ID: {subject.id}) for level {level.name} (ID: {level.id})")

print("Subjects populated successfully for levels 7, 8, and 9.")