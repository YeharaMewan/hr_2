from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.tools import tool
from backend.agents.base_agent import BaseHRAgent
from backend.models.state import HRAgentState, TaskType
from backend.tools.database_tools import (
    get_employee_by_id, 
    update_employee_leave_balance, 
    add_leave_history
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LeaveAgent(BaseHRAgent):
    """Specialized agent for leave management operations"""
    
    def __init__(self):
        # Define leave-specific tools
        leave_tools = [
            self.check_leave_balance_tool,
            self.apply_for_leave_tool,
            self.get_leave_history_tool,
            self.calculate_leave_entitlement_tool,
            self.check_leave_conflicts_tool
        ]
        
        super().__init__(
            name="leave_agent",
            description="Specialist in leave management, balance checks, applications, and leave policies",
            system_prompt="",
            tools=leave_tools,
            temperature=0.2
        )
    
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get the system prompt for the leave agent"""
        user_info = ""
        if user_context:
            user_info = f"""
Current User Context:
- User ID: {user_context.get('user_id', 'Unknown')}
- User Role: {user_context.get('user_role', 'Unknown')}
- User Name: {user_context.get('user_name', 'Unknown')}
- Department: {user_context.get('user_department', 'Unknown')}
"""
        
        return f"""You are the Leave Management Specialist in the HR multi-agent system.

{user_info}

## Your Expertise:
- Leave balance inquiries and calculations
- Leave applications and approvals
- Leave history tracking
- Leave policy guidance
- Holiday and vacation planning
- Leave entitlement calculations

## Available Tools:
1. **check_leave_balance_tool** - Check current leave balance for any employee
2. **apply_for_leave_tool** - Process leave applications
3. **get_leave_history_tool** - Retrieve leave history records
4. **calculate_leave_entitlement_tool** - Calculate leave entitlements
5. **check_leave_conflicts_tool** - Check for scheduling conflicts

## Authorization Rules:
- **HR Users**: Can check and modify leave data for all employees
- **Employee Users**: Can only access their own leave information
- Always verify user permissions before accessing other employees' data

## Leave Policies:
- Standard annual leave entitlement: 20 days per year
- Leave balance carries forward with approval
- Minimum notice period: 48 hours for regular leave
- Maximum consecutive leave: 10 days without special approval

## Response Guidelines:
- Always provide clear, accurate leave information
- Explain calculations when showing balances
- Inform users of policy requirements
- Suggest optimal leave scheduling when relevant
- Handle leave applications step by step
- Confirm all leave bookings with dates and remaining balance

## Common Scenarios:
1. **"Check my balance"** → Use check_leave_balance_tool with user's ID
2. **"Apply for leave on [dates]"** → Use apply_for_leave_tool with specified dates
3. **"Show my leave history"** → Use get_leave_history_tool for the user
4. **"How many days can I take?"** → Check balance and explain entitlements

Be helpful, accurate, and ensure all leave management follows company policies."""

    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Check if this agent can handle the task"""
        leave_task_types = [
            TaskType.LEAVE_BALANCE,
            TaskType.LEAVE_APPLICATION,
            TaskType.LEAVE_HISTORY
        ]
        
        if task_type in leave_task_types:
            return True
        
        # Check query content for leave-related keywords
        leave_keywords = [
            'leave', 'balance', 'holiday', 'vacation', 'time off', 
            'absence', 'days', 'apply', 'book', 'request'
        ]
        
        return any(keyword in user_query.lower() for keyword in leave_keywords)
    
    @tool
    def check_leave_balance_tool(self, employee_id: str) -> str:
        """Check leave balance for specified employee"""
        try:
            result = get_employee_by_id(employee_id)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            balance = employee_data.get("balance", 0)
            name = employee_data.get("name", "Unknown")
            
            return f"✅ **Leave Balance for {name} ({employee_id})**\n" \
                   f"📊 Current Balance: **{balance} days**\n" \
                   f"📅 Standard Entitlement: 20 days annually"
        
        except Exception as e:
            logger.error(f"Error checking leave balance: {e}")
            return f"❌ Error checking leave balance: {str(e)}"
    
    @tool
    def apply_for_leave_tool(self, employee_id: str, leave_dates: List[str], reason: str = "Personal") -> str:
        """Apply for leave on specified dates"""
        try:
            # Get current employee data
            result = get_employee_by_id(employee_id)
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            current_balance = employee_data.get("balance", 0)
            name = employee_data.get("name", "Unknown")
            
            # Validate dates
            if not leave_dates:
                return "❌ Please specify leave dates"
            
            requested_days = len(leave_dates)
            
            # Check sufficient balance
            if current_balance < requested_days:
                return f"❌ **Insufficient Leave Balance**\n" \
                       f"👤 {name} ({employee_id})\n" \
                       f"📊 Current Balance: {current_balance} days\n" \
                       f"📝 Requested: {requested_days} days\n" \
                       f"⚠️ You need {requested_days - current_balance} more days"
            
            # Process leave application
            new_balance = current_balance - requested_days
            
            # Update balance
            balance_result = update_employee_leave_balance(employee_id, new_balance)
            if not balance_result["success"]:
                return f"❌ Error updating balance: {balance_result['message']}"
            
            # Add to history
            history_result = add_leave_history(employee_id, leave_dates)
            if not history_result["success"]:
                return f"❌ Error updating history: {history_result['message']}"
            
            # Format dates nicely
            formatted_dates = ", ".join(leave_dates)
            
            return f"✅ **Leave Application Approved**\n" \
                   f"👤 {name} ({employee_id})\n" \
                   f"📅 Dates: {formatted_dates}\n" \
                   f"📝 Reason: {reason}\n" \
                   f"📊 Days Used: {requested_days}\n" \
                   f"💰 Remaining Balance: **{new_balance} days**\n\n" \
                   f"🎉 Enjoy your time off!"
        
        except Exception as e:
            logger.error(f"Error applying for leave: {e}")
            return f"❌ Error processing leave application: {str(e)}"
    
    @tool
    def get_leave_history_tool(self, employee_id: str) -> str:
        """Get leave history for specified employee"""
        try:
            result = get_employee_by_id(employee_id)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            name = employee_data.get("name", "Unknown")
            history = employee_data.get("history", [])
            
            if not history:
                return f"📋 **Leave History for {name} ({employee_id})**\n" \
                       f"ℹ️ No leave records found"
            
            # Sort dates and group by year
            sorted_dates = sorted(history, reverse=True)  # Most recent first
            
            response = f"📋 **Leave History for {name} ({employee_id})**\n"
            response += f"📊 Total Days Taken: **{len(history)} days**\n\n"
            
            # Group by year for better presentation
            from collections import defaultdict
            dates_by_year = defaultdict(list)
            
            for date_str in sorted_dates:
                try:
                    year = date_str.split('-')[0]
                    dates_by_year[year].append(date_str)
                except:
                    dates_by_year['Unknown'].append(date_str)
            
            for year in sorted(dates_by_year.keys(), reverse=True):
                response += f"📅 **{year}:**\n"
                for date in dates_by_year[year]:
                    response += f"   • {date}\n"
                response += "\n"
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting leave history: {e}")
            return f"❌ Error retrieving leave history: {str(e)}"
    
    @tool
    def calculate_leave_entitlement_tool(self, employee_id: str) -> str:
        """Calculate leave entitlement for employee"""
        try:
            result = get_employee_by_id(employee_id)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            name = employee_data.get("name", "Unknown")
            current_balance = employee_data.get("balance", 0)
            history = employee_data.get("history", [])
            
            # Standard calculations
            annual_entitlement = 20
            used_this_period = len(history)
            
            return f"📊 **Leave Entitlement for {name} ({employee_id})**\n\n" \
                   f"🎯 Annual Entitlement: {annual_entitlement} days\n" \
                   f"✅ Current Balance: {current_balance} days\n" \
                   f"📝 Used This Period: {used_this_period} days\n" \
                   f"🔄 Theoretical Total: {current_balance + used_this_period} days\n\n" \
                   f"ℹ️ Standard company policy provides 20 days annual leave"
        
        except Exception as e:
            logger.error(f"Error calculating entitlement: {e}")
            return f"❌ Error calculating leave entitlement: {str(e)}"
    
    @tool
    def check_leave_conflicts_tool(self, employee_id: str, proposed_dates: List[str]) -> str:
        """Check for potential leave conflicts"""
        try:
            # This is a simplified conflict checker
            # In a real system, you'd check against team schedules, other bookings, etc.
            
            result = get_employee_by_id(employee_id)
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employee_data = result["data"]
            name = employee_data.get("name", "Unknown")
            existing_history = employee_data.get("history", [])
            
            conflicts = []
            for date in proposed_dates:
                if date in existing_history:
                    conflicts.append(date)
            
            if conflicts:
                return f"⚠️ **Leave Conflicts Detected for {name}**\n\n" \
                       f"The following dates are already booked:\n" + \
                       "\n".join([f"• {date}" for date in conflicts])
            else:
                return f"✅ **No Conflicts Found for {name}**\n\n" \
                       f"All proposed dates are available:\n" + \
                       "\n".join([f"• {date}" for date in proposed_dates])
        
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
            return f"❌ Error checking leave conflicts: {str(e)}"