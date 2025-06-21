This is an overview of my backends.
it is divided into 9 django apps namely:academic_years, enrollment, grade_sheets, grades, levels, pass_and_failed, periods, students, and subjects.
1. enrollment: This is the part that connects a student to level and academic_year. it have a many to many keys, connecting and serving as bridge between student, level, and academic_year.
it have foreign keys to level, students, and academic_year, plus a model datefiled called date_enrolled and a model chatfield called status. 
The date enroll is use to track a student record consisting the date the student was enrolled in a specific level for a specific academic year.
The status is use to determine whether a student is enrolled or not.
enrollment has both views and serializers.

grades: This is one of the unique and important piece of the app. It is the heart of the app because one of the key goal of the app is to savely develever students grades on gradesheet digitally, and also keeping record of the student.
it also serve as bridge with a many to many keys. it serve as bridge to enrollment(which consist of student, level, and academic_year), subject, and period.
subjects are also special parts representing courses that a student will sit for per academic_years.
and periods are the terms the students will sit for.
So, a grade is for a student, in a specific level, for a specific_academic_year, a specific subject and a specific periods. we will discuss this more when we discuss grade_sheets.
grades also have some fields like score and updated_at.
scores are FloatField models use to represent digits which are grades for a student in a specific level, in a specific subject and a specific periods.
updated_at are DateTimeField models use to track the exact time a grade for a student was updated.
it also have other important files: helper, serializers, views.

grade_sheets:This is the heart beat of the app that shows everything within the app.

It combine the student to the level for a academic_year(i guess you might say but this is just enrollment and you are right. But i don't actually know if i could just use enrollment foreingkey here but anyway this diret way is cool.).
it takes the foreign key student, academic_year, and level.
it also have two DateTimeField model call created_at and updated_at.
created_at tracks when it was created and updated_at is when it was upadted(maybe i just use both for fancy, hahaha).
it also have two models.Charfield call pdf_path, which is use for pdf_path, and filename which is use to represent the pdf file name.
it also have other important files: helpers, pdf_utils, serializers, utils, views, yearly_pdf_utils.
i will share the codes for all the files within gradesheets so you can give each of them functions and also how i can connect else where.

students:The main kind that got this whole work being developed with joy.
the students are the main reason we got this. The model have no foreign key but it have few chartField: firstName, lastName, dob(date of birth), gender(whether male, female, or others), and also a DateTimeField call created_at(i'm not going to explain this because i have explain a lots of other created_at, thanks!!).
it also have other main files:helper, api(which contain all the apis of the other django apps), serializers, views.

levels: This is the representation of the classroom(but digitally, hahaha). This represent each student in a specific class also call levels ex.. 7, 8, 9.
it have only one charfield models call name, which is use to store the level name.
it also have other important files call helper, serializers, and views.

subjects: These are specific courses( i couldn't say subject again so i can avoid saying the same thing twice, hahaha) that a student will have grades in for a period.
it have one Charfiled model call subject which is use to store the subject name, and a foreign key call level which is use to assigned a specific subject to a specific level.
it also have other important files call helper, models, serializers, views.

periods:These are specific terms of the academic_year in which students received lessons and also take test at the end of each followed by a special test call exam which climax a semester made of three periods. They are divided into stable six call: 1st, 2nd,3rd,and a 1exam, then 4th, 5th,6th, and a 2exam.
it have a charfield model call period and a booleanfield model call is_exam.
it also have other important files call: helpers, serializers, views.

pass_and_failed:I guess you already know what this does from the name alone, hahaha. This is what use to determine whether a student will be promoted to another level or not. I guess you think it is more codes again, but the acutal reason that brought this model in was to help teachers or admiistrators connect what word template the app should use to display a specific student grade so that it can be generated as a pdf. it link the templates for the students based on whether they pass or failed or pass under condition.
it have a long list of choices:STATUS_CHOICES = (
        ('PASS', 'Pass'),
        ('FAIL', 'Failed'),
        ('CONDITIONAL', 'Pass Under Condition'),
        ('INCOMPLETE', 'Incomplete'),
        ('PENDING', 'Pending'),
    )
with many foreign keys and charfields, booleanfields. They are so many that i'm gonna paste because i can't afford to write all:student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='pass_failed_statuses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='INCOMPLETE')
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.CharField(max_length=100, null=True, blank=True)
    template_name = models.CharField(max_length=100, blank=True)
    grades_complete = models.BooleanField(default=False)
i hope you can understand and explain them too(maybe that's an assignment for whoever reading this).

I know you took notice of the file call helper which frequently occured: well it is use as helper to each django app. it lessen the codes for the views.py. it contain the logics while views run the bussiness.
you already knows the work of the serilizers,apis and and utils(maybe only the yearly_utils for gradesheet and pdf_utls, but i will share the codes).

grade_system:this is the engine right? maybe it is. Thisis where i have my settings, urls(let me share, because i'm not gonna explain):from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from grade_sheets.views import gradesheet_home, gradesheet_view, cors_test

urlpatterns = [
    path('api/', include('students.api')),
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





ckup.

 i will create a seperate files for all these actions so that i can better understand them. after creating the files i will call each within the grade_sheets/views which will serve as my main base to interact with my react frontend but for now let them remain here in this markdow.