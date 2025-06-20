from rest_framework.test import APIRequestFactory
from grade_sheets.views import GradeSheetViewSet  # Adjust import path if needed
from students.models import Student
from enrollment.models import Enrollment
from levels.models import Level
from academic_years.models import AcademicYear
from subjects.models import Subject
from periods.models import Period

# Get the objects by their IDs
student = Student.objects.get(id=1)
level = Level.objects.get(id=1)
year = AcademicYear.objects.get(id=6)  # 2026/2027
subject = Subject.objects.get(id=9)    # Agriculture
period = Period.objects.get(period="1st")
enrollment = Enrollment.objects.get(student=student, level=level, academic_year=year)

# Prepare the grades list
grades = [
    {
        "student_id": student.id,
        "score": 88,  # Example score
        "period_id": period.id
    }
]

# Prepare the POST data
data = {
    "level": level.id,
    "subject_id": subject.id,
    "period_id": period.id,
    "grades": grades,
    "academic_year": year.name
}

# Create the request and call the view
factory = APIRequestFactory()
request = factory.post('/api/grade_sheets/input/', data, format='json')
view = GradeSheetViewSet.as_view({'post': 'input_grades'})
response = view(request)
print(response.data)

from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear
from enrollment.models import Enrollment
from datetime import date

# Get the level and academic year
level = Level.objects.get(name="7")
year = AcademicYear.objects.get(name="2024/2025")

# Add the student with all required fields
student = Student.objects.create(
    firstName="John",
    lastName="Doe",
    dob="2012-05-15",      # Example date of birth
    gender="M"
)

# Enroll the student (provide date_enrolled)
enrollment = Enrollment.objects.create(
    student=student,
    level=level,
    academic_year=year,
    date_enrolled=date.today()  # or date(2024, 9, 1)
)




