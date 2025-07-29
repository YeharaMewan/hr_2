from typing import Dict, Any, List
from langchain_core.tools import tool
from backend.agents.base_agent import BaseHRAgent
from backend.models.state import HRAgentState, TaskType
from backend.tools.database_tools import (
    get_all_employees,
    get_department_statistics,
    get_low_balance_employees
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ReportingAgent(BaseHRAgent):
    """Specialized agent for HR reporting, statistics, and organizational overviews"""
    
    def __init__(self):
        # Define reporting-specific tools
        reporting_tools = [
            self.generate_employee_overview_tool,
            self.generate_department_report_tool,
            self.generate_leave_statistics_tool,
            self.generate_low_balance_report_tool,
            self.generate_organizational_summary_tool
        ]
        
        super().__init__(
            name="reporting_agent",
            description="Specialist in HR reporting, statistics, and organizational data analysis",
            system_prompt="",
            tools=reporting_tools,
            temperature=0.1  # Low temperature for consistent reporting
        )
    
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get the system prompt for the reporting agent"""
        user_info = ""
        if user_context:
            user_info = f"""
Current User Context:
- User ID: {user_context.get('user_id', 'Unknown')}
- User Role: {user_context.get('user_role', 'Unknown')}
- User Name: {user_context.get('user_name', 'Unknown')}
- Is HR: {user_context.get('is_hr', False)}
"""
        
        return f"""You are the HR Reporting Specialist in the HR multi-agent system.

{user_info}

## Your Expertise:
- Comprehensive HR reports and statistics
- Organizational overviews and summaries
- Department-wise analysis and breakdowns
- Leave utilization reports
- Employee distribution statistics
- Data-driven insights for HR decision making

## Available Tools:
1. **generate_employee_overview_tool** - Complete organizational employee overview
2. **generate_department_report_tool** - Detailed department-wise reporting
3. **generate_leave_statistics_tool** - Leave utilization and trend analysis
4. **generate_low_balance_report_tool** - Employees with low leave balances
5. **generate_organizational_summary_tool** - High-level organizational metrics

## Authorization:
⚠️ **IMPORTANT**: Reporting tools are primarily for HR personnel
- **HR Users**: Full access to all reports and statistics
- **Employee Users**: Limited access to organizational summaries only
- Always verify authorization before generating detailed reports

## Report Standards:
- Use clear, professional formatting with emojis for visual appeal
- Include relevant metrics and KPIs
- Provide context and insights, not just raw data
- Use tables and structured layouts for complex data
- Always include report generation timestamp
- Highlight key findings and actionable insights

## Report Types:
1. **Employee Overview**: Complete staff listings with key metrics
2. **Department Reports**: Department-specific analysis and statistics
3. **Leave Statistics**: Comprehensive leave utilization analysis
4. **Alert Reports**: Low balance employees and potential issues
5. **Executive Summaries**: High-level organizational metrics

## Response Guidelines:
- Generate professional, well-formatted reports
- Include executive summaries for complex reports
- Use consistent terminology and metrics
- Provide actionable insights and recommendations
- Respect data privacy and access controls
- Format numerical data clearly with appropriate units

Be thorough, accurate, and provide valuable insights that support HR decision-making."""

    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Check if this agent can handle the task"""
        reporting_task_types = [
            TaskType.EMPLOYEE_OVERVIEW,
            TaskType.DEPARTMENT_STATS,
            TaskType.REPORTING
        ]
        
        if task_type in reporting_task_types:
            return True
        
        # Check query content for reporting-related keywords
        reporting_keywords = [
            'report', 'overview', 'statistics', 'stats', 'summary',
            'all employees', 'department', 'organization', 'total',
            'breakdown', 'analysis', 'metrics'
        ]
        
        return any(keyword in user_query.lower() for keyword in reporting_keywords)
    
    @tool
    def generate_employee_overview_tool(self, requester_role: str = "Employee") -> str:
        """Generate comprehensive employee overview report"""
        try:
            # Check authorization
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nEmployee overview reports are restricted to HR personnel only. " \
                       "This is to protect employee privacy and maintain data security.\n\n" \
                       "If you need specific employee information, please contact HR or use the employee search function."
            
            result = get_all_employees()
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            
            # Generate comprehensive overview
            return self._generate_comprehensive_overview(employees)
        
        except Exception as e:
            logger.error(f"Error generating employee overview: {e}")
            return f"❌ Error generating employee overview: {str(e)}"
    
    @tool
    def generate_department_report_tool(self, department: str = "", requester_role: str = "Employee") -> str:
        """Generate detailed department report"""
        try:
            # Check authorization
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nDetailed department reports are restricted to HR personnel only."
            
            if department:
                # Specific department report
                return self._generate_specific_department_report(department)
            else:
                # All departments summary
                return self._generate_all_departments_report()
        
        except Exception as e:
            logger.error(f"Error generating department report: {e}")
            return f"❌ Error generating department report: {str(e)}"
    
    @tool
    def generate_leave_statistics_tool(self, requester_role: str = "Employee") -> str:
        """Generate comprehensive leave statistics report"""
        try:
            # Check authorization
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nLeave statistics reports are restricted to HR personnel only."
            
            result = get_all_employees()
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            
            return self._generate_leave_statistics(employees)
        
        except Exception as e:
            logger.error(f"Error generating leave statistics: {e}")
            return f"❌ Error generating leave statistics: {str(e)}"
    
    @tool
    def generate_low_balance_report_tool(self, threshold: int = 5, requester_role: str = "Employee") -> str:
        """Generate report of employees with low leave balances"""
        try:
            # Check authorization
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nLow balance reports are restricted to HR personnel only."
            
            result = get_low_balance_employees(threshold)
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            
            return self._generate_low_balance_report(employees, threshold)
        
        except Exception as e:
            logger.error(f"Error generating low balance report: {e}")
            return f"❌ Error generating low balance report: {str(e)}"
    
    @tool
    def generate_organizational_summary_tool(self, requester_role: str = "Employee") -> str:
        """Generate high-level organizational summary (accessible to all)"""
        try:
            result = get_all_employees()
            
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            
            # Generate summary based on role
            if requester_role.upper() == "HR":
                return self._generate_detailed_org_summary(employees)
            else:
                return self._generate_basic_org_summary(employees)
        
        except Exception as e:
            logger.error(f"Error generating organizational summary: {e}")
            return f"❌ Error generating organizational summary: {str(e)}"
    
    def _generate_comprehensive_overview(self, employees: List[Dict]) -> str:
        """Generate comprehensive employee overview"""
        from datetime import datetime
        
        # Calculate statistics
        total_employees = len(employees)
        total_leave_balance = sum(emp.get("balance", 0) for emp in employees)
        total_leaves_taken = sum(len(emp.get("history", [])) for emp in employees)
        
        # Department breakdown
        dept_stats = {}
        for emp in employees:
            dept = emp.get("department", "Unknown")
            if dept not in dept_stats:
                dept_stats[dept] = {"count": 0, "balance": 0, "taken": 0}
            dept_stats[dept]["count"] += 1
            dept_stats[dept]["balance"] += emp.get("balance", 0)
            dept_stats[dept]["taken"] += len(emp.get("history", []))
        
        response = "📊 **COMPREHENSIVE EMPLOYEE OVERVIEW REPORT**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Executive Summary
        response += "🎯 **EXECUTIVE SUMMARY**\n"
        response += f"├── Total Employees: **{total_employees}**\n"
        response += f"├── Total Leave Balance: **{total_leave_balance} days**\n"
        response += f"├── Total Leaves Taken: **{total_leaves_taken} days**\n"
        response += f"└── Average Balance per Employee: **{total_leave_balance/total_employees:.1f} days**\n\n"
        
        # Department Summary
        response += "🏢 **DEPARTMENT BREAKDOWN**\n"
        for dept, stats in sorted(dept_stats.items()):
            response += f"├── **{dept}**: {stats['count']} employees\n"
            response += f"│   ├── Total Balance: {stats['balance']} days\n"
            response += f"│   ├── Total Taken: {stats['taken']} days\n"
            response += f"│   └── Avg Balance: {stats['balance']/stats['count']:.1f} days\n"
        response += "\n"
        
        # Employee Listing
        response += "👥 **DETAILED EMPLOYEE LISTING**\n\n"
        
        # Sort employees by department, then by name
        sorted_employees = sorted(employees, key=lambda x: (x.get("department", ""), x.get("name", "")))
        
        current_dept = ""
        for emp in sorted_employees:
            dept = emp.get("department", "Unknown")
            if dept != current_dept:
                current_dept = dept
                response += f"🏢 **{dept.upper()} DEPARTMENT**\n"
            
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            role = emp.get("role", "Unknown")
            balance = emp.get("balance", 0)
            taken = len(emp.get("history", []))
            
            response += f"├── **{name}** ({emp_id})\n"
            response += f"│   ├── Role: {role}\n"
            response += f"│   ├── Leave Balance: {balance} days\n"
            response += f"│   ├── Leaves Taken: {taken} days\n"
            response += f"│   └── Email: {emp_id.lower()}@company.com\n"
        
        return response
    
    def _generate_specific_department_report(self, department: str) -> str:
        """Generate report for specific department"""
        from backend.tools.database_tools import get_employees_by_department
        
        result = get_employees_by_department(department)
        
        if not result["success"]:
            return f"❌ {result['message']}"
        
        employees = result["data"]["employees"]
        
        if not employees:
            return f"📊 **{department.upper()} DEPARTMENT REPORT**\n\n❌ No employees found in this department"
        
        from datetime import datetime
        
        response = f"📊 **{department.upper()} DEPARTMENT REPORT**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Department statistics
        total_employees = len(employees)
        total_balance = sum(emp.get("balance", 0) for emp in employees)
        total_taken = sum(len(emp.get("history", [])) for emp in employees)
        avg_balance = total_balance / total_employees
        avg_taken = total_taken / total_employees
        
        response += "🎯 **DEPARTMENT SUMMARY**\n"
        response += f"├── Total Employees: **{total_employees}**\n"
        response += f"├── Total Leave Balance: **{total_balance} days**\n"
        response += f"├── Average Balance: **{avg_balance:.1f} days**\n"
        response += f"├── Total Leaves Taken: **{total_taken} days**\n"
        response += f"└── Average Taken: **{avg_taken:.1f} days**\n\n"
        
        # Employee details
        response += "👥 **TEAM MEMBERS**\n\n"
        
        sorted_employees = sorted(employees, key=lambda x: x.get("name", ""))
        
        for emp in sorted_employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            role = emp.get("role", "Unknown")
            balance = emp.get("balance", 0)
            taken = len(emp.get("history", []))
            
            response += f"**{name}** ({emp_id})\n"
            response += f"├── Role: {role}\n"
            response += f"├── Leave Balance: {balance} days\n"
            response += f"├── Leaves Taken: {taken} days\n"
            response += f"└── Utilization: {(taken/(taken+balance)*100) if (taken+balance) > 0 else 0:.1f}%\n\n"
        
        return response
    
    def _generate_all_departments_report(self) -> str:
        """Generate summary report for all departments"""
        result = get_department_statistics()
        
        if not result["success"]:
            return f"❌ {result['message']}"
        
        dept_stats = result["data"]["department_stats"]
        
        from datetime import datetime
        
        response = "📊 **ALL DEPARTMENTS SUMMARY REPORT**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        response += "🏢 **DEPARTMENT STATISTICS**\n\n"
        
        for dept in dept_stats:
            dept_name = dept["_id"] or "Unknown"
            count = dept["employee_count"]
            total_balance = dept["total_balance"]
            avg_balance = dept["avg_balance"]
            total_taken = dept["total_leaves_taken"]
            avg_taken = dept["avg_leaves_taken"]
            
            response += f"**{dept_name.upper()} DEPARTMENT**\n"
            response += f"├── Employees: {count}\n"
            response += f"├── Total Balance: {total_balance:.0f} days\n"
            response += f"├── Avg Balance: {avg_balance:.1f} days\n"
            response += f"├── Total Taken: {total_taken:.0f} days\n"
            response += f"└── Avg Taken: {avg_taken:.1f} days\n\n"
        
        return response
    
    def _generate_leave_statistics(self, employees: List[Dict]) -> str:
        """Generate comprehensive leave statistics"""
        from datetime import datetime
        
        response = "📊 **COMPREHENSIVE LEAVE STATISTICS REPORT**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Overall statistics
        total_employees = len(employees)
        total_balance = sum(emp.get("balance", 0) for emp in employees)
        total_taken = sum(len(emp.get("history", [])) for emp in employees)
        avg_balance = total_balance / total_employees if total_employees > 0 else 0
        avg_taken = total_taken / total_employees if total_employees > 0 else 0
        
        response += "🎯 **OVERALL LEAVE STATISTICS**\n"
        response += f"├── Total Employees: {total_employees}\n"
        response += f"├── Total Leave Balance: {total_balance} days\n"
        response += f"├── Average Balance: {avg_balance:.1f} days per employee\n"
        response += f"├── Total Leaves Taken: {total_taken} days\n"
        response += f"├── Average Taken: {avg_taken:.1f} days per employee\n"
        response += f"└── Overall Utilization: {(total_taken/(total_taken+total_balance)*100) if (total_taken+total_balance) > 0 else 0:.1f}%\n\n"
        
        # Balance distribution
        balance_ranges = {"0-5": 0, "6-10": 0, "11-15": 0, "16-20": 0, "20+": 0}
        for emp in employees:
            balance = emp.get("balance", 0)
            if balance <= 5:
                balance_ranges["0-5"] += 1
            elif balance <= 10:
                balance_ranges["6-10"] += 1
            elif balance <= 15:
                balance_ranges["11-15"] += 1
            elif balance <= 20:
                balance_ranges["16-20"] += 1
            else:
                balance_ranges["20+"] += 1
        
        response += "📊 **LEAVE BALANCE DISTRIBUTION**\n"
        for range_name, count in balance_ranges.items():
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            response += f"├── {range_name} days: {count} employees ({percentage:.1f}%)\n"
        response += "\n"
        
        # Top leave takers
        leave_takers = [(emp.get("name", "Unknown"), emp.get("employee_id", "Unknown"), len(emp.get("history", []))) 
                       for emp in employees]
        leave_takers.sort(key=lambda x: x[2], reverse=True)
        
        response += "🔝 **TOP LEAVE UTILIZERS**\n"
        for i, (name, emp_id, taken) in enumerate(leave_takers[:5], 1):
            response += f"{i}. **{name}** ({emp_id}): {taken} days\n"
        response += "\n"
        
        # Low balance alerts
        low_balance = [emp for emp in employees if emp.get("balance", 0) <= 5]
        if low_balance:
            response += "⚠️ **LOW BALANCE ALERTS**\n"
            response += f"**{len(low_balance)} employees** have ≤5 days remaining:\n"
            for emp in low_balance:
                name = emp.get("name", "Unknown")
                emp_id = emp.get("employee_id", "Unknown")
                balance = emp.get("balance", 0)
                response += f"├── **{name}** ({emp_id}): {balance} days\n"
        
        return response
    
    def _generate_low_balance_report(self, employees: List[Dict], threshold: int) -> str:
        """Generate low balance employees report"""
        from datetime import datetime
        
        response = f"⚠️ **LOW LEAVE BALANCE REPORT (≤{threshold} days)**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if not employees:
            response += f"✅ **Good News!**\n\nNo employees currently have leave balance ≤{threshold} days.\n"
            response += "All team members have sufficient leave remaining."
            return response
        
        response += f"🚨 **ALERT: {len(employees)} employees need attention**\n\n"
        
        # Sort by balance (lowest first)
        sorted_employees = sorted(employees, key=lambda x: x.get("balance", 0))
        
        response += "👥 **EMPLOYEES REQUIRING ATTENTION**\n\n"
        
        for emp in sorted_employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            dept = emp.get("department", "Unknown")
            balance = emp.get("balance", 0)
            taken = len(emp.get("history", []))
            
            # Calculate urgency level
            if balance == 0:
                urgency = "🔴 CRITICAL"
            elif balance <= 2:
                urgency = "🟠 HIGH"
            else:
                urgency = "🟡 MEDIUM"
            
            response += f"{urgency} **{name}** ({emp_id})\n"
            response += f"├── Department: {dept}\n"
            response += f"├── Current Balance: **{balance} days**\n"
            response += f"├── Leaves Taken: {taken} days\n"
            response += f"└── Recommended Action: "
            
            if balance == 0:
                response += "Immediate leave refresh needed\n\n"
            elif balance <= 2:
                response += "Schedule leave refresh soon\n\n"
            else:
                response += "Monitor for upcoming refresh\n\n"
        
        # Recommendations
        response += "💡 **RECOMMENDED ACTIONS**\n"
        response += "├── Review annual leave refresh policies\n"
        response += "├── Consider bonus leave allocation\n"
        response += "├── Schedule individual discussions\n"
        response += "└── Monitor leave patterns going forward\n"
        
        return response
    
    def _generate_basic_org_summary(self, employees: List[Dict]) -> str:
        """Generate basic organizational summary for employees"""
        from datetime import datetime
        
        response = "🏢 **ORGANIZATIONAL SUMMARY**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Basic metrics only
        total_employees = len(employees)
        
        # Department breakdown
        dept_breakdown = {}
        for emp in employees:
            dept = emp.get("department", "Unknown")
            if dept not in dept_breakdown:
                dept_breakdown[dept] = 0
            dept_breakdown[dept] += 1
        
        response += "📊 **COMPANY OVERVIEW**\n"
        response += f"├── Total Employees: **{total_employees}**\n"
        response += f"└── Departments: **{len(dept_breakdown)}**\n\n"
        
        response += "🏢 **DEPARTMENT BREAKDOWN**\n"
        for dept, count in sorted(dept_breakdown.items()):
            response += f"├── {dept}: {count} employees\n"
        response += "\n"
        
        response += "ℹ️ For detailed statistics and reports, please contact HR."
        
        return response
    

    def _generate_low_balance_report(self, employees: List[Dict], threshold: int) -> str:
        """Generate low balance employees report"""
        from datetime import datetime
        
        response = f"⚠️ **LOW LEAVE BALANCE REPORT (≤{threshold} days)**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if not employees:
            response += f"✅ **Good News!**\n\nNo employees currently have leave balance ≤{threshold} days.\n"
            response += "All team members have sufficient leave remaining."
            return response
        
        response += f"🚨 **ALERT: {len(employees)} employees need attention**\n\n"
        
        # Sort by balance (lowest first)
        sorted_employees = sorted(employees, key=lambda x: x.get("balance", 0))
        
        response += "👥 **EMPLOYEES REQUIRING ATTENTION**\n\n"
        
        for emp in sorted_employees:
            name = emp.get("name", "Unknown")
            emp_id = emp.get("employee_id", "Unknown")
            dept = emp.get("department", "Unknown")
            balance = emp.get("balance", 0)
            taken = len(emp.get("history", []))
            
            # Calculate urgency level
            if balance == 0:
                urgency = "🔴 CRITICAL"
            elif balance <= 2:
                urgency = "🟠 HIGH"
            else:
                urgency = "🟡 MEDIUM"
            
            response += f"{urgency} **{name}** ({emp_id})\n"
            response += f"├── Department: {dept}\n"
            response += f"├── Current Balance: **{balance} days**\n"
            response += f"├── Leaves Taken: {taken} days\n"
            response += f"└── Recommended Action: "
            
            if balance == 0:
                response += "Immediate leave refresh needed\n\n"
            elif balance <= 2:
                response += "Schedule leave refresh soon\n\n"
            else:
                response += "Monitor for upcoming refresh\n\n"
        
        # Recommendations
        response += "💡 **RECOMMENDED ACTIONS**\n"
        response += "├── Review annual leave refresh policies\n"
        response += "├── Consider bonus leave allocation\n"
        response += "├── Schedule individual discussions\n"
        response += "└── Monitor leave patterns going forward\n"
        
        return response

    def _generate_detailed_org_summary(self, employees: List[Dict]) -> str:
        """Generate detailed organizational summary for HR"""
        from datetime import datetime
        
        response = "🏢 **ORGANIZATIONAL SUMMARY - DETAILED VIEW**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Key metrics
        total_employees = len(employees)
        total_balance = sum(emp.get("balance", 0) for emp in employees)
        total_taken = sum(len(emp.get("history", [])) for emp in employees)
        
        # Department breakdown
        dept_breakdown = {}
        dept_balance = {}
        dept_taken = {}
        role_breakdown = {}
        
        for emp in employees:
            dept = emp.get("department", "Unknown")
            role = emp.get("role", "Unknown")
            balance = emp.get("balance", 0)
            taken = len(emp.get("history", []))
            
            # Department statistics
            if dept not in dept_breakdown:
                dept_breakdown[dept] = 0
                dept_balance[dept] = 0
                dept_taken[dept] = 0
            dept_breakdown[dept] += 1
            dept_balance[dept] += balance
            dept_taken[dept] += taken
            
            # Role statistics
            if role not in role_breakdown:
                role_breakdown[role] = 0
            role_breakdown[role] += 1
        
        # Calculate averages
        avg_balance = total_balance / total_employees if total_employees > 0 else 0
        avg_taken = total_taken / total_employees if total_employees > 0 else 0
        
        response += "📊 **KEY METRICS**\n"
        response += f"├── Total Workforce: **{total_employees} employees**\n"
        response += f"├── Total Leave Balance: **{total_balance} days**\n"
        response += f"├── Total Leaves Utilized: **{total_taken} days**\n"
        response += f"├── Average Balance per Employee: **{avg_balance:.1f} days**\n"
        response += f"├── Average Leaves Taken: **{avg_taken:.1f} days**\n"
        response += f"├── Overall Utilization Rate: **{(total_taken/(total_taken+total_balance)*100) if (total_taken+total_balance) > 0 else 0:.1f}%**\n"
        response += f"└── Departments: **{len(dept_breakdown)}**\n\n"
        
        response += "👔 **ROLE DISTRIBUTION**\n"
        for role, count in sorted(role_breakdown.items()):
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            response += f"├── {role}: **{count} employees** ({percentage:.1f}%)\n"
        response += "\n"
        
        response += "🏢 **DEPARTMENT ANALYSIS**\n"
        # Sort departments by employee count
        sorted_depts = sorted(dept_breakdown.items(), key=lambda x: x[1], reverse=True)
        
        for dept, count in sorted_depts:
            dept_avg_balance = dept_balance[dept] / count if count > 0 else 0
            dept_avg_taken = dept_taken[dept] / count if count > 0 else 0
            dept_utilization = (dept_taken[dept] / (dept_taken[dept] + dept_balance[dept]) * 100) if (dept_taken[dept] + dept_balance[dept]) > 0 else 0
            
            response += f"**{dept.upper()} DEPARTMENT**\n"
            response += f"├── Employees: **{count}** ({count/total_employees*100:.1f}% of workforce)\n"
            response += f"├── Total Leave Balance: **{dept_balance[dept]} days**\n"
            response += f"├── Average Balance: **{dept_avg_balance:.1f} days**\n"
            response += f"├── Total Leaves Taken: **{dept_taken[dept]} days**\n"
            response += f"├── Average Taken: **{dept_avg_taken:.1f} days**\n"
            response += f"└── Utilization Rate: **{dept_utilization:.1f}%**\n\n"
        
        # Leave balance distribution analysis
        balance_ranges = {"0-5": 0, "6-10": 0, "11-15": 0, "16-20": 0, "20+": 0}
        for emp in employees:
            balance = emp.get("balance", 0)
            if balance <= 5:
                balance_ranges["0-5"] += 1
            elif balance <= 10:
                balance_ranges["6-10"] += 1
            elif balance <= 15:
                balance_ranges["11-15"] += 1
            elif balance <= 20:
                balance_ranges["16-20"] += 1
            else:
                balance_ranges["20+"] += 1
        
        response += "📊 **LEAVE BALANCE DISTRIBUTION**\n"
        for range_name, count in balance_ranges.items():
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            response += f"├── {range_name} days: **{count} employees** ({percentage:.1f}%)\n"
        response += "\n"
        
        # Key insights and alerts
        response += "🔍 **KEY INSIGHTS & ALERTS**\n"
        
        # Low balance alerts
        low_balance_employees = [emp for emp in employees if emp.get("balance", 0) <= 5]
        if low_balance_employees:
            response += f"├── ⚠️ **{len(low_balance_employees)} employees** have critical low balance (≤5 days)\n"
        else:
            response += f"├── ✅ No employees with critically low balance\n"
        
        # High balance analysis
        high_balance_employees = [emp for emp in employees if emp.get("balance", 0) > 18]
        if high_balance_employees:
            response += f"├── 📈 **{len(high_balance_employees)} employees** have high unused balance (>18 days)\n"
        
        # Department with lowest utilization
        if sorted_depts:
            dept_utilizations = []
            for dept, count in dept_breakdown.items():
                if count > 1:  # Only consider departments with more than 1 employee
                    util_rate = (dept_taken[dept] / (dept_taken[dept] + dept_balance[dept]) * 100) if (dept_taken[dept] + dept_balance[dept]) > 0 else 0
                    dept_utilizations.append((dept, util_rate))
            
            if dept_utilizations:
                dept_utilizations.sort(key=lambda x: x[1])
                lowest_util_dept, lowest_util_rate = dept_utilizations[0]
                highest_util_dept, highest_util_rate = dept_utilizations[-1]
                
                response += f"├── 📉 Lowest utilization: **{lowest_util_dept}** ({lowest_util_rate:.1f}%)\n"
                response += f"├── 📈 Highest utilization: **{highest_util_dept}** ({highest_util_rate:.1f}%)\n"
        
        # Overall health assessment
        if avg_balance < 8:
            response += f"└── 🚨 **Action Required**: Organization-wide leave refresh needed\n"
        elif avg_balance > 18:
            response += f"└── 📋 **Recommendation**: Encourage leave utilization to improve work-life balance\n"
        else:
            response += f"└── ✅ **Status**: Healthy leave balance across organization\n"
        
        response += "\n"
        
        # Summary recommendations
        response += "💡 **STRATEGIC RECOMMENDATIONS**\n"
        
        if len(low_balance_employees) > total_employees * 0.15:  # More than 15% have low balance
            response += "├── 🔴 **High Priority**: Immediate leave refresh for low-balance employees\n"
        
        if len(high_balance_employees) > total_employees * 0.25:  # More than 25% have high balance
            response += "├── 🟡 **Medium Priority**: Launch campaign to encourage leave utilization\n"
        
        # Department-specific recommendations
        if dept_utilizations:
            low_util_depts = [dept for dept, util in dept_utilizations if util < 30]
            if low_util_depts:
                response += f"├── 📊 **Focus Areas**: Review leave policies in {', '.join(low_util_depts)}\n"
        
        response += "└── 📈 **Monitor**: Regular review of leave patterns and employee wellbeing\n"
        
        return response