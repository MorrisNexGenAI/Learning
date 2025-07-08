OverView of the entire app:
🎓 Student Grading & Report Card System
An advanced full-stack school grading and reporting system, built with Django (Python) on the backend and React + TypeScript on the frontend. Designed to handle student enrollment, grading, report card generation (PDF/Word), academic evaluations, and flexible template rendering per school.

🧠 Backend Architecture – Django (Python)
The backend is organized into 9 modular Django apps, each serving a core part of the system:

1. enrollment
Connects students to levels and academic years. Serves as the bridge using foreign keys:

Student, Level, AcademicYear

Tracks: date_enrolled, status

2. grades
The core engine for storing and managing student scores.

Many-to-many logic: connects Enrollment, Subject, and Period

Tracks: score, updated_at

Includes: views, serializers, helper.py

3. grade_sheets
The heartbeat of the system, combining all logic to produce final report sheets.

Fields: student, level, academic_year, created_at, updated_at, pdf_path, filename

Includes: helpers, utils, pdf_utils, yearly_pdf_utils

4. students
The base model holding personal student information:

Fields: first_name, last_name, dob, gender, created_at

Includes: api/, views, serializers, helpers

5. levels
Represents digital classrooms (e.g., 7th grade, 8th grade):

Field: name (e.g., “Grade 9”)

Includes: views, serializers, helpers

6. subjects
Courses tied to specific levels.

Fields: subject, level (FK)

Includes: views, serializers, helpers

7. periods
Academic terms (e.g., 1st Term, 2nd Term, 1st Exam, etc.)

Fields: period, is_exam

Includes: views, serializers, helpers

8. pass_and_failed
Determines final student status and template to use.

STATUS_CHOICES: PASS, FAIL, CONDITIONAL, INCOMPLETE, PENDING

Tracks validation metadata and PDF template to use

Fields include: student, level, academic_year, status, template_name, etc.

9. academic_years
Defines school academic calendar years used throughout the system.

🧩 Core Technologies & Tools
Django REST Framework: API creation

pywin32: Word and PDF conversion via Windows COM interface (no WeasyPrint used)

Utils,Helper modules: Custom business logic per app

PDF generation: Uses .docx templates, converted to .pdf based on student pass/fail status

Custom api/ routing: All endpoints grouped in system/urls

🌐 Frontend – React + TypeScript
Built with reusability in mind and structured around school-specific themes.

🔁 Reusable Structure
Folders: src/api, hooks, components, types/, pages/, routes/

Key Reusables:

GradeInputForm, GradeSheetTable, StudentForm, StudentList

Sidebar, DashboardShell, ReusableForm, ReusableTable

🏫 School-Specific Templates
Each school has a custom UI under templates/, including styles, layout, and pages:

Bomi Junior High

Charity Day Care

Divine Day Care

Each school folder contains:

Copy
Edit
components/
  ├── common/
  └── layout/
pages/
styles/
bomi.tsx, Dashboard.tsx, etc.
Pages like BGradeEntryPage, BStudentsPage, etc., map to backend endpoints, tailored per school.

🔗 Data Flow
Backend APIs: Provide data endpoints for all entities

React Hooks: Handle data fetching and business logic

Type Definitions: Centralized in types/index.ts

Pages + Components: Render per-school UI

Tailwind CSS: Applied globally and per school template











                  > 
                  > 🎓 Backend - Student Grading & Report Card System

This is the backend of a full-stack student grading and report card system built with Django + Django REST Framework. It provides APIs for student management, grading logic, enrollment tracking, report generation, and academic evaluation.

⚙️ Django App Structure

The backend is modular, split across 9 Django apps:

1. academic_years

Defines yearly school calendars used by all other models.

2. students

Core student information: name, DOB, gender, created_at.

3. enrollment

Links students to academic years and levels. Tracks enrollment date and status.

4. levels

Represents student levels or classes (e.g., Grade 7, 8).

5. subjects

Courses students are graded in. Assigned per level.

6. periods

Defines school periods and exams (e.g., 1st Term, 1st Exam).

7. grades

Stores student scores. Many-to-many relationship with enrollment, subject, and period. Fields include score, updated_at.

8. grade_sheets

Compiles student results by year and level. Generates PDF reports using pywin32 for Word-to-PDF conversion.

Fields: pdf_path, filename, created_at, updated_at

Includes: pdf_utils.py, yearly_pdf_utils.py, helpers.py

9. pass_and_failed

Determines student status: Pass, Fail, Conditional, Pending. Also links to template name used for PDF export.

📄 Notable Features

Helper Modules: Each app includes a helper.py to handle business logic

DRF Serializers & Views: All models are exposed via RESTful endpoints

PDF Generation: Uses pywin32 to convert Word templates (.docx) to PDF dynamically

Status Tracking: Tracks student academic status and validations

CORS Support: Exposes a test endpoint for cross-origin verification

📂 Project Structure

project_root/
├── academic_years/
├── enrollment/
├── grade_sheets/
├── grades/
├── levels/
├── pass_and_failed/
├── periods/
├── students/
├── subjects/
├── grade_system/             # Main settings and URL routing
│   ├── settings.py
│   ├── urls.py               # Main route includes and views
│   └── wsgi.py
├── media/                    # Generated PDFs
└── manage.py

🚀 Running the Backend

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

Visit: http://localhost:8000/admin/ to access Django admin

📎 API Usage

All API endpoints are available under:

http://localhost:8000/api/

Defined in students/api/

🧠 Smart Logic with Helpers

Each app has a helper.py containing reusable logic, keeping views.py clean and focused on API tasks. For example:

grades.helper: validates and calculates student scores

pass_and_failed.helper: determines promotion eligibility

grade_sheets.pdf_utils: handles PDF export via Word templates

📄 License

MIT License

