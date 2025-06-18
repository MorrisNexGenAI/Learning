from django.core.cache import cache
from subjects.models import Subject
from .models import Level

def get_level_by_id(level_id):
    """Fetch a level by ID."""
    return Level.objects.filter(id=level_id).first()

def get_all_levels():
    """Fetch all levels, ordered by name."""
    cache_key = 'all_levels'
    levels = cache.get(cache_key)
    if levels is None:
        levels = Level.objects.all().order_by('name')
        cache.set(cache_key, levels, timeout=3600)  # Cache for 1 hour
    return levels

def get_subjects_by_level(level_id):
    """Fetch subjects for a level, with caching."""
    cache_key = f'subjects_level_{level_id}'
    subjects = cache.get(cache_key)
    if subjects is None:
        subjects = Subject.objects.filter(level_id=level_id).select_related('level')
        subjects_dict = {str(s.id): s.subject for s in subjects}
        cache.set(cache_key, subjects_dict, timeout=3600)  # Cache for 1 hour
    else:
        subjects_dict = subjects
    return subjects_dict