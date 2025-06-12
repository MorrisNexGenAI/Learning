# grades/models.py
from django.db import models

class GradeSheet(models.Model):
    class Meta:
         def __str__(self):
             return self.name
