from rest_framework import viewsets
from enrollment.models import Enrollment
from enrollment.serializers import EnrollmentSerializer

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

def get_enrollment_by_student_level(student_id, level_id):
    """Fetch enrollment by student and level."""
    try:
        return Enrollment.objects.get(student_id=student_id, level_id=level_id)
    except Enrollment.DoesNotExist:
        return None