from django.db import models
from levels.models import Level

class Subject(models.Model):
    subject = models.CharField(max_length=50)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subject', 'level')
        ordering = ['subject', 'level']

    def __str__(self):
        return f"{self.subject} ({self.level})"
