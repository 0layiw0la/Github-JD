from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Projects(db.Model):
    __tablename__ = 'projects'

    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False)
    projectname = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    bulletpoints = db.Column(db.Text, nullable=True)

    __table_args__ = (db.UniqueConstraint('username', 'projectname', name='uq_username_projectname'),)

    def __repr__(self):
        return f"{self.username}'s project {self.projectname}"


class User(db.Model):
    __tablename__ = 'users'

    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=True) 
    linkedin =    db.Column(db.Text, nullable=True) 
    github = db.Column(db.Text, nullable=True) 
    fullname = db.Column(db.Text, nullable=True)
    programming_languages = db.Column(db.Text, nullable=True)  # e.g., JSON string or comma-separated
    libraries = db.Column(db.Text, nullable=True)              # e.g., "pandas, NumPy"
    tools = db.Column(db.Text, nullable=True)                  # e.g., "VSCode, Git, Figma"
    school_name = db.Column(db.Text, nullable=True)
    course = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Text, nullable=True)               # e.g., "2021 - 2025"
    extracurriculars = db.Column(db.Text, nullable=True)       # store as JSON string
    

    def set_password(self, password):
        """Hashes the password before storing it"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the password"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"user {self.username} is here!"
