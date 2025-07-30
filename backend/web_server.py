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

from flask import Flask, request, jsonify, send_from_directory, send_file
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
import traceback

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
cors = CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000"])
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
        mongodb_collection = None 
    # Redis connection
    if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        logger.info("✅ Redis connected successfully")
    else:
        logger.warning("⚠️ Redis URL not configured")
        
except Exception as e:
    logger.error(f"❌ Database connection error: {e}")
    mongodb_collection = None  # Explicitly set to None
    mongodb_client = None

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

def save_conversation_to_db(user_id: str, user_message: str, ai_response: str):
    """Save conversation to MongoDB"""
    # ❌ Wrong: if not mongodb_collection:
    # ✅ Correct:
    if mongodb_collection is None:
        return False
    
    try:
        conversation_entry = {
            "user_id": user_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.now(),
            "session_id": active_sessions.get(user_id, {}).get("session_id", "unknown")
        }
        
        # Store in a conversations collection
        conversations_collection = mongodb_client.get_database("HRAgent")["conversations"]
        conversations_collection.insert_one(conversation_entry)
        return True
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")
        return False

@app.route('/')
def serve_index():
    """Serve the main application"""
    try:
        # Backend folder එකෙන් එකක් ඉහලට ගිහින් frontend folder එක හොයනවා
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
        return send_file(frontend_path)
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({"error": "Frontend not found"}), 404

@app.route('/frontend/')
def serve_frontend_index():
    """Serve the main application from /frontend/ path"""
    try:
        # Backend folder එකෙන් එකක් ඉහලට ගිහින් frontend folder එක හොයනවා
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
        return send_file(frontend_path)
    except Exception as e:
        logger.error(f"Error serving frontend index.html: {e}")
        return jsonify({"error": "Frontend not found"}), 404

@app.route('/frontend/<path:filename>')
def serve_frontend_files(filename):
    """Serve static frontend files"""
    try:
        # Backend folder එකෙන් එකක් ඉහලට ගිහින් frontend folder එක හොයනවා
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_dir, filename)
    except Exception as e:
        logger.error(f"Error serving frontend file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with system status"""
    cleanup_old_sessions()
    
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "conversational_ai": "active",
                "mongodb": mongodb_client is not None,
                "redis": redis_client is not None,
                "enhanced_swarm": swarm_available,
                "active_sessions": len(active_sessions)
            },
            "services": {
                "database": "up" if mongodb_client is not None else "down",
                "cache": "up" if redis_client else "down",
                "swarm_system": "up" if swarm_available else "fallback"
            }
        }
        
        if swarm_system:
            status["swarm_status"] = swarm_system.get_swarm_status()
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Enhanced login with session creation"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            logger.warning("⚠️ Login attempt with missing credentials")
            return jsonify({
                "success": False, 
                "message": "Username and password are required"
            }), 400
        
        logger.info(f"🔐 Login attempt for user: {username}")
        
        # ❌ Wrong: if mongodb_collection:
        # ✅ Correct: if mongodb_collection is not None:
        if mongodb_collection is not None:
            try:
                # Database එකෙන් user record එක find කරනවා
                user_record = mongodb_collection.find_one({"employee_id": username})
                
                # User තියෙනවාද සහ password correct ද check කරනවා
                if user_record and bcrypt.check_password_hash(user_record.get('password', ''), password):
                    # User context object එකක් create කරනවා
                    user_context = {
                        "user_id": username,
                        "user_name": user_record.get('name', username),
                        "user_role": user_record.get('role', 'Employee'),
                        "department": user_record.get('department', 'General'),
                        "employee_id": username,
                        "is_hr": user_record.get('role', '').upper() == 'HR'
                    }
                    
                    # New session එකක් create කරනවා
                    session_id = create_user_session(username, user_context)
                    
                    # JWT token එකක් create කරනවා
                    access_token = create_access_token(
                        identity=username,
                        additional_claims={
                            "session_id": session_id, 
                            "user_role": user_context["user_role"],
                            "user_name": user_context["user_name"]
                        }
                    )
                    
                    logger.info(f"✅ User {username} ({user_context['user_name']}) logged in successfully")
                    
                    return jsonify({
                        "success": True,
                        "message": f"Welcome {user_context['user_name']}! 😊",
                        "access_token": access_token,
                        "user": user_context,
                        "session_id": session_id
                    })
                else:
                    logger.warning(f"❌ Invalid login attempt for user: {username}")
                    return jsonify({
                        "success": False, 
                        "message": "Invalid credentials"
                    }), 401
                    
            except Exception as db_error:
                logger.error(f"❌ Database error during login: {db_error}")
                return jsonify({
                    "success": False, 
                    "message": "Authentication service temporarily unavailable"
                }), 503
        else:
            # Database නැති නම් fallback authentication (testing සඳහා)
            logger.warning("⚠️ Database not available, using fallback authentication")
            
            # Test users define කරනවා
            test_users = {
                'E001': {'name': 'Kalhar Dasanayaka', 'role': 'HR', 'department': 'HR'},
                'E002': {'name': 'Anjana Perera', 'role': 'HR', 'department': 'HR'},
                'E003': {'name': 'Ravindu Cooray', 'role': 'Employee', 'department': 'IT'}
            }
            
            # Test user ද සහ password correct ද check කරනවා
            if username in test_users and password == 'pw123':
                user_info = test_users[username]
                user_context = {
                    "user_id": username,
                    "user_name": user_info['name'],
                    "user_role": user_info['role'],
                    "department": user_info['department'],
                    "employee_id": username,
                    "is_hr": user_info['role'] == 'HR'
                }
                
                session_id = create_user_session(username, user_context)
                
                access_token = create_access_token(
                    identity=username,
                    additional_claims={
                        "session_id": session_id, 
                        "user_role": user_context["user_role"],
                        "user_name": user_context["user_name"]
                    }
                )
                
                logger.info(f"✅ Test user {username} logged in successfully")
                
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
        logger.error(f"❌ Login error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False, 
            "message": "Login failed due to server error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "message": "Endpoint not found",
        "error": "404 Not Found"
    }), 404

def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "message": "Internal server error",
        "error": "500 Internal Server Error"
    }), 500

@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 errors"""
    return jsonify({
        "success": False,
        "message": "Authentication required",
        "error": "401 Unauthorized"
    }), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return jsonify({
        "success": False,
        "message": "Access forbidden",
        "error": "403 Forbidden"
    }), 403

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "success": False,
        "message": "Token has expired",
        "error": "token_expired"
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "success": False,
        "message": "Invalid token",
        "error": "invalid_token"
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "success": False,
        "message": "Authentication token required",
        "error": "missing_token"
    }), 401

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

if settings.DEBUG:
    @app.route('/api/debug/sessions', methods=['GET'])
    def debug_sessions():
        """Debug endpoint to view active sessions"""
        return jsonify({
            "active_sessions": len(active_sessions),
            "sessions": [
                {
                    "session_id": sid[:8] + "...",
                    "user_id": session["user_id"],
                    "created_at": session["created_at"].isoformat(),
                    "last_activity": session["last_activity"].isoformat(),
                    "conversation_count": session["conversation_count"]
                }
                for sid, session in active_sessions.items()
            ]
        })
    
    @app.route('/api/debug/cleanup', methods=['POST'])
    def debug_cleanup():
        """Debug endpoint to cleanup old sessions"""
        old_count = len(active_sessions)
        cleanup_old_sessions()
        new_count = len(active_sessions)
        
        return jsonify({
            "message": f"Cleaned up {old_count - new_count} old sessions",
            "before": old_count,
            "after": new_count
        })

def start_background_tasks():
    """
    Background වල run වෙන maintenance tasks start කරන function
    - Old sessions cleanup කරනවා
    - System maintenance tasks run කරනවා
    """
    import threading
    import time
    
    def cleanup_task():
        """
        පැය පැයට old sessions cleanup කරන task
        - 24 පැයට වඩා පරණ sessions delete කරනවා
        - Memory usage අඩු කරනවා
        """
        while True:
            try:
                # පැයකට වරක් run වෙනවා (3600 seconds = 1 hour)
                time.sleep(3600)
                
                # Old sessions cleanup කරනවා
                old_count = len(active_sessions)  # cleanup කරන්න කලින් count එක
                cleanup_old_sessions()  # cleanup function call කරනවා
                new_count = len(active_sessions)  # cleanup කරන්න පස්සේ count එක
                
                # Log message එකක් දානවා
                cleaned_count = old_count - new_count
                logger.info(f"🧹 Cleaned up {cleaned_count} old sessions. Active sessions: {new_count}")
                
            except Exception as e:
                # Error එකක් ආවොත් log කරනවා
                logger.error(f"❌ Cleanup task error: {e}")
    
    def health_check_task():
        """
        System health periodically check කරන task
        """
        while True:
            try:
                # 5 මිනිත්තුකට වරක් health check කරනවා
                time.sleep(300)  # 300 seconds = 5 minutes
                
                # Database connections check කරනවා
                if mongodb_client is not None:
                    try:
                        mongodb_client.admin.command('ping')
                        logger.debug("✅ MongoDB connection healthy")
                    except Exception as db_error:
                        logger.error(f"❌ MongoDB connection issue: {db_error}")
                
                if redis_client:
                    try:
                        redis_client.ping()
                        logger.debug("✅ Redis connection healthy")
                    except Exception as redis_error:
                        logger.error(f"❌ Redis connection issue: {redis_error}")
                        
            except Exception as e:
                logger.error(f"❌ Health check task error: {e}")
    
    # Cleanup task එක background thread එකක start කරනවා
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("🧹 Started background cleanup task (runs every hour)")
    
    # Health check task එක background thread එකක start කරනවා
    health_thread = threading.Thread(target=health_check_task, daemon=True)
    health_thread.start()
    logger.info("🏥 Started background health check task (runs every 5 minutes)")
    
@app.route('/login', methods=['POST'])
def legacy_login():
    """Legacy login endpoint"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id', '').strip()
        password = data.get('password', '')
        
        # Convert to new format and call main login
        request_data = {
            'username': employee_id,
            'password': password
        }
        
        # Temporarily modify request data
        original_json = request.get_json
        request.get_json = lambda: request_data
        
        response = login()
        
        # Restore original method
        request.get_json = original_json
        
        return response
        
    except Exception as e:
        logger.error(f"Legacy login error: {e}")
        return jsonify({
            "success": False,
            "msg": "Login failed due to server error"
        }), 500


# Chat endpoint
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
        save_conversation_to_db(current_user_id, user_message, ai_response)
        
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
        logger.error(f"Traceback: {traceback.format_exc()}")
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
    
    # Handle leave-related queries
    if any(word in message_lower for word in ['leave', 'vacation', 'balance', 'time off', 'holiday']):
        try:
            # Try to get actual leave data
            employee_data = get_employee_by_id(user_context.get('employee_id', user_context.get('user_id')))
            
            if employee_data and employee_data.get('success'):
                data = employee_data['data']
                balance = data.get('balance', 0)
                history = data.get('history', [])
                
                if 'balance' in message_lower:
                    return f"Hi {user_name}! 🏖️ You currently have **{balance} days** of leave remaining. " \
                           f"You've taken {len(history)} days so far. Need help planning your time off? 😊"
                elif 'history' in message_lower:
                    if history:
                        recent_leaves = history[-3:] if len(history) > 3 else history
                        leaves_text = ", ".join(recent_leaves)
                        return f"Here's your recent leave history, {user_name}! 📅\n\n" \
                               f"Recent leaves: {leaves_text}\n" \
                               f"Total leaves taken: {len(history)} days\n" \
                               f"Current balance: {balance} days 🏖️"
                    else:
                        return f"You haven't taken any leave yet, {user_name}! 😊 You have {balance} days available whenever you need a break! 🏖️"
                else:
                    return f"I'd be happy to help with your leave questions, {user_name}! 🏖️ " \
                           f"You have {balance} days available. What would you like to know about your time off?"
            else:
                return f"I'd be happy to help you with leave-related questions, {user_name}! 🏖️ " \
                       f"I'm having trouble accessing your specific data right now, but I can still provide general assistance. " \
                       f"What would you like to know about leave policies or time off? ⏰"
        except Exception as e:
            logger.error(f"Error fetching leave data: {e}")
            return f"I'd love to help with your leave questions, {user_name}! 🏖️ " \
                   f"I'm having a small technical issue accessing the data right now, but I'm still here to help however I can!"
    
    # Handle employee searches
    if any(word in message_lower for word in ['find', 'employee', 'contact', 'who is', 'directory']):
        return f"I can help you find employee information, {user_name}! 👥 " \
               f"While my full directory features are temporarily limited, I'll do my best to assist. " \
               f"Who are you looking for, or what kind of contact information do you need? 🔍"
    
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
    
    # General conversational response
    return f"That's interesting, {user_name}! 😊 I'd love to help you with that. " \
           f"Could you tell me a bit more about what you're looking for? I want to make sure I help you in the best way possible! 🤝"

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user's profile information"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        # Try to get detailed profile from database
        # ❌ Wrong: if mongodb_collection:
        # ✅ Correct:
        if mongodb_collection is not None:
            try:
                user_record = mongodb_collection.find_one(
                    {"employee_id": current_user_id},
                    {"_id": 0, "password": 0}
                )
                
                if user_record:
                    return jsonify({
                        "success": True,
                        "data": {
                            "user_id": current_user_id,
                            "user_name": user_record.get('name', current_user_id),
                            "user_role": user_record.get('role', 'Employee'),
                            "department": user_record.get('department', 'Unknown'),
                            "employee_id": current_user_id,
                            "balance": user_record.get('balance', 0),
                            "is_hr": user_record.get('role', '').upper() == 'HR'
                        }
                    })
            except Exception as db_error:
                logger.error(f"Database error fetching profile: {db_error}")
        
        # Fallback to token data
        return jsonify({
            "success": True,
            "data": {
                "user_id": current_user_id,
                "user_name": claims.get('user_name', current_user_id),
                "user_role": claims.get('user_role', 'Employee'),
                "employee_id": current_user_id,
                "is_hr": claims.get('user_role', '').upper() == 'HR'
            }
        })
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to fetch profile"
        }), 500


@app.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get conversation history for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # ❌ Wrong: if mongodb_client:
        # ✅ Correct:
        if mongodb_client is not None:
            conversations_collection = mongodb_client.get_database("HRAgent")["conversations"]
            history = list(conversations_collection.find(
                {"user_id": current_user_id},
                {"_id": 0}
            ).sort("timestamp", -1).limit(50))
            
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
    """
    පරිශීලකයාගේ conversation session එක reset කරන function
    - Conversation count එක 0 කරනවා
    - Last activity time එක update කරනවා
    - Fresh start එකක් ලබා දෙනවා
    """
    try:
        # JWT token එකෙන් session ID එක ගන්නවා
        claims = get_jwt()
        session_id = claims.get('session_id')
        
        # Session ID එක තියෙනවාද සහ active sessions වල තියෙනවාද බලනවා
        if session_id and session_id in active_sessions:
            # Session එකේ conversation count එක 0 කරනවා
            active_sessions[session_id]["conversation_count"] = 0
            # Last activity time එක current time එකට update කරනවා
            active_sessions[session_id]["last_activity"] = datetime.now()
            
            logger.info(f"✅ Session reset for user: {active_sessions[session_id]['user_id']}")
            
            return jsonify({
                "success": True,
                "message": "Session reset successfully! 🔄 Fresh start!"
            })
        else:
            # Session ID එක නැති නම් error එකක් return කරනවා
            logger.warning(f"⚠️ Session not found for reset: {session_id}")
            return jsonify({
                "success": False,
                "message": "Session not found"
            }), 404
            
    except Exception as e:
        # කොහෙහරි error එකක් ආවොත් log කරලා error response එකක් දෙනවා
        logger.error(f"❌ Session reset error: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to reset session"
        }), 500



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
    
    # Start background tasks
    start_background_tasks()
    
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
    
    logger.info("📱 Frontend available at: http://localhost:5000/")
    logger.info("🔑 Login page at: http://localhost:5000/frontend/login.html")
    logger.info("🔧 API health check: http://localhost:5000/api/health")
    
    # Start the Flask application
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        threaded=True
    )