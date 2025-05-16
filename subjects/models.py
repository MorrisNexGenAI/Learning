from django.db import models
from levels.models import Level
# Create your models here.
class Subject(models.Model):
    name = models.CharField(max_length=100)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subjects')

    def __str__(self):
        return self.name
    
