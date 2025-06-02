from subjects.models import Subject
from levels.models import Level
from django.db import transaction

# Use a transaction to ensure all operations are atomic
with transaction.atomic():
    # Delete existing subjects and levels to start fresh
    Subject.objects.all().delete()
    print("Deleted all existing subjects.")
    Level.objects.all().delete()
    print("Deleted all existing levels.")

    # Create levels 1-9
    for i in range(1, 10):
        level = Level.objects.create(name=f"Level {i}")
        print(f"Created Level {i} (ID: {level.id})")

    # Create subjects for each level (1-9)
    subjects = [
        "Mathematics",
        "English",
        "Science",
        "Civics",
        "History",
        "Geography",
        "RME",
        "Vocabulary",
        "Agriculture"
    ]
    for level_id in range(1, 10):
        level = Level.objects.get(id=level_id)
        for idx, subject_name in enumerate(subjects, start=1):
            subject = Subject.objects.create(subject=subject_name, level=level)
            print(f"Created subject: {subject_name} (ID: {subject.id}) for level {level_id}")
            print("Subjects populated successfully for all levels.")