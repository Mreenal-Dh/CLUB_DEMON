from flask import Flask, render_template, request, redirect, url_for, session, flash
import itertools
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render uses postgresql:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clubs.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database
db = SQLAlchemy(app)

# Database Models
class Club(db.Model):
    __tablename__ = 'clubs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    logo_url = db.Column(db.String(200), nullable=True)
    members_count = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    is_recruiting = db.Column(db.Boolean, default=False)
    application_link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    members = db.relationship('ClubMember', backref='club', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Club {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo_url': self.logo_url,
            'members_count': self.members_count,
            'description': self.description,
            'is_recruiting': self.is_recruiting,
            'application_link': self.application_link
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

# Manager credentials (in production, use environment variables)
MANAGER_CREDENTIALS = {
    'username': os.environ.get('MANAGER_USERNAME', 'admin'),
    'password': os.environ.get('MANAGER_PASSWORD', 'adminpass')
}

# Initialize database and seed data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if clubs already exist
        if Club.query.count() == 0:
            # Seed initial data
            clubs_data = [
                {
                    'name': 'Astro Club',
                    'description': 'Exploring the cosmos and celestial wonders.',
                    'members_count': 45,
                    'is_recruiting': True,
                    'application_link': ''
                },
                {
                    'name': 'Code Warriors',
                    'description': 'Programming competitions and software development.',
                    'members_count': 78,
                    'is_recruiting': False,
                    'application_link': ''
                }
            ]
            
            for club_data in clubs_data:
                club = Club(**club_data)
                db.session.add(club)
            
            db.session.commit()
            print("Database initialized with seed data!")

# --- Public routes (catalogue) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        role = request.form.get('role', 'student')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if role == 'student':
            if username and password:
                session['student_logged_in'] = True
                session['student_username'] = username
                return redirect(url_for('home'))
            else:
                return render_template('index.html', message='Enter username and password to continue.')
        else:
            if username == MANAGER_CREDENTIALS['username'] and password == MANAGER_CREDENTIALS['password']:
                session['manager_logged_in'] = True
                return redirect(url_for('manager_dashboard'))
            return render_template('index.html', message='Invalid manager credentials.')

    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/clubs')
def clubs():
    clubs_list = Club.query.all()
    return render_template('clubs.html', clubs=clubs_list)

@app.route('/club/<int:club_id>')
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template('club_detail.html', club=club)

# --- Manager routes ---
def manager_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('manager_logged_in'):
            return redirect(url_for('index'))
        return fn(*args, **kwargs)
    return wrapper

@app.route('/manager/login', methods=['GET', 'POST'])
def manager_login():
    return redirect(url_for('index'))

@app.route('/manager/logout')
def manager_logout():
    session.pop('manager_logged_in', None)
    return redirect(url_for('home'))

@app.route('/manager/dashboard')
@manager_required
def manager_dashboard():
    clubs_list = Club.query.all()
    total_clubs = len(clubs_list)
    total_members = sum(club.members_count for club in clubs_list)
    return render_template('manager_dashboard.html', 
                         clubs=clubs_list, 
                         total_clubs=total_clubs, 
                         total_members=total_members)

@app.route('/manager/club/<int:club_id>/edit', methods=['GET', 'POST'])
@manager_required
def manager_edit_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    if request.method == 'POST':
        club.name = request.form.get('name', club.name)
        club.description = request.form.get('description', club.description)
        try:
            club.members_count = int(request.form.get('members_count', club.members_count))
        except ValueError:
            pass
        club.is_recruiting = bool(request.form.get('is_recruiting'))
        club.application_link = request.form.get('application_link', '')
        
        db.session.commit()
        flash('Club updated successfully!', 'success')
        return redirect(url_for('manager_dashboard'))
    
    return render_template('club_edit.html', club=club)

@app.route('/manager/club/new', methods=['GET', 'POST'])
@manager_required
def manager_new_club():
    if request.method == 'POST':
        new_club = Club(
            name=request.form.get('name', 'New Club'),
            description=request.form.get('description', ''),
            members_count=int(request.form.get('members_count', 0) or 0),
            is_recruiting=bool(request.form.get('is_recruiting')),
            application_link=request.form.get('application_link', '')
        )
        
        db.session.add(new_club)
        db.session.commit()
        flash('New club created successfully!', 'success')
        return redirect(url_for('manager_dashboard'))
    
    return render_template('club_edit.html', club=None)

@app.route('/manager/club/<int:club_id>/delete', methods=['POST'])
@manager_required
def manager_delete_club(club_id):
    club = Club.query.get_or_404(club_id)
    db.session.delete(club)
    db.session.commit()
    flash('Club deleted successfully!', 'success')
    return redirect(url_for('manager_dashboard'))

# Health check endpoint for Render
@app.route('/health')
def health():
    return {'status': 'healthy', 'database': 'connected' if db.engine else 'disconnected'}, 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)