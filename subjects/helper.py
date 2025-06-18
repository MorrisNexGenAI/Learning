from django.core.cache import cache
from .models import Subject

def get_subjects_by_level(level_id):
    """Fetch subjects for a level, with caching."""
    cache_key = f'subjects_level_{level_id}'
    subjects = cache.get(cache_key)
    if subjects is None:
        subjects_qs = Subject.objects.filter(level_id=level_id).select_related('level')
        subjects = {str(s.id): s.subject for s in subjects_qs}
        cache.set(cache_key, subjects, timeout=3600)  # Cache for 1 hour
    return subjects