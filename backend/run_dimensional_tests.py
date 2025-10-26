"""
Dimensional Processing Test Suite Runner
Executes all dimensional processing tests with real XML data

This script runs the complete test suite for dimensional processing:
1. End-to-end processing tests
2. Data quality validation tests  
3. Performance and load tests
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test modules
from test_dimensional_end_to_end_real_data import DimensionalEndToEndTester
from test_dimensional_data_quality_validation import DataQualityValidator
from test_dimensional_performance_load import DimensionalPerformanceTester


class DimensionalTestSuiteRunner:
    """Comprehensive test suite runner for dimensional processing"""
    
    def __init__(self):
        self.test_results = {
            'end_to_end': None,
            'data_quality': None,
            'performance_load': None,
            'overall_summary': {}
        }
    
    async def run_complete_test_suite(self):
        """Run the complete dimensional processing test suite"""
        print("🧪 DIMENSIONAL PROCESSING COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        overall_start_time = datetime.now()
        
        try:
            # 1. End-to-End Processing Tests
            print("\n🚀 PHASE 1: END-TO-END PROCESSING TESTS")
            print("-" * 60)
            
            e2e_start = datetime.now()
            try:
                e2e_tester = DimensionalEndToEndTester()
                await e2e_tester.run_dimensional_end_to_end_tests()
                
                self.test_results['end_to_end'] = {
                    'status': 'completed',
                    'duration_seconds': (datetime.now() - e2e_start).total_seconds(),
                    'test_results': e2e_tester.test_results,
                    'processing_metrics': e2e_tester.processing_metrics
                }
                
                print("✅ End-to-End Processing Tests Completed Successfully")
                
            except Exception as e:
                self.test_results['end_to_end'] = {
                    'status': 'failed',
                    'duration_seconds': (datetime.now() - e2e_start).total_seconds(),
                    'error': str(e)
                }
                print(f"❌ End-to-End Processing Tests Failed: {str(e)}")
            
            # 2. Data Quality Validation Tests
            print("\n🔍 PHASE 2: DATA QUALITY VALIDATION TESTS")
            print("-" * 60)
            
            quality_start = datetime.now()
            try:
                quality_validator = DataQualityValidator()
                await quality_validator.run_data_quality_validation_tests()
                
                self.test_results['data_quality'] = {
                    'status': 'completed',
                    'duration_seconds': (datetime.now() - quality_start).total_seconds(),
                    'validation_results': quality_validator.validation_results,
                    'quality_metrics': quality_validator.quality_metrics
                }
                
                print("✅ Data Quality Validation Tests Completed Successfully")
                
            except Exception as e:
                self.test_results['data_quality'] = {
                    'status': 'failed',
                    'duration_seconds': (datetime.now() - quality_start).total_seconds(),
                    'error': str(e)
                }
                print(f"❌ Data Quality Validation Tests Failed: {str(e)}")
            
            # 3. Performance and Load Tests
            print("\n⚡ PHASE 3: PERFORMANCE AND LOAD TESTS")
            print("-" * 60)
            
            perf_start = datetime.now()
            try:
                perf_tester = DimensionalPerformanceTester()
                await perf_tester.run_performance_and_load_tests()
                
                self.test_results['performance_load'] = {
                    'status': 'completed',
                    'duration_seconds': (datetime.now() - perf_start).total_seconds(),
                    'performance_results': perf_tester.performance_results,
                    'load_test_results': perf_tester.load_test_results
                }
                
                print("✅ Performance and Load Tests Completed Successfully")
                
            except Exception as e:
                self.test_results['performance_load'] = {
                    'status': 'failed',
                    'duration_seconds': (datetime.now() - perf_start).total_seconds(),
                    'error': str(e)
                }
                print(f"❌ Performance and Load Tests Failed: {str(e)}")
            
            # Generate overall summary
            overall_duration = (datetime.now() - overall_start_time).total_seconds()
            await self._generate_overall_summary(overall_duration)
            
        except Exception as e:
            print(f"\n❌ Test Suite Execution Failed: {str(e)}")
            raise
    
    async def _generate_overall_summary(self, total_duration: float):
        """Generate overall test suite summary"""
        print("\n" + "=" * 80)
        print("📊 OVERALL TEST SUITE SUMMARY")
        print("=" * 80)
        
        # Calculate overall statistics
        phases_completed = sum(1 for phase in self.test_results.values() 
                             if isinstance(phase, dict) and phase.get('status') == 'completed')
        phases_failed = sum(1 for phase in self.test_results.values() 
                          if isinstance(phase, dict) and phase.get('status') == 'failed')
        total_phases = phases_completed + phases_failed
        
        print(f"🕐 Total Execution Time: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        print(f"📋 Test Phases: {total_phases}")
        print(f"✅ Completed Phases: {phases_completed}")
        print(f"❌ Failed Phases: {phases_failed}")
        print(f"📈 Success Rate: {(phases_completed/total_phases*100):.1f}%")
        
        # Phase-specific summaries
        print(f"\n📊 Phase Results:")
        
        # End-to-End Tests Summary
        e2e_result = self.test_results.get('end_to_end')
        if e2e_result:
            print(f"   🚀 End-to-End Processing:")
            print(f"     Status: {'✅ Completed' if e2e_result['status'] == 'completed' else '❌ Failed'}")
            print(f"     Duration: {e2e_result['duration_seconds']:.2f}s")
            
            if e2e_result['status'] == 'completed':
                test_results = e2e_result.get('test_results', [])
                successful_tests = sum(1 for r in test_results if r.get('success'))
                print(f"     Files Processed: {successful_tests}/{len(test_results)}")
                
                processing_metrics = e2e_result.get('processing_metrics', {})
                print(f"     Documents Processed: {processing_metrics.get('documents_processed', 0)}")
                print(f"     Fact Records Created: {processing_metrics.get('fact_records_created', 0)}")
        
        # Data Quality Tests Summary
        quality_result = self.test_results.get('data_quality')
        if quality_result:
            print(f"   🔍 Data Quality Validation:")
            print(f"     Status: {'✅ Completed' if quality_result['status'] == 'completed' else '❌ Failed'}")
            print(f"     Duration: {quality_result['duration_seconds']:.2f}s")
            
            if quality_result['status'] == 'completed':
                validation_results = quality_result.get('validation_results', [])
                successful_validations = sum(1 for r in validation_results if r.get('success'))
                print(f"     Validations Passed: {successful_validations}/{len(validation_results)}")
                
                quality_metrics = quality_result.get('quality_metrics', {})
                print(f"     Total Validations: {quality_metrics.get('total_validations', 0)}")
                print(f"     Passed Validations: {quality_metrics.get('passed_validations', 0)}")
        
        # Performance Tests Summary
        perf_result = self.test_results.get('performance_load')
        if perf_result:
            print(f"   ⚡ Performance and Load:")
            print(f"     Status: {'✅ Completed' if perf_result['status'] == 'completed' else '❌ Failed'}")
            print(f"     Duration: {perf_result['duration_seconds']:.2f}s")
            
            if perf_result['status'] == 'completed':
                performance_results = perf_result.get('performance_results', [])
                load_results = perf_result.get('load_test_results', [])
                total_perf_tests = len(performance_results) + len(load_results)
                successful_perf_tests = sum(1 for r in performance_results + load_results if r.get('success', True))
                print(f"     Performance Tests: {successful_perf_tests}/{total_perf_tests}")
        
        # Overall recommendations
        print(f"\n💡 Overall Recommendations:")
        
        recommendations = []
        
        # Check if all phases completed
        if phases_completed == total_phases:
            recommendations.append("All test phases completed successfully - system is ready for production")
        else:
            recommendations.append(f"Some test phases failed - review failed phases before production deployment")
        
        # Check end-to-end success rate
        if e2e_result and e2e_result['status'] == 'completed':
            test_results = e2e_result.get('test_results', [])
            if test_results:
                success_rate = sum(1 for r in test_results if r.get('success')) / len(test_results)
                if success_rate < 0.8:
                    recommendations.append("End-to-end success rate below 80% - investigate processing issues")
                elif success_rate > 0.95:
                    recommendations.append("Excellent end-to-end success rate - processing pipeline is robust")
        
        # Check data quality
        if quality_result and quality_result['status'] == 'completed':
            quality_metrics = quality_result.get('quality_metrics', {})
            total_validations = quality_metrics.get('total_validations', 0)
            passed_validations = quality_metrics.get('passed_validations', 0)
            
            if total_validations > 0:
                quality_rate = passed_validations / total_validations
                if quality_rate < 0.8:
                    recommendations.append("Data quality validation rate below 80% - review data processing logic")
                elif quality_rate > 0.95:
                    recommendations.append("Excellent data quality - validation processes are working well")
        
        # Check performance
        if perf_result and perf_result['status'] == 'completed':
            performance_results = perf_result.get('performance_results', [])
            processing_times = [r.get('processing_time_seconds', 0) for r in performance_results if r.get('success')]
            
            if processing_times:
                import statistics
                avg_time = statistics.mean(processing_times)
                if avg_time > 15:
                    recommendations.append("Average processing time exceeds 15 seconds - consider performance optimization")
                elif avg_time < 5:
                    recommendations.append("Excellent processing performance - average time under 5 seconds")
        
        if not recommendations:
            recommendations.append("System performance appears adequate - continue monitoring")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Save comprehensive test suite results
        await self._save_comprehensive_results(total_duration)
    
    async def _save_comprehensive_results(self, total_duration: float):
        """Save comprehensive test suite results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dimensional_test_suite_results_{timestamp}.json"
        
        try:
            # Prepare summary statistics
            phases_completed = sum(1 for phase in self.test_results.values() 
                                 if isinstance(phase, dict) and phase.get('status') == 'completed')
            phases_failed = sum(1 for phase in self.test_results.values() 
                              if isinstance(phase, dict) and phase.get('status') == 'failed')
            
            comprehensive_results = {
                "test_suite_metadata": {
                    "execution_timestamp": datetime.now().isoformat(),
                    "total_duration_seconds": total_duration,
                    "total_phases": phases_completed + phases_failed,
                    "completed_phases": phases_completed,
                    "failed_phases": phases_failed,
                    "overall_success_rate": (phases_completed / (phases_completed + phases_failed) * 100) if (phases_completed + phases_failed) > 0 else 0
                },
                "phase_results": self.test_results,
                "summary_statistics": {
                    "end_to_end_tests": self._summarize_e2e_results(),
                    "data_quality_tests": self._summarize_quality_results(),
                    "performance_tests": self._summarize_performance_results()
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Comprehensive test suite results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save comprehensive results: {str(e)}")
    
    def _summarize_e2e_results(self) -> Dict:
        """Summarize end-to-end test results"""
        e2e_result = self.test_results.get('end_to_end')
        if not e2e_result or e2e_result['status'] != 'completed':
            return {'status': 'not_available'}
        
        test_results = e2e_result.get('test_results', [])
        processing_metrics = e2e_result.get('processing_metrics', {})
        
        successful_tests = sum(1 for r in test_results if r.get('success'))
        
        return {
            'status': 'completed',
            'total_files_tested': len(test_results),
            'successful_files': successful_tests,
            'success_rate': (successful_tests / len(test_results) * 100) if test_results else 0,
            'documents_processed': processing_metrics.get('documents_processed', 0),
            'emitentes_created': processing_metrics.get('emitentes_created', 0),
            'produtos_processed': processing_metrics.get('produtos_processed', 0),
            'fact_records_created': processing_metrics.get('fact_records_created', 0),
            'total_processing_time': processing_metrics.get('total_processing_time', 0)
        }
    
    def _summarize_quality_results(self) -> Dict:
        """Summarize data quality test results"""
        quality_result = self.test_results.get('data_quality')
        if not quality_result or quality_result['status'] != 'completed':
            return {'status': 'not_available'}
        
        validation_results = quality_result.get('validation_results', [])
        quality_metrics = quality_result.get('quality_metrics', {})
        
        successful_validations = sum(1 for r in validation_results if r.get('success'))
        
        return {
            'status': 'completed',
            'total_files_validated': len(validation_results),
            'successful_validations': successful_validations,
            'validation_success_rate': (successful_validations / len(validation_results) * 100) if validation_results else 0,
            'total_quality_checks': quality_metrics.get('total_validations', 0),
            'passed_quality_checks': quality_metrics.get('passed_validations', 0),
            'cnpj_validations': quality_metrics.get('cnpj_validations', 0),
            'financial_validations': quality_metrics.get('financial_validations', 0),
            'formatting_validations': quality_metrics.get('formatting_validations', 0)
        }
    
    def _summarize_performance_results(self) -> Dict:
        """Summarize performance test results"""
        perf_result = self.test_results.get('performance_load')
        if not perf_result or perf_result['status'] != 'completed':
            return {'status': 'not_available'}
        
        performance_results = perf_result.get('performance_results', [])
        load_results = perf_result.get('load_test_results', [])
        
        # Calculate performance statistics
        processing_times = [r.get('processing_time_seconds', 0) for r in performance_results if r.get('success')]
        memory_usage = [r.get('peak_memory_mb', 0) for r in performance_results if r.get('success')]
        
        import statistics
        
        return {
            'status': 'completed',
            'total_performance_tests': len(performance_results),
            'total_load_tests': len(load_results),
            'average_processing_time': statistics.mean(processing_times) if processing_times else 0,
            'fastest_processing_time': min(processing_times) if processing_times else 0,
            'slowest_processing_time': max(processing_times) if processing_times else 0,
            'average_memory_usage': statistics.mean(memory_usage) if memory_usage else 0,
            'peak_memory_usage': max(memory_usage) if memory_usage else 0,
            'concurrent_processing_tested': any('concurrency_level' in r for r in performance_results),
            'load_testing_completed': len(load_results) > 0
        }


async def main():
    """Main test suite execution"""
    print("🧪 Dimensional Processing Comprehensive Test Suite")
    print("This will run all dimensional processing tests with real XML data")
    print("Estimated time: 10-15 minutes depending on system performance")
    print()
    
    # Ask for confirmation
    try:
        response = input("Do you want to proceed with the complete test suite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Test suite execution cancelled.")
            return
    except KeyboardInterrupt:
        print("\nTest suite execution cancelled.")
        return
    
    runner = DimensionalTestSuiteRunner()
    await runner.run_complete_test_suite()


if __name__ == "__main__":
    asyncio.run(main())