from django.db import models

# Create your models here.
class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
   
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length =1,choices=GENDER_CHOICES)
    dob = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
   
   
    def __str__(self):
        return f"{self.first_name} {self.last_name}"