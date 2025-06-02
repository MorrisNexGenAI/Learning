from django.db import models

# Create your models here.
from django.db import models

class AcademicYear(models.Model):
    name = models.CharField(max_length=9, unique=True)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']  # Sort by most recent year