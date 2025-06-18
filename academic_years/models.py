from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime

class AcademicYear(models.Model):
    name = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^\d{4}/\d{4}$', message='Name must be in the format "YYYY/YYYY" (e.g., "2024/2025")')],
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        """Validate that end_date is after start_date and matches name years."""
        if self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')
        if self.name:
            start_year, end_year = map(int, self.name.split('/'))
            if self.start_date.year != start_year or self.end_date.year != end_year:
                raise ValidationError('Start and end dates must match the years in the name.')
            if end_year != start_year + 1:
                raise ValidationError('End year must be one year after start year.')

    def save(self, *args, **kwargs):
        self.full_clean()  # Run clean() before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']