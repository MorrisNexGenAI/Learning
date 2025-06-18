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

def create_period(period_code):
    """Create a new period if valid (e.g. '1st', '2exam')."""
    if period_code not in VALID_PERIODS:
        raise ValueError(f"Invalid period code: '{period_code}'.")
    period, created = Period.objects.get_or_create(
        period=period_code
    )
    return period, created

def update_period(period_id, new_code=None):
    """Update the code of a period if valid."""
    try:
        period = Period.objects.get(id=period_id)
        if new_code:
            if new_code not in VALID_PERIODS:
                raise ValueError(f"Invalid period code: '{new_code}'.")
            period.period = new_code
        period.save()
        return period
    except Period.DoesNotExist:
        raise ValueError(f"Period with id {period_id} does not exist.")

def delete_period(period_id):
    """Delete a period by ID."""
    try:
        period = Period.objects.get(id=period_id)
        period.delete()
        return True
    except Period.DoesNotExist:
        return False
