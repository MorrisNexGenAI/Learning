from django.db import models
from levels.models import Level

class Subject(models.Model):
    SUBJECT_CHOICES = (
        ('Mathematics', 'Mathematics'),
        ('English', 'English'),
        ('Science', 'Science'),
        ('Civics', 'Civics'),
        ('History', 'History'),
        ('Geography', 'Geography'),
        ('RME', 'RME'),
        ('Vocabulary', 'Vocabulary'),
        ('Agriculture', 'Agriculture'),
    )
    subject = models.CharField(max_length=15, choices=SUBJECT_CHOICES)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    def __str__(self):
        return self.subject

    class Meta:
        unique_together = ('subject', 'level')
        ordering = ['subject', 'level']
