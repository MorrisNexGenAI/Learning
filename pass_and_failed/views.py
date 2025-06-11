from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PassFailedStatus
from .serializers import PassFailedStatusSerializer
from .utils import validate_student_grades, promote_student
from grade_sheets.yearly_utils import generate_yearly_gradesheet_pdf
from students.models import Student
from enrollment.models import Enrollment
import logging
import datetime
import os
from django.http import FileResponse

logger = logging.getLogger(__name__)

class PassFailedStatusViewSet(viewsets.ModelViewSet):
    queryset = PassFailedStatus.objects.all()
    serializer_class = PassFailedStatusSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        level_id = self.request.query_params.get('level_id')
        academic_year_id = self.request.query_params.get('academic_year_id')
        if level_id:
            queryset = queryset.filter(level_id=level_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='by_level')
    def list_by_level(self, request):
        level_id = request.query_params.get('level_id')
        academic_year_id = request.query_params.get('academic_year_id')
        if not level_id or not academic_year_id:
            return Response({"error": "level_id and academic_year_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Fetching PassFailedStatus for level_id={level_id}, academic_year_id={academic_year_id}")
        enrollments = Enrollment.objects.filter(level_id=level_id, academic_year_id=academic_year_id).select_related('student')
        logger.info(f"Found {enrollments.count()} enrollments")

        result = []
        for enrollment in enrollments:
            student = enrollment.student
            status_obj, created = PassFailedStatus.objects.get_or_create(
                student=student,
                level_id=level_id,
                academic_year_id=academic_year_id,
                defaults={'enrollment': enrollment, 'status': 'INCOMPLETE', 'grades_complete': False}
            )
            if created:
                logger.info(f"Created PassFailedStatus for student_id={student.id}")
            is_complete, message = validate_student_grades(student.id, level_id, academic_year_id)
            if not is_complete and status_obj.status == 'INCOMPLETE':
                status_obj.status = 'INCOMPLETE'
                status_obj.grades_complete = False
                status_obj.save()
            result.append({
                'id': status_obj.id,
                'student_id': student.id,
                'student_name': f"{student.firstName} {student.lastName}",
                'status': status_obj.status,
                'is_complete': is_complete,
                'validation_message': message,
                'can_print': status_obj.status != 'INCOMPLETE',
                'grades_complete': status_obj.grades_complete
            })
        logger.info(f"Returning {len(result)} PassFailedStatus records")
        return Response(result)

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_status(self, request, pk=None):
        status_obj = self.get_object()
        new_status = request.data.get('status')
        validated_by = request.data.get('validated_by')
        if new_status not in ['PASS', 'FAIL', 'CONDITIONAL']:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        is_complete, message = validate_student_grades(status_obj.student.id, status_obj.level.id, status_obj.academic_year.id)
        if not is_complete:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
        status_obj.status = new_status
        status_obj.validated_at = datetime.datetime.now()
        status_obj.validated_by = validated_by
        status_obj.grades_complete = True
        status_obj.save()
        serializer = self.get_serializer(status_obj)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='promote')
    def promote(self, request, pk=None):
        status_obj = self.get_object()
        success, message = promote_student(status_obj.id)
        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

class ReportCardPrintView(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='print')
    def print_report_card(self, request):
        level_id = request.data.get('level_id')
        student_id = request.data.get('student_id')
        academic_year_id = request.data.get('academic_year_id')
        if not level_id or not academic_year_id:
            return Response({"error": "level_id and academic_year_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if student_id:
                status_obj = PassFailedStatus.objects.get(
                    student_id=student_id, level_id=level_id, academic_year_id=academic_year_id
                )
                if status_obj.status == 'INCOMPLETE':
                    return Response({"error": "Student is incomplete, cannot print report card"}, status=status.HTTP_400_BAD_REQUEST)
                template_name = f"yearly_card_{status_obj.status.lower()}.docx"
                pdf_paths = generate_yearly_gradesheet_pdf(level_id, student_id, template_name)
            else:
                statuses = PassFailedStatus.objects.filter(level_id=level_id, academic_year_id=academic_year_id)
                if any(s.status == 'INCOMPLETE' for s in statuses):
                    return Response({"error": "Not all students are validated, cannot print level report card"}, status=status.HTTP_400_BAD_REQUEST)
                pdf_paths = []
                for status in statuses:
                    template_name = f"yearly_card_{status.status.lower()}.docx"
                    pdf_paths.extend(generate_yearly_gradesheet_pdf(level_id, status.student.id, template_name))

            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            view_url = f"/api/pass_failed_statuses/print/view?file={os.path.basename(pdf_path)}"
            return Response({"view_url": view_url})
        except PassFailedStatus.DoesNotExist:
            return Response({"error": "Student status not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error printing report card: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
