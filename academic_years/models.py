from django.db import models

class AcademicYear(models.Model):
    ACADEMIC_CHOICE = (
        ('2024/2025', '2024/2025'),
        ('2025/2026', '2025/2026'),
        ('2026/2027', '2026/2027'),
        ('2027/2028', '2027/2028'),
    )
    name = models.CharField(
        max_length=9,  # Adjusted max_length to fit the academic year format
        choices=ACADEMIC_CHOICE,
        unique=True,
        default='2024/2025'  # Set a valid default value
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']  # Sort by most recent year