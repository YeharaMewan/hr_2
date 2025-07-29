from typing import List, Dict, Any, Optional, Annotated
from dataclasses import dataclass
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
import json


@dataclass
class HRAgentState(MessagesState):
    """Extended state for HR multi-agent system"""
    
    # User context
    user_id: str = ""
    user_role: str = "Employee"
    user_name: str = ""
    user_department: str = ""
    
    # Conversation context
    current_agent: str = "supervisor"
    previous_agent: str = ""
    task_type: str = ""
    task_description: str = ""
    
    # Data context
    query_results: Dict[str, Any] = None
    employee_data: Dict[str, Any] = None
    leave_data: Dict[str, Any] = None
    
    # Processing context
    processing_status: str = "active"  # active, completed, error
    iteration_count: int = 0
    max_iterations: int = 5
    
    # Agent handoff context
    handoff_reason: str = ""
    next_action: str = ""
    
    def __post_init__(self):
        if self.query_results is None:
            self.query_results = {}
        if self.employee_data is None:
            self.employee_data = {}
        if self.leave_data is None:
            self.leave_data = {}


@dataclass
class AgentResponse:
    """Response from an agent"""
    agent_name: str
    content: str
    status: str  # success, error, handoff
    data: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None
    reasoning: Optional[str] = None


@dataclass
class TaskContext:
    """Context for a specific task"""
    task_id: str
    task_type: str
    user_id: str
    user_role: str
    parameters: Dict[str, Any]
    created_at: str
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "parameters": self.parameters,
            "created_at": self.created_at,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        return cls(**data)


# Task type definitions
class TaskType:
    LEAVE_BALANCE = "leave_balance"
    LEAVE_APPLICATION = "leave_application"
    LEAVE_HISTORY = "leave_history"
    EMPLOYEE_OVERVIEW = "employee_overview"
    EMPLOYEE_SEARCH = "employee_search"
    DEPARTMENT_STATS = "department_stats"
    REPORTING = "reporting"
    ANALYTICS = "analytics"
    GENERAL_QUERY = "general_query"


# Agent names
class AgentNames:
    SUPERVISOR = "supervisor"
    LEAVE_AGENT = "leave_agent"
    EMPLOYEE_AGENT = "employee_agent"
    REPORTING_AGENT = "reporting_agent"
    ANALYSIS_AGENT = "analysis_agent"


# Processing status
class ProcessingStatus:
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    HANDOFF = "handoff"