from django.db import models
from django.core.validators import RegexValidator
from levels.models import Level

class Subject(models.Model):
    subject = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^[A-Z][a-zA-Z\s]*(?<!\s)$', message='Subject name must start with a capital letter and contain only letters and spaces, no trailing spaces.')],
    )
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subjects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('subject', 'level')

    def __str__(self):
        return f"{self.subject} (Grade {self.level.name})"