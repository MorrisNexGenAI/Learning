from django.db import models

class Level(models.Model):
    LEVEL_CHOICES = [
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
    ]

    name = models.CharField(
        max_length=1,
        choices=LEVEL_CHOICES,
        unique=True,
        default='7'
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        ordering = ['name']