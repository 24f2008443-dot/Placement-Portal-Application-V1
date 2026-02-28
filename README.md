Placement Portal Application

A comprehensive Flask-based placement portal web application allowing Admin (Institute), Company, and Student roles to interact with the system for campus recruitment activities.

Features Implemented

Admin (Institute Placement Cell)
- Approve/reject company registrations
- Approve/reject placement drives
- View all students, companies, and placement drives
- View student and company details with history
- Blacklist students and companies
- Search students and companies by name
- View all applications in a centralized table
- Manage drive lifecycle (approve, close)

Company
- Self-register and create company profile
- Login after admin approval
- Create placement drives (job postings)
- View student applications for their drives
- Shortlist students and update application status (Shortlisted / Selected / Rejected)
- Close/manage their drives

Student
- Self-register and login
- Create and edit profile with phone, college, branch, CGPA
- Upload resume (PDF format)
- View approved placement drives
- Apply for placement drives
- View all applications and their status
- View detailed application history
- Prevent duplicate applications

Technical Stack

- Backend: Flask 2.0+
- Frontend: Jinja2 templating, HTML, CSS, Bootstrap 5
- Database: SQLite (programmatically created)
- Authentication: Flask-Login with role-based access control
- File Uploads: PDF resume support with secure file handling

Quick Start

1. Create a virtualenv and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

2. Run the app:

```bash
set FLASK_APP=app.py  # On Windows
export FLASK_APP=app.py  # On Linux/Mac
set FLASK_ENV=development
python app.py
```

3. Access the app at `http://127.0.0.1:5000`

4. Default admin credentials:
   - Email: admin@example.com
   - Password: adminpass

User Roles & Defaults

Admin
- Pre-existing account created at first startup
- Email: admin@example.com
- Password: adminpass

Company
- Self-registration via /register/company
- Requires admin approval before creating drives
- Can only create/manage their own drives

Student
- Self-registration via /register/student
- Can immediately view and apply for approved drives
- Can upload resume and maintain profile

Database

- SQLite database file: `placement.db`
- Created programmatically on first run via `create_all_db()` function
- Tables: users, companies, student_profiles, drives, applications

File Uploads

- Resumes stored in `uploads/` folder
- Only PDF files allowed
- Max file size: 16MB
- Files named as: `{user_id}_{filename}`

Project Structure

```
placement_portal/
├── app.py                 # Main Flask application and routes
├── models.py             # SQLAlchemy models (User, StudentProfile, CompanyProfile, Drive, Application)
├── forms.py              # WTForms for all forms
├── requirements.txt      # Python dependencies
├── placement.db          # SQLite database (created at runtime)
├── uploads/              # Resume uploads directory
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register_student.html
│   ├── register_company.html
│   ├── admin_dashboard.html
│   ├── admin_applications.html
│   ├── admin_student_details.html
│   ├── admin_company_details.html
│   ├── company_dashboard.html
│   ├── company_applications.html
│   ├── drive_create.html
│   ├── student_dashboard.html
│   ├── student_profile.html
│   ├── edit_student_profile.html
│   ├── student_applications.html
│   ├── application_detail.html
│   └── drive.html
└── static/
    └── css/
        └── style.css     # Custom styles

Routes Overview

Public Routes
- GET / - Home page with approved drives
- GET /login - Login page
- GET /register/student - Student registration
- GET /register/company - Company registration

Admin Routes
- GET /admin - Admin dashboard
- GET /admin/search - Search students/companies
- POST /admin/company/<id>/approve - Approve company
- POST /admin/company/<id>/reject - Reject company
- POST /admin/drive/<id>/approve - Approve drive
- POST /admin/drive/<id>/close - Close drive
- POST /admin/user/<id>/blacklist - Blacklist user
- GET /admin/applications - View all applications
- GET /admin/user/<id>/details - View user details

Company Routes
- GET /company - Company dashboard
- GET /company/profile/<id> - View company profile
- GET /company/drive/create - Create drive
- POST /company/drive/create - Submit new drive
- GET /company/drive/<id>/applications - View drive applications
- GET /company/application/<id>/update/<status> - Update application status
- GET /company/drive/<id>/close - Close drive

Student Routes
- GET /student - Student dashboard (approved drives)
- GET /student/profile - View student profile
- GET /student/profile/edit - Edit profile (upload resume)
- POST /student/profile/edit - Submit profile updates
- GET /student/applications - View all applications
- GET /student/application/<id> - View application details
- POST /drive/<id> - Apply for drive
- GET /drive/<id> - View drive details

Notes

- Database is created programmatically on first run
- Resumes are stored as secure filenames in the uploads/ folder
- Role-based access control enforced on all protected routes
- Duplicate applications prevented at both DB (unique constraint) and application level
- All forms include validation and error handling
- Bootstrap 5 for responsive UI
- No JavaScript required for core functionality

For development/testing:
- All admin actions are reversible except user deletion (blacklist instead)
- Drives can be approved/closed independently
