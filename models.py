from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Club(db.Model):
    __tablename__ = 'clubs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    logo_filename = db.Column(db.String(200), nullable=True)  # Changed from logo_url
    members_count = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    is_recruiting = db.Column(db.Boolean, default=False)
    application_link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New fields for gallery and why join section
    why_join_reasons = db.Column(db.Text, nullable=True)  # JSON string of reasons
    gallery_images = db.Column(db.Text, nullable=True)  # JSON string of image filenames
    
    members = db.relationship('ClubMember', backref='club', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Club {self.name}>'
    
    def to_dict(self):
        """Safe dictionary conversion with defaults"""
        return {
            'id': self.id,
            'name': self.name or 'Unnamed Club',
            'logo_filename': self.logo_filename or '',
            'members_count': self.members_count or 0,
            'description': self.description or 'No description available.',
            'is_recruiting': bool(self.is_recruiting),
            'application_link': self.application_link or '',
            'why_join_reasons': self.why_join_reasons or '[]',
            'gallery_images': self.gallery_images or '[]'
        }

class ClubMember(db.Model):
    __tablename__ = 'club_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClubMember {self.name} - {self.role}>'

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    organizer = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    size_class = db.Column(db.String(20), default='size-medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.title}>'
