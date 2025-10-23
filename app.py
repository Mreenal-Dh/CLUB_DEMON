from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clubs.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database
db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

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
    
    members = db.relationship('ClubMember', backref='club', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Club {self.name}>'

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
    category = db.Column(db.String(50), nullable=False)  # Technical, Cultural, Sports, etc.
    date = db.Column(db.String(50), nullable=False)  # e.g., "October 25, 2025"
    time = db.Column(db.String(50), nullable=False)  # e.g., "9:00 AM - 5:00 PM"
    location = db.Column(db.String(200), nullable=False)
    organizer = db.Column(db.String(100), nullable=False)  # Club name
    image_url = db.Column(db.String(200), nullable=True)
    size_class = db.Column(db.String(20), default='size-medium')  # size-small, size-medium, size-large, size-wide, size-tall
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.title}>'

# Manager credentials
MANAGER_CREDENTIALS = {
    'username': os.environ.get('MANAGER_USERNAME', 'admin'),
    'password': os.environ.get('MANAGER_PASSWORD', 'adminpass')
}

# ==================== INITIALIZATION ====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Seed clubs if empty
        if Club.query.count() == 0:
            clubs_data = [
                {
                    'name': 'Astro Club',
                    'description': 'Exploring the cosmos and celestial wonders through stargazing sessions, astrophotography workshops, and discussions on space exploration.',
                    'members_count': 45,
                    'is_recruiting': True,
                    'application_link': ''
                },
                {
                    'name': 'Code Warriors',
                    'description': 'Programming competitions, hackathons, and software development projects. Join us to enhance your coding skills and build amazing applications.',
                    'members_count': 78,
                    'is_recruiting': False,
                    'application_link': ''
                },
                {
                    'name': 'Cultural Club',
                    'description': 'Celebrating diversity through arts, music, dance, and cultural events. Experience the vibrant traditions from around the world.',
                    'members_count': 92,
                    'is_recruiting': True,
                    'application_link': 'https://forms.gle/example'
                }
            ]
            
            for club_data in clubs_data:
                club = Club(**club_data)
                db.session.add(club)
            
            db.session.commit()
            print(f"✓ Seeded {len(clubs_data)} clubs")
        
        # Seed events if empty
        if Event.query.count() == 0:
            events_data = [
                {
                    'title': 'Tech Symposium 2025',
                    'description': 'Join us for our annual Tech Symposium featuring keynote speakers from leading tech companies, panel discussions on emerging technologies, and networking opportunities with industry professionals. This full-day event covers AI, Web3, Cloud Computing, and more.',
                    'category': 'Technical',
                    'date': 'October 25, 2025',
                    'time': '9:00 AM - 5:00 PM',
                    'location': 'Main Auditorium',
                    'organizer': 'Code Warriors',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-large'
                },
                {
                    'title': 'Cultural Fest',
                    'description': 'Experience the vibrant diversity of our campus at the Annual Cultural Fest! Enjoy music performances, dance competitions, drama presentations, and art exhibitions. Food stalls featuring cuisines from around the world will be available.',
                    'category': 'Cultural',
                    'date': 'November 5, 2025',
                    'time': '3:00 PM - 10:00 PM',
                    'location': 'Open Grounds',
                    'organizer': 'Cultural Club',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-medium'
                },
                {
                    'title': 'Hackathon 48hrs',
                    'description': 'Test your coding skills in this intense 48-hour hackathon! Form teams, build innovative solutions, and compete for prizes worth ₹1 Lakh. Mentorship from industry experts, free meals, and swag included.',
                    'category': 'Competition',
                    'date': 'November 12-14, 2025',
                    'time': '48 Hours Non-Stop',
                    'location': 'Computer Labs',
                    'organizer': 'Code Warriors',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-small'
                },
                {
                    'title': 'AI Workshop Series',
                    'description': 'A comprehensive 3-day workshop series covering Machine Learning fundamentals, Deep Learning architectures, and practical AI applications. Hands-on sessions with real datasets.',
                    'category': 'Workshop',
                    'date': 'November 18-20, 2025',
                    'time': '2:00 PM - 5:00 PM',
                    'location': 'Lab 301',
                    'organizer': 'Code Warriors',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-wide'
                },
                {
                    'title': 'Sports Meet 2025',
                    'description': 'Annual inter-college sports competition featuring cricket, football, basketball, badminton, and athletics. Represent your department and compete for the championship trophy.',
                    'category': 'Sports',
                    'date': 'December 2-4, 2025',
                    'time': '8:00 AM - 6:00 PM',
                    'location': 'Sports Complex',
                    'organizer': 'Sports Committee',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-medium'
                },
                {
                    'title': 'Guest Lecture: ML in Healthcare',
                    'description': 'Distinguished guest lecture by Dr. Sarah Johnson from MIT on Machine Learning Applications in Healthcare. Learn about cutting-edge research in medical diagnosis and personalized medicine.',
                    'category': 'Seminar',
                    'date': 'December 10, 2025',
                    'time': '4:00 PM - 6:00 PM',
                    'location': 'Seminar Hall',
                    'organizer': 'Astro Club',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-tall'
                },
                {
                    'title': 'Photography Contest',
                    'description': 'Capture the essence of campus life! Submit your best photographs in categories: Portrait, Landscape, Abstract, and Candid. Winners get cash prizes and featured exhibition.',
                    'category': 'Competition',
                    'date': 'December 15, 2025',
                    'time': 'Submission Deadline',
                    'location': 'Online Submission',
                    'organizer': 'Photography Club',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-small'
                },
                {
                    'title': 'Annual Day Celebration',
                    'description': 'Grand celebration of achievements and talent! Features award ceremonies, cultural performances, alumni meet, and entertainment show. Chief Guest: Renowned entrepreneur Mr. Raj Malhotra.',
                    'category': 'Cultural',
                    'date': 'January 8, 2026',
                    'time': '6:00 PM - 10:00 PM',
                    'location': 'Main Auditorium',
                    'organizer': 'Student Council',
                    'image_url': '/static/images/club.jpg',
                    'size_class': 'size-large'
                }
            ]
            
            for event_data in events_data:
                event = Event(**event_data)
                db.session.add(event)
            
            db.session.commit()
            print(f"✓ Seeded {len(events_data)} events")
        
        print("Database initialization complete!")

# ==================== PUBLIC ROUTES ====================

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
    events_list = Event.query.order_by(Event.created_at.desc()).all()
    return render_template('events.html', events=events_list)

@app.route('/clubs')
def clubs():
    clubs_list = Club.query.all()
    return render_template('clubs.html', clubs=clubs_list)

@app.route('/club/<int:club_id>')
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template('club_detail.html', club=club)

# ==================== MANAGER AUTHENTICATION ====================

def manager_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('manager_logged_in'):
            flash('Please login as manager to access this page', 'error')
            return redirect(url_for('index'))
        return fn(*args, **kwargs)
    return wrapper

@app.route('/manager/login')
def manager_login():
    return redirect(url_for('index'))

@app.route('/manager/logout')
def manager_logout():
    session.pop('manager_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

# ==================== MANAGER DASHBOARD ====================

@app.route('/manager/dashboard')
@manager_required
def manager_dashboard():
    clubs_list = Club.query.all()
    events_list = Event.query.order_by(Event.created_at.desc()).all()
    total_clubs = len(clubs_list)
    total_members = sum(club.members_count for club in clubs_list)
    total_events = len(events_list)
    
    return render_template('manager_dashboard.html', 
                         clubs=clubs_list,
                         events=events_list,
                         total_clubs=total_clubs, 
                         total_members=total_members,
                         total_events=total_events)

# ==================== CLUB MANAGEMENT ====================

@app.route('/manager/club/<int:club_id>/edit', methods=['GET', 'POST'])
@manager_required
def manager_edit_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    if request.method == 'POST':
        club.name = request.form.get('name', club.name)
        club.description = request.form.get('description', club.description)
        club.logo_url = request.form.get('logo_url', club.logo_url)
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
            logo_url=request.form.get('logo_url', ''),
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

# ==================== EVENT MANAGEMENT ====================

@app.route('/manager/event/<int:event_id>/edit', methods=['GET', 'POST'])
@manager_required
def manager_edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        event.title = request.form.get('title', event.title)
        event.description = request.form.get('description', event.description)
        event.category = request.form.get('category', event.category)
        event.date = request.form.get('date', event.date)
        event.time = request.form.get('time', event.time)
        event.location = request.form.get('location', event.location)
        event.organizer = request.form.get('organizer', event.organizer)
        event.image_url = request.form.get('image_url', event.image_url)
        event.size_class = request.form.get('size_class', event.size_class)
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('manager_dashboard'))
    
    return render_template('event_edit.html', event=event)

@app.route('/manager/event/new', methods=['GET', 'POST'])
@manager_required
def manager_new_event():
    if request.method == 'POST':
        new_event = Event(
            title=request.form.get('title', 'New Event'),
            description=request.form.get('description', ''),
            category=request.form.get('category', 'General'),
            date=request.form.get('date', ''),
            time=request.form.get('time', ''),
            location=request.form.get('location', ''),
            organizer=request.form.get('organizer', ''),
            image_url=request.form.get('image_url', '/static/images/club.jpg'),
            size_class=request.form.get('size_class', 'size-medium')
        )
        
        db.session.add(new_event)
        db.session.commit()
        flash('New event created successfully!', 'success')
        return redirect(url_for('manager_dashboard'))
    
    return render_template('event_edit.html', event=None)

@app.route('/manager/event/<int:event_id>/delete', methods=['POST'])
@manager_required
def manager_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('manager_dashboard'))

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500

# ==================== RUN ====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
