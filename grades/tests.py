from subjects.models import Subject
from grades.models import Grade

# Define the fixed subjects (order determines ID: 1 to 9)
fixed_subjects = [
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

# Step 1: Delete all existing subjects and grades to start fresh
for level_id in range(1, 10):
    # Delete all grades for this level to avoid foreign key issues
    Grade.objects.filter(enrollment__level_id=level_id).delete()
    print(f"Deleted all grades for level {level_id}")
    
    # Delete all subjects for this level
    Subject.objects.filter(level_id=level_id).delete()
    print(f"Deleted all subjects for level {level_id}")

# Step 2: Recreate subjects with IDs 1-9 for each level
for level_id in range(1, 10):
    for idx, subject_name in enumerate(fixed_subjects, start=1):
        # Create subject with ID corresponding to its position (1-9)
        subject, created = Subject.objects.get_or_create(level_id=level_id, subject=subject_name)
        if created:
            print(f"Created subject: {subject_name} (ID {idx}) for level {level_id}")
        else:
            print(f"Subject {subject_name} already exists for level {level_id}")
print("Subjects reset successfully with IDs 1-9 per level.")

