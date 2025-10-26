#!/usr/bin/env python3
"""
Comprehensive LLM Testing Suite Runner
Orchestrates all LLM integration tests and generates detailed reports
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import argparse

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from test_llm_integration_suite import LLMIntegrationTestSuite
from test_prompt_effectiveness import PromptEffectivenessTestSuite
from test_end_to_end_integration import EndToEndIntegrationTestSuite

import structlog
logger = structlog.get_logger(__name__)

class ComprehensiveLLMTestRunner:
    """Comprehensive test runner for all LLM integration tests"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    async def run_all_tests(self, test_categories: List[str] = None) -> Dict[str, Any]:
        """Run all LLM integration test suites"""
        self.start_time = time.time()
        
        print("🚀 COMPREHENSIVE LLM INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"⏰ Started: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔑 OpenAI API Key: {'✅ Configured' if settings.OPENAI_API_KEY else '❌ Not Configured'}")
        print(f"🐍 Python Version: {sys.version.split()[0]}")
        print(f"📁 Working Directory: {os.getcwd()}")
        print("=" * 80)
        
        # Default test categories
        if test_categories is None:
            test_categories = ["integration", "prompts", "end_to_end"]
        
        # Run test suites based on categories
        if "integration" in test_categories:
            await self._run_integration_tests()
        
        if "prompts" in test_categories:
            await self._run_prompt_tests()
        
        if "end_to_end" in test_categories:
            await self._run_end_to_end_tests()
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        comprehensive_results = self._generate_comprehensive_report()
        
        # Display final summary
        self._display_final_summary(comprehensive_results)
        
        # Save results to file if configured
        if self.config.get("save_results", True):
            await self._save_results_to_file(comprehensive_results)
        
        return comprehensive_results
    
    async def _run_integration_tests(self):
        """Run LLM integration tests"""
        print("\n🧪 RUNNING LLM INTEGRATION TESTS")
        print("-" * 50)
        
        try:
            integration_suite = LLMIntegrationTestSuite()
            self.test_results["integration"] = await integration_suite.run_comprehensive_test_suite()
            print("✅ LLM Integration tests completed")
        except Exception as e:
            print(f"❌ LLM Integration tests failed: {str(e)}")
            self.test_results["integration"] = {
                "error": str(e),
                "overall_results": {"success_rate": 0.0}
            }
    
    async def _run_prompt_tests(self):
        """Run prompt effectiveness tests"""
        print("\n📝 RUNNING PROMPT EFFECTIVENESS TESTS")
        print("-" * 50)
        
        try:
            prompt_suite = PromptEffectivenessTestSuite()
            self.test_results["prompts"] = await prompt_suite.run_prompt_effectiveness_tests()
            print("✅ Prompt effectiveness tests completed")
        except Exception as e:
            print(f"❌ Prompt effectiveness tests failed: {str(e)}")
            self.test_results["prompts"] = {
                "error": str(e),
                "overall_results": {"success_rate": 0.0}
            }
    
    async def _run_end_to_end_tests(self):
        """Run end-to-end integration tests"""
        print("\n🔄 RUNNING END-TO-END INTEGRATION TESTS")
        print("-" * 50)
        
        try:
            e2e_suite = EndToEndIntegrationTestSuite()
            self.test_results["end_to_end"] = await e2e_suite.run_end_to_end_test_suite()
            print("✅ End-to-end integration tests completed")
        except Exception as e:
            print(f"❌ End-to-end integration tests failed: {str(e)}")
            self.test_results["end_to_end"] = {
                "error": str(e),
                "overall_results": {"overall_success_rate": 0.0}
            }
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_execution_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Extract key metrics from each test suite
        metrics = {
            "execution_time": total_execution_time,
            "test_suites_run": len(self.test_results),
            "test_suites_passed": 0,
            "overall_success_rate": 0.0,
            "detailed_metrics": {}
        }
        
        success_rates = []
        
        # Integration tests metrics
        if "integration" in self.test_results:
            integration_results = self.test_results["integration"]
            if "error" not in integration_results:
                integration_success = integration_results.get("overall_results", {}).get("success_rate", 0.0)
                success_rates.append(integration_success)
                metrics["detailed_metrics"]["integration"] = {
                    "success_rate": integration_success,
                    "total_tests": integration_results.get("overall_results", {}).get("total_tests", 0),
                    "passed_tests": integration_results.get("overall_results", {}).get("total_passed", 0),
                    "average_accuracy": integration_results.get("overall_results", {}).get("average_accuracy", 0.0)
                }
                if integration_success >= 0.7:
                    metrics["test_suites_passed"] += 1
        
        # Prompt tests metrics
        if "prompts" in self.test_results:
            prompt_results = self.test_results["prompts"]
            if "error" not in prompt_results:
                prompt_success = prompt_results.get("overall_results", {}).get("success_rate", 0.0)
                success_rates.append(prompt_success)
                metrics["detailed_metrics"]["prompts"] = {
                    "success_rate": prompt_success,
                    "average_quality": prompt_results.get("overall_results", {}).get("average_quality_score", 0.0)
                }
                if prompt_success >= 0.7:
                    metrics["test_suites_passed"] += 1
        
        # End-to-end tests metrics
        if "end_to_end" in self.test_results:
            e2e_results = self.test_results["end_to_end"]
            if "error" not in e2e_results:
                e2e_success = e2e_results.get("overall_results", {}).get("overall_success_rate", 0.0)
                success_rates.append(e2e_success)
                metrics["detailed_metrics"]["end_to_end"] = {
                    "success_rate": e2e_success,
                    "workflow_success_rate": e2e_results.get("overall_results", {}).get("workflow_success_rate", 0.0),
                    "interface_success_rate": e2e_results.get("overall_results", {}).get("interface_success_rate", 0.0),
                    "average_execution_time": e2e_results.get("overall_results", {}).get("average_execution_time", 0.0)
                }
                if e2e_success >= 0.7:
                    metrics["test_suites_passed"] += 1
        
        # Calculate overall success rate
        metrics["overall_success_rate"] = sum(success_rates) / len(success_rates) if success_rates else 0.0
        
        return {
            "summary": metrics,
            "detailed_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "openai_configured": bool(settings.OPENAI_API_KEY),
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }
        }
    
    def _display_final_summary(self, comprehensive_results: Dict[str, Any]):
        """Display final comprehensive summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE LLM INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        summary = comprehensive_results["summary"]
        
        # Overall metrics
        print(f"⏱️  Total Execution Time: {summary['execution_time']:.1f} seconds")
        print(f"🧪 Test Suites Run: {summary['test_suites_run']}")
        print(f"✅ Test Suites Passed: {summary['test_suites_passed']}")
        print(f"🎯 Overall Success Rate: {summary['overall_success_rate']:.1%}")
        
        # Detailed metrics by category
        print(f"\n📈 DETAILED METRICS BY CATEGORY:")
        
        for category, metrics in summary["detailed_metrics"].items():
            print(f"\n   {category.upper()}:")
            print(f"      Success Rate: {metrics['success_rate']:.1%}")
            
            if "total_tests" in metrics:
                print(f"      Tests: {metrics['passed_tests']}/{metrics['total_tests']}")
            
            if "average_accuracy" in metrics:
                print(f"      Average Accuracy: {metrics['average_accuracy']:.2f}")
            
            if "average_quality" in metrics:
                print(f"      Average Quality: {metrics['average_quality']:.2f}")
            
            if "workflow_success_rate" in metrics:
                print(f"      Workflow Success: {metrics['workflow_success_rate']:.1%}")
                print(f"      Interface Success: {metrics['interface_success_rate']:.1%}")
        
        # Overall assessment
        print(f"\n🏆 OVERALL ASSESSMENT:")
        overall_rate = summary['overall_success_rate']
        
        if overall_rate >= 0.9:
            print("   🎉 EXCELLENT! LLM integration is performing exceptionally well.")
            print("   ✨ System is production-ready with high confidence.")
            print("   🚀 All major functionality is working as expected.")
        elif overall_rate >= 0.8:
            print("   ✅ VERY GOOD! LLM integration is performing well.")
            print("   🔧 Minor optimizations may improve performance further.")
            print("   📈 System is ready for production with monitoring.")
        elif overall_rate >= 0.7:
            print("   ⚠️  GOOD! LLM integration is functional with room for improvement.")
            print("   🔍 Review failed tests for optimization opportunities.")
            print("   📋 Consider additional testing before production deployment.")
        elif overall_rate >= 0.5:
            print("   ⚠️  MODERATE! LLM integration needs improvement.")
            print("   🛠️  Significant optimization required before production.")
            print("   📊 Focus on improving prompt quality and agent coordination.")
        else:
            print("   ❌ POOR! LLM integration requires major improvements.")
            print("   🚨 System not ready for production deployment.")
            print("   🔧 Review configuration, prompts, and agent implementations.")
        
        # Specific recommendations
        print(f"\n💡 SPECIFIC RECOMMENDATIONS:")
        
        if not comprehensive_results["environment"]["openai_configured"]:
            print("   🔑 Configure OpenAI API key for full LLM testing capabilities")
        
        # Category-specific recommendations
        for category, metrics in summary["detailed_metrics"].items():
            if metrics["success_rate"] < 0.7:
                if category == "integration":
                    print(f"   🧪 {category.upper()}: Improve agent LLM integration and prompt optimization")
                elif category == "prompts":
                    print(f"   📝 {category.upper()}: Enhance prompt templates and context management")
                elif category == "end_to_end":
                    print(f"   🔄 {category.upper()}: Optimize workflow coordination and error handling")
        
        # Performance recommendations
        if "end_to_end" in summary["detailed_metrics"]:
            avg_time = summary["detailed_metrics"]["end_to_end"].get("average_execution_time", 0)
            if avg_time > 30:
                print(f"   ⚡ PERFORMANCE: Consider optimizing workflow execution time (current: {avg_time:.1f}s)")
        
        print("\n" + "=" * 80)
    
    async def _save_results_to_file(self, comprehensive_results: Dict[str, Any]):
        """Save test results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_test_results_{timestamp}.json"
            filepath = os.path.join(os.getcwd(), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📄 Test results saved to: {filepath}")
            
        except Exception as e:
            print(f"⚠️  Failed to save results to file: {str(e)}")
    
    def get_exit_code(self, comprehensive_results: Dict[str, Any]) -> int:
        """Get appropriate exit code based on test results"""
        success_rate = comprehensive_results["summary"]["overall_success_rate"]
        
        if success_rate >= 0.6:
            return 0  # Excellent/Very Good
        elif success_rate >= 0.4:
            return 0  # Good (acceptable for development)
        else:
            return 1  # Needs improvement


async def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Comprehensive LLM Integration Test Suite")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["integration", "prompts", "end_to_end"],
        default=["integration", "prompts", "end_to_end"],
        help="Test categories to run"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        default=True,
        help="Save test results to JSON file"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {"save_results": args.save_results}
    if args.config_file and os.path.exists(args.config_file):
        try:
            with open(args.config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"⚠️  Failed to load config file: {str(e)}")
    
    # Run comprehensive test suite
    test_runner = ComprehensiveLLMTestRunner(config)
    results = await test_runner.run_all_tests(args.categories)
    
    # Return appropriate exit code
    exit_code = test_runner.get_exit_code(results)
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)