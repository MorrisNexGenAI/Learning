import logging
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from academic_years.models import AcademicYear
from pass_and_failed.models import PassFailedStatus
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF
from .generatePdf import generate_yearly_gradesheet_pdf

logger = logging.getLogger(__name__)

class ReportCardPrintView(APIView):
    """POST /api/grade_sheets/report_card_print/ - Generate yearly report card PDFs."""
    def post(self, request):
        level_id = request.data.get("level_id")
        student_id = request.data.get("student_id")
        academic_year = request.data.get("academic_year")

        if not level_id or not academic_year:
            return Response({"error": "level_id and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            status_obj = PassFailedStatus.objects.filter(
                student_id=student_id, level_id=level_id, academic_year=academic_year_obj
            ).first() if student_id else None
            pass_template = status_obj.status in ['PASS'] if status_obj else True
            conditional = status_obj.status == 'CONDITIONAL' if status_obj else False
            pdf_paths = generate_yearly_gradesheet_pdf(
                level_id=level_id,
                student_id=student_id,
                pass_template=pass_template,
                conditional=conditional,
                academic_year=academic_year
            )

            if not pdf_paths:
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            model.objects.update_or_create(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj,
                defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
            )

            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)