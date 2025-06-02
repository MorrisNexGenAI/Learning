# subjects/models.py
from django.db import models
from levels.models import Level

class Subject(models.Model):
    subject = models.CharField(max_length=100)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)  # This creates a reverse relation Level.subject_set

    def __str__(self):
        return self.subject