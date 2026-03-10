# backend/services/comparison.py
# Compares Cypress and Playwright test results

from typing import Dict, List

class ComparisonService:
    
    @staticmethod
    def compare_results(
        cypress_results: Dict,
        playwright_results: Dict
    ) -> Dict:
        """
        Compare Cypress and Playwright test results
        
        Returns:
            Dictionary with comparison data and accuracy
        """
        cypress_tests = {
            test["test_name"]: test 
            for test in cypress_results.get("tests", [])
        }
        
        playwright_tests = {
            test["test_name"]: test 
            for test in playwright_results.get("tests", [])
        }
        
        comparisons = []
        matching_tests = 0
        total_tests = 0
        
        # Compare each test
        all_test_names = set(cypress_tests.keys()) | set(playwright_tests.keys())
        
        for test_name in all_test_names:
            cy_test = cypress_tests.get(test_name, {})
            pw_test = playwright_tests.get(test_name, {})
            
            cy_status = cy_test.get("status", "not_found")
            pw_status = pw_test.get("status", "not_found")
            
            match = cy_status == pw_status
            if match:
                matching_tests += 1
            
            total_tests += 1
            
            comparisons.append({
                "file_name": cy_test.get("file_name") or pw_test.get("file_name", ""),
                "test_name": test_name,
                "cypress_status": cy_status,
                "playwright_status": pw_status,
                "cypress_duration": cy_test.get("duration", 0),
                "playwright_duration": pw_test.get("duration", 0),
                "match": match
            })
        
        # Calculate accuracy
        accuracy = (matching_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "comparisons": comparisons,
            "accuracy": round(accuracy, 2),
            "total_tests": total_tests,
            "matching_tests": matching_tests,
            "conversion_success": accuracy >= 90  # 90% threshold
        }

comparison_service = ComparisonService()