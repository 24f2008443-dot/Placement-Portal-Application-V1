from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'company', 'student'
    active = db.Column(db.Boolean, default=True)
    blacklisted = db.Column(db.Boolean, default=False)

    def get_id(self):
        return str(self.id)

class CompanyProfile(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(240), nullable=False)
    hr_contact = db.Column(db.String(120))
    website = db.Column(db.String(240))
    approved = db.Column(db.Boolean, default=False)
    blacklisted = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='company_profile', uselist=False)

class Drive(db.Model):
    __tablename__ = 'drives'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    job_title = db.Column(db.String(240), nullable=False)
    job_description = db.Column(db.Text)
    eligibility = db.Column(db.String(240))
    salary = db.Column(db.String(100))
    location = db.Column(db.String(120))
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending / Approved / Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('CompanyProfile', backref='drives')

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    resume_filename = db.Column(db.String(240))
    college = db.Column(db.String(120))
    branch = db.Column(db.String(120))
    cgpa = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='student_profile', uselist=False)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('drives.id'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')  # Applied / Shortlisted / Selected / Rejected

    student = db.relationship('User', backref='applications')
    drive = db.relationship('Drive', backref='applications')

    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='_student_drive_uc'),)
