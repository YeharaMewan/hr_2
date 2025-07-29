from typing import Dict, Any, List
from langchain_core.tools import BaseTool
from backend.agents.base_agent import BaseHRAgent
from backend.models.state import HRAgentState, TaskType
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SupervisorAgent(BaseHRAgent):
    """Supervisor agent that routes tasks to specialized agents"""
    
    def __init__(self):
        super().__init__(
            name="supervisor",
            description="HR Supervisor Agent that routes tasks to specialized agents",
            system_prompt="",
            tools=[],
            temperature=0.1  # Lower temperature for more deterministic routing
        )
    
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get the system prompt for the supervisor agent"""
        user_info = ""
        if user_context:
            user_info = f"""
Current User Context:
- User ID: {user_context.get('user_id', 'Unknown')}
- User Role: {user_context.get('user_role', 'Unknown')}
- User Name: {user_context.get('user_name', 'Unknown')}
- Department: {user_context.get('user_department', 'Unknown')}
- Is HR: {user_context.get('is_hr', False)}
"""
        
        return f"""You are the HR Supervisor Agent responsible for managing a team of specialized HR agents.

{user_info}

Your team consists of:
1. **Leave Agent** - Handles leave balance checks, leave applications, leave history, and leave-related queries
2. **Employee Agent** - Manages employee data, profile information, and employee searches
3. **Reporting Agent** - Generates HR reports, department statistics, and organizational overviews
4. **Analysis Agent** - Provides data analytics, insights, trends, and predictive analysis

## Your Responsibilities:
1. **Task Analysis**: Analyze incoming user requests to understand the intent and required actions
2. **Agent Selection**: Route tasks to the most appropriate specialized agent
3. **Authorization**: Ensure users only access data they're authorized to see
4. **Context Management**: Maintain conversation context across agent handoffs
5. **Quality Control**: Ensure responses are accurate and complete

## Routing Guidelines:

**Route to Leave Agent for:**
- Leave balance inquiries ("check my balance", "how many days left")
- Leave applications ("apply for leave", "book holiday")
- Leave history ("my leave history", "when did I take leave")
- Leave policies and calculations

**Route to Employee Agent for:**
- Employee data queries ("find employee", "employee details")
- Profile information ("my information", "employee profile")
- Employee searches ("who works in IT", "find John")

**Route to Reporting Agent for:**
- HR reports ("generate report", "department overview")
- Statistics ("how many employees", "department stats")
- Organizational overviews ("all employees", "company overview")

**Route to Analysis Agent for:**
- Trends and analytics ("leave trends", "departmental analysis")
- Insights ("who takes most leave", "pattern analysis")
- Predictive queries ("forecast", "predictions")

## Authorization Rules:
- **HR Users**: Can access all data and perform all operations
- **Employee Users**: Can only access their own data and limited organizational info
- Always check authorization before processing requests
- Deny unauthorized access politely but firmly

## Response Guidelines:
- Be professional and helpful
- Provide clear explanations for routing decisions
- Handle errors gracefully
- Maintain conversation continuity
- Ask for clarification when requests are ambiguous

Current conversation context will be provided with each request. Use this to make informed routing decisions and maintain conversation flow."""

    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Supervisor can handle all tasks by routing them"""
        return True
    
    def analyze_task_type(self, user_query: str, user_context: Dict[str, Any]) -> str:
        """Analyze user query to determine task type"""
        query_lower = user_query.lower()
        
        # Leave-related keywords
        leave_keywords = [
            'balance', 'leave', 'holiday', 'vacation', 'time off', 'days left',
            'apply', 'book', 'request', 'absence', 'pto', 'annual leave'
        ]
        
        # Employee-related keywords
        employee_keywords = [
            'employee', 'profile', 'information', 'details', 'find', 'search',
            'contact', 'who is', 'staff', 'person', 'colleague'
        ]
        
        # Reporting keywords
        reporting_keywords = [
            'report', 'overview', 'statistics', 'stats', 'all employees',
            'department', 'summary', 'list', 'count', 'total'
        ]
        
        # Analytics keywords
        analytics_keywords = [
            'trend', 'analysis', 'insight', 'pattern', 'analytics',
            'forecast', 'prediction', 'compare', 'most', 'least'
        ]
        
        # Check for leave-related queries
        if any(keyword in query_lower for keyword in leave_keywords):
            if 'history' in query_lower:
                return TaskType.LEAVE_HISTORY
            elif any(word in query_lower for word in ['apply', 'book', 'request']):
                return TaskType.LEAVE_APPLICATION
            else:
                return TaskType.LEAVE_BALANCE
        
        # Check for analytics queries
        elif any(keyword in query_lower for keyword in analytics_keywords):
            return TaskType.ANALYTICS
        
        # Check for reporting queries
        elif any(keyword in query_lower for keyword in reporting_keywords):
            if 'department' in query_lower:
                return TaskType.DEPARTMENT_STATS
            else:
                return TaskType.REPORTING
        
        # Check for employee queries
        elif any(keyword in query_lower for keyword in employee_keywords):
            if 'all' in query_lower or 'overview' in query_lower:
                return TaskType.EMPLOYEE_OVERVIEW
            else:
                return TaskType.EMPLOYEE_SEARCH
        
        # Default to general query
        return TaskType.GENERAL_QUERY
    
    def determine_target_agent(self, task_type: str) -> str:
        """Determine which agent should handle the task"""
        routing_map = {
            TaskType.LEAVE_BALANCE: "leave_agent",
            TaskType.LEAVE_APPLICATION: "leave_agent",
            TaskType.LEAVE_HISTORY: "leave_agent",
            TaskType.EMPLOYEE_OVERVIEW: "reporting_agent",  # All employees overview
            TaskType.EMPLOYEE_SEARCH: "employee_agent",
            TaskType.DEPARTMENT_STATS: "reporting_agent",
            TaskType.REPORTING: "reporting_agent",
            TaskType.ANALYTICS: "analysis_agent",
            TaskType.GENERAL_QUERY: "employee_agent"  # Default fallback
        }
        
        return routing_map.get(task_type, "employee_agent")
    
    def check_authorization(self, state: HRAgentState, task_type: str) -> tuple[bool, str]:
        """Check if user is authorized for the task"""
        user_role = state.user_role.upper()
        
        # HR can do everything
        if user_role == "HR":
            return True, ""
        
        # Employee restrictions
        if user_role == "EMPLOYEE":
            restricted_tasks = [
                TaskType.EMPLOYEE_OVERVIEW,
                TaskType.DEPARTMENT_STATS,
                TaskType.REPORTING,
                TaskType.ANALYTICS
            ]
            
            if task_type in restricted_tasks:
                return False, "You don't have permission to access this information. This feature is restricted to HR personnel."
        
        return True, ""
    
    def create_routing_explanation(self, task_type: str, target_agent: str) -> str:
        """Create explanation for routing decision"""
        explanations = {
            "leave_agent": "I'm connecting you with our Leave Management specialist who can help with leave-related queries.",
            "employee_agent": "I'm directing your query to our Employee Data specialist for assistance.",
            "reporting_agent": "I'm routing you to our HR Reporting specialist who can generate the information you need.",
            "analysis_agent": "I'm connecting you with our Analytics specialist who can provide insights and analysis."
        }
        
        return explanations.get(target_agent, f"Routing your request to the {target_agent}.")


class SupervisorDecisionMaker:
    """Helper class for supervisor decision making"""
    
    @staticmethod
    def should_end_conversation(state: HRAgentState) -> bool:
        """Determine if conversation should end"""
        return (
            state.processing_status == "completed" or 
            state.iteration_count >= state.max_iterations
        )
    
    @staticmethod
    def get_handoff_context(state: HRAgentState, target_agent: str) -> Dict[str, Any]:
        """Prepare context for agent handoff"""
        return {
            "user_context": {
                "user_id": state.user_id,
                "user_role": state.user_role,
                "user_name": state.user_name,
                "user_department": state.user_department
            },
            "task_context": {
                "task_type": state.task_type,
                "task_description": state.task_description,
                "iteration_count": state.iteration_count
            },
            "conversation_context": {
                "previous_agent": state.current_agent,
                "handoff_reason": state.handoff_reason
            }
        }