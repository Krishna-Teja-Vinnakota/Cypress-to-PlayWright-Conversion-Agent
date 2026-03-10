# backend/services/test_executor.py
# Executes Cypress and Playwright tests using subprocess

import subprocess
import json
import os
from typing import Dict, List, Optional
from backend.config import settings

class TestExecutor:
    
    @staticmethod
    async def run_cypress_tests(
        session_id: str,
        file_type: str,
        target_url: str
    ) -> Dict:
        """
        Run Cypress tests directly from template directories
        
        Args:
            session_id: Session ID for finding the right test files
            file_type: "js" or "ts"
            target_url: Base URL to test against
            
        Returns: Test results dictionary
        """
        try:
            # Use template directories directly - NO COPYING!
            if file_type == "js":
                work_dir = os.path.join(settings.TEMPLATES_DIR, "cypress-js")
            else:
                work_dir = os.path.join(settings.TEMPLATES_DIR, "cypress-ts")
            
            # Run Cypress with specific file pattern for this session
            cmd = [
                "npx", "cypress", "run",
                "--config", f"baseUrl={target_url}",
                "--spec", f"cypress/e2e/{session_id}_*.{file_type}",
                "--reporter", "json",
                "--reporter-options", f"output={work_dir}/results_{session_id}.json"
            ]
            
            print(f"🔵 Running Cypress tests directly from template: {work_dir}")
            print(f"Command: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            print(f"📊 Cypress exit code: {process.returncode}")
            
            # Parse results from stdout (Cypress JSON reporter outputs to console)
            try:
                # Find JSON in stdout (it's embedded in the output)
                stdout = process.stdout
                # Look for the JSON object that starts with {"stats"
                import re
                json_match = re.search(r'\{[\s\S]*?"stats"[\s\S]*?\}(?=\n|$)', stdout)
                
                if json_match:
                    results = json.loads(json_match.group(0))
                    print(f"✅ Parsed Cypress results: {results.get('stats', {})}")
                    return TestExecutor._parse_cypress_results(results)
                else:
                    # Try to read from file as fallback
                    results_file = os.path.join(work_dir, f"results_{session_id}.json")
                    if os.path.exists(results_file):
                        with open(results_file, 'r') as f:
                            results = json.load(f)
                        os.remove(results_file)
                        return TestExecutor._parse_cypress_results(results)
                    else:
                        print(f"⚠️ No JSON found in output")
                        return {
                            "success": False,
                            "error": "Could not parse test results",
                            "stdout": stdout[:500]
                        }
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                return {
                    "success": False,
                    "error": f"Failed to parse results: {str(e)}",
                    "stdout": process.stdout[:500]
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def run_playwright_tests(
        session_id: str,
        file_type: str,
        target_url: str
    ) -> Dict:
        """
        Run Playwright tests directly from template directories
        
        Args:
            session_id: Session ID for finding the right test files
            file_type: "js" or "ts"
            target_url: Base URL to test against
            
        Returns: Test results dictionary
        """
        try:
            # Use template directories directly - NO COPYING!
            if file_type == "js":
                work_dir = os.path.join(settings.TEMPLATES_DIR, "playwright-js")
            else:
                work_dir = os.path.join(settings.TEMPLATES_DIR, "playwright-ts")
            
            # Find the actual test file first
            import glob
            test_pattern = os.path.join(work_dir, "tests", f"{session_id}_*.spec.{file_type}")
            test_files = glob.glob(test_pattern)
            
            if not test_files:
                print(f"⚠️ No test files found matching: {test_pattern}")
                return {
                    "success": False,
                    "error": f"No test files found for session {session_id}",
                    "tests": [],
                    "summary": {"total": 0, "passed": 0, "failed": 0, "duration": 0}
                }
            
            # Get just the filename
            test_file = os.path.basename(test_files[0])
            
            # Run Playwright with specific file
            cmd = [
                "npx", "playwright", "test",
                test_file,
                "--reporter=json"
            ]
            
            # Set base URL as environment variable
            env = os.environ.copy()
            env["BASE_URL"] = target_url
            
            print(f"🟢 Running Playwright tests directly from template: {work_dir}")
            print(f"Command: {' '.join(cmd)}")
            print(f"Test file: {test_file}")
            
            process = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                env=env,
                timeout=300
            )
            
            print(f"📊 Playwright exit code: {process.returncode}")
            
            # Parse results from stdout (Playwright JSON reporter)
            try:
                results = json.loads(process.stdout)
                print(f"✅ Parsed Playwright results: {results.get('stats', {})}")
                return TestExecutor._parse_playwright_results(results)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"Stdout preview: {process.stdout[:500]}")
                return {
                    "success": False,
                    "error": f"Failed to parse results: {str(e)}",
                    "stdout": process.stdout[:500],
                    "stderr": process.stderr[:500]
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _parse_cypress_results(results: Dict) -> Dict:
        """Parse Cypress JSON results"""
        tests = []
        
        # Check if results have runs
        runs = results.get("runs", [])
        if not runs:
            print("⚠️ No test runs found in results")
            return {
                "success": False,
                "error": "No tests were executed. Make sure the target application is running.",
                "tests": [],
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "duration": 0
                }
            }
        
        for run in runs:
            specs = run.get("specs", [])
            if not specs:
                print("⚠️ No specs found in run")
                continue
                
            for spec in specs:
                spec_tests = spec.get("tests", [])
                if not spec_tests:
                    print(f"⚠️ No tests found in spec: {spec.get('name')}")
                    continue
                    
                for test in spec_tests:
                    tests.append({
                        "file_name": os.path.basename(spec["name"]),
                        "test_name": " - ".join(test.get("title", [])),
                        "status": "passed" if test["state"] == "passed" else "failed",
                        "duration": test.get("duration", 0),
                        "error": test.get("error", {}).get("message") if test.get("error") else None
                    })
        
        total = len(tests)
        passed = sum(1 for t in tests if t["status"] == "passed")
        
        if total == 0:
            print("⚠️ No tests were executed")
            return {
                "success": False,
                "error": "No tests were executed. Check if the application is running on the target URL.",
                "tests": [],
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "duration": 0
                }
            }
        
        return {
            "success": True,
            "tests": tests,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "duration": sum(t["duration"] for t in tests)
            }
        }
    
    @staticmethod
    def _parse_playwright_results(results: Dict) -> Dict:
        """Parse Playwright JSON results"""
        tests = []
        
        for suite in results.get("suites", []):
            for spec in suite.get("specs", []):
                for test in spec.get("tests", []):
                    for result in test.get("results", []):
                        tests.append({
                            "file_name": os.path.basename(spec.get("file", "")),
                            "test_name": spec.get("title", ""),
                            "status": result.get("status", "unknown"),
                            "duration": result.get("duration", 0),
                            "error": result.get("error", {}).get("message") if result.get("error") else None
                        })
        
        total = len(tests)
        passed = sum(1 for t in tests if t["status"] == "passed")
        
        return {
            "success": True,
            "tests": tests,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "duration": sum(t["duration"] for t in tests)
            }
        }

test_executor = TestExecutor()