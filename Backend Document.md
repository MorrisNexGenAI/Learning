Grade System Overview and Introduction
The Grade System is a Django-based web application designed to streamline the management of student grades, enrollments, and academic outcomes for an educational institution. It provides a robust backend for tracking student progress across various grade levels, subjects, and academic periods, enabling administrators to input grades, generate PDF report cards, and determine pass/fail statuses. The system supports both RESTful API endpoints for programmatic access and web-based interfaces for administrative tasks, making it versatile for integration with modern frontends and manual workflows. The application is modular, composed of multiple apps (students, levels, academic_years, enrollment, subjects, periods, grades, grade_sheets, pass_and_failed) that work together to deliver a comprehensive grade management solution.

Purpose and Functionality
The Grade System serves as a digital platform for:

Student Management: Storing student details (name, gender, date of birth) and associating them with enrollments in specific levels and academic years.
Level and Subject Organization: Defining grade levels (e.g., Grade 7) and subjects (e.g., Mathematics) linked to those levels, structuring the academic hierarchy.
Academic Year Tracking: Managing academic years (e.g., 2025/2026) to contextualize enrollments and grades.
Enrollment Management: Linking students to levels and academic years, ensuring accurate tracking of their academic journey.
Period Definition: Organizing academic terms (e.g., 1st period, 1st semester exam) for grade assignment.
Grade Recording: Capturing student grades for specific subjects and periods, with validation for score ranges (0–100).
Grade Sheet Generation: Producing PDF report cards for individual students or entire levels, integrating grades and pass/fail statuses.
Pass/Fail Determination: Evaluating student performance to assign statuses (PASS, FAIL, CONDITIONAL, INCOMPLETE, PENDING) and automate promotions to higher levels.
The system’s core strength lies in its integration of these components to provide a seamless flow from student enrollment to grade reporting and outcome determination. It supports both API-driven operations (e.g., for a frontend at localhost:5173) and web views for administrative tasks, such as grade input and report viewing.

Key Features
RESTful API: Endpoints for CRUD operations on students, levels, subjects, periods, grades, enrollments, academic years, grade sheets, and pass/fail statuses, accessible via /api/.
Web Interface: Views for grade input (grade_sheets/) and report viewing (grade_sheets/view/), with templates for administrative use.
PDF Generation: Automated creation of report cards using Word templates, stored as PDFs in the media directory.
Data Integrity: Unique constraints (e.g., one enrollment per student per level, one grade per subject per period) ensure consistency.
CORS Support: Configured for frontend integration at localhost:5173, with CSRF protection for secure form submissions.
Modular Design: Each app focuses on a specific domain, with helper functions and utilities for reusability.
Areas of Focus for Improvement
To ensure the Grade System operates smoothly and minimizes errors, the following areas require attention:

Data Consistency: Address overlapping fields (e.g., status in enrollment vs. pass_and_failed) and nullable foreign keys (e.g., enrollment in pass_and_failed) to prevent ambiguity.
Code Robustness: Fix logical errors (e.g., subjects’s destroy method, pass_and_failed’s order field assumption) and standardize period mappings to avoid breakage if naming changes.
Scalability: Optimize querysets with filtering/pagination, replace SQLite with a production-ready database (e.g., PostgreSQL), and add caching for PDF generation.
Security: Secure SECRET_KEY via environment variables, configure ALLOWED_HOSTS for production, and restrict sensitive serializer fields (e.g., GradeSheetPDF’s pdf_path).
Flexibility: Make grading policies configurable (e.g., number of required grades, passing thresholds) and support non-numeric level names (e.g., "Kindergarten").
Portability: Replace Windows-specific PDF generation (docx2pdf, pythoncom) with cross-platform alternatives (e.g., weasyprint) to support deployment on Linux servers.
User Experience: Enhance error messages for API consumers and web users, ensuring they are clear and actionable.
By focusing on these areas, the system can achieve greater reliability, scalability, and user-friendliness, reducing maintenance overhead and potential mistakes.

Lets dive into each step by step.

Enrollment App README
The enrollment app is a core component of the grade system backend, serving as a bridge that connects students to specific levels (classroom representations, e.g., Grade 7, 8, or 9) and academic years. It tracks student enrollment in a particular level for a given academic year, capturing essential details like the enrollment date and status. This app is foundational for other apps like grades and grade_sheets, which rely on enrollment data to associate grades and generate reports. The app includes a model for storing enrollment data, a serializer for API interactions, and a viewset for handling CRUD operations, along with a helper function for querying enrollments.

Files and Functionality
Models: The Enrollment model defines the structure for storing enrollment records. It includes foreign keys to the Student, Level, and AcademicYear models, ensuring a student is linked to a specific level and academic year. The date_enrolled field (DateField) tracks when the enrollment occurred, and the status field (CharField with choices: pass, failed, conditional, none) indicates the enrollment outcome. A unique_together constraint on student and level prevents duplicate enrollments for the same level, though it allows re-enrollment across different academic years. This model ensures data integrity and supports queries for enrollment details.
Serializers: The EnrollmentSerializer converts Enrollment model instances to JSON for API responses and validates incoming data. It includes nested serializers for student, level, and academic_year, providing detailed representations of related objects in API outputs. The serializer includes fields like id, student, level, academic_year, and date_enrolled, but excludes status, possibly indicating that status updates are managed internally or via another app. The read_only=True setting for nested fields ensures foreign keys are set by IDs during creation/updates.
Views: The EnrollmentViewSet provides RESTful API endpoints for CRUD operations (list, retrieve, create, update, delete) on Enrollment objects, using the EnrollmentSerializer. It uses a simple queryset (Enrollment.objects.all()), which retrieves all enrollments. A helper function, get_enrollment_by_student_level, allows querying enrollments by student_id, level_id, and an optional academic_year_id, returning a single enrollment or None if none exists. This function supports precise lookups, useful for validating enrollments in other apps.
Pros and Cons
Pros:
Effectively bridges Student, Level, and AcademicYear, enabling robust tracking of enrollments.
Provides a simple, RESTful API for managing enrollments, with nested serializers for rich data output.
The unique_together constraint ensures data integrity by preventing duplicate level enrollments.
The helper function enhances reusability for enrollment lookups across the system.
Cons:
The status field overlaps with the pass_and_failed app’s functionality, creating potential redundancy. It’s unclear whether status is for enrollment outcomes or academic performance, requiring clarification or consolidation.
The unique_together constraint excludes academic_year, allowing re-enrollment in the same level across years, which may or may not be desired.
The viewset’s queryset (Enrollment.objects.all()) lacks filtering or pagination, which could impact performance with large datasets.
The status field’s exclusion from the serializer limits API functionality for status updates.
A dedicated helper file was mentioned but not provided, suggesting potential organization issues if helper logic is scattered (e.g., in views.py).
Grades App README
The grades app is a central component of the grade system backend, described as the "heart" of the application due to its role in securely storing and delivering student grades. It connects enrollment data (student, level, academic year) with subjects and periods, allowing the system to record grades for a student in a specific subject during a specific period (e.g., 1st, 2nd, or exam periods). The app supports digital grade delivery and record-keeping, forming the basis for generating grade sheets. It includes a model for grade data, a serializer for API interactions, a viewset for CRUD operations, and a helper file with utilities for managing and calculating grades.

Files and Functionality
Models: The Grade model stores grade data, with foreign keys to Enrollment (linking student, level, academic year), Subject, and Period. The score field (FloatField, nullable) holds the grade value, and updated_at (DateTimeField, auto-updated) tracks when the grade was last modified. A unique_together constraint on enrollment, subject, and period ensures a student has only one grade per subject per period, maintaining data integrity. The model’s string representation shows the student, subject, period, and score, aiding debugging and display.
Serializers: The GradeSerializer handles serialization and validation for Grade objects. It includes derived fields: student_id and student_name (from the enrollment foreign key), and score (converted to DecimalField with two decimal places for precision). The validate_score method ensures scores are between 0 and 100, enhancing data quality. The serializer includes fields for student_id, student_name, score, enrollment, subject, and period, making it suitable for API responses and grade input.
Views: The GradeViewSet provides RESTful API endpoints for CRUD operations on Grade objects, using the GradeSerializer. It overrides get_queryset to support filtering by student_id, subject_id, and period_id via query parameters, improving query efficiency. The create method supports bulk creation (accepting a list of grades), and the update method allows partial updates, both with proper validation and error handling. The viewset uses a logger for debugging and error tracking.
Helper: The helper.py file contains two key functions:
get_grade_map: Retrieves grades for a given level_id, organizing them into a nested dictionary (student_id → subject_id → period → score). It normalizes period names (e.g., mapping "1st semester exam" to "1exam") and converts scores to floats, handling nullable scores. This function is likely used for generating grade reports or summaries.
save_grade: Creates or updates a grade for a given enrollment, subject_id, period_id, and score. It validates the period, subject, and score (ensuring 0–100 range), logs actions/errors, and returns the grade object or an error message. This function encapsulates grade-saving logic, reducing duplication in views.
calc_semester_avg and calc_final_avg: Utility functions for calculating semester and final averages from scores and exam grades, rounding results to two decimal places. These support grade sheet calculations.
Pros and Cons
Pros:
Robustly connects Enrollment, Subject, and Period, enabling precise grade tracking for students across academic periods.
The unique_together constraint ensures no duplicate grades for the same student, subject, and period, maintaining data integrity.
The serializer’s score validation (0–100) and decimal precision enhance data quality and consistency.
The viewset’s filtering and bulk creation capabilities improve usability and performance for API consumers.
The helper functions (get_grade_map, save_grade, etc.) encapsulate complex logic, making the app modular and maintainable.
Cons:
The score field’s FloatField allows nullable values, which may cause issues in calculations (e.g., calc_semester_avg handles this, but nulls could confuse consumers). Consider a default value or stricter validation.
The get_grade_map function’s period normalization (e.g., "1st semester exam" to "1exam") is hardcoded and may break if period names change. A more dynamic mapping (e.g., via model fields) would be robust.
The viewset’s base queryset (Grade.objects.all()) could be optimized further with default filters or pagination for large datasets.
Logging is used effectively, but error messages in save_grade could be more user-friendly for API consumers.
The calc_semester_avg and calc_final_avg functions assume equal weighting for scores and exams, which may not align with all grading policies.

Grade Sheets App README
The grade_sheets app is the "heartbeat" of the grade system backend, orchestrating the generation, storage, and delivery of student grade sheets in PDF format. It integrates data from multiple apps (students, levels, academic_years, grades, enrollment, subjects, periods, and pass_and_failed) to create comprehensive report cards for students, either individually or for an entire level. The app manages PDF storage, grade input, and retrieval of grade data, supporting both API and web-based interfaces. It includes a model for tracking PDF records, a serializer for API interactions, a viewset for API endpoints, views for web rendering, and utility files for PDF generation and cleanup.

Files and Functionality
Models: The GradeSheetPDF model stores metadata for generated PDF grade sheets. It includes foreign keys to Level, Student (nullable), and AcademicYear (nullable) to associate PDFs with specific students, levels, and years. The pdf_path (CharField, unique) stores the filesystem path to the PDF, and filename (CharField) holds the PDF’s name (e.g., report_card_Jenneh_Fully_20250613_085600.pdf). The created_at and updated_at fields (DateTimeField, auto-managed) track record creation and updates. A unique_together constraint on level, student, and academic_year ensures one PDF per student per level per year. The view_url property provides a URL for accessing the PDF via Django’s media settings.
Serializers: The GradeSheetSerializer is a simple serializer that exposes all fields of the GradeSheetPDF model (__all__) for API interactions. It allows retrieval and creation of PDF records, including paths and metadata, making it suitable for managing PDF storage and access via RESTful APIs.
Views: The GradeSheetViewSet provides RESTful API endpoints for grade sheet operations:
input_grades: Accepts bulk grade submissions for a level, subject, period, and academic year, saving grades via the save_grade helper and deleting outdated PDFs for affected students.
list_by_level: Retrieves grade data for all students in a level, optionally filtered by academic year, calculating semester and final averages for each subject.
generate_gradesheet_pdf: Generates PDF grade sheets for a level or single student, checking for outdated PDFs and regenerating if newer grades exist.
view_gradesheet_pdf: Serves existing PDFs or regenerates them if outdated or missing, returning a FileResponse for inline viewing.
fetch_by_subject_and_period: Retrieves grades for a level, subject, and optional period/academic year, formatted for display.
check_enrollment: Verifies if a student is enrolled in a level for a given academic year. Additional views (gradesheet_home, gradesheet_view, input_grades_view) render web templates for grade input and viewing, handling form submissions and redirects. The cors_test view supports CORS testing for frontend integration.
Utils: The utils.py file contains:
cleanup_old_pdfs: Deletes PDFs and their database records older than a specified number of days (default: 2), freeing storage.
determine_pass_fail: Calculates a student’s pass/fail status based on grades for a level and academic year, requiring at least 8 grades per subject and an average score above a passing threshold (default: 50). Returns PASSED, FAILED, or INCOMPLETE.
PDF Utils: The pdf_utils.py file defines generate_gradesheet_pdf, which generates PDF grade sheets using a Word template (report_card_compact.docx). It renders student data into the template, converts it to PDF using docx2pdf, and merges multiple PDFs for bulk printing. It handles single-student or level-wide generation, ensuring proper file permissions and cleanup of temporary .docx files.
Helper: The helper.py file contains get_grade_sheet_data, which compiles grade data for a student, level, and optional academic year. It retrieves grades, maps them to periods (e.g., 1st to 1, 1exam to 1s), and includes pass/fail status from determine_pass_fail. The data is structured for use in PDF templates, including student name, subject grades, and status.
Pros and Cons
Pros:
Seamlessly integrates data from multiple apps to generate comprehensive PDF grade sheets, fulfilling the app’s role as the system’s "heartbeat."
Supports both API and web interfaces, offering flexibility for frontend and administrative use.
The unique_together constraint ensures one PDF per student per level per year, maintaining data integrity.
Robust PDF management (generation, regeneration, cleanup) ensures up-to-date grade sheets and efficient storage use.
The determine_pass_fail function provides clear logic for pass/fail status, enhancing integration with pass_and_failed.
Cons:
Nullable student and academic_year fields in GradeSheetPDF may cause ambiguity for level-wide PDFs, requiring careful handling in queries.
The GradeSheetSerializer’s use of __all__ fields exposes potentially sensitive data (e.g., pdf_path) without restrictions, posing a security risk.
Hardcoded period mappings in get_grade_sheet_data (e.g., 1st to 1) may break if period names change, needing a dynamic solution.
PDF generation relies on external libraries (docx2pdf, PyPDF2) and a Windows-specific COM interface (pythoncom), limiting portability to non-Windows environments.
The pass/fail logic assumes 8 grades per subject and equal weighting, which may not align with all grading policies, requiring customization.


Students App README
The students app is the cornerstone of the grade system backend, representing the students for whom the entire system is designed. It manages student data, including personal details like name, gender, and date of birth, and integrates with other apps (enrollment, pass_and_failed, grades) to track student progress, enrollments, and academic outcomes. The app includes a model for storing student information, a serializer for API interactions, a viewset for CRUD operations, a helper file for utility functions, and an API configuration for routing across multiple apps.

Files and Functionality
Models: The Student model defines the structure for student records. It includes firstName and lastName (CharField, max length 50) for the student’s name, gender (CharField with choices: M, F, O for Male, Female, Other), dob (DateField) for date of birth, and created_at (DateTimeField, auto-added) to track record creation. The model has no foreign keys, focusing solely on student attributes. The __str__ method returns the full name (firstName lastName) for readable display.
Serializers: The StudentSerializer handles serialization and validation for Student objects. It includes core fields (id, firstName, lastName, gender, dob) and derived fields: level and academic_year, populated via SerializerMethodField. These fields fetch the student’s latest enrollment (if any) to include level and academic year details using LevelSerializer and a custom dictionary, respectively. The create method creates a student record, leaving enrollment handling to the viewset.
Views: The StudentViewSet provides RESTful API endpoints for CRUD operations on Student objects, using the StudentSerializer. The create method creates a student and optionally enrolls them in a level and academic year using helper functions (create_enrollment_for_student, create_pass_failed_status). The get_queryset method supports filtering by level_id and academic_year_name, returning students enrolled in the specified level and year, or an empty queryset if the level or year is invalid.
Helper: The helper.py file contains utility functions:
get_students_by_level: Retrieves students enrolled in a specific level, ensuring distinct results.
format_student_data: Formats a student’s data (ID and full name) for use in grade sheets, with an empty subjects list for external population.
format_student_name: Returns the student’s full name.
create_enrollment_for_student: Creates an Enrollment record for a student, level, and academic year.
create_pass_failed_status: Creates a PassFailedStatus record, determining the status (INCOMPLETE or PENDING) based on the number of grades relative to expected grades (8 per subject).
API: The api.py file configures a DefaultRouter for RESTful API routes across multiple apps, registering viewsets for students, subjects, grades, enrollments, levels, periods, grade_sheets, academic_years, and pass_failed_status. It also defines a custom URL for the ReportCardPrintView from grade_sheets, centralizing API routing for the system.
Pros and Cons
Pros:
Simple and focused Student model captures essential student details without unnecessary complexity.
The serializer’s derived fields (level, academic_year) provide rich data for API consumers by leveraging enrollment data.
The viewset’s filtering by level and academic year enhances query flexibility for enrollment-specific use cases.
Helper functions encapsulate reusable logic (e.g., enrollment and pass/fail creation), improving modularity.
Centralized API routing in api.py streamlines endpoint management across the system.
Cons:
The get_level and get_academic_year methods in the serializer rely on enrollment.first(), which may return inconsistent results if multiple enrollments exist, as it lacks sorting (e.g., by date_enrolled or most recent academic year).
The create method in the viewset allows student creation without enrollment, which may lead to incomplete records if level or academic_year is missing.
The get_queryset filtering assumes a single academic year and level, which may not handle cases where students are enrolled in multiple levels or years.
The pass/fail status logic in create_pass_failed_status assumes 8 grades per subject, which may not align with all grading policies and could be made configurable.
The api.py file, while centralizing routes, is part of the students app, which may cause confusion as it manages routes for all apps; consider moving it to a project-level directory.

Levels App README
The levels app represents the digital equivalent of classrooms in the grade system backend, defining the grade levels (e.g., Grade 7, 8, or 9) that students are enrolled in. It is a lightweight but essential component, providing a structure for organizing students, subjects, and grades by class level. The app integrates with enrollment, grades, and grade_sheets to ensure students are associated with the correct level for academic tracking. It includes a model for storing level data, a serializer for API interactions, a viewset for CRUD operations, and a helper file for utility functions.

Files and Functionality
Models: The Level model is a simple structure with a single field, name (CharField, max length 13), which stores the level’s name (e.g., "Grade 7"). The __str__ method attempts to use get_name_display(), which is typically used for fields with choices, but since name lacks choices, it effectively returns the name itself. The Meta class specifies ordering by name, ensuring consistent sorting in queries and displays.
Serializers: The LevelSerializer is straightforward, exposing all fields of the Level model (__all__, i.e., id and name) for API interactions. It supports serialization and deserialization for creating, retrieving, updating, or deleting levels via RESTful APIs.
Views: The LevelViewSet provides RESTful API endpoints for CRUD operations on Level objects, using the LevelSerializer. It uses a simple queryset (Level.objects.all()) to retrieve all levels, supporting standard operations like listing, retrieving, creating, updating, and deleting levels. The viewset is minimal, relying on Django REST Framework’s default functionality.
Helper: The helper.py file contains utility functions:
get_all_levels: Retrieves all levels, used in views or other apps for dropdowns or lists.
get_level_by_id: Fetches a level by its ID, returning None if it doesn’t exist.
get_level_by_name: Fetches a level by its name, also returning None if not found.
create_level: Creates a new level with the given name.
update_level: Updates a level’s name by ID, raising an error if the level doesn’t exist.
delete_level: Deletes a level by ID, returning True on success or False if the level doesn’t exist.
Pros and Cons
Pros:
Simple and focused Level model with a single name field, making it easy to maintain and integrate with other apps.
The serializer’s use of __all__ fields ensures all necessary data (ID and name) is available for API consumers.
The viewset provides a complete set of CRUD operations, sufficient for managing levels via API.
Helper functions cover common operations (fetch, create, update, delete), improving code reusability across the system.
The Meta ordering by name ensures consistent presentation of levels in UI or API responses.
Cons:
The __str__ method’s use of get_name_display() is misleading since name has no choices defined, potentially causing confusion; it should simply return self.name.
The name field’s max length of 13 may be restrictive for some level names (e.g., "Kindergarten" or "Advanced Placement"), risking truncation.
The viewset’s queryset (Level.objects.all()) lacks filtering or pagination, which could be inefficient for large datasets, though levels are likely few.
The get_level_by_name helper function is unused in the provided code, suggesting it may be redundant or planned for future use.
No validation ensures level names are unique, which could lead to duplicate levels (e.g., two "Grade 7" entries), potentially causing confusion in enrollment or grades.

Subjects App README
The subjects app manages the courses (referred to as subjects) that students take within specific grade levels in the grade system backend. It links subjects to levels (e.g., "Mathematics" for Grade 7), enabling the system to track grades for students in specific subjects during academic periods. The app integrates with grades, enrollment, and grade_sheets to support grade assignment and report generation. It includes a model for storing subject data, a serializer for API interactions, a viewset for CRUD operations, and a helper file for utility functions.
Files and Functionality

Models: The Subject model defines the structure for subject records. It includes subject (CharField, max length 50) for the subject name (e.g., "Mathematics") and a foreign key level to the Level model, linking the subject to a specific grade level. The Meta class enforces a unique_together constraint on subject and level, preventing duplicate subjects within the same level, and orders results by subject and level. The __str__ method returns a readable format (subject (level)), e.g., "Mathematics (Grade 7)".

Serializers: The SubjectSerializer exposes a subset of Subject model fields (id, subject) for API interactions, notably excluding the level field. This allows API consumers to retrieve or create subjects by name but requires the level to be specified separately (e.g., via query parameters or view logic).

Views: The SubjectViewSet provides RESTful API endpoints for CRUD operations on Subject objects, using the SubjectSerializer. It overrides the destroy method to handle subject deletion, checking if the subject exists using get_subjects_by_level and calling delete_subject to perform the deletion. The method logs actions and returns appropriate responses for success, not found, or errors. The base queryset (Subject.objects.all()) retrieves all subjects, supporting standard operations like listing, retrieving, creating, and updating.

Helper: The helper.py file contains utility functions:

get_subjects_by_level: Retrieves subjects for a given level ID, returning a dictionary mapping subject IDs to names, useful for grade sheets or dropdowns.
create_subject: Creates a subject for a specified level, ensuring the level exists and using get_or_create to avoid duplicates.
update_subject: Updates a subject’s name and/or level by ID, validating the new level if provided.
delete_subject: Deletes a subject by ID, returning True on success or False if the subject doesn’t exist.



Pros and Cons

Pros:

The Subject model’s unique_together constraint ensures no duplicate subjects per level, maintaining data integrity.
The serializer’s focus on id and subject simplifies API interactions for subject data, aligning with common use cases.
The viewset’s custom destroy method adds safety by checking subject existence before deletion, though it lacks grade association checks.
Helper functions provide reusable logic for subject management, enhancing modularity and integration with other apps (e.g., grade_sheets).
The model’s ordering by subject and level ensures consistent presentation in UI or API responses.


Cons:

The SubjectViewSet’s destroy method incorrectly uses get_subjects_by_level to fetch a single subject by ID, which is a logical error since it returns a dictionary of subjects for a level. It should use Subject.objects.get(id=id).
The destroy method references IndentationError and NotImplemented in error messages, indicating copy-paste errors or incomplete code, leading to misleading logs.
The serializer excludes the level field, requiring clients to infer or specify levels separately, which may complicate API usage for creating or updating subjects.
The destroy method does not check for associated grades, risking data integrity issues if a subject with grades is deleted (though your code suggests this check was intended).
The subject field’s max length of 50 may be restrictive for longer subject names (e.g., "Advanced Placement Biology"), risking truncation.


Periods App README
The periods app manages the academic terms within an academic year in the grade system backend, defining distinct periods (e.g., 1st, 2nd, 3rd, 1exam, 4th, 5th, 6th, 2exam) during which students receive lessons and take tests, culminating in semester exams. It supports the grades and grade_sheets apps by providing a structure for assigning grades to specific periods. The app includes a model for storing period data, a serializer for API interactions, a viewset for basic CRUD operations, and a helper file for utility functions.

Files and Functionality
Models: The Period model defines the structure for period records. It includes period (CharField, max length 9) with predefined choices (1st, 2nd, 3rd, 1exam, 4th, 5th, 6th, 2exam) to represent academic terms, with a unique constraint to prevent duplicates. The is_exam field (BooleanField, default False) flags whether a period is an exam (e.g., 1exam, 2exam). The __str__ method returns the period’s code (e.g., 1st), though it uses the raw value rather than the display name from choices.
Serializers: The PeriodSerializer exposes all fields of the Period model (id, period, is_exam) for API interactions. It supports serialization and deserialization for creating, retrieving, updating, or deleting periods via RESTful APIs, providing full access to period data.
Views: The PeriodViewSet provides RESTful API endpoints for managing periods, using the PeriodSerializer. It implements custom list and retrieve methods:
list: Fetches all periods using get_all_periods and returns serialized data.
retrieve: Fetches a single period by ID using get_period_by_id, returning a 404 if not found. The viewset logs actions and errors, but relies on Django REST Framework’s default methods for create, update, and delete operations. The base queryset is not explicitly defined, as the viewset overrides specific methods.
Helper: The helper.py file contains utility functions:
get_all_periods: Retrieves all periods, used in views and other apps (e.g., grade_sheets) for dropdowns or lists.
get_period_by_id: Fetches a period by ID, returning None if not found.
create_period: Creates a period with a given code and optional is_exam flag, using get_or_create to avoid duplicates.
update_period: Updates a period’s code or is_exam status by ID, raising an error if the period doesn’t exist.
delete_period: Deletes a period by ID, returning True on success or False if not found.
Pros and Cons
Pros:
The Period model’s predefined choices ensure consistent period naming, aligning with the described structure of six periods and two exams per year.
The unique constraint on period prevents duplicate periods, maintaining data integrity.
The serializer’s inclusion of all fields (id, period, is_exam) provides complete access to period data for API consumers.
Helper functions cover common operations (fetch, create, update, delete), enhancing modularity and reusability across apps.
Logging in the viewset aids debugging and monitoring of period-related API requests.
Cons:
The __str__ method returns the raw period value (e.g., 1st) instead of the display name (e.g., 1st period), which could be confusing in admin interfaces or logs.
The period field’s default value (1st period) mismatches the choices’ values (e.g., 1st), causing potential validation errors on creation.
The viewset lacks a custom destroy method to check for associated grades, risking data integrity if a period with grades is deleted.
The is_exam field is not automatically set based on the period choice (e.g., 1exam, 2exam), requiring manual setting and risking inconsistencies.
The create_period and update_period helpers allow arbitrary period codes, bypassing the model’s choices, which could introduce invalid periods.



Pass and Failed App README
The pass_and_failed app determines and tracks students' academic outcomes (pass, fail, conditional, incomplete, or pending) for a specific level and academic year in the grade system backend. It integrates with students, levels, academic_years, enrollment, and grades to assess whether students meet promotion criteria, generating appropriate statuses and triggering actions like promotion or PDF report generation. The app includes a model for storing status data, a serializer for API interactions, a viewset for CRUD operations, and utility/helper files for validation and promotion logic.

Files and Functionality
Models: The PassFailedStatus model tracks a student’s academic status. It includes foreign keys to Student, Level, AcademicYear, and Enrollment (nullable) to associate the status with a student’s enrollment in a level and year. The status field (CharField, choices: PASS, FAIL, CONDITIONAL, INCOMPLETE, PENDING) defaults to INCOMPLETE. Additional fields include validated_at (DateTimeField, nullable) and validated_by (CharField, nullable) for audit trails, template_name (CharField) for PDF templates, and grades_complete (BooleanField) to indicate if grades are complete. A unique_together constraint on student, level, and academic_year ensures one status per student per level per year. The save method dynamically sets template_name based on status (e.g., yearly_card_pass.docx for PASS). The __str__ method returns a readable format (e.g., "John Doe - Grade 7 - 2025/2026 - PASS").
Serializers: The PassFailedStatusSerializer serializes PassFailedStatus objects, including nested serializers for student, level, academic_year, and enrollment (read-only, allowing null). It exposes all fields (id, student, level, academic_year, enrollment, status, validated_at, validated_by, template_name, grades_complete), providing rich data for API consumers.
Views: The PassFailedStatusViewSet provides RESTful API endpoints for CRUD operations, using the PassFailedStatusSerializer. It overrides get_queryset to filter by level_id and academic_year, initializing missing statuses via initialize_missing_statuses. Custom actions include:
validate_status: Updates a status (e.g., to PASS) with a validator’s name, checking grade completeness and triggering promotion if eligible.
print_status: Generates a PDF grade sheet for a status using generate_yearly_gradesheet_pdf, storing it in GradeSheetPDF.
Utils: The utils.py file contains:
validate_student_grades: Checks if a student has complete grades for all subjects in a level and year, requiring grades for 8 periods and averages (1st, 2nd, 3rd, 1exam, 4th, 5th, 6th, 2exam, semester/final averages). Returns a boolean and message.
promote_student: Promotes a student to the next level and academic year if their status is PASS or CONDITIONAL, creating a new enrollment. It assumes level names are numeric (e.g., "7") and academic years follow a pattern (e.g., "2025/2026" to "2026/2027").
Helper: The helper.py file contains:
handle_validate_status: Handles the validate_status action, updating status and validator, checking grade completeness, and triggering promotion.
promote_student_if_eligible: Promotes a student to the next level (based on an assumed order field in Level), updating current enrollment to PROMOTED and creating a new ENROLLED enrollment.
initialize_missing_statuses: Creates PassFailedStatus records for enrollments lacking them, setting INCOMPLETE or PENDING based on grade count (8 per subject).
Pros and Cons
Pros:
The PassFailedStatus model’s unique_together constraint ensures one status per student per level per year, maintaining data integrity.
Nested serializers provide comprehensive status data, including related student, level, year, and enrollment details.
The viewset’s custom actions (validate_status, print_status) and filtering enhance functionality for status management and reporting.
Utility functions (validate_student_grades, promote_student) encapsulate complex logic, improving modularity and reusability.
The save method’s dynamic template_name assignment streamlines PDF generation integration with grade_sheets.
Cons:
The promote_student_if_eligible function assumes a non-existent order field in Level, causing errors; it should use promote_student from utils.py, which parses level names numerically.
The enrollment foreign key is nullable, but initialize_missing_statuses sets it, creating inconsistency; consider making it non-nullable.
Hardcoded period mappings in validate_student_grades (e.g., 1s for 1exam) may break if Period choices change, needing a dynamic approach.
The promotion logic assumes numeric level names (e.g., "7") and a specific academic year format, limiting flexibility for non-standard naming (e.g., "Kindergarten").
The grades_complete field and status logic rely on 8 grades per subject, which may not align with all grading policies and should be configurable.

Grade System URLs and Settings README
The grade_system project serves as the backbone of the grade management system, tying together various apps (students, grades, enrollment, subjects, levels, periods, grade_sheets, academic_years, pass_and_failed) through centralized URL routing and configuration. The urls.py file defines the project’s URL patterns, while settings.py configures the Django environment, including apps, middleware, database, REST framework, CORS, and static/media file handling. These files ensure seamless integration of the system’s components, supporting both API and web-based interfaces.

Files and Functionality
URLs (grade_system/urls.py): The urls.py file defines the project’s URL patterns, routing requests to appropriate views or included URL configurations:
path('api/', include('students.api')): Includes API routes from the students.api module, which uses a DefaultRouter to register endpoints for all apps (e.g., /api/students/, /api/grades/, /api/grade_sheets/).
path('grade_sheets/', gradesheet_home, name='gradesheet-home'): Maps to the gradesheet_home view in grade_sheets, rendering a web interface for grade input.
path('grade_sheets/view/', gradesheet_view, name='gradesheet'): Maps to the gradesheet_view view, displaying grade sheets for a level.
path('admin/', admin.site.urls): Provides access to Django’s admin interface for managing models.
path('api/cors-test/', cors_test, name='cors-test'): A test endpoint for CORS configuration, allowing frontend integration checks.
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT): Serves media files (e.g., PDFs in grade_sheets) during development, mapping /media/ to the MEDIA_ROOT directory.
Settings (grade_system/settings.py): The settings.py file configures the Django project, defining:
Project Structure: BASE_DIR sets the project root directory, used for paths like MEDIA_ROOT and STATICFILES_DIRS.
Security: SECRET_KEY (insecure, for development), DEBUG=True, and empty ALLOWED_HOSTS (needs updating for production).
Installed Apps: Includes Django’s core apps (admin, auth, etc.), third-party apps (rest_framework, corsheaders), and custom apps (students, grades, etc.).
Middleware: Configures security, session, CORS, CSRF, authentication, and message handling. corsheaders.middleware.CorsMiddleware is correctly placed before CommonMiddleware.
CORS: Allows requests from http://localhost:5173 and http://127.0.0.1:5173, with specific methods (GET, POST, etc.) and headers (e.g., x-csrftoken). CSRF_TRUSTED_ORIGINS includes localhost:5173 for CSRF protection.
Templates: Configures Django’s template engine, with DIRS pointing to a project-level templates directory and app-level template loading enabled.
Database: Uses SQLite (db.sqlite3) for simplicity, suitable for development.
REST Framework: Sets DATE_INPUT_FORMATS to YYYY-MM-DD and disables the browsable API renderer, ensuring JSON-only responses.
Static/Media Files: Defines STATIC_URL (/static/), STATICFILES_DIRS for static assets, MEDIA_URL (/media/), and MEDIA_ROOT for uploaded/generated files (e.g., PDFs).
Internationalization: Sets LANGUAGE_CODE to en-us, TIME_ZONE to UTC, and enables i18n and timezone support.
Password Validation: Enforces standard Django password validators (similarity, length, common, numeric).
Default Auto Field: Uses BigAutoField for primary keys.
Pros and Cons
Pros:
The urls.py file effectively centralizes routing, integrating API endpoints (via students.api) and web views (grade_sheets), supporting both RESTful and web interfaces.
The settings.py file includes essential configurations for CORS, REST framework, and media/static file handling, enabling frontend integration (e.g., at localhost:5173) and PDF serving.
All custom apps are correctly registered in INSTALLED_APPS, ensuring their models and views are available.
The SQLite database is lightweight and suitable for development, reducing setup complexity.
Disabling the browsable API renderer in REST_FRAMEWORK ensures consistent JSON responses, improving API reliability for frontend clients.
Cons:
The SECRET_KEY is hardcoded and marked as insecure, posing a security risk if deployed; it should be stored in environment variables.
ALLOWED_HOSTS is empty, preventing the app from running in production; it needs values like ['localhost', '127.0.0.1'] or domain names.
The students.api inclusion in urls.py is misleading, as it handles routes for all apps, suggesting it should be renamed (e.g., api.urls) or moved to a project-level api module.
The cors-test endpoint is useful for debugging but should be removed or secured in production to avoid unnecessary exposure.
The SQLite database may not scale for production use, requiring migration to a more robust database (e.g., PostgreSQL) for concurrent access.

Academic Years App
The academic_years app manages academic year records in the school management system, defining periods (e.g., "2024/2025") with start and end dates. It supports apps like enrollment, grade_sheets, and pass_and_failed by associating records with specific academic years. The app includes a model for storing year data, a serializer for API interactions, a viewset for CRUD operations, and a helper file for utility functions.
Files and Functionality
Models
The AcademicYear model defines the structure for academic year records. It includes:

name (CharField, max_length=20, unique=True): Year name in "YYYY/YYYY" format (e.g., "2024/2025").
start_date (DateField): Start date of the academic year.
end_date (DateField): End date of the academic year.
Validators: A regex validator ensures name follows "YYYY/YYYY". A clean() method validates that end_date is after start_date and matches the years in name.
The __str__ method returns the name (e.g., "2024/2025").
Meta: Unique constraint on name and ordering by -start_date (most recent first).

Serializers
The AcademicYearSerializer exposes id, name, start_date, and end_date for API interactions. It supports serialization and deserialization for creating, retrieving, updating, or deleting academic years via RESTful APIs. The id field is read-only to prevent accidental updates.
Views
The AcademicYearViewSet provides RESTful API endpoints for managing academic years, using the AcademicYearSerializer. It implements:

list: Fetches all academic years, with optional filtering by is_active (current year based on today’s date) or name.
retrieve: Fetches a single academic year by ID.
create/update/delete: Handled by Django REST Framework’s default methods.
Features: Pagination (100 items per page), caching (1-hour timeout), filtering by is_active (where start_date ≤ today ≤ end_date) and name, and ordering by -start_date.

Helper
The helper.py file contains utility functions:

get_all_academic_years: Retrieves all academic years, cached for 1 hour.
get_academic_year_by_id: Fetches an academic year by ID, returning None if not found.
get_academic_year_by_name: Fetches an academic year by name (e.g., "2024/2025"), returning None if not found.
get_current_academic_year: Returns the academic year containing today’s date, cached for 1 hour.
create_academic_year: Creates a new academic year with name, start_date, and end_date.
update_academic_year: Updates an academic year’s name, start_date, or end_date by ID, raising an error if not found.
delete_academic_year: Deletes an academic year by ID, returning True on success or False if not found.

Pros and Cons
Pros

The AcademicYear model’s unique constraint on name prevents duplicate years, ensuring data integrity.
The regex validator and clean() method enforce a consistent "YYYY/YYYY" format and valid date ranges.
The serializer explicitly defines fields (id, name, start_date, end_date), avoiding exposure of sensitive data.
Helper functions cover common operations (fetch, create, update, delete, current year), enhancing modularity and reusability.
The viewset’s filtering by is_active and caching improves efficiency for current-year queries.
Pagination and indexing on start_date and end_date support scalability for large datasets.

Cons

Lack of Validation for name Format (Resolved): The name field lacked validation for "YYYY/YYYY", risking inconsistent data.
Viewset Queryset Lacking Filtering (Resolved): The queryset didn’t filter by active status or date range, making current-year queries inefficient.
No Current Year Helper (Resolved): No function existed to retrieve the current academic year based on the system date.
No Created/Updated Timestamps: The model lacks created_at and updated_at fields, limiting auditability.
No Validation for Overlapping Years: The model allows overlapping date ranges (e.g., two years covering 2024), which could confuse logic.

Resolved Cons

Lack of Validation for name Format: Added a RegexValidator for "YYYY/YYYY" and a clean() method to validate start_date, end_date, and name year alignment.
Viewset Queryset Lacking Filtering: Added filtering by is_active=true (current year) and name, with pagination and caching.
No Current Year Helper: Added get_current_academic_year to fetch the active year based on today’s date, with caching.

