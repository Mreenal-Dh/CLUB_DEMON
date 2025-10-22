from app import app, db, Club

def init_database():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Check if clubs already exist
        if Club.query.count() == 0:
            print("Seeding initial data...")
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
                },
                {
                    'name': 'Cultural Club',
                    'description': 'Celebrating diversity through arts and culture.',
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
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_database()