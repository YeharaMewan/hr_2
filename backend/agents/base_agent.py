from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from backend.config.settings import settings
from backend.models.state import HRAgentState, AgentResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class BaseHRAgent(ABC):
    """Base class for all HR agents"""
    
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        tools: List[BaseTool] = None,
        temperature: float = None
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature or settings.GEMINI_TEMPERATURE,
            max_tokens=settings.GEMINI_MAX_TOKENS,
        )
        
        logger.info(f"Initialized {self.name} agent with {len(self.tools)} tools")
    
    @abstractmethod
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get the system prompt for this agent"""
        pass
    
    @abstractmethod
    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Determine if this agent can handle the given task"""
        pass
    
    def create_react_agent(self, handoff_tools: List[BaseTool] = None):
        """Create a ReAct agent with tools and handoff capabilities"""
        all_tools = self.tools.copy()
        if handoff_tools:
            all_tools.extend(handoff_tools)
        
        return create_react_agent(
            model=self.llm,
            tools=all_tools,
            prompt=self.get_system_prompt(),
            name=self.name
        )
    
    def format_response(
        self,
        content: str,
        status: str = "success",
        data: Optional[Dict[str, Any]] = None,
        next_agent: Optional[str] = None,
        reasoning: Optional[str] = None
    ) -> AgentResponse:
        """Format agent response"""
        return AgentResponse(
            agent_name=self.name,
            content=content,
            status=status,
            data=data,
            next_agent=next_agent,
            reasoning=reasoning
        )
    
    def extract_user_context(self, state: HRAgentState) -> Dict[str, Any]:
        """Extract user context from state"""
        return {
            "user_id": state.user_id,
            "user_role": state.user_role,
            "user_name": state.user_name,
            "user_department": state.user_department,
            "is_hr": state.user_role.upper() == "HR",
            "is_employee": state.user_role.upper() == "EMPLOYEE"
        }
    
    def is_authorized(self, state: HRAgentState, required_role: str = None) -> bool:
        """Check if user is authorized for the operation"""
        if not required_role:
            return True
        
        user_role = state.user_role.upper()
        required_role = required_role.upper()
        
        # HR can access everything
        if user_role == "HR":
            return True
        
        # Employees can only access their own data
        if required_role == "EMPLOYEE":
            return user_role == "EMPLOYEE"
        
        # Default deny
        return False
    
    def log_interaction(self, state: HRAgentState, action: str, result: str):
        """Log agent interaction"""
        logger.info(
            f"Agent: {self.name} | User: {state.user_id} | "
            f"Action: {action} | Result: {result[:100]}..."
        )


class AgentRegistry:
    """Registry to manage all agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseHRAgent] = {}
    
    def register(self, agent: BaseHRAgent):
        """Register an agent"""
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def get_agent(self, name: str) -> Optional[BaseHRAgent]:
        """Get agent by name"""
        return self.agents.get(name)
    
    def get_all_agents(self) -> List[BaseHRAgent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def find_suitable_agent(self, task_type: str, user_query: str) -> Optional[BaseHRAgent]:
        """Find the most suitable agent for a task"""
        for agent in self.agents.values():
            if agent.can_handle_task(task_type, user_query):
                return agent
        return None


# Global agent registry
agent_registry = AgentRegistry()