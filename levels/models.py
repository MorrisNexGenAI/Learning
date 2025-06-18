from django.db import models
from django.core.validators import RegexValidator

class Level(models.Model):
    name = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d+$', message='Level name must be a number (e.g., "7" for Grade 7)')],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grade {self.name}"