from app import app, db, Club, Event

def init_database():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Seed clubs if empty
        if Club.query.count() == 0:
            print("Seeding clubs data...")
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
        else:
            print(f"✓ Database already has {Club.query.count()} clubs")
        
        # Seed events if empty
        if Event.query.count() == 0:
            print("Seeding events data...")
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
                    'description': 'Test your coding skills in this intense 48-hour hackathon! Form teams, build innovative solutions, and compete for prizes worth ₹1 Lakh.',
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
                    'description': 'A comprehensive 3-day workshop series covering Machine Learning fundamentals, Deep Learning architectures, and practical AI applications.',
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
                    'description': 'Annual inter-college sports competition featuring cricket, football, basketball, badminton, and athletics.',
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
                    'description': 'Distinguished guest lecture by Dr. Sarah Johnson from MIT on Machine Learning Applications in Healthcare.',
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
                    'description': 'Capture the essence of campus life! Submit your best photographs in categories: Portrait, Landscape, Abstract, and Candid.',
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
                    'description': 'Grand celebration of achievements and talent! Features award ceremonies, cultural performances, and alumni meet.',
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
        else:
            print(f"✓ Database already has {Event.query.count()} events")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_database()
