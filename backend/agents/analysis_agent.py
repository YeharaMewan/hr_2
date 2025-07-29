from typing import Dict, Any, List, Tuple
from langchain_core.tools import tool
from backend.agents.base_agent import BaseHRAgent
from backend.models.state import HRAgentState, TaskType
from backend.tools.database_tools import get_all_employees, get_department_statistics
from backend.utils.logger import get_logger
import statistics
from collections import defaultdict, Counter

logger = get_logger(__name__)


class AnalysisAgent(BaseHRAgent):
    """Specialized agent for HR analytics, insights, and predictive analysis"""
    
    def __init__(self):
        # Define analysis-specific tools
        analysis_tools = [
            self.analyze_leave_trends_tool,
            self.analyze_department_patterns_tool,
            self.generate_predictive_insights_tool,
            self.analyze_leave_utilization_tool,
            self.identify_outliers_tool,
            self.generate_recommendations_tool
        ]
        
        super().__init__(
            name="analysis_agent",
            description="Specialist in HR analytics, data insights, and predictive analysis",
            system_prompt="",
            tools=analysis_tools,
            temperature=0.3  # Slightly higher for creative insights
        )
    
    def get_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Get the system prompt for the analysis agent"""
        user_info = ""
        if user_context:
            user_info = f"""
Current User Context:
- User ID: {user_context.get('user_id', 'Unknown')}
- User Role: {user_context.get('user_role', 'Unknown')}
- Is HR: {user_context.get('is_hr', False)}
"""
        
        return f"""You are the HR Analytics Specialist in the HR multi-agent system.

{user_info}

## Your Expertise:
- Advanced data analysis and statistical insights
- Leave pattern analysis and trend identification
- Predictive analytics for workforce planning
- Department-wise comparative analysis
- Outlier detection and anomaly identification
- Data-driven recommendations for HR strategy

## Available Tools:
1. **analyze_leave_trends_tool** - Identify trends in leave utilization
2. **analyze_department_patterns_tool** - Compare department-wise patterns
3. **generate_predictive_insights_tool** - Forecast future trends
4. **analyze_leave_utilization_tool** - Deep dive into leave usage patterns
5. **identify_outliers_tool** - Find unusual patterns or anomalies
6. **generate_recommendations_tool** - Provide actionable insights

## Authorization:
⚠️ **IMPORTANT**: Analytics are primarily for HR strategic planning
- **HR Users**: Full access to all analytics and insights
- **Employee Users**: Limited access to general trends only
- Detailed analytics may contain sensitive organizational data

## Analysis Standards:
- Use statistical methods and data science principles
- Provide clear visualizations and explanations
- Include confidence levels and data quality notes
- Offer actionable insights, not just observations
- Consider business context in all recommendations
- Highlight significant findings and correlations

## Analytical Approaches:
1. **Descriptive Analytics**: What happened? (Historical data analysis)
2. **Diagnostic Analytics**: Why did it happen? (Root cause analysis)
3. **Predictive Analytics**: What might happen? (Forecasting)
4. **Prescriptive Analytics**: What should we do? (Recommendations)

## Key Metrics:
- Leave utilization rates and patterns
- Department performance comparisons
- Seasonal trends and cyclical patterns
- Employee engagement indicators
- Workforce optimization opportunities

## Response Guidelines:
- Present insights clearly with supporting data
- Use charts, graphs, and visual aids when possible
- Explain methodology and assumptions
- Provide confidence intervals for predictions
- Include actionable recommendations
- Consider business impact of insights

Transform raw HR data into strategic insights that drive organizational success."""

    def can_handle_task(self, task_type: str, user_query: str) -> bool:
        """Check if this agent can handle the task"""
        if task_type == TaskType.ANALYTICS:
            return True
        
        # Check query content for analytics-related keywords
        analytics_keywords = [
            'trend', 'analysis', 'insight', 'pattern', 'analytics',
            'forecast', 'prediction', 'compare', 'most', 'least',
            'correlation', 'statistics', 'benchmark', 'optimization'
        ]
        
        return any(keyword in user_query.lower() for keyword in analytics_keywords)
    
    @tool
    def analyze_leave_trends_tool(self, requester_role: str = "Employee") -> str:
        """Analyze leave utilization trends across the organization"""
        try:
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nDetailed analytics are restricted to HR personnel only."
            
            result = get_all_employees()
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            return self._analyze_leave_trends(employees)
        
        except Exception as e:
            logger.error(f"Error analyzing leave trends: {e}")
            return f"❌ Error analyzing leave trends: {str(e)}"
    
    @tool
    def analyze_department_patterns_tool(self, requester_role: str = "Employee") -> str:
        """Analyze patterns and differences between departments"""
        try:
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nDepartment analytics are restricted to HR personnel only."
            
            result = get_department_statistics()
            if not result["success"]:
                return f"❌ {result['message']}"
            
            dept_stats = result["data"]["department_stats"]
            return self._analyze_department_patterns(dept_stats)
        
        except Exception as e:
            logger.error(f"Error analyzing department patterns: {e}")
            return f"❌ Error analyzing department patterns: {str(e)}"
    
    @tool
    def generate_predictive_insights_tool(self, requester_role: str = "Employee") -> str:
        """Generate predictive insights and forecasts"""
        try:
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nPredictive analytics are restricted to HR personnel only."
            
            result = get_all_employees()
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            return self._generate_predictive_insights(employees)
        
        except Exception as e:
            logger.error(f"Error generating predictive insights: {e}")
            return f"❌ Error generating predictive insights: {str(e)}"
    
    @tool
    def analyze_leave_utilization_tool(self, requester_role: str = "Employee") -> str:
        """Deep analysis of leave utilization patterns"""
        try:
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nUtilization analytics are restricted to HR personnel only."
            
            result = get_all_employees()
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            return self._analyze_utilization_patterns(employees)
        
        except Exception as e:
            logger.error(f"Error analyzing utilization: {e}")
            return f"❌ Error analyzing leave utilization: {str(e)}"
    
    @tool
    def identify_outliers_tool(self, requester_role: str = "Employee") -> str:
        """Identify statistical outliers and anomalies"""
        try:
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nOutlier analysis is restricted to HR personnel only."
            
            result = get_all_employees()
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            return self._identify_outliers(employees)
        
        except Exception as e:
            logger.error(f"Error identifying outliers: {e}")
            return f"❌ Error identifying outliers: {str(e)}"
    
    @tool
    def generate_recommendations_tool(self, focus_area: str = "general", requester_role: str = "Employee") -> str:
        """Generate strategic recommendations based on analysis"""
        try:
            if requester_role.upper() != "HR":
                return "❌ **Access Denied**\n\nStrategic recommendations are restricted to HR personnel only."
            
            result = get_all_employees()
            if not result["success"]:
                return f"❌ {result['message']}"
            
            employees = result["data"]["employees"]
            return self._generate_recommendations(employees, focus_area)
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return f"❌ Error generating recommendations: {str(e)}"
    
    def _analyze_leave_trends(self, employees: List[Dict]) -> str:
        """Analyze leave trends and patterns"""
        from datetime import datetime
        
        response = "📈 **LEAVE TRENDS ANALYSIS**\n"
        response += f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Calculate key metrics
        balances = [emp.get("balance", 0) for emp in employees]
        leaves_taken = [len(emp.get("history", [])) for emp in employees]
        
        if not balances:
            return response + "❌ No data available for analysis"
        
        # Statistical analysis
        avg_balance = statistics.mean(balances)
        median_balance = statistics.median(balances)
        balance_std = statistics.stdev(balances) if len(balances) > 1 else 0
        
        avg_taken = statistics.mean(leaves_taken)
        median_taken = statistics.median(leaves_taken)
        
        response += "📊 **STATISTICAL OVERVIEW**\n"
        response += f"├── Average Balance: {avg_balance:.1f} days\n"
        response += f"├── Median Balance: {median_balance:.1f} days\n"
        response += f"├── Balance Std Dev: {balance_std:.1f} days\n"
        response += f"├── Average Taken: {avg_taken:.1f} days\n"
        response += f"└── Median Taken: {median_taken:.1f} days\n\n"
        
        # Distribution analysis
        balance_ranges = self._calculate_distribution(balances)
        response += "📊 **BALANCE DISTRIBUTION TRENDS**\n"
        for range_name, percentage in balance_ranges.items():
            response += f"├── {range_name}: {percentage:.1f}%\n"
        response += "\n"
        
        # Trend insights
        response += "🔍 **KEY INSIGHTS**\n"
        
        # High/Low balance insights
        if avg_balance > 15:
            response += "├── ✅ Healthy leave balances across organization\n"
        elif avg_balance < 10:
            response += "├── ⚠️ Generally low leave balances - consider refresh\n"
        else:
            response += "├── 📊 Moderate leave balances - monitor trends\n"
        
        # Utilization insights
        utilization_rate = (avg_taken / (avg_taken + avg_balance)) * 100
        if utilization_rate > 60:
            response += "├── 📈 High leave utilization - good work-life balance\n"
        elif utilization_rate < 30:
            response += "├── 📉 Low leave utilization - employees may need encouragement\n"
        else:
            response += "├── ⚖️ Balanced leave utilization patterns\n"
        
        # Variance insights
        if balance_std > 5:
            response += "└── 📊 High variance in balances - investigate disparities\n"
        else:
            response += "└── ✅ Consistent balance distribution across team\n"
        
        return response
    
    def _analyze_department_patterns(self, dept_stats: List[Dict]) -> str:
        """Analyze patterns between departments"""
        from datetime import datetime
        
        response = "🏢 **DEPARTMENT PATTERN ANALYSIS**\n"
        response += f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if not dept_stats:
            return response + "❌ No department data available for analysis"
        
        # Extract metrics
        dept_data = []
        for dept in dept_stats:
            dept_data.append({
                'name': dept['_id'] or 'Unknown',
                'employees': dept['employee_count'],
                'avg_balance': dept['avg_balance'],
                'avg_taken': dept['avg_leaves_taken'],
                'total_balance': dept['total_balance']
            })
        
        # Sort by various metrics
        by_size = sorted(dept_data, key=lambda x: x['employees'], reverse=True)
        by_balance = sorted(dept_data, key=lambda x: x['avg_balance'], reverse=True)
        by_utilization = sorted(dept_data, key=lambda x: x['avg_taken'], reverse=True)
        
        response += "📊 **DEPARTMENT RANKINGS**\n\n"
        
        response += "👥 **By Team Size:**\n"
        for i, dept in enumerate(by_size[:3], 1):
            response += f"{i}. {dept['name']}: {dept['employees']} employees\n"
        response += "\n"
        
        response += "💰 **By Average Leave Balance:**\n"
        for i, dept in enumerate(by_balance[:3], 1):
            response += f"{i}. {dept['name']}: {dept['avg_balance']:.1f} days\n"
        response += "\n"
        
        response += "📈 **By Leave Utilization:**\n"
        for i, dept in enumerate(by_utilization[:3], 1):
            response += f"{i}. {dept['name']}: {dept['avg_taken']:.1f} days\n"
        response += "\n"
        
        # Comparative insights
        response += "🔍 **COMPARATIVE INSIGHTS**\n"
        
        # Find departments with significant differences
        avg_balances = [d['avg_balance'] for d in dept_data]
        overall_avg = statistics.mean(avg_balances)
        
        high_balance_depts = [d for d in dept_data if d['avg_balance'] > overall_avg + 3]
        low_balance_depts = [d for d in dept_data if d['avg_balance'] < overall_avg - 3]
        
        if high_balance_depts:
            response += f"├── 📈 High Balance Departments: {', '.join([d['name'] for d in high_balance_depts])}\n"
        
        if low_balance_depts:
            response += f"├── 📉 Low Balance Departments: {', '.join([d['name'] for d in low_balance_depts])}\n"
        
        # Utilization patterns
        avg_utilizations = [d['avg_taken'] for d in dept_data]
        util_avg = statistics.mean(avg_utilizations)
        
        high_util_depts = [d for d in dept_data if d['avg_taken'] > util_avg + 2]
        if high_util_depts:
            response += f"└── 🎯 High Utilization: {', '.join([d['name'] for d in high_util_depts])}\n"
        
        return response
    
    def _generate_predictive_insights(self, employees: List[Dict]) -> str:
        """Generate predictive insights and forecasts"""
        from datetime import datetime, timedelta
        
        response = "🔮 **PREDICTIVE INSIGHTS & FORECASTS**\n"
        response += f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Current metrics
        current_total_balance = sum(emp.get("balance", 0) for emp in employees)
        current_avg_balance = current_total_balance / len(employees) if employees else 0
        total_taken = sum(len(emp.get("history", [])) for emp in employees)
        
        response += "📊 **CURRENT STATE**\n"
        response += f"├── Total Leave Balance: {current_total_balance} days\n"
        response += f"├── Average Balance: {current_avg_balance:.1f} days\n"
        response += f"└── Total Utilized: {total_taken} days\n\n"
        
        # Predictive scenarios
        response += "🔮 **PREDICTIVE SCENARIOS (Next 6 Months)**\n\n"
        
        # Scenario 1: Current utilization rate continues
        current_util_rate = total_taken / (total_taken + current_total_balance) if (total_taken + current_total_balance) > 0 else 0
        projected_usage = current_total_balance * current_util_rate * 0.5  # 6 months
        
        response += "📈 **Scenario 1: Current Trends Continue**\n"
        response += f"├── Projected Usage: {projected_usage:.0f} days\n"
        response += f"├── Remaining Balance: {current_total_balance - projected_usage:.0f} days\n"
        response += f"└── Risk Level: {'🟢 Low' if (current_total_balance - projected_usage) > current_total_balance * 0.3 else '🟡 Medium' if (current_total_balance - projected_usage) > current_total_balance * 0.1 else '🔴 High'}\n\n"
        
        # Scenario 2: Increased utilization (encouraging leave)
        increased_util_rate = min(current_util_rate * 1.5, 0.8)  # Cap at 80%
        increased_usage = current_total_balance * increased_util_rate * 0.5
        
        response += "📈 **Scenario 2: Encouraged Leave Taking (+50%)**\n"
        response += f"├── Projected Usage: {increased_usage:.0f} days\n"
        response += f"├── Remaining Balance: {current_total_balance - increased_usage:.0f} days\n"
        response += f"└── Impact: Better work-life balance, potential refresh needed\n\n"
        
        # Critical thresholds
        response += "⚠️ **CRITICAL THRESHOLDS & ALERTS**\n"
        
        low_balance_employees = [emp for emp in employees if emp.get("balance", 0) <= 5]
        response += f"├── Employees at Risk (≤5 days): {len(low_balance_employees)}\n"
        
        zero_balance_risk = len([emp for emp in employees if emp.get("balance", 0) <= 2])
        response += f"├── Critical Risk (≤2 days): {zero_balance_risk}\n"
        
        if current_avg_balance < 10:
            response += f"└── ⚠️ Organization-wide refresh recommended within 3 months\n"
        else:
            response += f"└── ✅ Healthy organizational leave reserves\n"
        
        return response
    

    def _analyze_utilization_patterns(self, employees: List[Dict]) -> str:
        """Analyze detailed leave utilization patterns"""
        from datetime import datetime
        
        response = "📊 **LEAVE UTILIZATION PATTERN ANALYSIS**\n"
        response += f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Calculate utilization metrics
        utilization_data = []
        for emp in employees:
            balance = emp.get("balance", 0)
            taken = len(emp.get("history", []))
            total_allocation = balance + taken
            utilization_rate = (taken / total_allocation * 100) if total_allocation > 0 else 0
            
            utilization_data.append({
                'name': emp.get("name", "Unknown"),
                'id': emp.get("employee_id", "Unknown"),
                'department': emp.get("department", "Unknown"),
                'utilization': utilization_rate,
                'taken': taken,
                'balance': balance
            })
        
        # Sort by utilization rate
        sorted_by_utilization = sorted(utilization_data, key=lambda x: x['utilization'], reverse=True)
        
        # Calculate statistics
        utilizations = [d['utilization'] for d in utilization_data]
        avg_utilization = statistics.mean(utilizations) if utilizations else 0
        median_utilization = statistics.median(utilizations) if utilizations else 0
        
        response += "📈 **UTILIZATION STATISTICS**\n"
        response += f"├── Average Utilization: {avg_utilization:.1f}%\n"
        response += f"├── Median Utilization: {median_utilization:.1f}%\n"
        response += f"└── Standard Deviation: {statistics.stdev(utilizations) if len(utilizations) > 1 else 0:.1f}%\n\n"
        
        # Utilization categories
        high_utilizers = [d for d in utilization_data if d['utilization'] > 70]
        moderate_utilizers = [d for d in utilization_data if 30 <= d['utilization'] <= 70]
        low_utilizers = [d for d in utilization_data if d['utilization'] < 30]
        
        response += "🎯 **UTILIZATION CATEGORIES**\n"
        response += f"├── High Utilizers (>70%): {len(high_utilizers)} employees\n"
        response += f"├── Moderate Utilizers (30-70%): {len(moderate_utilizers)} employees\n"
        response += f"└── Low Utilizers (<30%): {len(low_utilizers)} employees\n\n"
        
        # Top and bottom utilizers
        response += "🔝 **TOP UTILIZERS**\n"
        for i, emp in enumerate(sorted_by_utilization[:5], 1):
            response += f"{i}. **{emp['name']}** ({emp['id']}): {emp['utilization']:.1f}% ({emp['taken']} days used)\n"
        response += "\n"
        
        response += "🔻 **LOWEST UTILIZERS**\n"
        for i, emp in enumerate(reversed(sorted_by_utilization[-5:]), 1):
            response += f"{i}. **{emp['name']}** ({emp['id']}): {emp['utilization']:.1f}% ({emp['taken']} days used)\n"
        response += "\n"
        
        # Department utilization comparison
        dept_utilization = defaultdict(list)
        for emp in utilization_data:
            dept_utilization[emp['department']].append(emp['utilization'])
        
        response += "🏢 **DEPARTMENT UTILIZATION AVERAGES**\n"
        dept_avg_util = []
        for dept, utils in dept_utilization.items():
            avg = statistics.mean(utils)
            dept_avg_util.append((dept, avg))
            response += f"├── {dept}: {avg:.1f}%\n"
        
        # Sort departments by utilization
        dept_avg_util.sort(key=lambda x: x[1], reverse=True)
        best_dept, best_util = dept_avg_util[0] if dept_avg_util else ("None", 0)
        
        response += f"\n🏆 **Best Utilizing Department**: {best_dept} ({best_util:.1f}%)\n"
        
        return response
    

    def _identify_outliers(self, employees: List[Dict]) -> str:
        """Identify statistical outliers in the data"""
        from datetime import datetime
        
        response = "🔍 **OUTLIER DETECTION ANALYSIS**\n"
        response += f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Prepare data for outlier detection
        balances = [emp.get("balance", 0) for emp in employees]
        leaves_taken = [len(emp.get("history", [])) for emp in employees]
        
        if len(balances) < 3:
            return response + "❌ Insufficient data for outlier analysis"
        
        # Calculate IQR for balance outliers
        balance_outliers = self._find_iqr_outliers(employees, balances, "balance")
        taken_outliers = self._find_iqr_outliers(employees, leaves_taken, "leaves_taken")
        
        response += "📊 **LEAVE BALANCE OUTLIERS**\n"
        if balance_outliers:
            for outlier in balance_outliers:
                emp_name = outlier['name']
                emp_id = outlier['id']
                value = outlier['value']
                outlier_type = outlier['type']
                response += f"├── **{emp_name}** ({emp_id}): {value} days ({outlier_type})\n"
        else:
            response += "├── ✅ No significant balance outliers detected\n"
        response += "\n"
        
        response += "📊 **LEAVE UTILIZATION OUTLIERS**\n"
        if taken_outliers:
            for outlier in taken_outliers:
                emp_name = outlier['name']
                emp_id = outlier['id']
                value = outlier['value']
                outlier_type = outlier['type']
                response += f"├── **{emp_name}** ({emp_id}): {value} days ({outlier_type})\n"
        else:
            response += "├── ✅ No significant utilization outliers detected\n"
        response += "\n"
        
        # Anomaly insights
        response += "🚨 **ANOMALY INSIGHTS**\n"
        
        # Extreme cases
        max_balance = max(balances)
        min_balance = min(balances)
        max_taken = max(leaves_taken)
        
        if max_balance > 25:
            max_balance_emp = next(emp for emp in employees if emp.get("balance", 0) == max_balance)
            response += f"├── 📈 Unusually high balance: **{max_balance_emp.get('name')}** with {max_balance} days\n"
        
        if min_balance == 0:
            zero_balance_emps = [emp for emp in employees if emp.get("balance", 0) == 0]
            response += f"├── ⚠️ Zero balance: {len(zero_balance_emps)} employees need immediate attention\n"
        
        if max_taken > 15:
            max_taken_emp = next(emp for emp in employees if len(emp.get("history", [])) == max_taken)
            response += f"└── 🏖️ High utilizer: **{max_taken_emp.get('name')}** with {max_taken} days taken\n"
        
        return response
    
    def _generate_recommendations(self, employees: List[Dict], focus_area: str) -> str:
        """Generate strategic recommendations based on analysis"""
        from datetime import datetime
        
        response = "💡 **STRATEGIC RECOMMENDATIONS**\n"
        response += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        response += f"🎯 Focus Area: {focus_area.title()}\n\n"
        
        # Analyze current state
        total_employees = len(employees)
        low_balance_count = len([emp for emp in employees if emp.get("balance", 0) <= 5])
        high_balance_count = len([emp for emp in employees if emp.get("balance", 0) > 15])
        avg_balance = sum(emp.get("balance", 0) for emp in employees) / total_employees if total_employees > 0 else 0
        avg_taken = sum(len(emp.get("history", [])) for emp in employees) / total_employees if total_employees > 0 else 0
        
        # Generate targeted recommendations
        recommendations = []
        
        # Leave balance recommendations
        if low_balance_count > total_employees * 0.2:  # More than 20% have low balance
            recommendations.append({
                "priority": "🔴 HIGH",
                "category": "Leave Refresh",
                "title": "Immediate Leave Balance Refresh Required",
                "description": f"{low_balance_count} employees ({low_balance_count/total_employees*100:.1f}%) have ≤5 days remaining",
                "actions": [
                    "Schedule immediate leave refresh for affected employees",
                    "Review annual leave allocation policies",
                    "Consider bonus leave allocation for high performers"
                ]
            })
        
        # High balance recommendations
        if high_balance_count > total_employees * 0.3:  # More than 30% have high balance
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "category": "Leave Utilization",
                "title": "Encourage Leave Taking",
                "description": f"{high_balance_count} employees have >15 days unused - potential burnout risk",
                "actions": [
                    "Launch wellness campaign encouraging leave usage",
                    "Implement 'use it or lose it' policies",
                    "Manager training on promoting work-life balance"
                ]
            })
        
        # Utilization recommendations
        if avg_taken < 8:  # Low overall utilization
            recommendations.append({
                "priority": "🟠 MEDIUM",
                "category": "Employee Wellbeing",
                "title": "Low Leave Utilization Detected",
                "description": f"Average of {avg_taken:.1f} days taken - below healthy levels",
                "actions": [
                    "Survey employees about leave-taking barriers",
                    "Promote mental health and wellness programs",
                    "Review workload distribution and staffing levels"
                ]
            })
        
        # Department-specific recommendations
        dept_stats = defaultdict(lambda: {"count": 0, "total_balance": 0, "total_taken": 0})
        for emp in employees:
            dept = emp.get("department", "Unknown")
            dept_stats[dept]["count"] += 1
            dept_stats[dept]["total_balance"] += emp.get("balance", 0)
            dept_stats[dept]["total_taken"] += len(emp.get("history", []))
        
        # Find departments with imbalanced patterns
        for dept, stats in dept_stats.items():
            if stats["count"] > 1:  # Only analyze departments with multiple employees
                avg_dept_balance = stats["total_balance"] / stats["count"]
                if avg_dept_balance < avg_balance - 5:  # Department significantly below average
                    recommendations.append({
                        "priority": "🟡 MEDIUM",
                        "category": "Department Focus",
                        "title": f"{dept} Department Needs Attention",
                        "description": f"Average balance ({avg_dept_balance:.1f} days) significantly below org average",
                        "actions": [
                            f"Review {dept} workload and leave policies",
                            "Meet with department manager to discuss leave patterns",
                            "Consider department-specific leave refresh"
                        ]
                    })
        
        # Policy recommendations
        recommendations.append({
            "priority": "🟢 LOW",
            "category": "Policy Enhancement",
            "title": "Optimize Leave Management Policies",
            "description": "Continuous improvement opportunities identified",
            "actions": [
                "Implement predictive analytics dashboard",
                "Automate low-balance alerts",
                "Create self-service leave planning tools",
                "Regular policy review and updates"
            ]
        })
        
        # Format recommendations
        if not recommendations:
            response += "✅ **No critical issues identified**\nCurrent leave management appears to be well-balanced.\n"
        else:
            response += f"📋 **{len(recommendations)} RECOMMENDATIONS IDENTIFIED**\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                response += f"**{i}. {rec['title']}**\n"
                response += f"├── Priority: {rec['priority']}\n"
                response += f"├── Category: {rec['category']}\n"
                response += f"├── Issue: {rec['description']}\n"
                response += f"└── Actions:\n"
                for action in rec['actions']:
                    response += f"    • {action}\n"
                response += "\n"
        
        # Success metrics
        response += "📊 **SUCCESS METRICS TO TRACK**\n"
        response += "├── Average leave balance maintenance (target: 12-18 days)\n"
        response += "├── Leave utilization rate (target: 40-60%)\n"
        response += "├── Employee satisfaction with leave policies\n"
        response += "├── Reduction in zero-balance incidents\n"
        response += "└── Department balance variance (target: <20%)\n"
        
        return response
    
    def _calculate_distribution(self, values: List[float]) -> Dict[str, float]:
        """Calculate distribution of values into ranges"""
        total = len(values)
        if total == 0:
            return {}
        
        ranges = {"0-5 days": 0, "6-10 days": 0, "11-15 days": 0, "16-20 days": 0, "20+ days": 0}
        
        for value in values:
            if value <= 5:
                ranges["0-5 days"] += 1
            elif value <= 10:
                ranges["6-10 days"] += 1
            elif value <= 15:
                ranges["11-15 days"] += 1
            elif value <= 20:
                ranges["16-20 days"] += 1
            else:
                ranges["20+ days"] += 1
        
        # Convert to percentages
        return {k: (v / total * 100) for k, v in ranges.items()}
    

    def _find_iqr_outliers(self, employees: List[Dict], values: List[float], metric_type: str) -> List[Dict]:
        """Find outliers using IQR method"""
        if len(values) < 4:
            return []
        
        # Calculate quartiles
        sorted_values = sorted(values)
        n = len(sorted_values)
        q1 = sorted_values[n // 4]
        q3 = sorted_values[3 * n // 4]
        iqr = q3 - q1
        
        # Define outlier bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append({
                    'name': employees[i].get('name', 'Unknown'),
                    'id': employees[i].get('employee_id', 'Unknown'),
                    'value': value,
                    'type': 'Extremely Low' if value < lower_bound else 'Extremely High'
                })
        
        return outliers
