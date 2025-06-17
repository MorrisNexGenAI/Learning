import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from grades.models import Grade
from .models import Period
from .serializers import PeriodSerializer
from .helpers import get_all_periods, get_period_by_id, create_period, delete_period

logger = logging.getLogger(__name__)

class PeriodViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing periods, including listing, retrieving, creating, and deleting.
    """
    def list(self, request):
        """
        GET /api/periods/
        Fetch all periods.
        """
        try:
            periods = get_all_periods()
            serializer = PeriodSerializer(periods, many=True)
            logger.debug(f"Fetched {len(periods)} periods")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching periods: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        """
        GET /api/periods/{id}/
        Fetch a specific period by ID.
        """
        try:
            period = get_period_by_id(pk)
            if not period:
                logger.warning(f"Period with id {pk} not found")
                return Response({"error": f"Period with id {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = PeriodSerializer(period)
            logger.debug(f"Fetched period: {period.period}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching period {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """
        POST /api/periods/
        Create a new period.
        Expects: {"period": "1st", "is_exam": false}
        """
        try:
            serializer = PeriodSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Invalid data for period creation: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            period_code = serializer.validated_data['period']
            is_exam = serializer.validated_data.get('is_exam', False)
            period, created = create_period(period_code, is_exam)

            if created:
                logger.info(f"Created period: {period_code}, is_exam={is_exam}")
                return Response(PeriodSerializer(period).data, status=status.HTTP_201_CREATED)
            else:
                logger.info(f"Period already exists: {period_code}")
                return Response(PeriodSerializer(period).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error creating period: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """
        DELETE /api/periods/{id}/
        Delete a period by ID, only if no grades are associated.
        """
        try:
            period = get_period_by_id(pk)
            if not period:
                logger.warning(f"Period with id {pk} not found")
                return Response({"error": f"Period with id {pk} not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check if grades are associated with this period
            if Grade.objects.filter(period_id=pk).exists():
                logger.warning(f"Cannot delete period {pk} as it has associated grades")
                return Response({"error": "Cannot delete period with associated grades"}, status=status.HTTP_400_BAD_REQUEST)

            if delete_period(pk):
                logger.info(f"Deleted period: {pk}")
                return Response({"message": f"Period {pk} deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            else:
                logger.error(f"Failed to delete period {pk}")
                return Response({"error": "Failed to delete period"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error deleting period {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)