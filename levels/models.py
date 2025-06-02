# levels/models.py
from django.db import models

class Level(models.Model):
    name = models.CharField(max_length=100)
    # No subject field here, but a reverse relation might exist

    def __str__(self):
        return self.name