from django.db import models

class Level(models.Model):
    name = models.CharField(max_length=13)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        ordering = ['name']