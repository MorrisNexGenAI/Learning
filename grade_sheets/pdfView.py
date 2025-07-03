import logging
import os
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from levels.models import Level
from academic_years.models import AcademicYear
from grades.models import Grade
from levels.helper import get_level_by_id
from students.helper import get_students_by_level
from enrollment.models import Enrollment
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF
from .generatePdf import generate_gradesheet_pdf, generate_yearly_gradesheet_pdf

logger = logging.getLogger(__name__)

class GradeSheetViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/generate')
    def generate_gradesheet_pdf(self, request):
        """GET /api/grade_sheets_pdf/gradesheet/pdf/generate/ - Generate periodic PDFs."""
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        student_id = request.query_params.get('student_id')

        logger.info(f"Received request for periodic PDF: level_id={level_id}, academic_year={academic_year}, student_id={student_id}")

        try:
            if not level_id or not academic_year:
                logger.error("Missing required parameters: level_id or academic_year")
                return Response({"error": "level_id and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)

            level = get_level_by_id(level_id)
            if not level:
                logger.error(f"Invalid level_id: {level_id}")
                return Response({"error": f"Invalid level_id: {level_id}"}, status=status.HTTP_400_BAD_REQUEST)

            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            logger.info(f"Found academic year: {academic_year_obj.name} (ID: {academic_year_obj.id})")

            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            filter_kwargs = {
                'level_id': level_id,
                'academic_year': academic_year_obj
            }
            student = None
            if student_id:
                student = get_students_by_level(level_id).filter(id=student_id).first()
                if not student:
                    logger.error(f"Invalid student_id: {student_id}")
                    return Response({"error": f"Invalid student_id: {student_id}"}, status=status.HTTP_400_BAD_REQUEST)
                filter_kwargs['student'] = student

            pdf_query = model.objects.filter(**filter_kwargs)
            if pdf_query.exists():
                pdf_record = pdf_query.first()
                latest_grade = Grade.objects.filter(
                    enrollment__level_id=level_id,
                    enrollment__student=student if student_id else None,
                    enrollment__academic_year=academic_year_obj
                ).order_by('-updated_at').first()
                if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                    logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                    pdf_query.delete()
                elif os.path.exists(pdf_record.pdf_path):
                    absolute_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{pdf_record.pdf_path.replace(os.sep, '/')}")
                    logger.info(f"Returning existing PDF: {absolute_url}")
                    return Response({
                        "message": "PDF retrieved successfully",
                        "view_url": absolute_url,
                        "pdf_path": pdf_record.pdf_path
                    })

            logger.info(f"Calling generate_gradesheet_pdf with level_id={level_id}, student_id={student_id}, academic_year_id={academic_year_obj.id}")
            pdf_paths = generate_gradesheet_pdf(
                level_id=int(level_id),
                student_id=int(student_id) if student_id else None,
                academic_year_id=academic_year_obj.id
            )
            logger.info(f"generate_gradesheet_pdf returned: {pdf_paths}")

            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            for pdf_path in pdf_paths:
                pdf_filename = os.path.basename(pdf_path)
                relative_pdf_path = os.path.join('output_gradesheets', pdf_filename)
                absolute_pdf_path = os.path.join(settings.MEDIA_ROOT, relative_pdf_path)
                model.objects.update_or_create(
                    **filter_kwargs,
                    defaults={'pdf_path': absolute_pdf_path, 'filename': pdf_filename}
                )

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            relative_pdf_path = os.path.join('output_gradesheets', pdf_filename)
            absolute_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{relative_pdf_path.replace(os.sep, '/')}")
            logger.info(f"Generated PDF: {absolute_url}")
            return Response({
                "message": "PDF generated successfully",
                "view_url": absolute_url,
                "pdf_path": pdf_path
            })

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='yearly/pdf/generate')
    def generate_yearly_gradesheet_pdf(self, request):
        """GET /api/grade_sheets_pdf/yearly/pdf/generate/ - Generate yearly PDFs."""
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')

        try:
            if not level_id or not academic_year:
                return Response({"error": "level_id and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)

            level = get_level_by_id(level_id)
            if not level:
                return Response({"error": f"Invalid level_id: {level_id}"}, status=status.HTTP_400_BAD_REQUEST)

            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            student = None
            if student_id:
                student = get_students_by_level(level_id).filter(id=student_id).first()
                if not student:
                    return Response({"error": f"Invalid student_id: {student_id}"}, status=status.HTTP_400_BAD_REQUEST)

            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            filter_kwargs = {
                'level_id': level_id,
                'academic_year': academic_year_obj
            }
            if student_id:
                filter_kwargs['student'] = student

            pdf_query = model.objects.filter(**filter_kwargs)
            if pdf_query.exists():
                pdf_record = pdf_query.first()
                latest_grade = Grade.objects.filter(
                    enrollment__level_id=level_id,
                    enrollment__student=student if student_id else None,
                    enrollment__academic_year=academic_year_obj
                ).order_by('-updated_at').first()
                if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                    logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                    pdf_query.delete()
                elif os.path.exists(pdf_record.pdf_path):
                    absolute_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{pdf_record.pdf_path.replace(os.sep, '/')}")
                    return Response({
                        "message": "PDF retrieved successfully",
                        "view_url": absolute_url,
                        "pdf_path": pdf_record.pdf_path
                    })

            pdf_paths = generate_yearly_gradesheet_pdf(
                level_id=int(level_id),
                student_id=int(student_id) if student_id else None,
                academic_year=academic_year
            )

            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            for pdf_path in pdf_paths:
                pdf_filename = os.path.basename(pdf_path)
                relative_pdf_path = os.path.join('output_gradesheets', pdf_filename)
                absolute_pdf_path = os.path.join(settings.MEDIA_ROOT, relative_pdf_path)
                model.objects.update_or_create(
                    **filter_kwargs,
                    defaults={'pdf_path': absolute_pdf_path, 'filename': pdf_filename}
                )

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            relative_pdf_path = os.path.join('output_gradesheets', pdf_filename)
            absolute_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{relative_pdf_path.replace(os.sep, '/')}")
            return Response({
                "message": "PDF generated successfully",
                "view_url": absolute_url,
                "pdf_path": pdf_path
            })

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error generating yearly PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/view')
    def view_gradesheet_pdf(self, request):
        """GET /api/grade_sheets_pdf/gradesheet/pdf/view/ - Serve PDF (periodic or yearly)."""
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')

        try:
            if not level_id or not academic_year:
                return Response({"error": "level_id and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)

            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            student = None
            if student_id:
                student = get_students_by_level(level_id).filter(id=student_id).first()
                if not student:
                    return Response({"error": f"Invalid student_id: {student_id}"}, status=status.HTTP_400_BAD_REQUEST)

            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            filter_kwargs = {
                'level_id': level_id,
                'academic_year': academic_year_obj
            }
            if student_id:
                filter_kwargs['student'] = student

            pdf_query = model.objects.filter(**filter_kwargs)
            if not pdf_query.exists():
                logger.warning(f"No PDF record found for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "PDF not found"}, status=status.HTTP_404_NOT_FOUND)

            pdf_record = pdf_query.first()
            pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_record.pdf_path)
            latest_grade = Grade.objects.filter(
                enrollment__level_id=level_id,
                enrollment__student=student if student_id else None,
                enrollment__academic_year=academic_year_obj
            ).order_by('-updated_at').first()

            if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                pdf_query.delete()
                pdf_paths = (
                    generate_yearly_gradesheet_pdf(
                        level_id=int(level_id),
                        student_id=int(student_id) if student_id else None,
                        academic_year=academic_year
                    ) if 'yearly' in pdf_record.pdf_path else
                    generate_gradesheet_pdf(
                        level_id=int(level_id),
                        student_id=int(student_id) if student_id else None,
                        academic_year_id=academic_year_obj.id
                    )
                )
                if not pdf_paths:
                    return Response({"error": "Failed to re-generate PDF"}, status=status.HTTP_404_NOT_FOUND)
                pdf_path = pdf_paths[0]
                pdf_filename = os.path.basename(pdf_path)
                relative_pdf_path = os.path.join('output_gradesheets', pdf_filename)
                absolute_pdf_path = os.path.join(settings.MEDIA_ROOT, relative_pdf_path)
                model.objects.update_or_create(
                    **filter_kwargs,
                    defaults={'pdf_path': absolute_pdf_path, 'filename': pdf_filename}
                )

            if not os.path.exists(pdf_path):
                logger.warning(f"PDF file not found: {pdf_path}")
                pdf_paths = (
                    generate_yearly_gradesheet_pdf(
                        level_id=int(level_id),
                        student_id=int(student_id) if student_id else None,
                        academic_year=academic_year
                    ) if 'yearly' in pdf_path else
                    generate_gradesheet_pdf(
                        level_id=int(level_id),
                        student_id=int(student_id) if student_id else None,
                        academic_year_id=academic_year_obj.id
                    )
                )
                if not pdf_paths:
                    return Response({"error": "Failed to re-generate PDF"}, status=status.HTTP_404_NOT_FOUND)
                pdf_path = pdf_paths[0]
                pdf_filename = os.path.basename(pdf_path)
                relative_pdf_path = os.path.join('output_gradesheets', pdf_filename)
                absolute_pdf_path = os.path.join(settings.MEDIA_ROOT, relative_pdf_path)
                model.objects.update_or_create(
                    **filter_kwargs,
                    defaults={'pdf_path': absolute_pdf_path, 'filename': pdf_filename}
                )

            with open(pdf_path, 'rb') as f:
                response = FileResponse(f, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
                logger.info(f"Serving PDF for viewing: {pdf_path}")
                return response

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error serving PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)