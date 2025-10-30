from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort, jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from chatbot import ClubChatbot
import logging
import sys
import json

app = Flask(__name__)

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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

# Initialize chatbot with token from environment
chatbot = None

def init_chatbot():
    """Initialize chatbot with proper token"""
    global chatbot
    hf_token = os.environ.get('HUGGINGFACE_API_TOKEN')
    
    if not hf_token:
        logger.warning("⚠️ HUGGINGFACE_API_TOKEN not found in environment variables!")
        logger.warning("Please add it to your Render environment variables")
    else:
        logger.info("✓ Hugging Face token found")
    
    try:
        chatbot = ClubChatbot(hf_token=hf_token)
        logger.info("✓ Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"✗ Error initializing chatbot: {str(e)}")
        chatbot = None

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
    
    def to_dict(self):
        """Safe dictionary conversion with defaults"""
        return {
            'id': self.id,
            'name': self.name or 'Unnamed Club',
            'logo_url': self.logo_url or '',
            'members_count': self.members_count or 0,
            'description': self.description or 'No description available.',
            'is_recruiting': bool(self.is_recruiting),
            'application_link': self.application_link or ''
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

# Manager credentials
MANAGER_CREDENTIALS = {
    'username': os.environ.get('MANAGER_USERNAME', 'admin'),
    'password': os.environ.get('MANAGER_PASSWORD', 'adminpass')
}

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 Error: {error}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {error}")
    db.session.rollback()
    return render_template('500.html'), 500

# ==================== HELPER FUNCTIONS ====================

def get_available_images():
    """Scan templates/images directory for available images"""
    images_path = os.path.join(app.root_path, 'templates', 'images')
    
    # Create directory if it doesn't exist
    if not os.path.exists(images_path):
        try:
            os.makedirs(images_path)
            logger.info(f"Created images directory at {images_path}")
        except Exception as e:
            logger.error(f"Error creating images directory: {str(e)}")
            return []
    
    # Get all image files
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    images = []
    
    try:
        for filename in os.listdir(images_path):
            if any(filename.lower().endswith(ext) for ext in valid_extensions):
                images.append(filename)
    except Exception as e:
        logger.error(f"Error scanning images directory: {str(e)}")
    
    return sorted(images)

# Custom Jinja filter to parse JSON
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

# ==================== INITIALIZATION ====================

def init_db():
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
            
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
                logger.info(f"Seeded {len(clubs_data)} clubs")
            
            # Seed events if empty
            if Event.query.count() == 0:
                events_data = [
                    {
                        'title': 'Tech Symposium 2025',
                        'description': 'Join us for our annual Tech Symposium featuring keynote speakers from leading tech companies, panel discussions on emerging technologies, and networking opportunities with industry professionals.',
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
                        'description': 'Experience the vibrant diversity of our campus at the Annual Cultural Fest!',
                        'category': 'Cultural',
                        'date': 'November 5, 2025',
                        'time': '3:00 PM - 10:00 PM',
                        'location': 'Open Grounds',
                        'organizer': 'Cultural Club',
                        'image_url': '/static/images/club.jpg',
                        'size_class': 'size-medium'
                    }
                ]
                
                for event_data in events_data:
                    event = Event(**event_data)
                    db.session.add(event)
                
                db.session.commit()
                logger.info(f"Seeded {len(events_data)} events")
            
            logger.info("Database initialization complete!")
            
            # Initialize chatbot after database is ready
            init_chatbot()
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}", exc_info=True)
            raise

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
    try:
        events_list = Event.query.order_by(Event.created_at.desc()).all()
        logger.info(f"Fetched {len(events_list)} events")
        return render_template('events.html', events=events_list)
    except Exception as e:
        logger.error(f"Error in events route: {str(e)}", exc_info=True)
        flash('Error loading events', 'error')
        return render_template('events.html', events=[])

@app.route('/clubs')
def clubs():
    try:
        clubs_list = Club.query.all()
        logger.info(f"Fetched {len(clubs_list)} clubs")
        return render_template('clubs.html', clubs=clubs_list)
    except Exception as e:
        logger.error(f"Error in clubs route: {str(e)}", exc_info=True)
        flash('Error loading clubs', 'error')
        return render_template('clubs.html', clubs=[])

@app.route('/club/<int:club_id>')
def club_detail(club_id):
    try:
        logger.info(f"Attempting to fetch club with ID: {club_id}")
        
        # Fetch club
        club = Club.query.get(club_id)
        
        if not club:
            logger.warning(f"Club with ID {club_id} not found")
            flash(f'Club not found', 'error')
            return redirect(url_for('clubs'))
        
        logger.info(f"Successfully fetched club: {club.name}")
        logger.debug(f"Club data: {club.to_dict()}")
        
        # Ensure all fields have safe values
        if not club.name:
            club.name = f"Club {club_id}"
        if club.description is None:
            club.description = "No description available."
        if club.members_count is None:
            club.members_count = 0
        if club.is_recruiting is None:
            club.is_recruiting = False
            
        return render_template('club_detail.html', club=club)
        
    except Exception as e:
        logger.error(f"Error in club_detail for ID {club_id}: {str(e)}", exc_info=True)
        flash('Error loading club details', 'error')
        return redirect(url_for('clubs'))

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
    try:
        clubs_list = Club.query.all()
        events_list = Event.query.order_by(Event.created_at.desc()).all()
        total_clubs = len(clubs_list)
        total_members = sum(club.members_count or 0 for club in clubs_list)
        total_events = len(events_list)
        
        return render_template('manager_dashboard.html', 
                             clubs=clubs_list,
                             events=events_list,
                             total_clubs=total_clubs, 
                             total_members=total_members,
                             total_events=total_events)
    except Exception as e:
        logger.error(f"Error in manager_dashboard: {str(e)}", exc_info=True)
        flash('Error loading dashboard', 'error')
        return render_template('manager_dashboard.html', 
                             clubs=[], events=[], 
                             total_clubs=0, total_members=0, total_events=0)

# ==================== CLUB MANAGEMENT ====================

@app.route('/manager/club/<int:club_id>/edit', methods=['GET', 'POST'])
@manager_required
def manager_edit_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    if request.method == 'POST':
        try:
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
        except Exception as e:
            logger.error(f"Error updating club: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('Error updating club', 'error')
    
    available_images = get_available_images()
    return render_template('club_edit.html', club=club, available_images=available_images)

@app.route('/manager/club/new', methods=['GET', 'POST'])
@manager_required
def manager_new_club():
    if request.method == 'POST':
        try:
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
        except Exception as e:
            logger.error(f"Error creating club: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('Error creating club', 'error')
    
    available_images = get_available_images()
    return render_template('club_edit.html', club=None, available_images=available_images)

@app.route('/manager/club/<int:club_id>/delete', methods=['POST'])
@manager_required
def manager_delete_club(club_id):
    try:
        club = Club.query.get_or_404(club_id)
        db.session.delete(club)
        db.session.commit()
        flash('Club deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting club: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('Error deleting club', 'error')
    
    return redirect(url_for('manager_dashboard'))

# ==================== CLUB MEMBER MANAGEMENT ====================

@app.route('/manager/club/<int:club_id>/members', methods=['GET'])
@manager_required
def manager_club_members(club_id):
    try:
        club = Club.query.get_or_404(club_id)
        members = ClubMember.query.filter_by(club_id=club_id).order_by(ClubMember.joined_at.desc()).all()
        return render_template('club_members.html', club=club, members=members)
    except Exception as e:
        logger.error(f"Error loading club members: {str(e)}", exc_info=True)
        flash('Error loading club members', 'error')
        return redirect(url_for('manager_dashboard'))

@app.route('/manager/club/<int:club_id>/members/add', methods=['POST'])
@manager_required
def manager_add_member(club_id):
    try:
        club = Club.query.get_or_404(club_id)
        
        new_member = ClubMember(
            name=request.form.get('name', '').strip(),
            role=request.form.get('role', '').strip(),
            club_id=club_id
        )
        
        if not new_member.name or not new_member.role:
            flash('Name and role are required', 'error')
            return redirect(url_for('manager_club_members', club_id=club_id))
        
        db.session.add(new_member)
        db.session.commit()
        flash(f'{new_member.name} added successfully!', 'success')
    except Exception as e:
        logger.error(f"Error adding club member: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('Error adding member', 'error')
    
    return redirect(url_for('manager_club_members', club_id=club_id))

@app.route('/manager/club/<int:club_id>/members/<int:member_id>/edit', methods=['POST'])
@manager_required
def manager_edit_member(club_id, member_id):
    try:
        member = ClubMember.query.get_or_404(member_id)
        
        if member.club_id != club_id:
            flash('Member does not belong to this club', 'error')
            return redirect(url_for('manager_dashboard'))
        
        member.name = request.form.get('name', member.name).strip()
        member.role = request.form.get('role', member.role).strip()
        
        db.session.commit()
        flash(f'{member.name} updated successfully!', 'success')
    except Exception as e:
        logger.error(f"Error updating club member: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('Error updating member', 'error')
    
    return redirect(url_for('manager_club_members', club_id=club_id))

@app.route('/manager/club/<int:club_id>/members/<int:member_id>/delete', methods=['POST'])
@manager_required
def manager_delete_member(club_id, member_id):
    try:
        member = ClubMember.query.get_or_404(member_id)
        
        if member.club_id != club_id:
            flash('Member does not belong to this club', 'error')
            return redirect(url_for('manager_dashboard'))
        
        member_name = member.name
        db.session.delete(member)
        db.session.commit()
        flash(f'{member_name} removed successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting club member: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('Error removing member', 'error')
    
    return redirect(url_for('manager_club_members', club_id=club_id))

# ==================== EVENT MANAGEMENT ====================

@app.route('/manager/event/<int:event_id>/edit', methods=['GET', 'POST'])
@manager_required
def manager_edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        try:
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
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('Error updating event', 'error')
    
    return render_template('event_edit.html', event=event)

@app.route('/manager/event/new', methods=['GET', 'POST'])
@manager_required
def manager_new_event():
    if request.method == 'POST':
        try:
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
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('Error creating event', 'error')
    
    return render_template('event_edit.html', event=None)

@app.route('/manager/event/<int:event_id>/delete', methods=['POST'])
@manager_required
def manager_delete_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('Error deleting event', 'error')
    
    return redirect(url_for('manager_dashboard'))

# ==================== CHATBOT ROUTES ====================

@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """Handle chatbot messages"""
    try:
        # Check if chatbot is initialized
        if not chatbot:
            logger.error("Chatbot not initialized")
            return jsonify({
                'error': 'Chatbot service unavailable',
                'response': "I'm currently unavailable. Please check that the Hugging Face API token is configured. 🔧"
            }), 500
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        logger.info(f"Received chatbot message: {user_message[:50]}...")
        
        # Generate response with database context
        with app.app_context():
            response = chatbot.generate_response(user_message, db)
            context = chatbot.get_database_context(db)
            suggestions = chatbot.get_quick_suggestions(context)
        
        logger.info("Generated chatbot response successfully")
        
        return jsonify({
            'response': response,
            'suggestions': suggestions,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to generate response',
            'response': "I'm having trouble right now. Please try again! 🔄"
        }), 500

@app.route('/api/chatbot/clear', methods=['POST'])
def chatbot_clear():
    """Clear chatbot conversation history"""
    try:
        if chatbot:
            chatbot.clear_history()
            return jsonify({'message': 'Conversation cleared'}), 200
        else:
            return jsonify({'error': 'Chatbot not initialized'}), 500
    except Exception as e:
        logger.error(f"Error clearing chat: {str(e)}")
        return jsonify({'error': 'Failed to clear conversation'}), 500

@app.route('/api/chatbot/suggestions', methods=['GET'])
def chatbot_suggestions():
    """Get quick reply suggestions"""
    try:
        if not chatbot:
            return jsonify({'suggestions': []}), 200
            
        with app.app_context():
            context = chatbot.get_database_context(db)
            suggestions = chatbot.get_quick_suggestions(context)
        return jsonify({'suggestions': suggestions}), 200
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        return jsonify({'error': 'Failed to get suggestions'}), 500

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        chatbot_status = 'initialized' if chatbot else 'not initialized'
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'chatbot': chatbot_status
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# ==================== IMAGE SERVING ROUTE ====================

@app.route('/templates/images/<path:filename>')
def serve_template_image(filename):
    """Serve images from templates/images directory"""
    images_path = os.path.join(app.root_path, 'templates', 'images')
    try:
        return send_from_directory(images_path, filename)
    except FileNotFoundError:
        logger.error(f"Image not found: {filename}")
        abort(404)

# ==================== RUN ====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
