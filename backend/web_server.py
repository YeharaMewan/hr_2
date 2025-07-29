# backend/web_server.py - Fixed Configuration Issues

#!/usr/bin/env python3
"""
Enhanced HR Multi-Agent System Web Server - Fixed Version
Resolves database connection and abstract class implementation issues
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import asyncio
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
import redis
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
import uuid

# Load environment variables
load_dotenv()

# Import our enhanced modules with fixed configuration
try:
    from backend.config.settings import settings
    from backend.tools.database_tools import (
        get_employee_by_id, 
        save_conversation_history, 
        get_conversation_history
    )
    from backend.utils.logger import get_logger
    from backend.multiagent.swarm_system import (
        HRSwarmSystem,
        get_swarm_system,
        initialize_swarm_system
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying relative imports...")
    from config.settings import settings
    from tools.database_tools import (
        get_employee_by_id, 
        save_conversation_history, 
        get_conversation_history
    )
    from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize Flask
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
cors = CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize databases with fixed settings
mongodb_client = None
mongodb_collection = None
redis_client = None

try:
    # MongoDB connection - using MONGO_URI instead of MONGODB_URI
    if hasattr(settings, 'MONGO_URI') and settings.MONGO_URI:
        mongodb_client = MongoClient(settings.MONGO_URI)
        # Extract database name from settings or use default
        db_name = getattr(settings, 'MONGODB_DB_NAME', 'HRAgent')
        db = mongodb_client[db_name]
        mongodb_collection = db.employees
        logger.info("✅ MongoDB connected successfully")
    else:
        logger.warning("⚠️ MONGO_URI not configured in settings")
        
    # Redis connection
    if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        logger.info("✅ Redis connected successfully")
    else:
        logger.warning("⚠️ Redis URL not configured")
        
except Exception as e:
    logger.error(f"❌ Database connection error: {e}")

# Initialize Enhanced Swarm System with error handling
swarm_system = None
swarm_available = False

try:
    swarm_system = initialize_swarm_system()
    swarm_available = True
    logger.info("🚀 Enhanced Conversational HR Swarm System initialized successfully!")
except Exception as e:
    logger.error(f"⚠️ Enhanced swarm system initialization failed: {e}")
    logger.info("🔄 Running in fallback mode with basic conversational capabilities")

# Session management for conversations
active_sessions = {}

def create_user_session(user_id: str, user_data: Dict) -> str:
    """Create a new user session for conversation tracking"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "user_id": user_id,
        "user_data": user_data,
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "conversation_count": 0
    }
    return session_id

def update_session_activity(session_id: str):
    """Update last activity timestamp for session"""
    if session_id in active_sessions:
        active_sessions[session_id]["last_activity"] = datetime.now()
        active_sessions[session_id]["conversation_count"] += 1

def get_session_context(session_id: str) -> Optional[Dict]:
    """Get user context from session"""
    return active_sessions.get(session_id)

def cleanup_old_sessions():
    """Clean up sessions older than 24 hours"""
    cutoff_time = datetime.now() - timedelta(hours=24)
    sessions_to_remove = [
        sid for sid, session in active_sessions.items()
        if session["last_activity"] < cutoff_time
    ]
    for sid in sessions_to_remove:
        del active_sessions[sid]

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with system status"""
    cleanup_old_sessions()
    
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_info": {
            "conversational_ai": "active",
            "enhanced_swarm": swarm_available,
            "mongodb": mongodb_client is not None,
            "redis": redis_client is not None,
            "active_sessions": len(active_sessions)
        }
    }
    
    if swarm_system:
        status["swarm_status"] = swarm_system.get_swarm_status()
    
    return jsonify(status)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Enhanced login with session creation"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                "success": False, 
                "message": "Username and password are required"
            }), 400
        
        # Simple authentication (replace with your auth logic)
        if username in ['hr_user', 'employee_user']:
            # Create user context
            user_context = {
                "user_id": username,
                "user_name": username.replace('_', ' ').title(),
                "user_role": "HR" if username == 'hr_user' else "Employee",
                "department": "Human Resources" if username == 'hr_user' else "General",
                "is_hr": username == 'hr_user'
            }
            
            # Create session
            session_id = create_user_session(username, user_context)
            
            # Create JWT token
            access_token = create_access_token(
                identity=username,
                additional_claims={"session_id": session_id, "user_role": user_context["user_role"]}
            )
            
            logger.info(f"✅ User {username} logged in successfully with session {session_id}")
            
            return jsonify({
                "success": True,
                "message": f"Welcome {user_context['user_name']}! 😊",
                "access_token": access_token,
                "user": user_context,
                "session_id": session_id
            })
        else:
            return jsonify({
                "success": False, 
                "message": "Invalid credentials"
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "success": False, 
            "message": "Login failed due to server error"
        }), 500

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def enhanced_chat():
    """Enhanced chat endpoint with conversational AI"""
    try:
        # Get user identity and session info
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        session_id = claims.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({
                "success": False,
                "message": "Invalid session. Please log in again."
            }), 401
        
        # Update session activity
        update_session_activity(session_id)
        
        # Get user context
        session_context = get_session_context(session_id)
        user_context = session_context["user_data"]
        
        # Get message from request
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                "success": False,
                "message": "Message cannot be empty"
            }), 400
        
        logger.info(f"💬 {user_context['user_name']} ({session_id[:8]}): {user_message}")
        
        # Process with enhanced conversational system
        if swarm_system and swarm_available:
            try:
                # Use enhanced swarm system with conversational AI
                ai_response = swarm_system.process_message(
                    user_message=user_message,
                    user_context=user_context,
                    thread_id=session_id
                )
                
                system_mode = "Enhanced Conversational Swarm"
                
            except Exception as e:
                logger.error(f"Swarm processing error: {e}")
                ai_response = get_fallback_conversational_response(user_message, user_context)
                system_mode = "Fallback Conversational Mode"
        else:
            # Fallback conversational mode
            ai_response = get_fallback_conversational_response(user_message, user_context)
            system_mode = "Basic Conversational Mode"
        
        # Save conversation history
        if mongodb_collection:
            try:
                save_conversation_history(
                    user_id=current_user_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    collection=mongodb_collection
                )
            except Exception as e:
                logger.warning(f"Failed to save conversation: {e}")
        
        logger.info(f"🤖 Maya → {user_context['user_name']}: {ai_response[:100]}...")
        
        return jsonify({
            "success": True,
            "response": ai_response,
            "system_mode": system_mode,
            "user_context": user_context,
            "conversation_metadata": {
                "session_id": session_id,
                "conversation_count": session_context["conversation_count"],
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "success": False,
            "message": "I'm experiencing a technical hiccup, but I'm still here to help! 😊 Please try again."
        }), 500

def get_fallback_conversational_response(message: str, user_context: Dict) -> str:
    """Provide conversational fallback when enhanced systems aren't available"""
    user_name = user_context.get('user_name', 'friend')
    user_role = user_context.get('user_role', 'Employee')
    message_lower = message.lower().strip()
    
    # Handle greetings
    if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
        greetings = [
            f"Hello {user_name}! 😊 I'm Maya, your AI HR assistant. How can I brighten your day?",
            f"Hi there {user_name}! 👋 Great to see you! What can I help you with today?",
            f"Hey {user_name}! 🌟 I'm here and ready to help with whatever you need!"
        ]
        import random
        return random.choice(greetings)
    
    # Handle gratitude
    if any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        gratitude_responses = [
            f"You're so welcome, {user_name}! 😊 It's genuinely my pleasure to help!",
            f"Aww, thank you {user_name}! 🤗 That really makes my day!",
            f"My absolute pleasure, {user_name}! 💙 I'm always here when you need me!"
        ]
        import random
        return random.choice(gratitude_responses)
    
    # Handle how are you
    if any(phrase in message_lower for phrase in ['how are you', 'how\'s it going', 'what\'s up']):
        responses = [
            f"Thanks for asking, {user_name}! 😊 I'm doing fantastic - I love getting to help wonderful people like you!",
            f"I'm great, thank you! 🌟 Every conversation brings something new and interesting. How are YOU doing?",
            f"Aww, you're so thoughtful! 💙 I'm having a wonderful day helping everyone. What's going on with you?"
        ]
        import random
        return random.choice(responses)
    
    # Handle help requests
    if any(word in message_lower for word in ['help', 'assist', 'support', 'what can you do']):
        help_response = f"I'd love to help you, {user_name}! 🌟 I'm Maya, your AI HR assistant.\n\n"
        
        if user_role.upper() == "HR":
            help_response += "As an HR professional, I can help you with:\n"
            help_response += "🏖️ **Leave Management** - Employee requests, balances, approvals\n"
            help_response += "👥 **Employee Database** - Staff directory, searches, profiles\n"  
            help_response += "📊 **Reporting** - Department analytics, organizational insights\n"
            help_response += "📈 **Analytics** - Trends, predictions, strategic recommendations\n"
        else:
            help_response += "Here's how I can support you:\n"
            help_response += "🏖️ **Your Leave Info** - Check balances, view history\n"
            help_response += "👥 **Find Colleagues** - Employee directory, contact info\n"
            help_response += "📋 **General Info** - Company policies, updates\n"
        
        help_response += "\n💬 **Plus, I love casual conversation too!** Feel free to just chat with me anytime. 😊\n\n"
        help_response += "What would you like to start with? ✨"
        
        return help_response
    
    # Handle emotional support
    if any(word in message_lower for word in ['stressed', 'tough', 'difficult', 'frustrated', 'tired']):
        support_responses = [
            f"I hear you, {user_name}. 💙 That sounds really challenging. Remember that tough days don't last, but resilient people like you do!",
            f"I'm sorry you're having a difficult time, {user_name}. 🤗 You don't have to handle everything alone - I'm here to help however I can.",
            f"That sounds tough, {user_name}. 💚 Thank you for sharing that with me. Is there anything specific I can help with to lighten the load?"
        ]
        import random
        return random.choice(support_responses)
    
    # Handle leave-related queries
    if any(word in message_lower for word in ['leave', 'vacation', 'balance', 'time off', 'holiday']):
        return f"I'd be happy to help you with leave-related questions, {user_name}! 🏖️ " \
               f"While I'm working with limited functionality right now, I can still provide basic assistance. " \
               f"What specifically would you like to know about your leave or time off? ⏰"
    
    # Handle employee searches
    if any(word in message_lower for word in ['find', 'employee', 'contact', 'who is', 'directory']):
        return f"I can help you find employee information, {user_name}! 👥 " \
               f"While my full directory features are temporarily limited, I'll do my best to assist. " \
               f"Who are you looking for, or what kind of contact information do you need? 🔍"
    
    # General conversational response
    return f"That's interesting, {user_name}! 😊 I'd love to help you with that. " \
           f"While I'm running with some limitations right now, I'm still here to assist and chat. " \
           f"Could you tell me a bit more about what you're looking for? I want to make sure I help you in the best way possible! 🤝"

@app.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get conversation history for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        if mongodb_collection:
            history = get_conversation_history(current_user_id, mongodb_collection)
            return jsonify({
                "success": True,
                "history": history
            })
        else:
            return jsonify({
                "success": False,
                "message": "Conversation history not available"
            }), 503
            
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to retrieve conversation history"
        }), 500

@app.route('/api/system/status', methods=['GET'])
@jwt_required()
def get_system_status():
    """Get comprehensive system status"""
    try:
        cleanup_old_sessions()
        
        status = {
            "system_type": "Enhanced Conversational HR System",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "conversational_ai": "active",
                "mongodb": mongodb_client is not None,
                "redis": redis_client is not None,
                "enhanced_swarm": swarm_available
            },
            "session_info": {
                "active_sessions": len(active_sessions),
                "total_conversations": sum(s["conversation_count"] for s in active_sessions.values())
            },
            "features": [
                "Natural conversation handling",
                "Emotional intelligence and support", 
                "Context-aware responses",
                "Intelligent intent detection",
                "Multi-agent collaboration",
                "Conversation memory",
                "Real-time session management"
            ]
        }
        
        if swarm_system:
            status["swarm_details"] = swarm_system.get_swarm_status()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to get system status"
        }), 500

@app.route('/api/user/session/reset', methods=['POST'])
@jwt_required()
def reset_user_session():
    """Reset user's conversation session"""
    try:
        claims = get_jwt()
        session_id = claims.get('session_id')
        
        if session_id and session_id in active_sessions:
            # Reset conversation count and update timestamp
            active_sessions[session_id]["conversation_count"] = 0
            active_sessions[session_id]["last_activity"] = datetime.now()
            
            return jsonify({
                "success": True,
                "message": "Session reset successfully! 🔄 Fresh start!"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Session not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Session reset error: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to reset session"
        }), 500

def check_system_requirements():
    """Check system requirements and availability"""
    checks = []
    
    # Database checks
    if mongodb_client is not None:
        try:
            count = mongodb_collection.count_documents({})
            checks.append(f"✅ MongoDB connected ({count} employees)")
        except Exception as e:
            checks.append(f"❌ MongoDB error: {e}")
    else:
        checks.append("❌ MongoDB not connected")
    
    # Redis check
    if redis_client is not None:
        checks.append("✅ Redis connected")
    else:
        checks.append("❌ Redis not connected")
    
    # Enhanced swarm system status
    if swarm_available:
        checks.append("✅ Enhanced Conversational Swarm system active")
    else:
        checks.append("⚠️ Enhanced Swarm system: Using fallback conversational mode")
    
    return checks

if __name__ == '__main__':
    # Perform startup checks
    logger.info("=== Enhanced Conversational HR System Starting ===")
    
    startup_checks = check_system_requirements()
    for check in startup_checks:
        logger.info(check)
    
    # Check for critical failures
    critical_failures = [check for check in startup_checks if check.startswith("❌")]
    if critical_failures and not settings.DEBUG:
        logger.error("Critical system components are not available:")
        for failure in critical_failures:
            logger.error(failure)
        logger.error("Exiting due to critical failures in production mode")
        exit(1)
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Environment: {settings.FLASK_ENV}")
    
    if swarm_available:
        logger.info("🚀 Running with Enhanced Conversational Swarm system!")
        logger.info("🤖 Maya AI: Natural conversations, emotional intelligence, real-world interactions")
        logger.info("👥 Multi-agent collaboration: leave, employee, reporting, analysis specialists")
        logger.info("🧠 Advanced features: Context awareness, intent detection, session management")
    else:
        logger.info("⚠️ Running in fallback conversational mode. Core conversation features available.")
    
    # Start the Flask application
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )