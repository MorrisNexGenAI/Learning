from django.db import models

# Create your models here.


from django.db import models
from levels.models import Level
# Create your models here.
class Subject(models.Model):
    SUBJECT_CHOICES = (
        ('Math', 'Mathematics'),
        ('Eng', 'English'),
        ('Sci', 'Science'),
        ('Hist', 'History'),
        ('Geo', 'Geography'),
        ('Civ', 'Civics'),
        ('RME', 'RME'),
        ('Vob', 'Vobucabulary'),
        ('Lit', 'Literature'),
        ('Agr', 'Agriculture'),
    )
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subjects')
    subject = models.CharField(max_length =12, choices = SUBJECT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


    def __str__(self):
        return f'{self.level} - {self.subject}'
    
 

