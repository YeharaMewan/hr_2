from typing import Dict, Any, List
from langchain_core.tools import tool
from backend.agents.base_agent import BaseHRAgent
from backend.models.state import HRAgentState, TaskType
from backend.tools.database_tools import (
    get_employee_by_id,
    get_all_employees,
    get_employees_by_department
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EmployeeAgent(BaseHRAgent):
    """Specialized agent for employee data management and searches"""
    
    def __init__(self):
        # Define employee-specific tools
        employee_tools = [
            self.get_employee_details_tool,
            self.search_employees_tool,
            self.get_department_employees_tool,
            self.get_employee_contact_info_tool,
            self.validate_employee_id_tool
        ]
        
        super().__init__(
            name="employee_agent",
            description="Specialist in employee data management, searches, and profile information",
            system_prompt="",
            tools=employee_tools,
            temperature=0.2
        )
    
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get the system prompt for the employee agent"""
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
        
        return f"""You are the Employee Data Management Specialist in the HR multi-agent system.

{user_info}

## Your Expertise:
- Employee profile management and searches
- Employee contact information and details
- Department-based employee queries
- Employee ID validation and lookup
- Staff directory management
- Employee data verification

## Available Tools:
1. **get_employee_details_tool** - Get comprehensive employee information
2. **search_employees_tool** - Search for employees by name or criteria
3. **get_department_employees_tool** - Get all employees in a specific department
4. **get_employee_contact_info_tool** - Get contact details for employees
5. **validate_employee_id_tool** - Validate and verify employee IDs

## Authorization Rules:
- **HR Users**: Can access detailed information for all employees
- **Employee Users**: Can access basic information but NOT sensitive data of other employees
- Always respect privacy and data protection policies
- Only provide information that users are authorized to see

## Privacy Guidelines:
- For non-HR users, limit information to: Name, Department, Employee ID
- Never expose passwords or sensitive personal data
- HR users can access full profiles including contact details
- Always explain access limitations when applicable

## Response Guidelines:
- Provide clear, well-formatted employee information
- Use professional language and proper formatting
- Explain any access restrictions politely
- Suggest alternatives when access is denied
- Format employee lists in an easy-to-read manner
- Include relevant context like department and role when available

## Common Scenarios:
1. **"Find employee John"** → Use search_employees_tool with name "John"
2. **"Who works in IT?"** → Use get_department_employees_tool with "IT"
3. **"Get my details"** → Use get_employee_details_tool with user's ID
4. **"Is E001 valid?"** → Use validate_employee_id_tool with "E001"

Be helpful while maintaining appropriate privacy boundaries and data security."""

    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Check if this agent can handle the task"""
        employee_task_types = [
            TaskType.EMPLOYEE_SEARCH,
            TaskType.GENERAL_QUERY
        ]
        
        if task_type in employee_task_types:
            return True
        
        # Check query content for employee-related keywords
        employee_keywords = [
            'employee', 'staff', 'person', 'who', 'find', 'search',
            'profile', 'details', 'information', 'contact', 'colleague'
        ]
        
        return any(keyword in user_query.lower() for keyword in employee_keywords)
    
    @tool
    def get_employee_details_tool(self, employee_id: str, requester_role: str = "Employee") -> str:
        """Get detailed employee information with role-based access control"""
        try:
            result = get_employee_by_id(employee_id)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            
            # Format response based on requester role
            if requester_role.upper() == "HR":
                return self._format_full_employee_details(employee_data)
            else:
                return self._format_basic_employee_details(employee_data)
        
        except Exception as e:
            logger.error(f"Error getting employee details: {e}")
            return f"❌ Error retrieving employee details: {str(e)}"
    
    @tool
    def search_employees_tool(self, search_term: str, requester_role: str = "Employee") -> str:
        """Search for employees by name or other criteria"""
        try:
            # Get all employees
            result = get_all_employees()
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            search_term_lower = search_term.lower()
            
            # Search in name, employee_id, and department
            matches = []
            for emp in employees:
                if (search_term_lower in emp.get("name", "").lower() or
                    search_term_lower in emp.get("employee_id", "").lower() or
                    search_term_lower in emp.get("department", "").lower()):
                    matches.append(emp)
            
            if not matches:
                return f"🔍 **Search Results for '{search_term}'**\n" \
                       f"❌ No employees found matching your search criteria"
            
            # Format results based on role
            if requester_role.upper() == "HR":
                return self._format_employee_search_results_hr(matches, search_term)
            else:
                return self._format_employee_search_results_basic(matches, search_term)
        
        except Exception as e:
            logger.error(f"Error searching employees: {e}")
            return f"❌ Error searching employees: {str(e)}"
    
    @tool
    def get_department_employees_tool(self, department: str, requester_role: str = "Employee") -> str:
        """Get all employees in a specific department"""
        try:
            result = get_employees_by_department(department)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            
            if not employees:
                return f"🏢 **{department.title()} Department**\n" \
                       f"❌ No employees found in this department"
            
            # Format results based on role
            if requester_role.upper() == "HR":
                return self._format_department_employees_hr(employees, department)
            else:
                return self._format_department_employees_basic(employees, department)
        
        except Exception as e:
            logger.error(f"Error getting department employees: {e}")
            return f"❌ Error retrieving department employees: {str(e)}"
    
    @tool
    def get_employee_contact_info_tool(self, employee_id: str, requester_role: str = "Employee") -> str:
        """Get employee contact information (HR only for detailed info)"""
        try:
            result = get_employee_by_id(employee_id)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            name = employee_data.get("name", "Unknown")
            dept = employee_data.get("department", "Unknown")
            
            if requester_role.upper() == "HR":
                # HR gets full contact details (would need to add these fields to DB)
                return f"📞 **Contact Information for {name} ({employee_id})**\n\n" \
                       f"👤 Name: {name}\n" \
                       f"🏢 Department: {dept}\n" \
                       f"🆔 Employee ID: {employee_id}\n" \
                       f"📧 Email: {employee_id.lower()}@company.com\n" \
                       f"📱 Phone: [Contact HR for details]\n\n" \
                       f"ℹ️ Additional contact details available in HR system"
            else:
                # Regular employees get basic info
                return f"📞 **Contact Information for {name}**\n\n" \
                       f"👤 Name: {name}\n" \
                       f"🏢 Department: {dept}\n" \
                       f"🆔 Employee ID: {employee_id}\n" \
                       f"📧 Email: {employee_id.lower()}@company.com\n\n" \
                       f"ℹ️ For additional contact details, please contact HR"
        
        except Exception as e:
            logger.error(f"Error getting contact info: {e}")
            return f"❌ Error retrieving contact information: {str(e)}"
    
    @tool
    def validate_employee_id_tool(self, employee_id: str) -> str:
        """Validate if an employee ID exists in the system"""
        try:
            result = get_employee_by_id(employee_id)
            
            if result["success"]:
                employee_data = result["data"]
                name = employee_data.get("name", "Unknown")
                dept = employee_data.get("department", "Unknown")
                
                return f"✅ **Employee ID Validation**\n\n" \
                       f"🆔 ID: {employee_id} is **VALID**\n" \
                       f"👤 Name: {name}\n" \
                       f"🏢 Department: {dept}"
            else:
                return f"❌ **Employee ID Validation**\n\n" \
                       f"🆔 ID: {employee_id} is **INVALID**\n" \
                       f"⚠️ This employee ID does not exist in the system"
        
        except Exception as e:
            logger.error(f"Error validating employee ID: {e}")
            return f"❌ Error validating employee ID: {str(e)}"
    
    def _format_full_employee_details(self, employee_data: Dict[str, Any]) -> str:
        """Format full employee details for HR users"""
        name = employee_data.get("name", "Unknown")
        emp_id = employee_data.get("employee_id", "Unknown")
        dept = employee_data.get("department", "Unknown")
        role = employee_data.get("role", "Unknown")
        balance = employee_data.get("balance", 0)
        history = employee_data.get("history", [])
        
        response = f"👤 **Complete Employee Profile - {name}**\n\n"
        response += f"🆔 **Employee ID:** {emp_id}\n"
        response += f"🏢 **Department:** {dept}\n"
        response += f"👔 **Role:** {role}\n"
        response += f"💰 **Leave Balance:** {balance} days\n"
        response += f"📊 **Total Leaves Taken:** {len(history)} days\n"
        response += f"📧 **Email:** {emp_id.lower()}@company.com\n"
        response += f"📱 **Phone:** [Available in HR system]\n\n"
        
        if history:
            response += f"📋 **Recent Leave History:**\n"
            recent_leaves = sorted(history, reverse=True)[:5]  # Last 5 leaves
            for leave_date in recent_leaves:
                response += f"   • {leave_date}\n"
        else:
            response += f"📋 **Leave History:** No leaves taken\n"
        
        return response
    
    def _format_basic_employee_details(self, employee_data: Dict[str, Any]) -> str:
        """Format basic employee details for regular users"""
        name = employee_data.get("name", "Unknown")
        emp_id = employee_data.get("employee_id", "Unknown")
        dept = employee_data.get("department", "Unknown")
        
        return f"👤 **Employee Information - {name}**\n\n" \
               f"🆔 **Employee ID:** {emp_id}\n" \
               f"🏢 **Department:** {dept}\n" \
               f"📧 **Email:** {emp_id.lower()}@company.com\n\n" \
               f"ℹ️ For additional details, please contact HR"
    
    def _format_employee_search_results_hr(self, employees: List[Dict], search_term: str) -> str:
        """Format search results for HR users"""
        response = f"🔍 **Search Results for '{search_term}' - {len(employees)} found**\n\n"
        
        for emp in employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            dept = emp.get("department", "Unknown")
            role = emp.get("role", "Unknown")
            balance = emp.get("balance", 0)
            
            response += f"👤 **{name}** ({emp_id})\n"
            response += f"   🏢 Department: {dept}\n"
            response += f"   👔 Role: {role}\n"
            response += f"   💰 Leave Balance: {balance} days\n"
            response += f"   📧 Email: {emp_id.lower()}@company.com\n\n"
        
        return response
    
    def _format_employee_search_results_basic(self, employees: List[Dict], search_term: str) -> str:
        """Format search results for regular users"""
        response = f"🔍 **Search Results for '{search_term}' - {len(employees)} found**\n\n"
        
        for emp in employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            dept = emp.get("department", "Unknown")
            
            response += f"👤 **{name}** ({emp_id})\n"
            response += f"   🏢 Department: {dept}\n"
            response += f"   📧 Email: {emp_id.lower()}@company.com\n\n"
        
        return response
    
    def _format_department_employees_hr(self, employees: List[Dict], department: str) -> str:
        """Format department employees for HR users"""
        response = f"🏢 **{department.title()} Department - {len(employees)} employees**\n\n"
        
        # Sort by name
        sorted_employees = sorted(employees, key=lambda x: x.get("name", ""))
        
        for emp in sorted_employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            role = emp.get("role", "Unknown")
            balance = emp.get("balance", 0)
            
            response += f"👤 **{name}** ({emp_id})\n"
            response += f"   👔 Role: {role}\n"
            response += f"   💰 Leave Balance: {balance} days\n"
            response += f"   📧 Email: {emp_id.lower()}@company.com\n\n"
        
        return response
    
    def _format_department_employees_basic(self, employees: List[Dict], department: str) -> str:
        """Format department employees for regular users"""
        response = f"🏢 **{department.title()} Department - {len(employees)} employees**\n\n"
        
        # Sort by name
        sorted_employees = sorted(employees, key=lambda x: x.get("name", ""))
        
        for emp in sorted_employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            
            response += f"👤 **{name}** ({emp_id})\n"
            response += f"   📧 Email: {emp_id.lower()}@company.com\n\n"
        
        return response