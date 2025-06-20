from django.contrib import admin

# Register your models here.
from .models import StudentGradeSheetPDF
from .models import LevelGradeSheetPDF

admin.site.register(StudentGradeSheetPDF)
admin.site.register(LevelGradeSheetPDF)