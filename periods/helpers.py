from .models import Period

VALID_PERIODS = [choice[0] for choice in Period.PERIOD_CHOICE]

def get_all_periods():
    """Fetch all periods."""
    return Period.objects.all()

def get_period_by_id(period_id):
    """Fetch a specific period by ID."""
    try:
        return Period.objects.get(id=period_id)
    except Period.DoesNotExist:
        return None