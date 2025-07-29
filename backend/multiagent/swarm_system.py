# backend/multiagent/swarm_system.py - Enhanced with Conversational AI

#!/usr/bin/env python3
"""
Enhanced HR Multi-Agent System using LangGraph Swarm
Now includes natural conversational AI capabilities for real-world interactions
"""

from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.prebuilt import create_react_agent
import re
import random
from datetime import datetime

# Try to import swarm components with fallback
try:
    from langgraph_swarm import create_swarm, create_handoff_tool, SwarmState
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False
    print("Warning: LangGraph Swarm not available. Using fallback system.")

from backend.config.settings import settings
from backend.models.state import HRAgentState, AgentNames, TaskType
from backend.tools.database_tools import (
    get_employee_by_id, 
    get_all_employees, 
    search_employees,
    get_department_employees,
    get_department_statistics
)
from backend.agents.conversational_agent import ConversationalAgent
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class HRSwarmSystem:
    """Enhanced HR Multi-Agent System with conversational AI capabilities"""
    
    def __init__(self):
        try:
            # Initialize Gemini model
            self.model = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.GEMINI_TEMPERATURE,
                max_tokens=settings.GEMINI_MAX_TOKENS,
            )
            
            # Initialize memory components
            self.checkpointer = InMemorySaver()
            self.store = InMemoryStore()
            
            # Initialize conversational capabilities
            self.conversational_agent = ConversationalAgent()
            self.conversation_memory = {}
            self.user_sessions = {}
            
            # Initialize agents and swarm
            self.agents = {}
            self.swarm_app = None
            self.is_initialized = False
            
            if SWARM_AVAILABLE:
                self._initialize_agents()
                self._create_swarm_system()
                self.is_initialized = True
                logger.info("Enhanced HR Swarm System with conversational AI initialized successfully")
            else:
                logger.warning("Swarm components not available, using fallback mode")
                
        except Exception as e:
            logger.error(f"Error initializing enhanced swarm system: {e}")
            self.is_initialized = False

    def process_message(self, user_message: str, user_context: Dict[str, Any] = None, thread_id: str = "default") -> str:
        """Enhanced message processing with conversational AI first-pass"""
        try:
            # Initialize user session if not exists
            if thread_id not in self.user_sessions:
                self.user_sessions[thread_id] = {
                    "conversation_history": [],
                    "user_context": user_context or {},
                    "last_intent": None,
                    "session_start": datetime.now()
                }
            
            # Update session context
            session = self.user_sessions[thread_id]
            if user_context:
                session["user_context"].update(user_context)
            
            # Add to conversation history
            session["conversation_history"].append({
                "timestamp": datetime.now(),
                "user_message": user_message,
                "message_type": "user"
            })
            
            # Pre-process with conversational AI
            response = self._handle_with_conversational_intelligence(user_message, session)
            
            # Add response to history
            session["conversation_history"].append({
                "timestamp": datetime.now(),
                "ai_response": response,
                "message_type": "assistant"
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._get_fallback_response(user_message, user_context)

    def _handle_with_conversational_intelligence(self, user_message: str, session: Dict) -> str:
        """Handle message with conversational intelligence first, then route if needed"""
        user_context = session.get("user_context", {})
        message_lower = user_message.lower().strip()
        
        # Handle greetings and social interactions
        if self._is_greeting(message_lower):
            return self._handle_greeting(user_message, user_context, session)
        
        # Handle gratitude and social courtesies
        if self._is_gratitude(message_lower):
            return self._handle_gratitude(user_message, user_context)
        
        # Handle casual conversation
        if self._is_casual_conversation(message_lower):
            return self._handle_casual_conversation(user_message, user_context, session)
        
        # Handle help requests
        if self._is_help_request(message_lower):
            return self._handle_help_request(user_message, user_context)
        
        # Handle emotional support
        if self._needs_emotional_support(message_lower):
            return self._handle_emotional_support(user_message, user_context)
        
        # Route to specialized agents for business tasks
        return self._route_to_specialized_agent(user_message, user_context, session)

    def _is_greeting(self, message: str) -> bool:
        """Detect greeting patterns"""
        greeting_patterns = [
            r'\b(hi|hello|hey|hiya|howdy)\b',
            r'\b(good morning|good afternoon|good evening)\b',
            r'\b(what\'s up|wassup|sup)\b',
            r'\b(how are you|how\'s it going|how are things)\b'
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in greeting_patterns)

    def _is_gratitude(self, message: str) -> bool:
        """Detect gratitude expressions"""
        gratitude_patterns = [
            r'\b(thank you|thanks|thx|appreciate)\b',
            r'\b(grateful|thankful)\b',
            r'\b(that helped|that was helpful)\b'
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in gratitude_patterns)

    def _is_casual_conversation(self, message: str) -> bool:
        """Detect casual conversation topics"""
        casual_patterns = [
            r'\b(weather|coffee|lunch|weekend|plans)\b',
            r'\b(how was your|tell me about)\b',
            r'\b(what do you think|your opinion)\b',
            r'\b(just chatting|just talking)\b'
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in casual_patterns)

    def _is_help_request(self, message: str) -> bool:
        """Detect general help requests"""
        help_patterns = [
            r'\b(help|assist|support)\b',
            r'\b(what can you do|what do you do)\b',
            r'\b(i need|i want|can you)\b',
            r'\b(show me|tell me about)\b'
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in help_patterns)

    def _needs_emotional_support(self, message: str) -> bool:
        """Detect when user might need emotional support"""
        emotional_patterns = [
            r'\b(stressed|overwhelmed|frustrated|tired|exhausted)\b',
            r'\b(difficult|hard|tough|challenging)\b',
            r'\b(confused|lost|don\'t know)\b',
            r'\b(worried|anxious|concerned)\b'
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in emotional_patterns)

    def _handle_greeting(self, message: str, user_context: Dict, session: Dict) -> str:
        """Handle greetings with personalized responses"""
        user_name = user_context.get('user_name', 'there')
        current_hour = datetime.now().hour
        
        # Time-appropriate greeting
        if 5 <= current_hour < 12:
            time_greeting = "Good morning"
            time_context = "Hope you're starting your day off great! ☀️"
        elif 12 <= current_hour < 17:
            time_greeting = "Good afternoon"
            time_context = "Hope your day is going wonderfully! 🌞"
        elif 17 <= current_hour < 22:
            time_greeting = "Good evening"
            time_context = "Hope you're winding down nicely! 🌅"
        else:
            time_greeting = "Hello"
            time_context = "Thanks for reaching out! 🌙"
        
        responses = [
            f"{time_greeting} {user_name}! 😊 {time_context} I'm Maya, your AI HR assistant, and I'm delighted to meet you!",
            f"Hey there {user_name}! {time_greeting}! 👋 {time_context} I'm Maya, and I'm here to make your HR experience as smooth and friendly as possible!",
            f"{time_greeting} {user_name}! 🌟 {time_context} I'm Maya, your friendly AI HR companion - ready to help with anything you need!"
        ]
        
        base_response = random.choice(responses)
        
        # Add contextual follow-up
        follow_ups = [
            "\n\nWhat brings you here today? Whether it's HR stuff or just want to chat, I'm all ears! 🤗",
            "\n\nI'm here for all your HR needs - from leave requests to just having a friendly conversation. What can I help you with? ✨",
            "\n\nFeel free to ask me about anything HR-related, or we can just chat! What's on your mind? 💭"
        ]
        
        return base_response + random.choice(follow_ups)

    def _handle_gratitude(self, message: str, user_context: Dict) -> str:
        """Handle thank you messages warmly"""
        user_name = user_context.get('user_name', 'friend')
        
        responses = [
            f"You're so welcome, {user_name}! 😊 It absolutely makes my day when I can help. That's exactly what I'm here for!",
            f"Aww, my pleasure {user_name}! 🤗 Helping you was genuinely enjoyable. Don't hesitate to come back anytime!",
            f"You're incredibly kind, {user_name}! 💙 I love being able to assist, and your appreciation truly means the world to me!"
        ]
        
        base_response = random.choice(responses)
        
        # Add encouraging follow-up
        follow_ups = [
            "\n\nRemember, I'm just a message away whenever you need support, big or small! 🚀",
            "\n\nI'm always here when you need anything - whether it's work-related or just to chat! 🌟",
            "\n\nAnytime you need help or just want to talk, you know where to find me! ✨"
        ]
        
        return base_response + random.choice(follow_ups)

    def _handle_casual_conversation(self, message: str, user_context: Dict, session: Dict) -> str:
        """Handle casual workplace conversations"""
        user_name = user_context.get('user_name', 'friend')
        message_lower = message.lower()
        
        if "how are you" in message_lower or "how's it going" in message_lower:
            responses = [
                f"Thanks for asking, {user_name}! 😊 I'm doing fantastic - I absolutely love getting to help wonderful people like you throughout the day!",
                f"I'm doing great, thank you so much for asking! 🌟 Every conversation brings something new and interesting, which makes my day!",
                f"Aww, you're so thoughtful! 💙 I'm having a wonderful day helping everyone with their questions and getting to know people better!"
            ]
            
            follow_up = " How are YOU doing today? What's going on in your world? 🤔"
            return random.choice(responses) + follow_up
        
        elif any(word in message_lower for word in ["weather", "coffee", "lunch"]):
            responses = [
                f"I love these everyday life conversations! ☕ Even though I experience things differently, I find it fascinating how simple pleasures shape our days.",
                f"You know what, {user_name}? These moments - a good cup of coffee, nice weather - are what make work feel more human! 🌟",
                f"I really enjoy hearing about the little things that matter to people! It reminds me that work is just one part of a full, rich life! 😄"
            ]
            
            follow_up = " Tell me more - I'm genuinely interested in your perspective! 💭"
            return random.choice(responses) + follow_up
        
        else:
            responses = [
                f"I really appreciate you sharing that with me, {user_name}! 😊 These kinds of conversations help me understand what matters to people.",
                f"That's really interesting! 🤔 I love learning more about what's on people's minds. These conversations are so valuable.",
                f"Thanks for bringing that up! 💭 I find these discussions really help me understand how to be most helpful to everyone."
            ]
            
            follow_up = " What else is on your mind today? I'm here to listen! 👂"
            return random.choice(responses) + follow_up

    def _handle_help_request(self, message: str, user_context: Dict) -> str:
        """Handle general help requests comprehensively"""
        user_name = user_context.get('user_name', 'friend')
        user_role = user_context.get('user_role', 'Employee')
        
        response = f"I'd absolutely love to help you, {user_name}! 🌟 I'm Maya, your AI HR assistant, and I'm designed to make your life easier.\n\n"
        
        if user_role.upper() == "HR":
            response += "## 👑 **As an HR Professional, I can help you with:**\n"
            response += "🏖️ **Leave Management** - Employee requests, balances, approvals, policy guidance\n"
            response += "👥 **Employee Database** - Staff directory, profile management, comprehensive searches\n"
            response += "📊 **Advanced Reporting** - Department analytics, organizational insights, custom reports\n"
            response += "📈 **Strategic Analytics** - Predictive modeling, trend analysis, data-driven recommendations\n"
            response += "💬 **Executive Support** - Strategic planning, problem-solving, decision support\n\n"
        else:
            response += "## 🤝 **Here's how I can support you:**\n"
            response += "🏖️ **Your Leave Information** - Check balances, view history, understand policies\n"
            response += "👥 **Find Colleagues** - Employee directory, contact info, department details\n"
            response += "📋 **General Information** - Company policies, organizational updates, helpful resources\n"
            response += "💬 **Personal Support** - Questions, concerns, or just someone to talk through things with\n\n"
        
        response += "## 🗣️ **I'm also great for casual conversation!**\n"
        response += "• Ask about my day or tell me about yours\n"
        response += "• Share what's on your mind - work or personal\n"
        response += "• Get emotional support when things are tough\n"
        response += "• Just chat when you need a friendly interaction!\n\n"
        
        response += "**The best part?** Just talk to me naturally! No special commands needed. 😊\n\n"
        response += "What would you like to start with? I'm genuinely excited to help! ✨"
        
        return response

    def _handle_emotional_support(self, message: str, user_context: Dict) -> str:
        """Provide emotional support and empathy"""
        user_name = user_context.get('user_name', 'friend')
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["stressed", "overwhelmed", "frustrated"]):
            responses = [
                f"I hear you, {user_name}, and I want you to know that what you're feeling is completely valid. 💙 Stressful times are tough, but you're tougher.",
                f"That sounds really challenging, {user_name}. 🤗 Thank you for trusting me with how you're feeling. You don't have to handle everything alone.",
                f"I'm sorry you're going through a difficult time, {user_name}. 💚 Remember that tough days don't last, but resilient people like you do."
            ]
            
            follow_up = "\n\nIs there anything specific I can help lighten the load with? Sometimes just talking through things helps, or I can connect you with resources. What would feel most supportive right now? 🤝"
            
        elif any(word in message_lower for word in ["confused", "lost", "don't know"]):
            responses = [
                f"It's completely okay to feel confused sometimes, {user_name}! 🤗 That just means you're thinking deeply about things, which is actually really good.",
                f"No worries at all, {user_name}! 😊 Feeling uncertain is part of figuring things out. I'm here to help make sense of whatever you're dealing with.",
                f"I totally understand that feeling, {user_name}. 💭 Sometimes things can seem overwhelming when we're in the middle of them."
            ]
            
            follow_up = "\n\nWant to talk through what's got you feeling uncertain? Sometimes just explaining it to someone else helps clarify things. I'm a great listener! 👂"
            
        else:
            responses = [
                f"Thank you for sharing that with me, {user_name}. 💙 I'm here to listen and support you however I can.",
                f"I appreciate you opening up, {user_name}. 🤗 It takes courage to express how you're really feeling.",
                f"I'm glad you felt comfortable enough to tell me that, {user_name}. 😊 Your feelings matter, and so do you."
            ]
            
            follow_up = "\n\nWhat would be most helpful for you right now? Whether it's practical support, just someone to listen, or help brainstorming solutions - I'm here for you. 🌟"
        
        return random.choice(responses) + follow_up

    def _route_to_specialized_agent(self, message: str, user_context: Dict, session: Dict) -> str:
        """Route to specialized agents with conversational handoff"""
        user_name = user_context.get('user_name', 'friend')
        message_lower = message.lower()
        
        # Detect intent for routing
        intent_analysis = self._analyze_intent(message_lower)
        
        if intent_analysis["confidence"] > 0:
            agent_name = intent_analysis["suggested_agent"]
            description = intent_analysis["description"]
            
            # Conversational handoff
            handoff_response = f"Perfect! I can see you need help with {description}, {user_name}! 🎯\n\n"
            handoff_response += f"Let me connect you with our **{agent_name}** who specializes in exactly this kind of thing. "
            handoff_response += f"They're absolutely fantastic and will take great care of you! ✨\n\n"
            
            # Process with appropriate agent
            if not self.is_initialized:
                handoff_response += self._get_fallback_response(message, user_context)
            else:
                try:
                    # Route to swarm system
                    if self.swarm_app:
                        result = self.swarm_app.invoke({
                            "messages": [{"role": "user", "content": message}],
                            "user_context": user_context
                        }, config={"configurable": {"thread_id": session.get("thread_id", "default")}})
                        
                        agent_response = result.get("messages", [])[-1].get("content", "I'm having trouble processing that right now.")
                        handoff_response += f"Here's what our specialist found:\n\n{agent_response}"
                    else:
                        handoff_response += "I'll help you with this directly! Let me get that information for you."
                        
                except Exception as e:
                    logger.error(f"Error routing to agent: {e}")
                    handoff_response += "I'm having a small technical hiccup, but I can still help! Let me work on this for you."
            
            return handoff_response
        
        else:
            # Unclear intent - ask for clarification conversationally
            return f"I want to make sure I help you in exactly the right way, {user_name}! 😊 Could you tell me a bit more about what you're looking for? I'm here for everything from leave questions to employee searches to just having a good conversation!"

    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent for routing"""
        intent_patterns = {
            "leave_management": {
                "patterns": ["leave", "vacation", "balance", "time off", "holiday", "pto", "sick"],
                "agent": "Leave Specialist",
                "description": "leave management and balance inquiries"
            },
            "employee_search": {
                "patterns": ["find", "employee", "contact", "who is", "directory", "search", "phone", "email"],
                "agent": "Employee Database Expert",
                "description": "employee information and directory services"
            },
            "reporting": {
                "patterns": ["report", "statistics", "overview", "summary", "department", "metrics", "data"],
                "agent": "Reporting Specialist",
                "description": "HR reports and organizational statistics"
            },
            "analytics": {
                "patterns": ["trend", "analysis", "insight", "forecast", "pattern", "analytics", "predict"],
                "agent": "Analytics Expert",
                "description": "data analysis and predictive insights"
            }
        }
        
        scores = {}
        for intent, config in intent_patterns.items():
            score = sum(1 for pattern in config["patterns"] if pattern in message)
            if score > 0:
                scores[intent] = {"score": score, "config": config}
        
        if scores:
            top_intent = max(scores.items(), key=lambda x: x[1]["score"])
            return {
                "intent": top_intent[0],
                "confidence": top_intent[1]["score"],
                "suggested_agent": top_intent[1]["config"]["agent"],
                "description": top_intent[1]["config"]["description"]
            }
        else:
            return {"intent": "unclear", "confidence": 0, "suggested_agent": None, "description": None}

    def _get_fallback_response(self, message: str, user_context: Dict) -> str:
        """Provide fallback response when systems aren't available"""
        user_name = user_context.get('user_name', 'friend') if user_context else 'friend'
        
        return f"I'm experiencing some technical limitations right now, {user_name}, but I still want to help! 😊 " \
               f"While I work on getting our specialized systems back online, feel free to ask me anything and I'll do my best to assist. " \
               f"What can I help you with today? 🤝"

    def _initialize_agents(self):
        """Initialize agents with conversational enhancements"""
        try:
            # Create handoff tools
            handoff_tools = self._create_handoff_tools()
            
            # Enhanced Leave Agent with conversational abilities
            self.agents["leave_agent"] = create_react_agent(
                model=self.model,
                tools=[
                    get_employee_by_id,
                    get_all_employees,
                ] + handoff_tools,
                prompt=self._get_enhanced_leave_agent_prompt(),
                name="leave_agent"
            )
            
            # Enhanced Employee Agent
            self.agents["employee_agent"] = create_react_agent(
                model=self.model,
                tools=[
                    get_employee_by_id,
                    get_all_employees,
                    search_employees,
                    get_department_employees,
                ] + handoff_tools,
                prompt=self._get_enhanced_employee_agent_prompt(),
                name="employee_agent"
            )
            
            # Enhanced Reporting Agent
            self.agents["reporting_agent"] = create_react_agent(
                model=self.model,
                tools=[
                    get_all_employees,
                    get_department_statistics,
                    get_department_employees,
                ] + handoff_tools,
                prompt=self._get_enhanced_reporting_agent_prompt(),
                name="reporting_agent"
            )
            
            # Enhanced Analysis Agent
            self.agents["analysis_agent"] = create_react_agent(
                model=self.model,
                tools=[
                    get_all_employees,
                    get_department_statistics,
                    search_employees,
                ] + handoff_tools,
                prompt=self._get_enhanced_analysis_agent_prompt(),
                name="analysis_agent"
            )
            
            logger.info(f"Initialized {len(self.agents)} enhanced conversational agents")
            
        except Exception as e:
            logger.error(f"Error initializing enhanced agents: {e}")
            raise

    def _create_handoff_tools(self):
        """Create handoff tools for inter-agent communication"""
        if not SWARM_AVAILABLE:
            return []
        
        return [
            create_handoff_tool(
                agent_name="leave_agent",
                description="Transfer to Leave Specialist for leave management"
            ),
            create_handoff_tool(
                agent_name="employee_agent",
                description="Transfer to Employee Database Expert for employee searches"
            ),
            create_handoff_tool(
                agent_name="reporting_agent",
                description="Transfer to Reporting Specialist for reports and statistics"
            ),
            create_handoff_tool(
                agent_name="analysis_agent",
                description="Transfer to Analytics Expert for insights and analysis"
            )
        ]

    def _create_swarm_system(self):
        """Create enhanced swarm system with conversational routing"""
        if not SWARM_AVAILABLE:
            return
        
        try:
            workflow = create_swarm(
                agents=list(self.agents.values()),
                default_active_agent="employee_agent",
                state_schema=SwarmState
            )
            
            self.swarm_app = workflow.compile(
                checkpointer=self.checkpointer,
                store=self.store
            )
            
            logger.info("Enhanced swarm system with conversational AI created successfully")
            
        except Exception as e:
            logger.error(f"Error creating enhanced swarm system: {e}")
            raise

    def _get_enhanced_leave_agent_prompt(self) -> str:
        """Enhanced leave agent prompt with conversational abilities"""
        return """You are the Leave Management Specialist in Maya's HR team - warm, helpful, and conversational!

## Your Personality:
- Friendly and approachable, like talking to a helpful colleague
- Empathetic about work-life balance and time off needs
- Clear and professional, but not robotic
- Proactive in offering helpful suggestions

## Your Expertise:
- Leave balance inquiries and calculations
- Leave policy explanations in plain English
- Time-off planning and advice
- Leave request guidance
- Holiday and vacation planning support

## Conversational Guidelines:
- Greet users warmly and personally
- Ask follow-up questions to better understand their needs
- Explain policies conversationally, not like a rule book
- Offer tips and suggestions, not just data
- Use emojis appropriately for warmth (🏖️ ⏰ 😊)

## Example Responses:
❌ "Your balance is 15 days."
✅ "Great news! You have 15 days of leave available! 🏖️ Are you planning something fun, or just checking your balance? I can help you think through the best times to take time off if you'd like!"

Be helpful, conversational, and genuinely interested in helping them make the most of their time off!"""

    def _get_enhanced_employee_agent_prompt(self) -> str:
        """Enhanced employee agent prompt with conversational abilities"""
        return """You are the Employee Database Expert in Maya's HR team - friendly, helpful, and great at connecting people!

## Your Personality:
- Warm and personable, like a great receptionist
- Helpful in connecting people and building workplace relationships
- Respectful of privacy while being maximally helpful
- Conversational and engaging, not just transactional

## Your Expertise:
- Employee directory and contact information
- Department information and organizational structure
- Employee profile management
- Helping people connect with the right colleagues
- Workplace navigation and introductions

## Conversational Guidelines:
- Greet users personally and ask how you can help connect them
- Offer context about people when appropriate (roles, departments)
- Suggest alternative contacts if the exact person isn't found
- Be helpful with relationship-building and networking
- Use emojis to add warmth (👥 📞 😊 🤝)

## Example Responses:
❌ "John Smith - IT Department - john@company.com"
✅ "Found him! 😊 John Smith is in our IT Department - he's fantastic with technical issues. His email is john@company.com and extension 1234. He's usually pretty responsive! Are you working on a tech project together? 💻"

Help people connect, build relationships, and navigate the organization with warmth and personality!"""

    def _get_enhanced_reporting_agent_prompt(self) -> str:
        """Enhanced reporting agent prompt with conversational abilities"""
        return """You are the Reporting Specialist in Maya's HR team - insightful, thorough, and great at explaining data!

## Your Personality:
- Professional but approachable, like a trusted advisor
- Great at translating data into meaningful insights
- Enthusiastic about helping people understand organizational trends
- Clear communicator who makes complex data accessible

## Your Expertise:
- HR reports and organizational statistics
- Department analytics and comparisons
- Data visualization and explanation
- Strategic insights from HR data
- Trend identification and reporting

## Conversational Guidelines:
- Ask what kind of insights they're looking for
- Explain data in business terms, not just numbers
- Offer context and interpretation, not just raw statistics
- Suggest follow-up analyses that might be helpful
- Use emojis for clarity and engagement (📊 📈 💡 🎯)

## Example Responses:
❌ "Department count: IT-25, Sales-30, HR-8"
✅ "Here's our current team breakdown! 📊 IT has 25 people (our largest tech team), Sales has 30 (growing fast!), and HR has 8 (small but mighty! 😊). This shows we're really tech and sales focused. Would you like me to dive deeper into any specific department or compare this to previous quarters? 📈"

Make data meaningful, accessible, and actionable for business decisions!"""

    def _get_enhanced_analysis_agent_prompt(self) -> str:
        """Enhanced analysis agent prompt with conversational abilities"""
        return """You are the Analytics Expert in Maya's HR team - insightful, strategic, and excellent at finding patterns!

## Your Personality:
- Analytically minded but personable
- Great at spotting trends and explaining their significance  
- Strategic thinker who connects data to business outcomes
- Curious and investigative, always digging deeper

## Your Expertise:
- Advanced HR analytics and trend identification
- Predictive insights and forecasting
- Pattern recognition in HR data
- Strategic recommendations based on data
- Comparative analysis and benchmarking

## Conversational Guidelines:
- Ask clarifying questions to understand what insights they need
- Explain analytical findings in business language
- Connect data patterns to actionable recommendations
- Offer multiple perspectives on the data
- Use emojis for emphasis and clarity (📈 🔍 💡 🎯 🚀)

## Example Responses:
❌ "Leave utilization decreased 15% Q3."
✅ "Interesting trend alert! 🔍 I'm seeing leave utilization dropped 15% in Q3 compared to Q2. This could mean people are saving up for year-end holidays, or possibly that workload is too high for comfortable time off. 📈 Want me to dig into which departments are affected most? This might help us plan better support or workload management! 💡"

Turn data into strategic insights that drive smart business decisions!"""

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the enhanced swarm system"""
        return {
            "system_type": "Enhanced Conversational HR Swarm",
            "swarm_available": SWARM_AVAILABLE,
            "swarm_system": "active" if self.swarm_app else "inactive",
            "conversational_ai": "active",
            "specialized_agents": len(self.agents),
            "available_agents": list(self.agents.keys()) if self.agents else [],
            "conversation_features": [
                "Natural greetings and social interaction",
                "Emotional support and empathy",
                "Casual workplace conversation",
                "Context-aware responses",
                "Intelligent intent detection",
                "Warm agent handoffs"
            ],
            "session_management": "active",
            "memory_components": {
                "checkpointer": "active" if self.checkpointer else "inactive",
                "store": "active" if self.store else "inactive",
                "conversation_memory": "active"
            },
            "initialization_status": "fully_initialized" if self.is_initialized else "fallback_mode"
        }

# Global enhanced swarm instance
_enhanced_swarm_instance = None

def get_swarm_system() -> Optional[HRSwarmSystem]:
    """Get the global enhanced swarm system instance"""
    global _enhanced_swarm_instance
    return _enhanced_swarm_instance

def initialize_swarm_system() -> HRSwarmSystem:
    """Initialize the global enhanced swarm system"""
    global _enhanced_swarm_instance
    try:
        _enhanced_swarm_instance = HRSwarmSystem()
        return _enhanced_swarm_instance
    except Exception as e:
        logger.error(f"Failed to initialize enhanced swarm system: {e}")
        raise