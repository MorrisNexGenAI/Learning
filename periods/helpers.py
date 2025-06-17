from .models import Period

def get_all_periods():
    """Fetch all periods."""
    return Period.objects.all()

def get_period_by_id(period_id):
    """Fetch a specific period by ID."""
    try:
        return Period.objects.get(id=period_id)
    except Period.DoesNotExist:
        return None

def create_period(period_code, is_exam=False):
    """Create a new period (e.g. '1st', '2exam')."""
    period, created = Period.objects.get_or_create(
        period=period_code,
        defaults={'is_exam': is_exam}
    )
    return period, created

def update_period(period_id, new_code=None, new_is_exam=None):
    """Update the code or exam status of a period."""
    try:
        period = Period.objects.get(id=period_id)
        if new_code:
            period.period = new_code
        if new_is_exam is not None:
            period.is_exam = new_is_exam
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
