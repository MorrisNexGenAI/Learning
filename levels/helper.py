from .models import Level

def get_all_levels():
    """Fetch all levels."""
    return Level.objects.all()

def get_level_by_id(level_id):
    """Fetch a level by ID."""
    try:
        return Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        return None

def get_level_by_name(name):
    """Fetch a level by name (if you add a name field)."""
    try:
        return Level.objects.get(name=name)
    except Level.DoesNotExist:
        return None

def create_level(name):
    """Create a new level."""
    return Level.objects.create(name=name)

def update_level(level_id, new_name=None):
    """Update a level's name."""
    try:
        level = Level.objects.get(id=level_id)
        if new_name:
            level.name = new_name
        level.save()
        return level
    except Level.DoesNotExist:
        raise ValueError(f"Level with ID {level_id} does not exist.")

def delete_level(level_id):
    """Delete a level by ID."""
    try:
        level = Level.objects.get(id=level_id)
        level.delete()
        return True
    except Level.DoesNotExist:
        return False
