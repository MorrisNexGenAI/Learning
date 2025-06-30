from docx import Document
import os
from django.conf import settings
import logging
from grade_sheets.helpers import get_grade_sheet_data
from docx2pdf import convert
import win32com.client
import pythoncom

logger = logging.getLogger(__name__)

def replace_placeholders(doc, data):
    """Replace placeholders in a DOCX template with provided data."""
    try:
        # Placeholder mapping to align template with data keys
        key_map = {
            '1': '1st', '2': '2nd', '3': '3rd', '1s': '1exam', '1a': '1a',
            '4': '4th', '5': '5th', '6': '6th', '2s': '2exam', '2a': '2a', 'f': 'f'
        }

        # Log document content
        logger.info("Document paragraphs before replacement:")
        for para in doc.paragraphs:
            logger.info(f"Paragraph: {para.text}")
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    logger.info(f"Cell: {cell.text}")

        # Replace in paragraphs
        for paragraph in doc.paragraphs:
            for key, value in data.items():
                if key != 's' and isinstance(value, str):
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in paragraph.text:
                        paragraph.text = paragraph.text.replace(placeholder, value)
                        logger.info(f"Replaced {placeholder} with {value} in paragraph")

        # Replace in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for key, value in data.items():
                        if key == 's' and isinstance(value, list):
                            for i, item in enumerate(value):
                                for template_key, data_key in key_map.items():
                                    for fmt in [f"{{{{s[{i}][\"{template_key}\"]}}}}", f"{{{{s[{i}].{template_key}}}}}"]:
                                        if fmt in cell.text:
                                            cell.text = cell.text.replace(fmt, str(item.get(data_key, '-')))
                                            logger.info(f"Replaced {fmt} with {item.get(data_key, '-')} in table")
                                # Replace subject name
                                placeholder_sn = f"{{{{s[{i}].sn}}}}"
                                if placeholder_sn in cell.text:
                                    cell.text = cell.text.replace(placeholder_sn, str(item.get('sn', '-')))
                                    logger.info(f"Replaced {placeholder_sn} with {item.get('sn', '-')} in table")
                        elif isinstance(value, str):
                            placeholder = f"{{{{{key}}}}}"
                            if placeholder in cell.text:
                                cell.text = cell.text.replace(placeholder, value)
                                logger.info(f"Replaced {placeholder} with {value} in table")

        # Log document content after replacement
        logger.info("Document paragraphs after replacement:")
        for para in doc.paragraphs:
            logger.info(f"Paragraph: {para.text}")
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    logger.info(f"Cell: {cell.text}")

        return doc
    except Exception as e:
        logger.error(f"Error replacing placeholders: {str(e)}")
        raise

def generate_periodic_pdf(level_id, student_id=None, academic_year_id=None):
    """Generate PDF for a student or level."""
    word = None
    try:
        pythoncom.CoInitialize()
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            logger.info("Word COM object created successfully")
        except Exception as e:
            logger.warning(f"Failed to create Word COM object: {str(e)}")
            word = None

        template_path = os.path.join(settings.MEDIA_ROOT, 'templates', 'report_card_compact.docx')
        if not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return []

        output_dir = os.path.join(settings.MEDIA_ROOT, 'output_gradesheets')
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        data = get_grade_sheet_data(student_id=student_id, level_id=level_id, academic_year_id=academic_year_id)
        if not data:
            logger.warning(f"No data found for level_id={level_id}, student_id={student_id}, academic_year_id={academic_year_id}")
            return []

        pdf_paths = []
        if student_id:
            doc = Document(template_path)
            doc = replace_placeholders(doc, data)
            safe_name = data.get('name', 'student').replace(' ', '_').replace(':', '_').replace('/', '_')
            temp_filename = f"temp_report_card_{safe_name}_{academic_year_id}.docx"
            temp_path = os.path.join(temp_dir, temp_filename)
            try:
                doc.save(temp_path)
                logger.info(f"Saved temporary DOCX: {temp_path}")
                if not os.path.exists(temp_path):
                    logger.error(f"Failed to save temporary DOCX: {temp_path}")
                    return []
            except Exception as e:
                logger.error(f"Error saving DOCX: {str(e)}")
                return []

            pdf_filename = temp_filename.replace('.docx', '.pdf')
            pdf_path = os.path.join(output_dir, pdf_filename)
            try:
                convert(temp_path, pdf_path)
                if os.path.exists(pdf_path):
                    pdf_paths.append(pdf_path)
                    logger.info(f"PDF generated: {pdf_path}")
                else:
                    logger.error(f"PDF not created at {pdf_path}")
                    return []
            except Exception as e:
                logger.error(f"docx2pdf conversion failed: {str(e)}")
                return []
            finally:
                if os.path.exists(temp_path):
                    logger.info(f"Temporary DOCX retained at: {temp_path}")
                else:
                    logger.warning(f"Temporary DOCX not found: {temp_path}")
        else:
            from students.helper import get_students_by_level
            students = get_students_by_level(level_id)
            for student in students:
                student_data = get_grade_sheet_data(student_id=student.id, level_id=level_id, academic_year_id=academic_year_id)
                if not student_data:
                    continue
                doc = Document(template_path)
                doc = replace_placeholders(doc, student_data)
                safe_name = student_data.get('name', 'student').replace(' ', '_').replace(':', '_').replace('/', '_')
                temp_filename = f"temp_report_card_{safe_name}_{academic_year_id}.docx"
                temp_path = os.path.join(temp_dir, temp_filename)
                try:
                    doc.save(temp_path)
                    logger.info(f"Saved temporary DOCX: {temp_path}")
                    if not os.path.exists(temp_path):
                        logger.error(f"Failed to save temporary DOCX: {temp_path}")
                        continue
                except Exception as e:
                    logger.error(f"Error saving DOCX for student {student.id}: {str(e)}")
                    continue

                pdf_filename = temp_filename.replace('.docx', '.pdf')
                pdf_path = os.path.join(output_dir, pdf_filename)
                try:
                    convert(temp_path, pdf_path)
                    if os.path.exists(pdf_path):
                        pdf_paths.append(pdf_path)
                        logger.info(f"PDF generated for student {student.id}: {pdf_path}")
                    else:
                        logger.error(f"PDF not created for student {student.id} at {pdf_path}")
                    continue
                except Exception as e:
                    logger.error(f"docx2pdf conversion failed for student {student.id}: {str(e)}")
                    continue
                finally:
                    if os.path.exists(temp_path):
                        logger.info(f"Temporary DOCX retained at: {temp_path}")
                    else:
                        logger.warning(f"Temporary DOCX not found: {temp_path}")

            if pdf_paths:
                pdf_paths = pdf_paths[:1]  # Return first PDF for now

        return pdf_paths
    except Exception as e:
        logger.error(f"Error generating periodic PDF: {str(e)}")
        return []
    finally:
        if word:
            try:
                word.Quit()
                logger.info("Word COM object closed")
            except Exception as e:
                logger.warning(f"Error closing Word COM object: {str(e)}")
        try:
            pythoncom.CoUninitialize()
        except Exception as e:
            logger.warning(f"Error during COM uninitialization: {str(e)}")