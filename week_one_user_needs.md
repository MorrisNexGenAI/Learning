
i think the School should be a Django app because it is going to play a key part in the multi-tenant system.
the school will be use to tie all other Django apps to it so that we can create an engine. The goal is to have a single engine that is flexible enough to serve as many schools as possible.

the models will be consisiting of fields like:
Name: For the school name, which is crucial
Header: For the school header. This will consist of the school name and logos
Footer: For school specific footers
Theme: For schools specific themes

Views:
we will filter everything within the app by the school model which means the school is like a house which holds everything else. 
once a school is been created, with it comes the power of all the other django apps.

each school is unique to a identity.

serializers
helpers(for specific helper codes)
urls
settings


The React frontend
we will have a general admin page for managing schools like add, deleting, and editing schools specific informations.

we will have a landing page where we will add school by  loggin in.
each school will have a token and account with unique password and Name plus the other infomations from the school backend models.
To access a school, you will enter a password and the school name and then you will login to the school.

so, admin will control this process.
The landing page will be like this;
when you arrive it will be like this:
a button and box to login and then a button below with the option to login as admin.
when you login as admin then you will have the accesss to create new school.
when you click add or create new school then you will have access to the school creation page where you will enter these infomations:

you will enter the school name
enter a new password
choose the school theme
upload the school logo
and then enter your footer and click new. A new school will be created and to access it, you will have to login with the name and password.
Then the new created schools administration can login their site with their unique password and School name.


their will be another admin page within the school which is already been implemented halfly.
This page will have the options to add, edit, and delete:
1. status and templates(pass,failed, and optional (conditional))
conditional status will be optional because not all schools use it. so it will be optional.
Schools can upload their microsoft word file which will be use to render their student grades.
they will upload Report card compact which is use for periodic.

For yearly:
they will upload pass templates
failed templates
and optional conditional templates.
now, conditional is by choice. This means if the school wish to use conditional then they can upload conditional templates, this means that if a school doesn't upload conditional templates then which means they won't be using conditional for thier students.


2. They will set the rules that will be use to arrange students reportcard for printing yearly result for a level:
These rules will be use to arrange students as Pass, Failed, or optional conditional(This depends if a school chose conditional).
These rules will be chosen when creating a new level, which means a new level will be tie to them, so all studennts grades and gradesheets within that level will be filter by that rule.
Rules 1: Conditional (def conditional_rule)
This means that the school will be using pass under condition for students and that rules goes with this law:

1x= means only once
2x= means twice
3x = means thrice

if avg contain 1x(69 below) and Tavg(total avg) = 70 above
setStatus(Pass)
elif:
avg contain 2x(69 below) and Tavg = 70 above
setStatus(conditional)
else:
setStatus(Failed).

Rule 2: No Conditional 1 (def no_conditional_rule_one)
if avg contain 1x (69 below) Tavg = 70 above
setStatus(Pass)
else:
setStatus(Failed)

Rule 3: No Conditional 2 (no_conditional_rule_two)
if avg contain 2x(69 below) and Tavg = 70 above
setStatus(Pass)000
else:
setStatus (Failed)

each rule only apply to the level it is tie to and a level can only have or be govern by one rules.

3. Level
this will be use to add, edit, and delete level.
each level will be added by rules which means the level is tie to the rules.
So, the rules aren't functional unless a level is created and tie to it. i could have tie the rules to schools but some schools use Hybrids - meaning they uses two of the rules simultenously. so by tieing it to a level i think it will be okay.
now if a level is creaed and tie to the rules example
level 7: all students within thier grades will be filter by those rules.

4. Academic year
5. Periods
6. Subjects
7. Templates(This is where you will upload a microsoft word templates for your schooll). Three templates will be uploaded, and an optional one which is conditional templates.
The first template will be report_card_compact.docx
this template will be use to generate the periodic student and level pdf.
the second will be yearly_pass.docx for the yearly students that pass
the third is yearly_failed.docx: this is for the students that failed
the optional one is yearly_conditional.docx: This is optional for schools only that uses the first rule which is conditinal rules. and if a school chooses the first rule than they are mandated to picked this also, but if not then they don't have to upload this template.

currently what we have is build for single schools so it doesn't manually support many schools, how ever we need to create a template app which will store all templates specific logics. 


so back to the backend.
the template app will be mainly focus on uploading templates per schools.
we will have Report card compact which will be use to generate periodic results

and then the Yearly templates for yearly results.


Let focus on the backend School Django app



