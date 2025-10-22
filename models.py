# models.py
from app import db # Assuming 'db' is initialized in your main app file (like app.py)

class Club(db.Model):
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Club main info
    name = db.Column(db.String(100), unique=True, nullable=False)
    logo_url = db.Column(db.String(200), nullable=True)
    members_count = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    is_recruiting = db.Column(db.Boolean, default=False)
    application_link = db.Column(db.String(300), nullable=True) # Google Form link

    # Relation to club members
    members = db.relationship('ClubMember', backref='club', lazy='dynamic')
    
    def __repr__(self):
        return f'<Club {self.name}>'

class ClubMember(db.Model):
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False) # e.g., 'Club Head', 'Core Member', 'Team Member'
    
    # Foreign Key: links the member to a Club
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))

    def __repr__(self):
        return f'<ClubMember {self.name} - {self.role}>'

# models intentionally left minimal for Project_x