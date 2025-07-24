Software Development Life Cycle (SDLC) for Student Grading & Report Card System



This was the Initial plan for the system. I haven't started phrase 2 yet.

1. Project Overview

The Student Grading & Report Card System is a full-stack web application designed to streamline grading and reporting for schools, initially targeting Bomi Junior High. It addresses challenges in Liberian and West African schools, such as manual grade calculations, lost records, and lack of digital academic histories. The system will start with a Minimum Viable Product (MVP) for a single school, with planned expansions for multi-tenancy, enhanced authentication, Progressive Web App (PWA), attendance tracking, mobile/desktop apps, and AI-assisted feedback.

Current Status: Pre-development, with requirements and design based on observed school needs. Future Vision: A scalable, multi-tenant system serving thousands of schools with customized branding, automated workflows, offline capabilities, and AI-driven insights.

2. SDLC Phases

Phase 1: Requirements Analysis

Objective: Define core problems and system requirements for the MVP based on school needs. Activities:





Identify pain points: manual grade entry, lost records, no academic history, and lack of progress tracking for teachers, students, and parents.



Define MVP functional requirements:





Teachers input grades once; system handles calculations, averages, and report card generation.



Secure digital storage of academic history in a database.



Admin access to manage years, subjects, students, and generate reports.



Support for customizable report card templates (PDF/Word).



User-friendly dashboard for quick access to student data and grades.



Define non-functional requirements:





Scalability for future multi-school support.



Responsive, intuitive UI for teachers and admins.



Modular architecture for easy feature expansion.



Plan future phases:





Phase 2: Multi-tenancy, enhanced authentication, PWA.



Phase 3: Attendance tracking, mobile/desktop apps for offline use.



Phase 4: AI-assisted feedback for student progress.

Deliverables:





Requirements document outlining problems, MVP features, and future roadmap.



User stories for teachers, admins, students, and parents.



Phase 2: System Design

Objective: Architect a modular, scalable system for the MVP with a clear tech stack. Activities:





Select tech stack:





Backend: Python + Django + Django REST Framework (DRF) for rapid development, API support, and scalability; SQLite for development, PostgreSQL for production.



Frontend: React + TypeScript + Vite for type-safe, modular UI with fast builds; Tailwind CSS for responsive styling.



Database: SQLite (development) for simplicity, PostgreSQL (production) for performance.



Design modular Django apps for MVP:





students: Store student data (name, DOB, gender) with unique constraints and CRUD APIs.



enrollment: Link students to levels (e.g., Grade 7) and academic years (e.g., 2024–2025).



subjects: Manage courses per level with regex validation.



periods: Define academic terms/exams (e.g., 1st, 2nd, 1exam) with data protection.



academic_years: Manage school years with date validation.



grades: Record scores by subject, period, and enrollment with validation.



pass_and_failed: Determine student statuses (PASS, FAIL, CONDITIONAL) with dynamic template mapping.



grade_sheets: Generate PDF/Word report cards using .docx templates.



grade_system: Centralize settings, URLs, CORS, CSRF, and media handling.



Design frontend structure:





Modular folders: api/, components/, hooks/, pages/, routes/, templates/, types/, styles/.



Reusable components: Sidebar, Header, Footer, AdminList, AdminForm.



Bomi Junior High theming (green/white palette).



Custom hooks: useDashboard, useStudent, useGradeEntry, useGradeSheets, useReportCard.



Plan future phase designs:





Multi-tenancy: Core app with School/User models, tenant isolation via foreign keys.



Authentication: JWT with MFA and SSO.



PWA: Service workers for offline support.



Attendance Tracking: Models and APIs for attendance records.



Mobile/Desktop Apps: React Native for mobile, Electron for desktop offline support.



AI Feedback: Integration of AI models for progress insights.

Deliverables:





System architecture diagram (backend apps, frontend structure, data flow).



Database schema (models, relationships, constraints).



API specifications (DRF endpoints with pagination).



Frontend wireframes and component hierarchy.



Phase 3: Implementation (MVP)

Objective: Develop and integrate backend and frontend for the MVP. Activities:





Backend Development:





Build 9 Django apps (students, enrollment, subjects, periods, academic_years, grades, pass_and_failed, grade_sheets, grade_system).



Implement models, serializers, views, and helpers for modularity.



Configure settings.py for CORS, CSRF, and media handling (PDFs, static assets).



Add caching for subjects and academic_years; unique constraints for data integrity.



Use docxtpl for dynamic PDF/Word report card generation.



Frontend Development:





Build React + TypeScript frontend with Vite.



Develop reusable components (Sidebar, Header, Footer, AdminList, AdminForm) with Bomi Junior High theming.



Create custom hooks for data fetching and state management.



Implement pages for dashboard, student management, grade entry, grade sheets, and report cards.



Use Tailwind CSS for responsive, consistent styling.



Integration:





Connect backend APIs to frontend via apiClient.ts with Axios.



Implement toast-based error handling for API calls.



Use iterative prototyping to refine features based on feedback.

Deliverables:





Functional MVP source code (Django backend, React frontend).



API documentation (e.g., /api/students/, /api/grade_sheets/).



Deployable prototype themed for Bomi Junior High.



Phase 4: Testing (MVP)

Objective: Ensure MVP reliability, data integrity, and usability. Activities:





Write unit tests for backend (models, serializers, views) to validate logic (e.g., grade calculations, status determination).



Perform integration tests for API-frontend connectivity.



Conduct manual testing for UI responsiveness and user flows (e.g., grade entry, report generation).



Collect feedback from Bomi Junior High to refine usability.

Deliverables:





Test cases for core functionality.



Bug reports and fixes for identified issues.

Timeline: 1 month.

Phase 5: Deployment (MVP)

Objective: Deploy the MVP for Bomi Junior High. Activities:





Deploy with SQLite for development and PostgreSQL for production.



Configure media handling for PDFs and static assets.



Test local deployment (Vite: npm run dev, Django server).



Set up production environment with PostgreSQL.

Deliverables:





Deployed MVP for Bomi Junior High.



Deployment guide for local and production environments.



Phase 6: Multi-Tenancy, Authentication, and PWA (Planned)

Objective: Expand the system to support multiple schools, secure authentication, and PWA functionality. Activities:





Core App:





Models: School (name, logo, theme_color, header, footer, password_hash), User (email, role, school, password_hash).



Features: Tenant isolation via foreign keys, JWT authentication, paginated API responses.



Middleware: tenant_middleware.py to filter queries by School.id.



APIs: /api/school/, /api/school/login/, /api/school/branding/.



School Config App:





Model: LevelConfig (school, level, rule_type, rule_config JSONField).



Rules: conditional (1x <69 & avg ≥70: Pass, 2x <69 & avg ≥70: Conditional, else Failed), no_conditional_one (1x <69 & avg ≥70: Pass, else Failed), no_conditional_two (2x <69 & avg ≥70: Pass, else Failed).



APIs: Paginated CRUD for level-specific rules (/api/school/config/).



Evaluation App:





Features: Process grades using LevelConfig rules, output statuses (Pass, Failed, Conditional).



APIs: /api/evaluation/process/, /api/evaluation/results/ (paginated).



Report Cards App:





Features: Generate branded PDF/Word reports using school_config rules and templates’ .docx files (report_card_compact, yearly_pass, yearly_failed, yearly_conditional).



APIs: /api/reports/generate/, /api/reports/list/ (paginated).



Templates App:





Model: Template (school, template_type, file).



Features: Store .docx files for report generation.



Automation App:





Model: TaskLog (school, task_type, status, result).



Features: Celery tasks for auto-promotions and reminders, paginated task logs.



Authentication:





Implement JWT with MFA and SSO.



Enhance refresh token handling.



PWA:





Add service workers for offline support and installable app icon.

Deliverables:





Multi-tenant system with core, school_config, evaluation, report_cards, templates, automation apps.



Secure authentication system.



PWA with offline capabilities.



Updated API documentation and test suites.



Phase 7: Attendance Tracking and Mobile/Desktop Apps (Planned)

Objective: Add attendance tracking and offline-capable mobile/desktop apps. Activities:





Attendance Tracking:





Models: Attendance (student, date, status, school).



APIs: CRUD endpoints for attendance records, integrated with core’s tenant isolation.



Frontend: Pages and components for attendance entry and reporting.



Mobile Apps:





Build React Native apps for iOS/Android with dashboard, grade entry, and attendance tracking.



Add push notifications for updates.



Desktop App:





Develop Electron-based app for full offline functionality.



Sync data with backend when online.

Deliverables:





Attendance tracking feature integrated into backend and frontend.



Mobile apps (iOS/Android) and desktop app.



Offline sync mechanism and documentation.

Timeline: 4 months.

Phase 8: AI-Assisted Feedback (Planned)

Objective: Integrate AI-driven insights for student progress. Activities:





Develop AI models to analyze grades and provide feedback (e.g., identify strengths, suggest improvement areas).



Integrate AI feedback into dashboard and report cards.



Create APIs for AI-driven insights (/api/feedback/).



Update frontend with AI feedback display components.

Deliverables:





AI feedback feature integrated into system.



Updated API documentation and test suites.



3. Current Progress





Pre-development stage; requirements and design derived from observed school needs and planned features.



MVP planned for Bomi Junior High with single-tenant functionality.



Future phases outlined for multi-tenancy, authentication, PWA, attendance tracking, mobile/desktop apps, and AI feedback.

4. Future Roadmap





Short-Term:





Complete MVP (Phases 1–5): Requirements, design, implementation, testing, and deployment for Bomi Junior High.



Medium-Term:





Implement multi-tenancy, authentication, and PWA (Phase 6).



Long-Term:





Add attendance tracking and mobile/desktop apps (Phase 7).



Integrate AI-assisted feedback (Phase 8).



Expand to additional schools with multi-tenant support and customized branding.

5. Team Roles and Responsibilities





Backend Developers: Build Django apps, implement APIs, and ensure tenant isolation (Phase 6).



Frontend Developers: Develop React components, hooks, and pages; build mobile/desktop apps (Phase 7).



DevOps: Configure deployment with PostgreSQL, Redis, and Celery; manage media storage.



Testers: Write test cases for backend, frontend, and integrations; validate tenant isolation and offline functionality.



Project Manager: Coordinate tasks, track progress, and gather feedback from schools.



UI/UX Designer: Design responsive, school-themed interfaces for web, mobile, and desktop.

6. Key Takeaways





Modularity: Django apps and React components ensure maintainability and scalability.



Type Safety: TypeScript and DRF serializers reduce errors.



User-Centric Design: Iterative feedback ensures usability for teachers and admins.



Scalability: Pagination and tenant isolation (Phase 6) support thousands of schools.



Automation: Celery tasks (Phase 6) reduce manual work.



Challenges: Plan for performance optimization, error handling, and template validation in later phases.

7. Conclusion

The Student Grading & Report Card System is poised to transform education management, starting with a robust MVP for Bomi Junior High. The SDLC outlines a clear path from pre-development to a scalable, multi-tenant platform with offline capabilities and AI-driven insights. With team collaboration, the system will deliver automated, branded, and accessible solutions for schools across West Africa. Currently i'm just refining the mvp inorder to start with the Multi-tenancy.  

i'm concluding the Admin Page to perform CRUD for subjects, periods, academicYear, and levels. So, we can enhance the UI/UX because i didn't paid much time to it. i was more of connecting the backend and frontend.

After going through it, i'll be awaiting to get feedback on what i should do next.