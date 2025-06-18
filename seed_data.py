from academic_years.models import AcademicYear
from levels.models import Level
from subjects.models import Subject
from students.models import Student
from enrollment.models import Enrollment
from periods.models import Period
from grades.models import Grade
from students.helper import create_pass_failed_status
import datetime

def create_test_data():
    ay = AcademicYear.objects.create(name="2024/2025", start_date="2024-09-01", end_date="2025-06-30")
    next_ay = AcademicYear.objects.create(name="2025/2026", start_date="2025-09-01", end_date="2026-06-30")
    level = Level.objects.create(name="7")
    next_level = Level.objects.create(name="8")
    subject = Subject.objects.create(subject="Mathematics", level=level)
    student = Student.objects.create(firstName="John", lastName="Doe", dob="2010-01-01", gender="M")
    enrollment = Enrollment.objects.create(
        student=student,
        level=level,
        academic_year=ay,
        date_enrolled="2024-09-01",
        enrollment_status="ENROLLED"
    )
    period = Period.objects.create(period="1st", is_exam=False)
    Grade.objects.create(enrollment=enrollment, subject=subject, period=period, score=85)
    return student, level, ay, enrollment