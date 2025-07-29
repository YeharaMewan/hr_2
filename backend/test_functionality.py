#!/usr/bin/env python3
"""
HR Multi-Agent System Functionality Test Script
Tests all core functionalities of the HR system
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import sys

# Configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 30

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

class HRSystemTester:
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
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")
    
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
        
        print(f"{symbol} {Colors.BOLD}{test_name:<40}{Colors.END} {color}{status}{Colors.END}")
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
    
    def test_health_check(self):
        """Test system health endpoint"""
        try:
            response = self.make_request("GET", "/api/health")
            
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                services = health_data.get("services", {})
                
                self.print_test("Health Check", "PASS", f"Status: {status}")
                
                # Check individual services
                for service, service_status in services.items():
                    self.print_test(f"  └─ {service.capitalize()} Service", 
                                  "PASS" if service_status == "up" else "WARN", 
                                  f"Status: {service_status}")
            else:
                self.print_test("Health Check", "FAIL", f"HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Health Check", "FAIL", str(e))
    
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
    
    def test_chat_functionality(self):
        """Test chat endpoint with various queries"""
        test_queries = [
            {
                "user_type": "employee_user",
                "query": "check my balance",
                "expected_keywords": ["balance", "days", "E003"]
            },
            {
                "user_type": "employee_user", 
                "query": "show my history",
                "expected_keywords": ["history", "E003"]
            },
            {
                "user_type": "hr_user",
                "query": "check balance for E003",
                "expected_keywords": ["balance", "E003", "Ravindu"]
            },
            {
                "user_type": "hr_user",
                "query": "help",
                "expected_keywords": ["help", "commands", "balance"]
            },
            {
                "user_type": "employee_user",
                "query": "hello",
                "expected_keywords": ["HR Assistant", "help"]
            }
        ]
        
        for test_query in test_queries:
            user_type = test_query["user_type"]
            query = test_query["query"]
            expected = test_query["expected_keywords"]
            
            if user_type not in self.tokens:
                self.print_test(f"Chat - {query[:20]}...", "FAIL", f"No token for {user_type}")
                continue
            
            try:
                headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
                response = self.make_request("POST", "/api/chat", {"message": query}, headers)
                
                if response.status_code == 200:
                    chat_data = response.json()
                    response_text = chat_data.get("response", "").lower()
                    
                    # Check if expected keywords are in response
                    keywords_found = sum(1 for keyword in expected if keyword.lower() in response_text)
                    
                    if keywords_found >= len(expected) // 2:  # At least half the keywords found
                        self.print_test(f"Chat - {query}", "PASS", 
                                      f"Found {keywords_found}/{len(expected)} keywords")
                    else:
                        self.print_test(f"Chat - {query}", "WARN", 
                                      f"Only {keywords_found}/{len(expected)} keywords found")
                else:
                    error_msg = response.json().get("error", "Unknown error")
                    self.print_test(f"Chat - {query}", "FAIL", 
                                  f"HTTP {response.status_code}: {error_msg}")
            
            except Exception as e:
                self.print_test(f"Chat - {query}", "FAIL", str(e))
    
    def test_direct_api_endpoints(self):
        """Test direct API endpoints"""
        # Test balance endpoint
        for user_type, credentials in TEST_USERS.items():
            if user_type not in self.tokens:
                continue
            
            try:
                headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
                employee_id = credentials["employee_id"]
                
                # Test own balance
                response = self.make_request("GET", f"/api/tools/balance/{employee_id}", headers=headers)
                
                if response.status_code == 200:
                    balance_data = response.json()
                    if balance_data.get("success"):
                        self.print_test(f"API Balance - {employee_id}", "PASS", 
                                      f"Balance: {balance_data['data']['balance']} days")
                    else:
                        self.print_test(f"API Balance - {employee_id}", "FAIL", 
                                      balance_data.get("message", "Unknown error"))
                else:
                    self.print_test(f"API Balance - {employee_id}", "FAIL", 
                                  f"HTTP {response.status_code}")
                
                # Test history endpoint
                response = self.make_request("GET", f"/api/tools/history/{employee_id}", headers=headers)
                
                if response.status_code == 200:
                    history_data = response.json()
                    if history_data.get("success"):
                        history_count = len(history_data['data']['history'])
                        self.print_test(f"API History - {employee_id}", "PASS", 
                                      f"History entries: {history_count}")
                    else:
                        self.print_test(f"API History - {employee_id}", "FAIL", 
                                      history_data.get("message", "Unknown error"))
                else:
                    self.print_test(f"API History - {employee_id}", "FAIL", 
                                  f"HTTP {response.status_code}")
            
            except Exception as e:
                self.print_test(f"API Endpoints - {employee_id}", "FAIL", str(e))
    
    def test_authorization(self):
        """Test authorization controls"""
        if "employee_user" not in self.tokens or "hr_user" not in self.tokens:
            self.print_test("Authorization Tests", "FAIL", "Missing authentication tokens")
            return
        
        # Test employee trying to access other employee's data
        try:
            headers = {"Authorization": f"Bearer {self.tokens['employee_user']}"}
            response = self.make_request("GET", "/api/tools/balance/E001", headers=headers)
            
            if response.status_code == 403:
                self.print_test("Employee Access Control", "PASS", "Correctly denied access to other employee data")
            else:
                self.print_test("Employee Access Control", "FAIL", 
                              f"Should have been denied, got HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Employee Access Control", "FAIL", str(e))
        
        # Test HR accessing system status
        try:
            headers = {"Authorization": f"Bearer {self.tokens['hr_user']}"}
            response = self.make_request("GET", "/api/system/status", headers=headers)
            
            if response.status_code == 200:
                status_data = response.json()
                self.print_test("HR System Status", "PASS", 
                              f"Total employees: {status_data.get('total_employees', 'unknown')}")
            else:
                self.print_test("HR System Status", "FAIL", f"HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("HR System Status", "FAIL", str(e))
        
        # Test employee trying to access system status
        try:
            headers = {"Authorization": f"Bearer {self.tokens['employee_user']}"}
            response = self.make_request("GET", "/api/system/status", headers=headers)
            
            if response.status_code == 403:
                self.print_test("Employee System Status Denied", "PASS", "Correctly denied access")
            else:
                self.print_test("Employee System Status Denied", "FAIL", 
                              f"Should have been denied, got HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Employee System Status Denied", "FAIL", str(e))
    
    def test_frontend_serving(self):
        """Test frontend file serving"""
        try:
            response = self.make_request("GET", "/")
            
            if response.status_code == 200 and "html" in response.headers.get("content-type", "").lower():
                self.print_test("Frontend Root", "PASS", "HTML content served")
            else:
                self.print_test("Frontend Root", "FAIL", f"HTTP {response.status_code}")
            
            # Test specific frontend file
            response = self.make_request("GET", "/frontend/login.html")
            
            if response.status_code == 200:
                self.print_test("Frontend Login Page", "PASS", "Login page accessible")
            else:
                self.print_test("Frontend Login Page", "FAIL", f"HTTP {response.status_code}")
        
        except Exception as e:
            self.print_test("Frontend Serving", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"{Colors.BOLD}{Colors.PURPLE}")
        print("🚀 HR Multi-Agent System Functionality Tests")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {self.base_url}")
        print(f"{Colors.END}")
        
        # Run test suites
        self.print_header("System Health Tests")
        self.test_health_check()
        
        self.print_header("Authentication Tests")
        self.test_authentication()
        
        self.print_header("Chat Functionality Tests")
        self.test_chat_functionality()
        
        self.print_header("Direct API Tests")
        self.test_direct_api_endpoints()
        
        self.print_header("Authorization Tests")
        self.test_authorization()
        
        self.print_header("Frontend Serving Tests")
        self.test_frontend_serving()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        
        print(f"\n{Colors.BOLD}Total Tests:{Colors.END} {total_tests}")
        print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {self.test_results['passed']}")
        print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {self.test_results['failed']}")
        print(f"{Colors.BOLD}Pass Rate:{Colors.END} {pass_rate:.1f}%")
        
        if self.test_results["errors"]:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS:{Colors.END}")
            for error in self.test_results["errors"]:
                print(f"  {Colors.RED}• {error}{Colors.END}")
        
        # Overall status
        if pass_rate >= 80:
            status_color = Colors.GREEN
            status = "EXCELLENT ✨"
        elif pass_rate >= 60:
            status_color = Colors.YELLOW
            status = "GOOD ⚡"
        else:
            status_color = Colors.RED
            status = "NEEDS IMPROVEMENT ⚠️"
        
        print(f"\n{Colors.BOLD}Overall Status: {status_color}{status}{Colors.END}")
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1]
    
    print(f"{Colors.BOLD}{Colors.BLUE}Checking if server is running at {BASE_URL}...{Colors.END}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code not in [200, 503]:
            print(f"{Colors.RED}❌ Server not responding properly. Please start the server first.{Colors.END}")
            print(f"{Colors.YELLOW}Run: python backend/web_server.py{Colors.END}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"{Colors.RED}❌ Cannot connect to server at {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Please make sure the server is running:${Colors.END}")
        print(f"{Colors.YELLOW}  cd backend && python web_server.py${Colors.END}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✅ Server is running. Starting tests...{Colors.END}")
    time.sleep(1)
    
    # Run tests
    tester = HRSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()