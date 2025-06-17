import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from grades.models import Grade
from .models import Period
from .serializers import PeriodSerializer
from .helpers import get_all_periods, get_period_by_id

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
