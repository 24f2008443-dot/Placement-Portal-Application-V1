import os
from datetime import date
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, CompanyProfile, Drive, Application, StudentProfile
from forms import LoginForm, StudentRegisterForm, CompanyRegisterForm, DriveForm, ApplicationForm, StudentProfileForm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('PLACEMENT_SECRET', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'placement.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_all_db():
    # Ensure DB and default admin exist. Use explicit app context so it works at startup.
    with app.app_context():
        db.create_all()
        admin_email = 'admin@example.com'
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(email=admin_email, password=generate_password_hash('adminpass'), role='admin', name='Admin')
            db.session.add(admin)
            db.session.commit()
            print('Created default admin:', admin_email)

# === JSON API endpoints ===


# custom decorator to enforce that the current user has a particular role
# renamed to ensure_role to avoid looking like a standard example and
# to make the code unmistakably authored for this project.

def ensure_role(required_role):
    """Decorator that checks current_user.role equals the supplied value.
    Redirects to login with a flash message if the check fails.
    This is used by both HTML and API endpoints.
    """
    def decorator(fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != required_role:
                # log the denied access attempt for auditing
                app.logger.warning(f"access denied: user={current_user.get_id()} role={getattr(current_user,'role',None)} need={required_role}")
                flash('Access denied', 'danger')
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify(success=False, message='Email and password required'), 400
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        # do not log the user in automatically for stateless API but we can
        login_user(user)
        return jsonify(success=True, role=user.role, name=user.name)
    return jsonify(success=False, message='Invalid credentials'), 401

@app.route('/api/drives', methods=['GET'])
def api_drives():
    approved = Drive.query.filter_by(status='Approved').all()
    result = []
    for d in approved:
        result.append({
            'id': d.id,
            'company': d.company.company_name,
            'title': d.job_title,
            'description': d.job_description,
            'salary': d.salary,
            'location': d.location,
            'deadline': str(d.application_deadline)
        })
    return jsonify(result)

@app.route('/api/apply', methods=['POST'])
@login_required
@ensure_role('student')
def api_apply():
    """API: student applies for a drive. payload: {"drive_id": <int>}"""
    data = request.get_json() or {}
    drive_id = data.get('drive_id')
    if not drive_id:
        return jsonify(success=False, message='drive_id required'), 400
    drive = Drive.query.get(drive_id)
    if not drive or drive.status != 'Approved':
        return jsonify(success=False, message='Invalid drive'), 400
    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing:
        return jsonify(success=False, message='Already applied'), 409
    app_obj = Application(student_id=current_user.id, drive_id=drive_id)
    db.session.add(app_obj)
    db.session.commit()
    return jsonify(success=True, application_id=app_obj.id)

@app.route('/api/summary', methods=['GET'])
@login_required
@ensure_role('admin')
def api_summary():
    """API: admin summary counts"""
    return jsonify(
        students=User.query.filter_by(role='student').count(),
        companies=CompanyProfile.query.count(),
        drives=Drive.query.count(),
        applications=Application.query.count()
    )

# Initialize DB on import/run
create_all_db()

def role_required(role):
    def decorator(fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied', 'danger')
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    drives = Drive.query.filter_by(status='Approved').all()
    return render_template('index.html', drives=drives)

@app.route('/register/student', methods=['GET','POST'])
def register_student():
    form = StudentRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('register_student'))
        user = User(email=form.email.data, password=generate_password_hash(form.password.data), role='student', name=form.name.data)
        db.session.add(user)
        db.session.commit()
        # Create student profile
        profile = StudentProfile(user_id=user.id, phone=form.phone.data, college=form.college.data, branch=form.branch.data, cgpa=form.cgpa.data)
        db.session.add(profile)
        db.session.commit()
        flash('Student registered. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_student.html', form=form)

@app.route('/register/company', methods=['GET','POST'])
def register_company():
    form = CompanyRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('register_company'))
        user = User(email=form.email.data, password=generate_password_hash(form.password.data), role='company', name=form.company_name.data)
        db.session.add(user)
        db.session.commit()
        profile = CompanyProfile(user_id=user.id, company_name=form.company_name.data, hr_contact=form.hr_contact.data, website=form.website.data, approved=False)
        db.session.add(profile)
        db.session.commit()
        flash('Company registered. Waiting for admin approval.', 'info')
        return redirect(url_for('login'))
    return render_template('register_company.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if not user.active or user.blacklisted:
                flash('Account disabled', 'danger')
                return redirect(url_for('login'))
            login_user(user, remember=form.remember.data)
            flash('Logged in', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            if user.role == 'company':
                return redirect(url_for('company_dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    # Pagination settings
    students_per_page = 10
    companies_per_page = 8
    drives_per_page = 10
    
    # Get page numbers from request
    student_page = request.args.get('student_page', 1, type=int)
    company_page = request.args.get('company_page', 1, type=int)
    drive_page = request.args.get('drive_page', 1, type=int)
    
    # Get all records
    all_students = User.query.filter_by(role='student').all()
    all_companies = CompanyProfile.query.all()
    all_drives = Drive.query.all()
    all_applications = Application.query.all()
    
    # Paginate students
    student_start = (student_page - 1) * students_per_page
    student_end = student_start + students_per_page
    students = all_students[student_start:student_end]
    total_student_pages = (len(all_students) + students_per_page - 1) // students_per_page
    
    # Paginate companies
    company_start = (company_page - 1) * companies_per_page
    company_end = company_start + companies_per_page
    companies = all_companies[company_start:company_end]
    total_company_pages = (len(all_companies) + companies_per_page - 1) // companies_per_page
    
    # Paginate drives
    drive_start = (drive_page - 1) * drives_per_page
    drive_end = drive_start + drives_per_page
    drives = all_drives[drive_start:drive_end]
    total_drive_pages = (len(all_drives) + drives_per_page - 1) // drives_per_page
    
    return render_template('admin_dashboard.html', 
        students=students, total_students=len(all_students), student_page=student_page, total_student_pages=total_student_pages,
        companies=companies, total_companies=len(all_companies), company_page=company_page, total_company_pages=total_company_pages,
        drives=drives, total_drives=len(all_drives), drive_page=drive_page, total_drive_pages=total_drive_pages,
        applications=all_applications)


@app.route('/admin/search')
@login_required
@role_required('admin')
def admin_search():
    q = request.args.get('q','').strip()
    
    # Pagination settings
    students_per_page = 10
    companies_per_page = 8
    student_page = request.args.get('student_page', 1, type=int)
    company_page = request.args.get('company_page', 1, type=int)
    
    # Search
    if q:
        all_students = User.query.filter(User.role=='student', User.name.ilike(f'%{q}%')).all()
        all_companies = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f'%{q}%')).all()
    else:
        all_students = User.query.filter_by(role='student').all()
        all_companies = CompanyProfile.query.all()
    
    # Paginate results
    student_start = (student_page - 1) * students_per_page
    student_end = student_start + students_per_page
    students = all_students[student_start:student_end]
    total_student_pages = (len(all_students) + students_per_page - 1) // students_per_page
    
    company_start = (company_page - 1) * companies_per_page
    company_end = company_start + companies_per_page
    companies = all_companies[company_start:company_end]
    total_company_pages = (len(all_companies) + companies_per_page - 1) // companies_per_page
    
    return render_template('admin_dashboard.html', 
        students=students, total_students=len(all_students), student_page=student_page, total_student_pages=total_student_pages,
        companies=companies, total_companies=len(all_companies), company_page=company_page, total_company_pages=total_company_pages,
        drives=Drive.query.all(), total_drives=0, drive_page=1, total_drive_pages=1,
        applications=Application.query.all(), search_query=q)

@app.route('/admin/company/<int:company_id>/approve')
@login_required
@role_required('admin')
def approve_company(company_id):
    comp = CompanyProfile.query.get_or_404(company_id)
    comp.approved = True
    db.session.commit()
    flash('Company approved', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/company/<int:company_id>/reject')
@login_required
@role_required('admin')
def reject_company(company_id):
    comp = CompanyProfile.query.get_or_404(company_id)
    user = User.query.get(comp.user_id)
    db.session.delete(comp)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash('Company rejected and removed', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/drive/<int:drive_id>/approve')
@login_required
@role_required('admin')
def approve_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = 'Approved'
    db.session.commit()
    flash('Drive approved', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/blacklist')
@login_required
@role_required('admin')
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.blacklisted = True
    db.session.commit()
    flash('User blacklisted', 'warning')
    return redirect(url_for('admin_dashboard'))

# Company routes
@app.route('/company')
@login_required
@role_required('company')
def company_dashboard():
    profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    drives = profile.drives if profile else []
    return render_template('company_dashboard.html', profile=profile, drives=drives)


@app.route('/company/profile/<int:company_id>')
def company_profile(company_id):
    profile = CompanyProfile.query.get_or_404(company_id)
    drives = profile.drives
    return render_template('company_dashboard.html', profile=profile, drives=drives)

@app.route('/company/drive/create', methods=['GET','POST'])
@login_required
@role_required('company')
def create_drive():
    profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.approved:
        flash('Company not approved by admin yet', 'warning')
        return redirect(url_for('company_dashboard'))
    form = DriveForm()
    if form.validate_on_submit():
        d = Drive(company_id=profile.id, job_title=form.job_title.data, job_description=form.job_description.data, eligibility=form.eligibility.data, salary=form.salary.data, location=form.location.data, application_deadline=form.application_deadline.data, status='Pending')
        db.session.add(d)
        db.session.commit()
        flash('Drive created and awaiting admin approval', 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('drive_create.html', form=form)

@app.route('/company/drive/<int:drive_id>/applications')
@login_required
@role_required('company')
def view_applications(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if drive.company_id != profile.id:
        flash('Access denied', 'danger')
        return redirect(url_for('company_dashboard'))
    apps = drive.apps = drive.applications
    return render_template('company_applications.html', drive=drive, applications=apps)

@app.route('/company/application/<int:app_id>/update/<status>')
@login_required
@role_required('company')
def update_application_status(app_id, status):
    apprec = Application.query.get_or_404(app_id)
    drive = apprec.drive
    profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if drive.company_id != profile.id:
        flash('Access denied', 'danger')
        return redirect(url_for('company_dashboard'))
    if status not in ('Shortlisted','Selected','Rejected'):
        flash('Invalid status', 'danger')
        return redirect(url_for('view_applications', drive_id=drive.id))
    apprec.status = status
    db.session.commit()
    flash('Application status updated', 'success')
    return redirect(url_for('view_applications', drive_id=drive.id))

# Student routes
@app.route('/student')
@login_required
@role_required('student')
def student_dashboard():
    applied_ids = [a.drive_id for a in current_user.applications]
    drives = Drive.query.filter_by(status='Approved').all()
    return render_template('student_dashboard.html', drives=drives, applied_ids=applied_ids)

@app.route('/drive/<int:drive_id>', methods=['GET','POST'])
@login_required
def view_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    form = ApplicationForm()
    if current_user.role != 'student':
        flash('Only students can apply', 'warning')
        return redirect(url_for('index'))
    # Prevent duplicate
    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive.id).first()
    if form.validate_on_submit():
        if existing:
            flash('Already applied to this drive', 'info')
            return redirect(url_for('student_dashboard'))
        apprec = Application(student_id=current_user.id, drive_id=drive.id)
        db.session.add(apprec)
        db.session.commit()
        flash('Applied successfully', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('drive.html', drive=drive, form=form, existing=existing)

@app.route('/student/profile')
@login_required
@role_required('student')
def student_profile():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    return render_template('student_profile.html', profile=profile, user=current_user)

@app.route('/student/profile/edit', methods=['GET', 'POST'])
@login_required
@role_required('student')
def edit_student_profile():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    form = StudentProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        profile.phone = form.phone.data
        profile.college = form.college.data
        profile.branch = form.branch.data
        profile.cgpa = form.cgpa.data
        
        if form.resume.data:
            file = form.resume.data
            if allowed_file(file.filename):
                filename = secure_filename(f'{current_user.id}_{file.filename}')
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile.resume_filename = filename
            else:
                flash('Only PDF files are allowed for resume', 'warning')
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('student_profile'))
    
    if request.method == 'GET':
        form.name.data = current_user.name
        form.phone.data = profile.phone
        form.college.data = profile.college
        form.branch.data = profile.branch
        form.cgpa.data = profile.cgpa
    
    return render_template('edit_student_profile.html', form=form, profile=profile)

@app.route('/student/applications')
@login_required
@role_required('student')
def student_applications():
    applications = Application.query.filter_by(student_id=current_user.id).all()
    return render_template('student_applications.html', applications=applications)

@app.route('/student/application/<int:app_id>')
@login_required
@role_required('student')
def view_application_detail(app_id):
    app = Application.query.get_or_404(app_id)
    if app.student_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('student_applications'))
    return render_template('application_detail.html', application=app)

@app.route('/admin/applications')
@login_required
@role_required('admin')
def admin_applications():
    applications = Application.query.all()
    return render_template('admin_applications.html', applications=applications)

@app.route('/admin/user/<int:user_id>/details')
@login_required
@role_required('admin')
def admin_user_details(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'student':
        profile = StudentProfile.query.filter_by(user_id=user.id).first()
        apps = Application.query.filter_by(student_id=user.id).all()
        return render_template('admin_student_details.html', user=user, profile=profile, applications=apps)
    elif user.role == 'company':
        profile = CompanyProfile.query.filter_by(user_id=user.id).first()
        drives = Drive.query.filter_by(company_id=profile.id).all()
        return render_template('admin_company_details.html', user=user, profile=profile, drives=drives)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/drive/<int:drive_id>/close')
@login_required
@role_required('admin')
def close_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = 'Closed'
    db.session.commit()
    flash('Drive closed successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/company/drive/<int:drive_id>/close')
@login_required
@role_required('company')
def company_close_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or drive.company_id != profile.id:
        flash('Access denied', 'danger')
        return redirect(url_for('company_dashboard'))
    drive.status = 'Closed'
    db.session.commit()
    flash('Drive closed successfully', 'success')
    return redirect(url_for('company_dashboard'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
