import logging
import os
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import PassFailedStatusSerializer
from .models import PassFailedStatus
from academic_years.models import AcademicYear
from .helper import initialize_missing_statuses
from evaluations.statues_logics import handle_validate_status
from grade_sheets.yearly_pdf import generate_yearly_pdf
from grade_sheets.models import StudentGradeSheetPDF

logger = logging.getLogger(__name__)

class PassFailedStatusViewSet(viewsets.ModelViewSet):
    queryset = PassFailedStatus.objects.all()
    serializer_class = PassFailedStatusSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        level_id = self.request.query_params.get('level_id')
        academic_year = self.request.query_params.get('academic_year')

        if level_id and academic_year:
            try:
                initialize_missing_statuses(level_id, academic_year, logger)
                academic_year_obj = AcademicYear.objects.get(name=academic_year)
                queryset = queryset.filter(level_id=level_id, academic_year=academic_year_obj)
            except AcademicYear.DoesNotExist:
                logger.error(f"Academic year {academic_year} not found")
                return PassFailedStatus.objects.none()

        return queryset.order_by('id')  # Ensure consistent pagination

    @action(detail=True, methods=['POST'], url_path='validate')
    def validate_status(self, request, pk=None):
        logger.debug(f"Validating status for pk={pk}, data={request.data}")
        return handle_validate_status(self, request, pk, logger)

    @action(detail=True, methods=['POST'], url_path='print')
    def print_status(self, request, pk=None):
        try:
            status_obj = self.get_object()
            logger.debug(f"Printing status for pk={pk}, student={status_obj.student.id}, level={status_obj.level.id}")

            pass_template = status_obj.status in ['PASS', 'CONDITIONAL']
            pdf_paths = generate_yearly_pdf(
                level_id=status_obj.level.id,
                student_id=status_obj.student.id,
                pass_template=pass_template,
                conditional=status_obj.status == 'CONDITIONAL',
                academic_year_id=status_obj.academic_year.id  # Use numeric ID
            )

            if not pdf_paths:
                logger.warning(f"No PDF generated for student {status_obj.student.id}")
                return Response({"error": "No PDF generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            StudentGradeSheetPDF.objects.update_or_create(
                level_id=status_obj.level.id,
                student_id=status_obj.student.id,
                academic_year=status_obj.academic_year,
                defaults={
                    'pdf_path': pdf_path,
                    'filename': pdf_filename,
                }
            )

            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            logger.info(f"Generated PDF for student {status_obj.student.id}: {pdf_path}")
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error printing status {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)