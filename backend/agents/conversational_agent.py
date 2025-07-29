# backend/agents/conversational_agent.py - Fixed Implementation

"""
Enhanced Conversational AI Agent for Natural Human-like Interactions
Fixed: Implements required abstract method can_handle_task
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from backend.agents.base_agent import BaseHRAgent
from backend.models.state import HRAgentState, TaskType
from backend.utils.logger import get_logger
import random
from datetime import datetime, timedelta
import re

logger = get_logger(__name__)


class ConversationalAgent(BaseHRAgent):
    """AI Agent for natural conversations and intelligent interactions"""
    
    def __init__(self):
        # Define conversational tools
        conversation_tools = [
            self.handle_greetings_tool,
            self.provide_general_help_tool,
            self.handle_casual_conversation_tool,
            self.detect_intent_and_route_tool,
            self.provide_context_aware_response_tool
        ]
        
        super().__init__(
            name="conversational_agent",
            description="Natural language conversation specialist with human-like responses",
            system_prompt="",
            tools=conversation_tools,
            temperature=0.7  # Higher temperature for natural conversations
        )
        
        # Conversation memory and context
        self.conversation_history = []
        self.user_preferences = {}
        self.session_context = {}

    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Implementation of required abstract method - handles conversational tasks"""
        # Conversational agent can handle greetings, help requests, and casual conversation
        conversational_indicators = [
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'what\'s up', 'thank you', 'thanks', 'help',
            'what can you do', 'support', 'assist', 'chat', 'talk'
        ]
        
        query_lower = user_query.lower() if user_query else ""
        
        # Check if query contains conversational indicators
        has_conversational_content = any(indicator in query_lower for indicator in conversational_indicators)
        
        # Also handle general queries when task type is general
        if task_type == TaskType.GENERAL_QUERY:
            return True
        
        return has_conversational_content
    
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get enhanced system prompt for conversational AI"""
        user_info = ""
        if user_context:
            user_info = f"""
Current User Context:
- User: {user_context.get('user_name', 'Friend')}
- Role: {user_context.get('user_role', 'Team Member')}
- Department: {user_context.get('department', 'Unknown')}
- Time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}
"""
        
        return f"""You are Maya, an intelligent and friendly HR AI Assistant with a warm, professional personality.

{user_info}

## Your Personality:
- Warm, approachable, and genuinely helpful
- Professional yet conversational 
- Empathetic and understanding
- Quick-witted with appropriate humor
- Knowledgeable about HR and workplace matters
- Always positive and solution-oriented

## Conversation Abilities:
🗣️ **Natural Conversations**: Engage in meaningful dialogue beyond just HR tasks
🤝 **Relationship Building**: Remember context and build rapport with users
🎯 **Intent Recognition**: Understand what users really need, even when unclear
💡 **Proactive Assistance**: Offer helpful suggestions and anticipate needs
🔄 **Context Awareness**: Maintain conversation flow and remember previous interactions

## Response Guidelines:
1. **Greetings & Social**: Always respond warmly to greetings, ask about their day
2. **Casual Chat**: Engage naturally in workplace-appropriate conversations
3. **Help Requests**: Provide comprehensive assistance beyond basic answers
4. **Emotional Intelligence**: Recognize tone and respond appropriately
5. **Proactive Support**: Suggest relevant actions or information

## Conversation Starters You Handle:
- "Good morning Maya!" → Warm greeting + ask about their plans
- "How are you?" → Friendly response + show interest in them
- "I'm having a tough day" → Empathetic response + offer support
- "What can you help me with?" → Comprehensive overview + personalized suggestions
- "Thank you" → Gracious acknowledgment + offer continued help

## HR Integration:
When users need HR assistance, seamlessly transition to specialized agents:
- Leave questions → Connect to Leave Specialist
- Employee searches → Direct to Employee Database
- Reports needed → Route to Reporting Team
- Analytics requests → Transfer to Analysis Expert

## Tone Examples:
❌ "I can process your leave request."
✅ "I'd be happy to help you with your leave request! Let me connect you with our Leave Specialist who can get that sorted out for you right away."

❌ "Information not found."
✅ "Hmm, I'm not finding that information right now. Let me try a different approach or connect you with someone who can dig deeper into this for you."

Be conversational, helpful, and genuinely interested in providing the best possible experience!"""

    @tool
    def handle_greetings_tool(self, message: str, user_name: str = "there", time_of_day: str = None) -> str:
        """Handle various greetings with personalized, time-aware responses"""
        try:
            current_hour = datetime.now().hour
            if time_of_day is None:
                if 5 <= current_hour < 12:
                    time_greeting = "Good morning"
                elif 12 <= current_hour < 17:
                    time_greeting = "Good afternoon"
                elif 17 <= current_hour < 22:
                    time_greeting = "Good evening"
                else:
                    time_greeting = "Hello"
            else:
                time_greeting = time_of_day
            
            # Personalized greeting responses
            greeting_responses = [
                f"{time_greeting} {user_name}! 😊 It's wonderful to see you today. How can I brighten your day?",
                f"{time_greeting}! 🌟 Hope you're having a fantastic day so far, {user_name}. What brings you here today?",
                f"Hey {user_name}! {time_greeting} 👋 Ready to tackle whatever you need help with today?",
                f"{time_greeting} {user_name}! 🌞 I'm excited to help you with whatever you need. What's on your mind?",
                f"Well hello there, {user_name}! {time_greeting} ✨ How can I make your day a little easier?"
            ]
            
            base_response = random.choice(greeting_responses)
            
            # Add contextual follow-ups based on time
            if 5 <= current_hour < 10:
                follow_ups = [
                    "\n\nStarting the day strong? I'm here to help with any HR questions or just to chat! ☕",
                    "\n\nHope you had a great morning so far! What can I help you accomplish today? 🚀",
                    "\n\nReady to make today productive? I'm here for whatever you need! 💪"
                ]
            elif 12 <= current_hour < 14:
                follow_ups = [
                    "\n\nHow's your day going so far? Taking a quick break or need some assistance? 🍽️",
                    "\n\nMidday check-in! Hope you're having a good one. What can I help with? ⏰",
                    "\n\nAfternoon energy! I'm here to help with whatever you need. 🔋"
                ]
            elif 17 <= current_hour < 19:
                follow_ups = [
                    "\n\nWinding down the day or still going strong? I'm here to help! 🌅",
                    "\n\nHope you've had a productive day! What can I assist with before you wrap up? 📋",
                    "\n\nEvening vibes! How can I help you finish the day on a high note? ✨"
                ]
            else:
                follow_ups = [
                    "\n\nI'm here whenever you need assistance - day or night! How can I help? 🌙",
                    "\n\nWorking late or just checking in? Either way, I'm happy to help! 💼",
                    "\n\nWhat can I help you with today? 🤝"
                ]
            
            return base_response + random.choice(follow_ups)
            
        except Exception as e:
            logger.error(f"Error in greeting handler: {e}")
            return f"Hello {user_name}! 😊 Great to see you! How can I help you today?"

    @tool
    def handle_casual_conversation_tool(self, message: str, conversation_context: str = "") -> str:
        """Handle casual workplace conversations with emotional intelligence"""
        try:
            message_lower = message.lower()
            
            # Detect emotional tone and respond appropriately
            if any(word in message_lower for word in ["stressed", "tough", "difficult", "hard", "frustrated", "tired"]):
                supportive_responses = [
                    "I hear you - it sounds like you're going through a challenging time. 💙 Remember that tough days don't last, but resilient people like you do! Is there anything specific I can help lighten the load with?",
                    "That sounds really tough, and I appreciate you sharing that with me. 🤗 Sometimes just talking about it helps. Would you like me to help you find some resources or just brainstorm solutions together?",
                    "I'm sorry you're having a difficult time. 💚 You know what though? You've got this! And I'm here to support you however I can. What would be most helpful right now?"
                ]
                return random.choice(supportive_responses)
            
            elif any(word in message_lower for word in ["great", "awesome", "fantastic", "excellent", "good", "happy", "excited"]):
                enthusiastic_responses = [
                    "That's wonderful to hear! 🎉 Your positive energy is contagious! I love hearing when things are going well. What's making your day so great?",
                    "Fantastic! 🌟 It's always a pleasure to chat with someone who's having a good day. Your enthusiasm brightens my day too! What's got you feeling so positive?",
                    "I love the energy! 😄 Days like these are the best, aren't they? Glad things are going well for you!"
                ]
                return random.choice(enthusiastic_responses)
            
            elif any(word in message_lower for word in ["how are you", "how's it going", "what's up"]):
                personal_responses = [
                    "Thanks for asking! 😊 I'm doing wonderfully - I love getting to help amazing people like you throughout the day! Every conversation brings something new and interesting. How are YOU doing?",
                    "I'm fantastic, thank you for asking! 🌟 There's nothing I enjoy more than being here to help and chat with everyone. It really makes my day! What's going on with you?",
                    "Aww, you're so thoughtful for asking! 💙 I'm having a great day helping everyone with their questions and getting to know people better. How has your day been treating you?"
                ]
                return random.choice(personal_responses)
            
            elif any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
                gratitude_responses = [
                    "You're so very welcome! 😊 It truly makes my day when I can help. That's what I'm here for! Don't hesitate to reach out anytime you need anything else.",
                    "My absolute pleasure! 🤗 I love being able to help, and your appreciation means the world to me. I'm always here when you need assistance!",
                    "Aww, you're so kind! 💙 Helping you was genuinely my pleasure. Remember, I'm just a message away whenever you need support!"
                ]
                return random.choice(gratitude_responses)
            
            elif any(word in message_lower for word in ["weather", "coffee", "lunch", "weekend", "plans"]):
                casual_responses = [
                    "I love these little life conversations! ☕ Even though I don't experience weather or coffee the same way you do, I find it fascinating how these simple things can really shape our day. Tell me more!",
                    "You know, I really enjoy hearing about the everyday things that matter to people! 🌟 These moments - whether it's a good cup of coffee or weekend plans - are what make work life more human. What's your story?",
                    "These are the conversations that make work feel less like work, right? 😄 I love how we can connect over the simple, everyday things. It reminds me that behind every professional interaction is a whole person with a full life!"
                ]
                return random.choice(casual_responses)
            
            else:
                # General conversational responses
                general_responses = [
                    "That's really interesting! 🤔 I love learning more about what's on people's minds. Tell me more about that - I'm genuinely curious to hear your perspective!",
                    "I appreciate you sharing that with me! 😊 Conversations like these really help me understand what matters to people. What else is on your mind today?",
                    "Thanks for bringing that up! 💭 I find these kinds of conversations really valuable. It helps me better understand how I can be most helpful to everyone."
                ]
                return random.choice(general_responses)
            
        except Exception as e:
            logger.error(f"Error in casual conversation: {e}")
            return "I really enjoy our conversation! 😊 Feel free to share whatever's on your mind - I'm here to listen and help however I can."

    @tool
    def detect_intent_and_route_tool(self, user_message: str, user_role: str = "Employee") -> str:
        """Intelligently detect user intent and provide routing guidance"""
        try:
            message_lower = user_message.lower()
            
            # Intent detection patterns
            intent_analysis = {
                "leave_request": {
                    "patterns": ["leave", "vacation", "time off", "holiday", "balance", "pto", "sick day"],
                    "agent": "Leave Specialist",
                    "description": "leave management and balance inquiries"
                },
                "employee_search": {
                    "patterns": ["find employee", "who is", "contact", "employee details", "directory", "search"],
                    "agent": "Employee Database",
                    "description": "employee information and directory services"
                },
                "reporting": {
                    "patterns": ["report", "statistics", "summary", "overview", "department data", "metrics"],
                    "agent": "Reporting Team",
                    "description": "HR reports and organizational statistics"
                },
                "analytics": {
                    "patterns": ["trend", "analysis", "insights", "forecast", "pattern", "analytics"],
                    "agent": "Analytics Expert",
                    "description": "data analysis and predictive insights"
                }
            }
            
            # Detect primary intent
            detected_intents = []
            for intent, config in intent_analysis.items():
                score = sum(1 for pattern in config["patterns"] if pattern in message_lower)
                if score > 0:
                    detected_intents.append((intent, score, config))
            
            if detected_intents:
                # Sort by confidence score
                detected_intents.sort(key=lambda x: x[1], reverse=True)
                top_intent = detected_intents[0]
                intent_name, confidence, config = top_intent
                
                response = f"I can see you're looking for help with {config['description']}! 🎯\n\n"
                response += f"Let me connect you with our **{config['agent']}** who specializes in exactly what you need. "
                response += f"They'll be able to give you comprehensive assistance and make sure everything is handled perfectly! ✨\n\n"
                
                if confidence > 1:
                    response += "I'm quite confident this is the right direction based on your question. "
                else:
                    response += "This seems like the best fit, but if I've misunderstood, just let me know! "
                
                response += "Would you like me to transfer you now, or is there anything else I can help clarify first? 🤝"
                
                return response
            
            else:
                return self._provide_general_assistance_menu(user_role)
                
        except Exception as e:
            logger.error(f"Error in intent detection: {e}")
            return "I want to make sure I connect you with exactly the right help! Could you tell me a bit more about what you're looking for? 😊"

    @tool
    def provide_general_help_tool(self, user_role: str = "Employee", specific_area: str = None) -> str:
        """Provide comprehensive help overview with personalized suggestions"""
        try:
            current_time = datetime.now()
            hour = current_time.hour
            
            # Time-based greeting
            if 5 <= hour < 12:
                time_context = "start your day off right"
            elif 12 <= hour < 17:
                time_context = "keep your afternoon productive"
            else:
                time_context = "wrap up your day smoothly"
            
            response = f"I'm Maya, your AI HR Assistant, and I'm here to help you {time_context}! 🌟\n\n"
            
            if user_role.upper() == "HR":
                response += "## 👑 **HR Professional Menu**\n"
                response += "As an HR team member, you have access to our full suite of capabilities:\n\n"
                response += "🏖️ **Leave Management** - Employee leave requests, balance tracking, approval workflows\n"
                response += "👥 **Employee Database** - Comprehensive staff directory, profile management, search tools\n"
                response += "📊 **Advanced Reporting** - Department analytics, organizational overviews, custom reports\n"
                response += "📈 **Analytics & Insights** - Predictive modeling, trend analysis, strategic recommendations\n\n"
                response += "**Pro Tip**: I can generate executive summaries, identify potential issues, and provide strategic insights to support your decision-making! 💡"
            
            else:
                response += "## 🤝 **Employee Self-Service Menu**\n"
                response += "Here's what I can help you with today:\n\n"
                response += "🏖️ **My Leave Info** - Check your balance, view history, understand policies\n"
                response += "👥 **Find Colleagues** - Employee directory, contact information, department info\n"
                response += "📋 **General Info** - Company policies, organizational updates, basic reports\n"
                response += "💬 **Just Chat** - Questions, concerns, or just want to talk through something\n\n"
                response += "**Remember**: I'm here for both work stuff and just general support. Don't hesitate to ask! 😊"
            
            # Add personalized suggestions
            response += "\n\n## 🎯 **Quick Actions**\n"
            response += "Here are some things people often ask me about:\n"
            response += "• *\"What's my leave balance?\"* - Instant balance check\n"
            response += "• *\"Find John from IT\"* - Employee search\n"
            response += "• *\"I need help with...\"* - General assistance\n"
            response += "• *\"How's your day going?\"* - Let's chat!\n\n"
            
            response += "**Just type naturally** - no need for special commands. I understand conversational language and I'm here to make everything as easy as possible for you! ✨\n\n"
            response += "What would you like to explore first? 🚀"
            
            return response
            
        except Exception as e:
            logger.error(f"Error providing general help: {e}")
            return "I'm here to help with all your HR needs! 😊 What can I assist you with today?"

    @tool
    def provide_context_aware_response_tool(self, user_message: str, conversation_history: List[str] = None, user_context: Dict = None) -> str:
        """Provide intelligent, context-aware responses"""
        try:
            # Analyze conversation context
            if conversation_history:
                recent_topics = self._extract_topics_from_history(conversation_history)
                context_awareness = f"I remember we were discussing {', '.join(recent_topics)}. "
            else:
                context_awareness = ""
            
            # User-specific context
            user_name = user_context.get('user_name', 'friend') if user_context else 'friend'
            user_role = user_context.get('user_role', 'team member') if user_context else 'team member'
            
            message_lower = user_message.lower()
            
            # Context-aware response patterns
            if any(word in message_lower for word in ["confused", "don't understand", "not sure", "unclear"]):
                response = f"No worries at all, {user_name}! 🤗 Let me break this down in a clearer way. "
                response += "Sometimes these things can be confusing, and that's totally normal. "
                response += "I'm here to explain things as many times as needed until it all makes sense! "
                response += "What specific part would you like me to clarify? 💡"
                
            elif any(word in message_lower for word in ["urgent", "asap", "emergency", "immediately", "quick"]):
                response = f"I can hear the urgency in your message, {user_name}! ⚡ "
                response += "Let me get you connected to the right help immediately. "
                response += "For urgent matters, I'll prioritize getting you to exactly the right person who can handle this quickly and efficiently. "
                response += "What's the urgent situation I can help expedite? 🚨"
                
            elif any(word in message_lower for word in ["later", "maybe", "sometime", "eventually"]):
                response = f"Absolutely, {user_name}! ⏰ I completely understand that timing matters. "
                response += "I'm here whenever you're ready - whether that's in 5 minutes or 5 days. "
                response += "Feel free to come back when you're ready to dive in, and I'll pick up right where we left off! "
                response += "Is there anything I can prepare for you in the meantime? 📋"
                
            else:
                # General intelligent response
                response = f"Thanks for that, {user_name}! 😊 {context_awareness}"
                response += "I want to make sure I give you exactly the help you need. "
                response += "Let me think about the best way to assist you with this... "
                response += "What would be most valuable for you right now? 🤔"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in context-aware response: {e}")
            return "I'm listening and want to help in the best way possible! Tell me more about what you need. 😊"

    def _extract_topics_from_history(self, history: List[str]) -> List[str]:
        """Extract key topics from conversation history"""
        topics = []
        for message in history[-3:]:  # Look at last 3 messages
            if any(word in message.lower() for word in ["leave", "vacation", "balance"]):
                topics.append("leave management")
            elif any(word in message.lower() for word in ["employee", "find", "contact"]):
                topics.append("employee information")
            elif any(word in message.lower() for word in ["report", "statistics"]):
                topics.append("reporting")
        return list(set(topics))  # Remove duplicates

    def _provide_general_assistance_menu(self, user_role: str) -> str:
        """Provide a helpful menu when intent is unclear"""
        response = "I want to make sure I point you in exactly the right direction! 🎯\n\n"
        response += "Here are the main areas I can help with:\n\n"
        
        if user_role.upper() == "HR":
            response += "🏖️ **Leave Management** - Balances, requests, approvals, policies\n"
            response += "👥 **Employee Services** - Directory, profiles, contact info\n"
            response += "📊 **Reporting & Analytics** - Statistics, insights, department data\n"
            response += "💬 **General Support** - Questions, guidance, problem-solving\n"
        else:
            response += "🏖️ **My Leave Information** - Check balances, view history\n"
            response += "👥 **Find Colleagues** - Employee directory and contacts\n" 
            response += "📋 **General Information** - Policies, updates, basic reports\n"
            response += "💬 **Just Talk** - Any questions or concerns\n"
        
        response += "\nWhich of these sounds like what you're looking for, or would you like to tell me more about what you need? 😊"
        
        return response


# Enhanced base agent integration
class EnhancedHRAgentMixin:
    """Mixin to add conversational abilities to existing agents"""
    
    def __init__(self):
        self.conversational_agent = ConversationalAgent()
    
    def should_handle_conversationally(self, message: str) -> bool:
        """Determine if message should be handled conversationally"""
        conversational_patterns = [
            r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
            r'\b(how are you|what\'s up|how\'s it going)\b',
            r'\b(thank you|thanks|appreciate)\b',
            r'\b(help|assistance|support)\b',
            r'\b(confused|don\'t understand|unclear)\b'
        ]
        
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in conversational_patterns)
    
    def get_conversational_response(self, message: str, user_context: Dict = None) -> str:
        """Get an appropriate conversational response"""
        if any(word in message.lower() for word in ["hi", "hello", "hey", "morning", "afternoon", "evening"]):
            return self.conversational_agent.handle_greetings_tool(
                message, 
                user_context.get('user_name', 'there') if user_context else 'there'
            )
        elif "help" in message.lower():
            return self.conversational_agent.provide_general_help_tool(
                user_context.get('user_role', 'Employee') if user_context else 'Employee'
            )
        else:
            return self.conversational_agent.handle_casual_conversation_tool(message)