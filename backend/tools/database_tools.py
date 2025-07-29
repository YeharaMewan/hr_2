# backend/tools/database_tools.py - Complete Fixed Version

from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
import redis
import json
from datetime import datetime, timedelta
from langchain_core.tools import tool

# Import with fallback
try:
    from backend.config.settings import settings
    from backend.utils.logger import get_logger
except ImportError:
    from config.settings import settings
    from utils.logger import get_logger

logger = get_logger(__name__)

# Database connections
try:
    mongo_client = MongoClient(settings.MONGO_URI)
    db = mongo_client.get_database("HRAgent")
    employees_collection: Collection = db["employees"]
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    employees_collection = None

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


@tool
def get_employee_by_id(employee_id: str) -> Dict[str, Any]:
    """Get employee information by ID"""
    try:
        if employees_collection is None:
            return {
                "success": False, 
                "message": "Database connection error", 
                "data": None
            }
        
        employee = employees_collection.find_one(
            {"employee_id": employee_id}, 
            {"_id": 0, "password": 0}
        )
        
        if employee:
            return {
                "success": True,
                "message": f"Found employee {employee['name']} ({employee_id})",
                "data": employee
            }
        else:
            return {
                "success": False,
                "message": f"Employee {employee_id} not found",
                "data": None
            }
    except Exception as e:
        logger.error(f"Error getting employee {employee_id}: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "data": None
        }


@tool
def get_all_employees() -> Dict[str, Any]:
    """Get all employees from database"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": []
            }
        
        employees = list(employees_collection.find(
            {}, 
            {"_id": 0, "password": 0}
        ))
        
        return {
            "success": True,
            "message": f"Found {len(employees)} employees",
            "data": employees
        }
    except Exception as e:
        logger.error(f"Error getting all employees: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "data": []
        }


@tool
def search_employees(search_term: str) -> Dict[str, Any]:
    """Search employees by name or other criteria"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": []
            }
        
        # Create search query
        search_regex = {"$regex": search_term, "$options": "i"}
        query = {
            "$or": [
                {"name": search_regex},
                {"employee_id": search_regex},
                {"department": search_regex},
                {"role": search_regex}
            ]
        }
        
        employees = list(employees_collection.find(
            query, 
            {"_id": 0, "password": 0}
        ))
        
        return {
            "success": True,
            "message": f"Found {len(employees)} employees matching '{search_term}'",
            "data": employees
        }
    except Exception as e:
        logger.error(f"Error searching employees: {e}")
        return {
            "success": False,
            "message": f"Search error: {str(e)}",
            "data": []
        }


@tool
def get_department_employees(department: str) -> Dict[str, Any]:
    """Get all employees in a specific department"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": []
            }
        
        employees = list(employees_collection.find(
            {"department": {"$regex": f"^{department}$", "$options": "i"}}, 
            {"_id": 0, "password": 0}
        ))
        
        return {
            "success": True,
            "message": f"Found {len(employees)} employees in {department}",
            "data": employees
        }
    except Exception as e:
        logger.error(f"Error getting department employees: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "data": []
        }


@tool
def get_department_statistics() -> Dict[str, Any]:
    """Get statistics by department"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": {}
            }
        
        # Aggregate pipeline for department statistics
        pipeline = [
            {
                "$group": {
                    "_id": "$department",
                    "employee_count": {"$sum": 1},
                    "total_balance": {"$sum": "$balance"},
                    "avg_balance": {"$avg": "$balance"},
                    "roles": {"$addToSet": "$role"}
                }
            },
            {
                "$sort": {"employee_count": -1}
            }
        ]
        
        stats = list(employees_collection.aggregate(pipeline))
        
        # Format the results
        department_stats = {}
        for stat in stats:
            dept_name = stat["_id"] or "Unknown"
            department_stats[dept_name] = {
                "employee_count": stat["employee_count"],
                "total_leave_balance": stat["total_balance"],
                "average_leave_balance": round(stat["avg_balance"], 2),
                "roles": stat["roles"]
            }
        
        return {
            "success": True,
            "message": f"Generated statistics for {len(department_stats)} departments",
            "data": department_stats
        }
    except Exception as e:
        logger.error(f"Error getting department statistics: {e}")
        return {
            "success": False,
            "message": f"Statistics error: {str(e)}",
            "data": {}
        }


@tool
def get_low_balance_employees(threshold: int = 5) -> Dict[str, Any]:
    """Get employees with leave balance below threshold"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": []
            }
        
        employees = list(employees_collection.find(
            {"balance": {"$lte": threshold}},
            {"_id": 0, "password": 0}
        ))
        
        return {
            "success": True,
            "message": f"Found {len(employees)} employees with balance ≤ {threshold}",
            "data": employees
        }
    except Exception as e:
        logger.error(f"Error getting low balance employees: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "data": []
        }


@tool
def update_employee_leave_balance(employee_id: str, new_balance: int) -> Dict[str, Any]:
    """Update employee leave balance"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": None
            }
        
        result = employees_collection.update_one(
            {"employee_id": employee_id},
            {"$set": {"balance": new_balance}}
        )
        
        if result.matched_count > 0:
            return {
                "success": True,
                "message": f"Updated leave balance for {employee_id} to {new_balance}",
                "data": {"employee_id": employee_id, "new_balance": new_balance}
            }
        else:
            return {
                "success": False,
                "message": f"Employee {employee_id} not found",
                "data": None
            }
    except Exception as e:
        logger.error(f"Error updating leave balance for {employee_id}: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "data": None
        }


@tool
def add_leave_history(employee_id: str, leave_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Add leave entry to employee history"""
    try:
        if employees_collection is None:
            return {
                "success": False,
                "message": "Database connection error",
                "data": None
            }
        
        # Add timestamp if not provided
        if "date" not in leave_entry:
            leave_entry["date"] = datetime.now().strftime("%Y-%m-%d")
        
        result = employees_collection.update_one(
            {"employee_id": employee_id},
            {"$push": {"history": leave_entry}}
        )
        
        if result.matched_count > 0:
            return {
                "success": True,
                "message": f"Added leave entry to {employee_id} history",
                "data": {"employee_id": employee_id, "entry": leave_entry}
            }
        else:
            return {
                "success": False,
                "message": f"Employee {employee_id} not found",
                "data": None
            }
    except Exception as e:
        logger.error(f"Error adding leave history for {employee_id}: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "data": None
        }


# Conversation history functions
def save_conversation_history(user_id: str, conversation: List[Dict[str, Any]]) -> bool:
    """Save conversation history to Redis"""
    try:
        if redis_client is None:
            logger.warning("Redis not available, conversation history not saved")
            return False
        
        key = f"conversation:{user_id}"
        redis_client.setex(key, 3600, json.dumps(conversation))  # 1 hour expiry
        return True
    except Exception as e:
        logger.error(f"Error saving conversation history: {e}")
        return False


def get_conversation_history(user_id: str) -> List[Dict[str, Any]]:
    """Get conversation history from Redis"""
    try:
        if redis_client is None:
            return []
        
        key = f"conversation:{user_id}"
        history = redis_client.get(key)
        
        if history:
            return json.loads(history)
        return []
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []


# Additional utility functions
def validate_employee_exists(employee_id: str) -> bool:
    """Validate if an employee ID exists"""
    try:
        if employees_collection is None:
            return False
        
        count = employees_collection.count_documents({"employee_id": employee_id})
        return count > 0
    except Exception as e:
        logger.error(f"Error validating employee: {e}")
        return False


def get_employee_count() -> int:
    """Get total employee count"""
    try:
        if employees_collection is None:
            return 0
        
        return employees_collection.count_documents({})
    except Exception as e:
        logger.error(f"Error getting employee count: {e}")
        return 0


# Department-related functions
def get_all_departments() -> List[str]:
    """Get list of all departments"""
    try:
        if employees_collection is None:
            return []
        
        departments = employees_collection.distinct("department")
        return [dept for dept in departments if dept]  # Filter out None/empty values
    except Exception as e:
        logger.error(f"Error getting departments: {e}")
        return []