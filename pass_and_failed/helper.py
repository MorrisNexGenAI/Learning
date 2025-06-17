from rest_framework.response import Response
from rest_framework import status
from .models import PassFailedStatus
from enrollment.models import Enrollment
from academic_years.models import AcademicYear
from grades.models import Grade
from levels.models import Level
from subjects.models import Subject

def handle_validate_status(view, request, pk, logger):
    try:
        status_obj = view.get_object()
        status_value = request.data.get('status')
        validated_by = request.data.get('validated_by')

        if status_value not in ['PASS', 'FAIL', 'CONDITIONAL', 'PENDING', 'INCOMPLETE']:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        if not status_obj.grades_complete and status_value in ['PASS', 'FAIL', 'CONDITIONAL']:
            return Response({"error": "Grades incomplete"}, status=status.HTTP_200_OK)

        status_obj.status = status_value
        status_obj.validated_by = validated_by
        status_obj.save()
        logger.info(f"Status validated: {status_obj.id} as {status_value}")

        if status_value in ['PASS', 'CONDITIONAL']:
            promote_student_if_eligible(status_obj, logger)

        serializer = view.get_serializer(status_obj)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Error validating status {pk}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def promote_student_if_eligible(status_obj, logger):
    current_level = status_obj.level
    next_level = Level.objects.filter(order__gt=current_level.order).order_by('order').first()

    if next_level:
        current_enrollment = Enrollment.objects.filter(
            student=status_obj.student,
            level=current_level,
            academic_year=status_obj.academic_year
        ).first()

        if current_enrollment:
            current_enrollment.status = 'PROMOTED'
            current_enrollment.save()

            Enrollment.objects.create(
                student=status_obj.student,
                level=next_level,
                academic_year=status_obj.academic_year,
                enrollment_date=status_obj.academic_year.start_date,
                status='ENROLLED'
            )
            logger.info(f"Student {status_obj.student.id} auto-promoted to level {next_level.id}")
        else:
            logger.warning(f"No current enrollment found for student {status_obj.student.id}")
    else:
        logger.warning(f"No higher level found for promotion from level {current_level.id}")

def initialize_missing_statuses(level_id, academic_year_name, logger):
    try:
        level = Level.objects.get(id=level_id)
        academic_year = AcademicYear.objects.get(name=academic_year_name)
        enrollments = Enrollment.objects.filter(level=level, academic_year=academic_year)

        for enrollment in enrollments:
            if not PassFailedStatus.objects.filter(
                student=enrollment.student,
                level=level,
                academic_year=academic_year
            ).exists():
                grades = Grade.objects.filter(enrollment=enrollment)
                subject_count = Subject.objects.filter(level=level).count()
                expected_grades = subject_count * 8 if subject_count else 1
                grades_complete = grades.exists()
                status_value = 'INCOMPLETE' if grades.count() < expected_grades else 'PENDING'

                PassFailedStatus.objects.create(
                    student=enrollment.student,
                    level=level,
                    academic_year=academic_year,
                    enrollment=enrollment,
                    grades_complete=grades_complete,
                    status=status_value,
                    template_name='pass_template.html'
                )
                logger.info(f"Created PassFailedStatus for student {enrollment.student.id}, level {level.id}, year {academic_year.name}")

        return PassFailedStatus.objects.filter(
            student__in=[e.student_id for e in enrollments]
        )

    except (Level.DoesNotExist, AcademicYear.DoesNotExist) as e:
        logger.error(f"Error filtering statuses: {str(e)}")
        return PassFailedStatus.objects.none()
    except Exception as e:
        logger.error(f"Unexpected error in initialize_missing_statuses: {str(e)}")
        return PassFailedStatus.objects.none()