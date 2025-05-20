from django.db import models

# Create your models here.
class Level(models.Model):
      LEVEL_CHOICE = (
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
    )
    
      levels = models.CharField(max_length =3, choices = LEVEL_CHOICE)
      
      def __str__(self):
        return f'{self.levels}' 