from venv import logger
from rest_framework.response import Response
from rest_framework import status
from pass_and_failed.models import PassFailedStatus
from enrollment.models import Enrollment
from academic_years.models import AcademicYear
from grades.models import Grade, GradePolicy
from levels.models import Level
from subjects.models import Subject
from datetime import date, timedelta
from .promotional_logics import promote_student_if_eligible


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


def determine_pass_fail(student_id, level_id, academic_year_id):
    """Calculate pass/fail status based on grades and update PassFailedStatus."""
    try:
        enrollment = Enrollment.objects.get(student_id=student_id, level_id=level_id, academic_year_id=academic_year_id)
        grades = Grade.objects.filter(enrollment=enrollment)
        subjects = Subject.objects.filter(level_id=level_id)
        policy = GradePolicy.objects.filter(level_id=level_id).first()
        required_grades = policy.required_grades if policy else 8
        passing_threshold = policy.passing_threshold if policy else 50
        conditional_threshold = policy.conditional_threshold if policy and hasattr(policy, 'conditional_threshold') else 40  # Assume conditional threshold

        if not grades.exists():
            status = 'INCOMPLETE'
        else:
            status = 'PASS'  # Default to PASS, adjust based on checks
            for subject in subjects:
                subject_grades = grades.filter(subject=subject)
                if subject_grades.count() < required_grades:
                    status = 'INCOMPLETE'
                    break
                avg_score = sum(g.score for g in subject_grades) / subject_grades.count()
                if avg_score < passing_threshold:
                    if avg_score >= conditional_threshold:
                        status = 'CONDITIONAL'
                    else:
                        status = 'FAIL'
                        break

        # Update or create PassFailedStatus
        pass_failed_status, created = PassFailedStatus.objects.update_or_create(
            student_id=student_id,
            level_id=level_id,
            academic_year_id=academic_year_id,
            defaults={
                'status': status,
                'enrollment': enrollment,
                'grades_complete': status not in ['INCOMPLETE'],
            }
        )
        logger.info(f"{'Created' if created else 'Updated'} PassFailedStatus for student {student_id}, level {level_id}, year {academic_year_id}: {status}")

        # Trigger promotion if PASS or CONDITIONAL
        if status in ['PASS', 'CONDITIONAL']:
            promote_student_if_eligible(pass_failed_status, logger)

        return status
    except Enrollment.DoesNotExist:
        logger.error(f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year_id={academic_year_id}")
        return 'INCOMPLETE'
    except Exception as e:
        logger.error(f"Error determining pass/fail for student {student_id}: {str(e)}")
        return 'INCOMPLETE'

