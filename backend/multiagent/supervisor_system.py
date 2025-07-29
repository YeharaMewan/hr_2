from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.prebuilt import create_react_agent

from backend.config.settings import settings
from backend.models.state import HRAgentState, AgentNames, TaskType
from backend.agents.base_agent import agent_registry
from backend.agents.supervisor_agent import SupervisorAgent
from backend.agents.leave_agent import LeaveAgent
from backend.agents.employee_agent import EmployeeAgent
from backend.agents.reporting_agent import ReportingAgent
from backend.agents.analysis_agent import AnalysisAgent
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class HRSupervisorSystem:
    """HR Multi-Agent System using LangGraph Supervisor Architecture"""
    
    def __init__(self):
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
        
        # Initialize agents
        self.agents = {}
        self.supervisor_app = None
        
        self._initialize_agents()
        self._create_supervisor_system()
        
        logger.info("HR Supervisor System initialized successfully")
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        try:
            # Create specialized agents
            supervisor = SupervisorAgent()
            leave_agent = LeaveAgent()
            employee_agent = EmployeeAgent()
            reporting_agent = ReportingAgent()
            analysis_agent = AnalysisAgent()
            
            # Register agents
            agent_registry.register(supervisor)
            agent_registry.register(leave_agent)
            agent_registry.register(employee_agent)
            agent_registry.register(reporting_agent)
            agent_registry.register(analysis_agent)
            
            # Create ReAct agents for each specialist
            self.agents = {
                AgentNames.LEAVE_AGENT: leave_agent.create_react_agent(),
                AgentNames.EMPLOYEE_AGENT: employee_agent.create_react_agent(),
                AgentNames.REPORTING_AGENT: reporting_agent.create_react_agent(),
                AgentNames.ANALYSIS_AGENT: analysis_agent.create_react_agent()
            }
            
            logger.info(f"Initialized {len(self.agents)} specialized agents")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise
    
    def _create_supervisor_system(self):
        """Create the supervisor-based multi-agent system"""
        try:
            # Create supervisor system with specialized agents
            self.supervisor_app = create_supervisor(
                agents=list(self.agents.values()),
                model=self.model,
                prompt=self._get_supervisor_prompt()
            ).compile(
                checkpointer=self.checkpointer,
                store=self.store
            )
            
            logger.info("Supervisor system created and compiled successfully")
            
        except Exception as e:
            logger.error(f"Error creating supervisor system: {e}")
            raise
    
    def _get_supervisor_prompt(self) -> str:
        """Get the supervisor agent system prompt"""
        return """You are the HR Supervisor managing a team of specialized HR agents.

Your team consists of:
1. **leave_agent** - Handles leave balances, applications, and leave history
2. **employee_agent** - Manages employee data, searches, and profile information  
3. **reporting_agent** - Generates HR reports, statistics, and organizational overviews
4. **analysis_agent** - Provides analytics, insights, and predictive analysis

## Your Responsibilities:
1. **Route Requests**: Analyze user queries and delegate to the most appropriate agent
2. **Maintain Context**: Ensure conversation continuity across agent handoffs
3. **Verify Authorization**: Check user permissions before processing requests
4. **Quality Control**: Ensure responses are complete and accurate

## Routing Guidelines:
- **Leave queries** → leave_agent (balance, applications, history)
- **Employee searches** → employee_agent (find staff, get details)
- **Reports & statistics** → reporting_agent (overviews, summaries)
- **Analytics & insights** → analysis_agent (trends, predictions)

## Authorization Rules:
- **HR Users**: Full access to all functions
- **Employee Users**: Limited to their own data and basic organizational info
- Always verify permissions before delegating tasks

Be professional, efficient, and ensure users get the help they need from the right specialist."""
    
    async def process_query(
        self,
        user_query: str,
        user_id: str,
        user_role: str,
        conversation_history: List[Dict[str, Any]] = None,
        thread_id: str = None
    ) -> str:
        """Process a user query through the supervisor system"""
        try:
            # Prepare the input for the supervisor
            input_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"User: {user_id} ({user_role})\nQuery: {user_query}"
                    }
                ]
            }
            
            # Configuration for the run
            config = {
                "configurable": {
                    "thread_id": thread_id or f"thread_{user_id}_{hash(user_query)}"
                }
            }
            
            # Stream the response from supervisor
            response_content = ""
            async for chunk in self.supervisor_app.astream(input_data, config=config):
                if "messages" in chunk:
                    for message in chunk["messages"]:
                        if hasattr(message, 'content') and message.content:
                            response_content += str(message.content)
            
            return response_content or "I apologize, but I couldn't process your request. Please try again."
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents in the system"""
        return {
            "supervisor_system": "active" if self.supervisor_app else "inactive",
            "specialized_agents": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "memory_components": {
                "checkpointer": "active" if self.checkpointer else "inactive",
                "store": "active" if self.store else "inactive"
            }
        }
    
    def reset_conversation(self, thread_id: str) -> bool:
        """Reset conversation history for a specific thread"""
        try:
            # In a real implementation, you'd clear the specific thread
            # For now, we'll return success
            logger.info(f"Reset conversation for thread: {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting conversation: {e}")
            return False


class SupervisorTaskRouter:
    """Helper class for routing tasks in supervisor system"""
    
    @staticmethod
    def analyze_query_intent(query: str, user_role: str) -> Dict[str, Any]:
        """Analyze user query to determine intent and routing"""
        query_lower = query.lower()
        
        # Define routing patterns
        patterns = {
            AgentNames.LEAVE_AGENT: [
                'leave', 'balance', 'holiday', 'vacation', 'time off',
                'apply', 'book', 'request', 'absence', 'days left'
            ],
            AgentNames.EMPLOYEE_AGENT: [
                'employee', 'staff', 'find', 'search', 'profile',
                'contact', 'who is', 'details', 'information'
            ],
            AgentNames.REPORTING_AGENT: [
                'report', 'overview', 'statistics', 'stats', 'summary',
                'all employees', 'department', 'total', 'count'
            ],
            AgentNames.ANALYSIS_AGENT: [
                'trend', 'analysis', 'insight', 'pattern', 'analytics',
                'forecast', 'prediction', 'compare', 'most', 'least'
            ]
        }
        
        # Score each agent based on keyword matches
        scores = {}
        for agent, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[agent] = score
        
        # Determine best match
        if scores:
            best_agent = max(scores, key=scores.get)
            confidence = scores[best_agent] / len(patterns[best_agent])
        else:
            best_agent = AgentNames.EMPLOYEE_AGENT  # Default
            confidence = 0.1
        
        return {
            "target_agent": best_agent,
            "confidence": confidence,
            "all_scores": scores,
            "routing_reason": f"Matched {scores.get(best_agent, 0)} keywords for {best_agent}"
        }
    
    @staticmethod
    def check_authorization(user_role: str, target_agent: str, query: str) -> tuple[bool, str]:
        """Check if user is authorized for the target agent/query"""
        user_role_upper = user_role.upper()
        
        # HR can access everything
        if user_role_upper == "HR":
            return True, ""
        
        # Employee restrictions
        if user_role_upper == "EMPLOYEE":
            # Check for restricted operations
            restricted_patterns = [
                ('all employees', AgentNames.REPORTING_AGENT),
                ('employee overview', AgentNames.REPORTING_AGENT),
                ('department stats', AgentNames.REPORTING_AGENT),
                ('analytics', AgentNames.ANALYSIS_AGENT),
                ('insights', AgentNames.ANALYSIS_AGENT)
            ]
            
            query_lower = query.lower()
            for pattern, restricted_agent in restricted_patterns:
                if pattern in query_lower and target_agent == restricted_agent:
                    return False, f"Access denied: {pattern} queries are restricted to HR personnel"
        
        return True, ""


# Global supervisor system instance
supervisor_system = None

def get_supervisor_system() -> HRSupervisorSystem:
    """Get or create the global supervisor system instance"""
    global supervisor_system
    if supervisor_system is None:
        supervisor_system = HRSupervisorSystem()
    return supervisor_system

def initialize_supervisor_system() -> HRSupervisorSystem:
    """Initialize the supervisor system"""
    try:
        system = HRSupervisorSystem()
        logger.info("Supervisor system initialized successfully")
        return system
    except Exception as e:
        logger.error(f"Failed to initialize supervisor system: {e}")
        raise