// ===== AI CHATBOT FUNCTIONALITY =====

(function() {
    'use strict';
    
    // DOM Elements
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatbotClear = document.getElementById('chatbotClear');
    const chatInputField = document.getElementById('chatInputField');
    const chatSendBtn = document.getElementById('chatSendBtn');
    const chatbotMessages = document.getElementById('chatbotMessages');
    const quickSuggestions = document.getElementById('quickSuggestions');
    
    // State
    let isOpen = false;
    let isTyping = false;
    
    // Initialize
    function init() {
        // Show welcome message
        showWelcomeMessage();
        
        // Load suggestions
        loadSuggestions();
        
        // Event Listeners
        chatbotToggle.addEventListener('click', toggleChatbot);
        chatbotClose.addEventListener('click', toggleChatbot);
        chatbotClear.addEventListener('click', clearConversation);
        chatSendBtn.addEventListener('click', sendMessage);
        chatInputField.addEventListener('keypress', handleKeyPress);
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                toggleChatbot();
            }
        });
    }
    
    // Toggle chatbot window
    function toggleChatbot() {
        isOpen = !isOpen;
        if (isOpen) {
            chatbotWindow.classList.add('active');
            chatInputField.focus();
        } else {
            chatbotWindow.classList.remove('active');
        }
    }
    
    // Show welcome message
    function showWelcomeMessage() {
        const welcomeHTML = `
            <div class="welcome-message">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                    <line x1="9" y1="9" x2="9.01" y2="9"></line>
                    <line x1="15" y1="9" x2="15.01" y2="9"></line>
                </svg>
                <h3>Hi! I'm your Campus Assistant</h3>
                <p>Ask me anything about clubs, events, or campus activities!</p>
            </div>
        `;
        chatbotMessages.innerHTML = welcomeHTML;
    }
    
    // Load quick suggestions
    async function loadSuggestions() {
        try {
            const response = await fetch('/api/chatbot/suggestions');
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            }
        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    }
    
    // Display suggestions
    function displaySuggestions(suggestions) {
        quickSuggestions.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('button');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.addEventListener('click', () => {
                chatInputField.value = suggestion;
                sendMessage();
            });
            quickSuggestions.appendChild(chip);
        });
    }
    
    // Handle key press
    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }
    
    // Send message
    async function sendMessage() {
        const message = chatInputField.value.trim();
        
        if (!message || isTyping) return;
        
        // Clear input
        chatInputField.value = '';
        
        // Remove welcome message if exists
        const welcomeMsg = chatbotMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        // Add user message
        addMessage(message, 'user');
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send to backend
            const response = await fetch('/api/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();
            
            if (response.ok) {
                // Add bot response
                addMessage(data.response, 'bot');
                
                // Update suggestions if provided
                if (data.suggestions && data.suggestions.length > 0) {
                    displaySuggestions(data.suggestions);
                }
            } else {
                // Show error
                addMessage(data.response || 'Sorry, I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            hideTypingIndicator();
            addMessage('Sorry, I\'m having trouble connecting. Please try again later. 🔄', 'bot');
        }
    }
    
    // Add message to chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const avatarInitial = sender === 'user' ? 'U' : '🤖';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarInitial}</div>
            <div class="message-content-wrapper">
                <div class="message-content">${escapeHtml(text)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        chatbotMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        isTyping = true;
        chatSendBtn.disabled = true;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        chatbotMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        isTyping = false;
        chatSendBtn.disabled = false;
        
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Clear conversation
    async function clearConversation() {
        if (!confirm('Clear conversation history?')) return;
        
        try {
            await fetch('/api/chatbot/clear', {
                method: 'POST'
            });
            
            // Clear messages
            chatbotMessages.innerHTML = '';
            showWelcomeMessage();
            
            // Reload suggestions
            loadSuggestions();
        } catch (error) {
            console.error('Error clearing conversation:', error);
        }
    }
    
    // Scroll to bottom
    function scrollToBottom() {
        chatbotMessages.scrollTo({
            top: chatbotMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
