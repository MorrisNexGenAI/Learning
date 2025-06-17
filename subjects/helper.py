from .models import Subject

def get_subjects_by_level(level_id):
    """Fetch subjects by level and return as a dictionary {id: subject_name}."""
    subjects = Subject.objects.filter(level_id=level_id)
    return {s.id: s.subject for s in subjects}

def create_subject(subject_name, level_id):
    """Create a subject for a given level if it doesn't exist."""
    from levels.models import Level
    try:
        level = Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        raise ValueError(f"Level with id {level_id} does not exist.")
    subject, created = Subject.objects.get_or_create(subject=subject_name, level=level)
    return subject, created

def update_subject(subject_id, new_name=None, new_level_id=None):
    """Update subject name and/or level."""
    try:
        subject = Subject.objects.get(id=subject_id)
        if new_name:
            subject.subject = new_name
        if new_level_id:
            from levels.models import Level
            level = Level.objects.get(id=new_level_id)
            subject.level = level
        subject.save()
        return subject
    except Subject.DoesNotExist:
        raise ValueError(f"Subject with id {subject_id} does not exist.")

def delete_subject(subject_id):
    """Delete a subject by its id."""
    try:
        subject = Subject.objects.get(id=subject_id)
        subject.delete()
        return True
    except Subject.DoesNotExist:
        return False
