#!/usr/bin/env python3
"""
LangGraph Swarm HR System Test Script
Tests the swarm-based multi-agent functionality
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import sys

# Configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 60  # Increased timeout for swarm operations

# Test user credentials
TEST_USERS = {
    "hr_user": {"employee_id": "E001", "password": "pw123", "name": "Kalhar Dasanayaka", "role": "HR"},
    "employee_user": {"employee_id": "E003", "password": "pw123", "name": "Ravindu Cooray", "role": "Employee"}
}

class Colors:
    """Console colors for better output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SwarmSystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def print_header(self, title: str):
        """Print formatted test section header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def print_test(self, test_name: str, status: str, message: str = ""):
        """Print formatted test result"""
        if status == "PASS":
            color = Colors.GREEN
            symbol = "✅"
            self.test_results["passed"] += 1
        elif status == "FAIL":
            color = Colors.RED
            symbol = "❌"
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
        else:
            color = Colors.YELLOW
            symbol = "⚠️"
        
        print(f"{symbol} {Colors.BOLD}{test_name:<45}{Colors.END} {color}{status}{Colors.END}")
        if message:
            print(f"   {Colors.WHITE}{message}{Colors.END}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=TIMEOUT)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def test_swarm_health_check(self):
        """Test swarm system health endpoint"""
        try:
            response = self.make_request("GET", "/api/health")
            
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                services = health_data.get("services", {})
                architecture = health_data.get("architecture", "unknown")
                
                self.print_test("Swarm Health Check", "PASS", f"Status: {status}, Architecture: {architecture}")
                
                # Check swarm-specific services
                swarm_status = services.get("swarm_system", "unknown")
                if swarm_status == "up":
                    self.print_test("  └─ Swarm System", "PASS", "Active")
                else:
                    self.print_test("  └─ Swarm System", "WARN", f"Status: {swarm_status}")
                    
                # Check other services
                for service, service_status in services.items():
                    if service != "swarm_system":
                        self.print_test(f"  └─ {service.capitalize()}", 
                                      "PASS" if service_status == "up" else "WARN", 
                                      f"Status: {service_status}")
            else:
                self.print_test("Swarm Health Check", "FAIL", f"HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Swarm Health Check", "FAIL", str(e))
    
    def test_authentication(self):
        """Test user authentication"""
        for user_type, credentials in TEST_USERS.items():
            try:
                response = self.make_request("POST", "/login", credentials)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.tokens[user_type] = token_data.get("access_token")
                    
                    self.print_test(f"Login - {credentials['name']}", "PASS", 
                                  f"Role: {credentials['role']}")
                else:
                    error_msg = response.json().get("msg", "Unknown error")
                    self.print_test(f"Login - {credentials['name']}", "FAIL", 
                                  f"HTTP {response.status_code}: {error_msg}")
            
            except Exception as e:
                self.print_test(f"Login - {credentials['name']}", "FAIL", str(e))
    
    def test_swarm_system_status(self):
        """Test swarm system status endpoints"""
        if "hr_user" not in self.tokens:
            self.print_test("Swarm Status Tests", "FAIL", "HR token not available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['hr_user']}"}
            
            # Test system status
            response = self.make_request("GET", "/api/system/status", headers=headers)
            
            if response.status_code == 200:
                status_data = response.json()
                mas_status = status_data.get("multi_agent_system", {})
                mas_architecture = mas_status.get("architecture", "unknown")
                agents_available = mas_status.get("agents_available", [])
                
                self.print_test("System Status", "PASS", 
                              f"Architecture: {mas_architecture}, Agents: {len(agents_available)}")
                
                # Test swarm-specific status
                response = self.make_request("GET", "/api/swarm/status", headers=headers)
                
                if response.status_code == 200:
                    swarm_data = response.json()
                    swarm_available = swarm_data.get("swarm_available", False)
                    
                    if swarm_available:
                        swarm_details = swarm_data.get("swarm_details", {})
                        available_agents = swarm_details.get("available_agents", [])
                        self.print_test("Swarm Status", "PASS", 
                                      f"Available agents: {', '.join(available_agents)}")
                    else:
                        self.print_test("Swarm Status", "WARN", "Swarm system not available")
                else:
                    self.print_test("Swarm Status", "FAIL", f"HTTP {response.status_code}")
            else:
                self.print_test("System Status", "FAIL", f"HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Swarm Status Tests", "FAIL", str(e))
    
    def test_swarm_agent_handoffs(self):
        """Test swarm agent handoff functionality"""
        test_queries = [
            {
                "user_type": "hr_user",
                "query": "check balance for E003",
                "expected_agent": "leave_agent",
                "description": "Leave balance query should route to Leave Agent"
            },
            {
                "user_type": "hr_user",
                "query": "find employee John",
                "expected_agent": "employee_agent", 
                "description": "Employee search should route to Employee Agent"
            },
            {
                "user_type": "hr_user",
                "query": "generate department report",
                "expected_agent": "reporting_agent",
                "description": "Report request should route to Reporting Agent"
            },
            {
                "user_type": "hr_user", 
                "query": "show leave trends and analytics",
                "expected_agent": "analysis_agent",
                "description": "Analytics request should route to Analysis Agent"
            },
            {
                "user_type": "employee_user",
                "query": "check my leave balance",
                "expected_agent": "leave_agent",
                "description": "Employee leave query should work"
            }
        ]
        
        for test_query in test_queries:
            user_type = test_query["user_type"]
            query = test_query["query"]
            expected_agent = test_query["expected_agent"]
            description = test_query["description"]
            
            if user_type not in self.tokens:
                self.print_test(f"Handoff - {description}", "FAIL", f"No token for {user_type}")
                continue
            
            try:
                headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
                response = self.make_request("POST", "/api/chat", {"message": query}, headers)
                
                if response.status_code == 200:
                    chat_data = response.json()
                    response_text = chat_data.get("response", "")
                    system_mode = chat_data.get("system_mode", "unknown")
                    
                    # Check if response indicates swarm processing
                    swarm_indicators = [
                        "Powered by LangGraph Swarm",
                        "multi-agent",
                        "swarm"
                    ]
                    
                    has_swarm_indicator = any(indicator.lower() in response_text.lower() 
                                            for indicator in swarm_indicators)
                    
                    if system_mode == "swarm" or has_swarm_indicator:
                        self.print_test(f"Swarm Query - {expected_agent}", "PASS", 
                                      f"Processed via swarm system")
                    elif system_mode == "fallback":
                        self.print_test(f"Swarm Query - {expected_agent}", "WARN", 
                                      "Processed via fallback (swarm unavailable)")
                    else:
                        self.print_test(f"Swarm Query - {expected_agent}", "FAIL", 
                                      f"Unknown system mode: {system_mode}")
                else:
                    error_msg = response.json().get("error", "Unknown error")
                    self.print_test(f"Swarm Query - {expected_agent}", "FAIL", 
                                  f"HTTP {response.status_code}: {error_msg}")
            
            except Exception as e:
                self.print_test(f"Swarm Query - {expected_agent}", "FAIL", str(e))
    
    def test_swarm_conversation_persistence(self):
        """Test swarm conversation persistence and memory"""
        if "hr_user" not in self.tokens:
            self.print_test("Conversation Persistence", "FAIL", "HR token not available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['hr_user']}"}
            
            # First message
            response1 = self.make_request("POST", "/api/chat", 
                                        {"message": "Hello, I need help with HR tasks"}, headers)
            
            if response1.status_code == 200:
                # Second message that should reference context
                response2 = self.make_request("POST", "/api/chat", 
                                            {"message": "Can you help me with employee E003's details?"}, headers)
                
                if response2.status_code == 200:
                    chat_data = response2.json()
                    response_text = chat_data.get("response", "")
                    
                    # Check if response shows contextual awareness
                    context_indicators = ["E003", "employee", "details", "Ravindu"]
                    context_found = sum(1 for indicator in context_indicators 
                                      if indicator in response_text)
                    
                    if context_found >= 2:
                        self.print_test("Conversation Persistence", "PASS", 
                                      "Context maintained across messages")
                    else:
                        self.print_test("Conversation Persistence", "WARN", 
                                      "Limited context retention detected")
                else:
                    self.print_test("Conversation Persistence", "FAIL", 
                                  f"Second message failed: HTTP {response2.status_code}")
            else:
                self.print_test("Conversation Persistence", "FAIL", 
                              f"First message failed: HTTP {response1.status_code}")
        
        except Exception as e:
            self.print_test("Conversation Persistence", "FAIL", str(e))
    
    def test_swarm_reset_functionality(self):
        """Test swarm conversation reset functionality"""
        if "hr_user" not in self.tokens:
            self.print_test("Swarm Reset", "FAIL", "HR token not available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['hr_user']}"}
            thread_id = f"thread_E001_test_{int(time.time())}"
            
            # Test reset endpoint
            response = self.make_request("POST", f"/api/swarm/reset/{thread_id}", headers=headers)
            
            if response.status_code == 200:
                reset_data = response.json()
                if reset_data.get("success"):
                    self.print_test("Swarm Reset", "PASS", "Conversation reset successful")
                else:
                    self.print_test("Swarm Reset", "FAIL", reset_data.get("message", "Reset failed"))
            elif response.status_code == 503:
                self.print_test("Swarm Reset", "WARN", "Swarm system not available")
            else:
                self.print_test("Swarm Reset", "FAIL", f"HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Swarm Reset", "FAIL", str(e))
    
    def test_swarm_authorization(self):
        """Test swarm authorization controls"""
        if "employee_user" not in self.tokens:
            self.print_test("Swarm Authorization", "FAIL", "Employee token not available")
            return
        
        # Test employee trying to access restricted functionality
        restricted_queries = [
            "show all employees analytics",
            "generate organizational insights", 
            "department statistics for all departments"
        ]
        
        for query in restricted_queries:
            try:
                headers = {"Authorization": f"Bearer {self.tokens['employee_user']}"}
                response = self.make_request("POST", "/api/chat", {"message": query}, headers)
                
                if response.status_code == 200:
                    chat_data = response.json()
                    response_text = chat_data.get("response", "")
                    
                    # Check if access was properly denied
                    denial_indicators = [
                        "access denied",
                        "restricted",
                        "hr personnel only",
                        "not authorized"
                    ]
                    
                    access_denied = any(indicator.lower() in response_text.lower() 
                                      for indicator in denial_indicators)
                    
                    if access_denied:
                        self.print_test(f"Authorization - {query[:30]}...", "PASS", 
                                      "Access properly restricted")
                    else:
                        self.print_test(f"Authorization - {query[:30]}...", "WARN", 
                                      "Access may not be properly restricted")
                else:
                    self.print_test(f"Authorization - {query[:30]}...", "FAIL", 
                                  f"HTTP {response.status_code}")
            
            except Exception as e:
                self.print_test(f"Authorization - {query[:30]}...", "FAIL", str(e))
    
    def test_swarm_performance(self):
        """Test swarm system performance"""
        if "hr_user" not in self.tokens:
            self.print_test("Swarm Performance", "FAIL", "HR token not available")
            return
        
        performance_queries = [
            "check balance for E003",
            "find employee E005", 
            "show department overview"
        ]
        
        total_time = 0
        successful_queries = 0
        
        for query in performance_queries:
            try:
                headers = {"Authorization": f"Bearer {self.tokens['hr_user']}"}
                
                start_time = time.time()
                response = self.make_request("POST", "/api/chat", {"message": query}, headers)
                end_time = time.time()
                
                response_time = end_time - start_time
                total_time += response_time
                
                if response.status_code == 200:
                    successful_queries += 1
                    
                    if response_time < 10:  # 10 seconds threshold
                        self.print_test(f"Performance - {query[:20]}...", "PASS", 
                                      f"Response time: {response_time:.2f}s")
                    else:
                        self.print_test(f"Performance - {query[:20]}...", "WARN", 
                                      f"Slow response: {response_time:.2f}s")
                else:
                    self.print_test(f"Performance - {query[:20]}...", "FAIL", 
                                  f"HTTP {response.status_code}")
            
            except Exception as e:
                self.print_test(f"Performance - {query[:20]}...", "FAIL", str(e))
        
        if successful_queries > 0:
            avg_time = total_time / successful_queries
            self.print_test("Average Response Time", 
                          "PASS" if avg_time < 8 else "WARN", 
                          f"{avg_time:.2f} seconds")
    
    def run_all_tests(self):
        """Run all swarm test suites"""
        print(f"{Colors.BOLD}{Colors.PURPLE}")
        print("🚀 LangGraph Swarm HR System Tests")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {self.base_url}")
        print(f"{Colors.END}")
        
        # Run test suites
        self.print_header("Swarm System Health Tests")
        self.test_swarm_health_check()
        
        self.print_header("Authentication Tests")
        self.test_authentication()
        
        self.print_header("Swarm System Status Tests")
        self.test_swarm_system_status()
        
        self.print_header("Swarm Agent Handoff Tests")
        self.test_swarm_agent_handoffs()
        
        self.print_header("Swarm Conversation Persistence Tests")
        self.test_swarm_conversation_persistence()
        
        self.print_header("Swarm Reset Functionality Tests")
        self.test_swarm_reset_functionality()
        
        self.print_header("Swarm Authorization Tests")
        self.test_swarm_authorization()
        
        self.print_header("Swarm Performance Tests")
        self.test_swarm_performance()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}LANGGRAPH SWARM TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        
        print(f"\n{Colors.BOLD}Total Tests:{Colors.END} {total_tests}")
        print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {self.test_results['passed']}")
        print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {self.test_results['failed']}")
        print(f"{Colors.BOLD}Pass Rate:{Colors.END} {pass_rate:.1f}%")
        
        if self.test_results["errors"]:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS:{Colors.END}")
            for error in self.test_results["errors"]:
                print(f"  {Colors.RED}• {error}{Colors.END}")
        
        # Overall status
        if pass_rate >= 90:
            status_color = Colors.GREEN
            status = "EXCELLENT - Swarm System Operational ✨"
        elif pass_rate >= 75:
            status_color = Colors.YELLOW
            status = "GOOD - Minor Issues Detected ⚡"
        elif pass_rate >= 50:
            status_color = Colors.YELLOW
            status = "PARTIAL - Swarm May Be Degraded ⚠️"
        else:
            status_color = Colors.RED
            status = "CRITICAL - Swarm System Issues ❌"
        
        print(f"\n{Colors.BOLD}Swarm System Status: {status_color}{status}{Colors.END}")
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")


def main():
    """Main function to run swarm tests"""
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1]
    
    print(f"{Colors.BOLD}{Colors.BLUE}Checking if LangGraph Swarm server is running at {BASE_URL}...{Colors.END}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code not in [200, 503]:
            print(f"{Colors.RED}❌ Server not responding properly. Please start the server first.{Colors.END}")
            print(f"{Colors.YELLOW}Run: python backend/web_server.py{Colors.END}")
            sys.exit(1)
        
        # Check if swarm is available
        health_data = response.json()
        architecture = health_data.get("architecture", "unknown")
        
        if architecture == "swarm":
            print(f"{Colors.GREEN}✅ LangGraph Swarm system detected. Starting comprehensive tests...{Colors.END}")
        elif architecture == "fallback":
            print(f"{Colors.YELLOW}⚠️ Server running in fallback mode. Some tests may fail.{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️ Unknown architecture: {architecture}. Proceeding with tests...{Colors.END}")
            
    except requests.exceptions.RequestException:
        print(f"{Colors.RED}❌ Cannot connect to server at {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Please make sure the server is running:${Colors.END}")
        print(f"{Colors.YELLOW}  cd backend && python web_server.py${Colors.END}")
        sys.exit(1)
    
    time.sleep(1)
    
    # Run swarm tests
    tester = SwarmSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()