from django.utils import timezone
from django.core.cache import cache
from .models import AcademicYear

def get_all_academic_years():
    """Return all academic years, cached."""
    cache_key = 'all_academic_years'
    years = cache.get(cache_key)
    if years is None:
        years = AcademicYear.objects.all()
        cache.set(cache_key, years, timeout=3600)  # Cache for 1 hour
    return years

def get_academic_year_by_id(year_id):
    """Return a specific academic year by ID."""
    try:
        return AcademicYear.objects.get(id=year_id)
    except AcademicYear.DoesNotExist:
        return None

def get_academic_year_by_name(name):
    """Return academic year by name (e.g., '2024/2025')."""
    try:
        return AcademicYear.objects.get(name=name)
    except AcademicYear.DoesNotExist:
        return None

def get_current_academic_year():
    """Return the academic year containing today's date."""
    cache_key = 'current_academic_year'
    year = cache.get(cache_key)
    if year is None:
        today = timezone.now().date()
        year = AcademicYear.objects.filter(start_date__lte=today, end_date__gte=today).first()
        cache.set(cache_key, year, timeout=3600)  # Cache for 1 hour
    return year

def create_academic_year(name, start_date, end_date):
    """Create a new academic year."""
    return AcademicYear.objects.create(name=name, start_date=start_date, end_date=end_date)

def update_academic_year(year_id, name=None, start_date=None, end_date=None):
    """Update an existing academic year."""
    try:
        year = AcademicYear.objects.get(id=year_id)
        if name:
            year.name = name
        if start_date:
            year.start_date = start_date
        if end_date:
            year.end_date = end_date
        year.save()
        return year
    except AcademicYear.DoesNotExist:
        raise ValueError(f"Academic year with ID {year_id} does not exist.")

def delete_academic_year(year_id):
    """Delete an academic year."""
    try:
        year = AcademicYear.objects.get(id=year_id)
        year.delete()
        return True
    except AcademicYear.DoesNotExist:
        return False