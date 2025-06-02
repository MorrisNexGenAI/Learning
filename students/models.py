from django.db import models
from levels.models import Level

# Create your models here.
class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
   
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    gender = models.CharField(max_length =1,choices=GENDER_CHOICES)
    dob = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
   
   
   
    def __str__(self):
        return f"{self.firstName} {self.lastName}"