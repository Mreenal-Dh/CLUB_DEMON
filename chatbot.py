import os
import json
from datetime import datetime
from huggingface_hub import InferenceClient

class ClubChatbot:
    """AI Chatbot for club and event information using Hugging Face"""
    
    def __init__(self, hf_token=None):
        """Initialize the chatbot with Hugging Face API"""
        self.hf_token = hf_token or os.environ.get('HUGGINGFACE_API_TOKEN')
        
        # Initialize Hugging Face Inference Client
        # Using Mistral-7B-Instruct for good performance on free tier
        self.client = InferenceClient(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            token=self.hf_token
        )
        
        self.conversation_history = []
        self.max_history = 5  # Keep last 5 exchanges
    
    def get_database_context(self, db):
        """Extract relevant information from database"""
        from app import Club, Event
        
        context = {
            'clubs': [],
            'events': [],
            'stats': {}
        }
        
        try:
            # Get all clubs
            clubs = Club.query.all()
            for club in clubs:
                context['clubs'].append({
                    'name': club.name,
                    'description': club.description,
                    'members_count': club.members_count,
                    'is_recruiting': club.is_recruiting,
                    'application_link': club.application_link
                })
            
            # Get all events
            events = Event.query.all()
            for event in events:
                context['events'].append({
                    'title': event.title,
                    'description': event.description,
                    'category': event.category,
                    'date': event.date,
                    'time': event.time,
                    'location': event.location,
                    'organizer': event.organizer
                })
            
            # Calculate stats
            context['stats'] = {
                'total_clubs': len(clubs),
                'total_members': sum(club.members_count or 0 for club in clubs),
                'total_events': len(events),
                'recruiting_clubs': len([c for c in clubs if c.is_recruiting])
            }
            
        except Exception as e:
            print(f"Error fetching database context: {e}")
        
        return context
    
    def build_system_prompt(self, context):
        """Build system prompt with database information"""
        clubs_info = "\n".join([
            f"- {club['name']}: {club['description']} "
            f"({'Recruiting' if club['is_recruiting'] else 'Not recruiting'}, "
            f"{club['members_count']} members)"
            for club in context['clubs']
        ])
        
        events_info = "\n".join([
            f"- {event['title']} ({event['category']}): {event['description']} "
            f"on {event['date']} at {event['time']} in {event['location']}, "
            f"organized by {event['organizer']}"
            for event in context['events'][:10]  # Limit to avoid token overflow
        ])
        
        system_prompt = f"""You are a helpful assistant for IIIT Naya Raipur's Student Club Portal. 
You help students find information about clubs, events, and campus activities.

CURRENT CAMPUS INFORMATION:

CLUBS ({context['stats']['total_clubs']} total):
{clubs_info}

UPCOMING EVENTS ({context['stats']['total_events']} total):
{events_info}

STATISTICS:
- Total Clubs: {context['stats']['total_clubs']}
- Total Members: {context['stats']['total_members']}
- Recruiting Clubs: {context['stats']['recruiting_clubs']}
- Total Events: {context['stats']['total_events']}

Guidelines:
1. Be friendly, concise, and helpful
2. Provide specific information from the data above
3. If asked about a club or event not in the data, say you don't have that information
4. Encourage students to join clubs and attend events
5. Keep responses under 200 words
6. Use emojis occasionally to be friendly 😊

Answer the student's question based on the information provided above."""

        return system_prompt
    
    def generate_response(self, user_message, db):
        """Generate response using Hugging Face API"""
        try:
            # Get fresh database context
            context = self.get_database_context(db)
            system_prompt = self.build_system_prompt(context)
            
            # Build conversation messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in self.conversation_history[-self.max_history:]:
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = ""
            for message in self.client.chat_completion(
                messages=messages,
                max_tokens=300,
                temperature=0.7,
                stream=True
            ):
                if message.choices[0].delta.content:
                    response += message.choices[0].delta.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Keep only recent history
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm having trouble connecting right now. Please try again in a moment! 🔄"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_quick_suggestions(self, context):
        """Get quick reply suggestions based on context"""
        suggestions = [
            "What clubs are recruiting?",
            "Show me upcoming events",
            "Tell me about technical clubs",
        ]
        
        # Add specific club suggestions
        if context['clubs']:
            suggestions.append(f"Tell me about {context['clubs'][0]['name']}")
        
        # Add event suggestions
        if context['events']:
            suggestions.append(f"When is {context['events'][0]['title']}?")
        
        return suggestions[:5]
