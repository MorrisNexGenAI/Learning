from rest_framework import viewsets
from enrollment.models import Enrollment
from enrollment.serializers import EnrollmentSerializer

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

def get_enrollment_by_student_level(student_id, level_id, academic_year_id=None):
    """Fetch enrollment by student, level, and optional academic year."""
    try:
        query = Enrollment.objects.filter(student_id=student_id, level_id=level_id)
        if academic_year_id:
            query = query.filter(academic_year_id=academic_year_id)
        return query.get()
    except Enrollment.DoesNotExist:
        return None