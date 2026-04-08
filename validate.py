"""
Validation script for Field Tech Visual Assistant.
Tests OpenEnv compliance before submission.
"""

import os
import sys
import time
import requests
import subprocess
from typing import Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_status(message: str, status: str):
    """Print colored status message."""
    if status == "PASS":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "FAIL":
        print(f"{RED}✗{RESET} {message}")
    elif status == "WARN":
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"  {message}")


def check_files() -> bool:
    """Check required files exist."""
    print("\n📁 Checking Required Files...")
    
    required_files = [
        "app.py",
        "inference.py", 
        "env.py",
        "models.py",
        "requirements.txt",
        "Dockerfile",
        "openenv.yaml"
    ]
    
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print_status(f"{file}", "PASS")
        else:
            print_status(f"{file} - MISSING", "FAIL")
            all_present = False
    
    return all_present


def check_env_vars() -> Tuple[bool, list]:
    """Check environment variables."""
    print("\n🔧 Checking Environment Variables...")
    
    issues = []
    
    # HF_TOKEN must be set (required)
    if not os.getenv("HF_TOKEN"):
        print_status("HF_TOKEN - NOT SET (REQUIRED!)", "FAIL")
        issues.append("HF_TOKEN not set")
    else:
        print_status("HF_TOKEN - SET", "PASS")
    
    # These should have defaults
    api_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    model = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    
    print_status(f"API_BASE_URL - {api_url}", "PASS")
    print_status(f"MODEL_NAME - {model}", "PASS")
    
    return len(issues) == 0, issues


def check_inference_code() -> Tuple[bool, list]:
    """Check inference.py follows requirements."""
    print("\n📝 Checking inference.py Compliance...")
    
    issues = []
    
    with open("inference.py", "r") as f:
        content = f.read()
    
    # Check OpenAI import
    if "from openai import OpenAI" in content:
        print_status("Uses OpenAI client", "PASS")
    else:
        print_status("Missing 'from openai import OpenAI'", "FAIL")
        issues.append("No OpenAI import")
    
    # Check environment variables
    if 'os.getenv("HF_TOKEN")' in content:
        print_status("Reads HF_TOKEN from env", "PASS")
    else:
        print_status("Doesn't read HF_TOKEN properly", "FAIL")
        issues.append("HF_TOKEN not from env")
    
    # Check no hardcoded defaults for HF_TOKEN
    if 'HF_TOKEN' in content and 'default' not in content.split('HF_TOKEN')[1].split('\n')[0].lower():
        print_status("No default for HF_TOKEN", "PASS")
    else:
        print_status("Has default for HF_TOKEN (NOT ALLOWED!)", "WARN")
    
    # Check log format
    if "[START]" in content and "[STEP]" in content and "[END]" in content:
        print_status("Uses [START]/[STEP]/[END] log format", "PASS")
    else:
        print_status("Missing required log format", "FAIL")
        issues.append("Wrong log format")
    
    return len(issues) == 0, issues


def test_server_startup() -> bool:
    """Test if server starts successfully."""
    print("\n🚀 Testing Server Startup...")
    
    try:
        # Start server in background
        proc = subprocess.Popen(
            ["python", "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print_status("Waiting for server to start...", "INFO")
        time.sleep(5)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:7860/health", timeout=5)
            if response.status_code == 200:
                print_status("Server started successfully", "PASS")
                result = True
            else:
                print_status(f"Server returned {response.status_code}", "FAIL")
                result = False
        except requests.exceptions.RequestException as e:
            print_status(f"Server not responding: {e}", "FAIL")
            result = False
        
        # Kill server
        proc.terminate()
        proc.wait(timeout=5)
        
        return result
        
    except Exception as e:
        print_status(f"Error starting server: {e}", "FAIL")
        return False


def test_openenv_endpoints() -> Tuple[bool, list]:
    """Test OpenEnv API endpoints."""
    print("\n🔌 Testing OpenEnv Endpoints...")
    
    issues = []
    
    # Start server
    proc = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)
    
    try:
        # Test /reset endpoint
        print_status("Testing POST /reset...", "INFO")
        reset_resp = requests.post(
            "http://localhost:7860/reset",
            json={"task_id": "cable_id_basic"},
            timeout=10
        )
        
        if reset_resp.status_code == 200:
            data = reset_resp.json()
            if "observation" in data:
                print_status("POST /reset - Returns observation", "PASS")
            else:
                print_status("POST /reset - Missing observation", "FAIL")
                issues.append("/reset missing observation")
        else:
            print_status(f"POST /reset - Failed ({reset_resp.status_code})", "FAIL")
            issues.append(f"/reset returned {reset_resp.status_code}")
        
        # Test /step endpoint
        print_status("Testing POST /step...", "INFO")
        step_resp = requests.post(
            "http://localhost:7860/step",
            json={"action": "Cable C"},
            timeout=10
        )
        
        if step_resp.status_code == 200:
            data = step_resp.json()
            required_fields = ["observation", "reward", "done"]
            missing = [f for f in required_fields if f not in data]
            
            if not missing:
                print_status("POST /step - All required fields present", "PASS")
            else:
                print_status(f"POST /step - Missing: {missing}", "FAIL")
                issues.append(f"/step missing {missing}")
        else:
            print_status(f"POST /step - Failed ({step_resp.status_code})", "FAIL")
            issues.append(f"/step returned {step_resp.status_code}")
        
    except Exception as e:
        print_status(f"Endpoint test error: {e}", "FAIL")
        issues.append(str(e))
    
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    
    return len(issues) == 0, issues


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("🔍 OPENENV VALIDATION - Field Tech Visual Assistant")
    print("=" * 60)
    
    all_passed = True
    
    # Check files
    if not check_files():
        all_passed = False
    
    # Check environment variables
    env_ok, env_issues = check_env_vars()
    if not env_ok:
        all_passed = False
        print(f"\n{RED}Environment Issues:{RESET}")
        for issue in env_issues:
            print(f"  - {issue}")
    
    # Check inference.py code
    code_ok, code_issues = check_inference_code()
    if not code_ok:
        all_passed = False
        print(f"\n{RED}Code Issues:{RESET}")
        for issue in code_issues:
            print(f"  - {issue}")
    
    # Test server (only if HF_TOKEN is set)
    if os.getenv("HF_TOKEN"):
        if not test_server_startup():
            all_passed = False
        
        endpoints_ok, endpoint_issues = test_openenv_endpoints()
        if not endpoints_ok:
            all_passed = False
            print(f"\n{RED}Endpoint Issues:{RESET}")
            for issue in endpoint_issues:
                print(f"  - {issue}")
    else:
        print(f"\n{YELLOW}⚠ Skipping server tests - HF_TOKEN not set{RESET}")
    
    # Final result
    print("\n" + "=" * 60)
    if all_passed:
        print(f"{GREEN}✓ ALL CHECKS PASSED{RESET}")
        print("Your project is ready for submission!")
    else:
        print(f"{RED}✗ SOME CHECKS FAILED{RESET}")
        print("Please fix the issues above before submitting.")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
