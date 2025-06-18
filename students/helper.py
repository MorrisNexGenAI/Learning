from .models import Student
from enrollment.models import Enrollment
from pass_and_failed.models import PassFailedStatus
from grades.models import Grade, GradePolicy
from subjects.models import Subject

def get_students_by_level(level_id, academic_year_id=None):
    """Fetch students by level ID, optionally filtered by academic year."""
    queryset = Student.objects.filter(enrollment__level_id=level_id)
    if academic_year_id:
        queryset = queryset.filter(enrollment__academic_year_id=academic_year_id)
    return queryset.select_related('enrollment').distinct()

def format_student_data(student):
    """Format student data for use in grade sheets."""
    return {
        "student_id": student.id,
        "student_name": f"{student.firstName} {student.lastName}",
        "subjects": []
    }

def format_student_name(student):
    """Format student full name."""
    return f"{student.firstName} {self.lastName}"

def create_enrollment_for_student(student, level, academic_year):
    """Create an enrollment record."""
    return Enrollment.objects.create(
        student=student,
        level=level,
        academic_year=academic_year
    )

def create_pass_failed_status(student, level, academic_year, enrollment):
    """Auto-create pass/fail status for a student."""
    grades = Grade.objects.filter(enrollment=enrollment)
    policy = GradePolicy.objects.filter(level=level).first()
    required_grades = policy.required_grades if policy else 8
    passing_threshold = policy.passing_threshold if policy else 50.0
    subject_count = Subject.objects.filter(level=level).count()
    expected_grades = subject_count * required_grades
    grades_complete = grades.exists()
    status_value = 'INCOMPLETE'

    if grades.count() >= expected_grades:
        for subject in Subject.objects.filter(level=level):
            subject_grades = grades.filter(subject=subject)
            if subject_grades.count() < required_grades:
                status_value = 'INCOMPLETE'
                break
            avg_score = sum(g.score for g in subject_grades) / subject_grades.count()
            if avg_score < passing_threshold:
                status_value = 'FAILED'
                break
        else:
            status_value = 'PASSED'

    return PassFailedStatus.objects.create(
        student=student,
        level=level,
        academic_year=academic_year,
        enrollment=enrollment,
        grades_complete=grades_complete,
        status=status_value,
        template_name='pass_template.html'
    )