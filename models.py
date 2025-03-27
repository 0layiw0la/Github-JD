from app import db


class Projects(db.Model):
    __tablename__ = 'projects'

    pid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False)
    projectname = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    bulletpoints = db.Column(db.Text, nullable=True)

    __table_args__ = (db.UniqueConstraint('username', 'projectname', name='uq_username_projectname'),)

    def __repr__(self):
        return f"{self.username}'s project {self.projectname}"


class User(db.Model):
    __tablename__ = 'users'

    pid = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.Text, nullable=False,unique=True)
    password = db.Column(db.Text,nullable=False)

    def __repr__(self):
        return f"user {self.username} is here!"
    