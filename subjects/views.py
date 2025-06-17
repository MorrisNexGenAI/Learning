from django.shortcuts import render
import logging
# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from subjects.models import Subject
from subjects.serializers import SubjectSerializer
from .helper import get_subjects_by_level, delete_subject
logger = logging.getLogger(__name__)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def destroy(self, request, id=None):
        """
        DELETE /api/subjects/{id}/
        Delete a subject by ID, only if no grades are associated.
        """
        try:
            subject = get_subjects_by_level(id)
            if not subject:
                logger.warning(f"Subject with id {id} not found")
                return Response({"error": f"Subject with id {IndentationError} not found"}, status=status.HTTP_404_NOT_FOUND)

           

            if delete_subject(id):
                logger.info(f"Deleted period: {id}")
                return Response({"message": f"Subject {id} deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            else:
                logger.error(f"Failed to delete period {id}")
                return Response({"error": "Failed to delete period"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error deleting subject {NotImplemented}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)