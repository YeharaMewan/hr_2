# backend/utils/error_handler.py - Create this new file

import traceback
from functools import wraps
from flask import jsonify, current_app
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def handle_api_errors(f):
    """Decorator for handling API errors gracefully"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log the full traceback
            error_id = f"ERR_{int(time.time())}"
            logger.error(f"API Error {error_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return user-friendly error
            if current_app.debug:
                return jsonify({
                    "error": str(e),
                    "error_id": error_id,
                    "traceback": traceback.format_exc()
                }), 500
            else:
                return jsonify({
                    "error": "An internal error occurred",
                    "error_id": error_id,
                    "message": "Please try again or contact support"
                }), 500
    
    return decorated_function

def handle_swarm_errors(f):
    """Decorator specifically for swarm system errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ImportError as e:
            logger.warning(f"Swarm import error: {e}")
            return None  # Will trigger fallback
        except Exception as e:
            logger.error(f"Swarm error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None  # Will trigger fallback
    
    return decorated_function

# Add this to web_server.py imports:
# from backend.utils.error_handler import handle_api_errors, handle_swarm_errors

# Then decorate your chat endpoint:
# @handle_api_errors
# @app.route('/api/chat', methods=['POST'])
# @jwt_required()
# def chat():