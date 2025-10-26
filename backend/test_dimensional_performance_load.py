"""
Dimensional Processing Performance and Load Tests
Task 7.3: Implementar testes de performance e carga

This test suite validates performance characteristics of the dimensional processing pipeline,
including concurrent processing, memory usage, and system behavior under load.
"""

import asyncio
import json
import os
import sys
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Import dimensional processing components
from agents.dimensional_coordinator import DimensionalCoordinator
from utils.database import get_supabase_client


class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Monitor system metrics in a loop"""
        while self.monitoring:
            try:
                # Get current process
                process = psutil.Process()
                
                # Collect metrics
                metric = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'memory_percent': process.memory_percent(),
                    'threads': process.num_threads(),
                    'open_files': len(process.open_files()),
                    'connections': len(process.connections()),
                    'system_cpu': psutil.cpu_percent(),
                    'system_memory': psutil.virtual_memory().percent,
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                }
                
                self.metrics.append(metric)
                
            except Exception as e:
                logger.warning("Performance monitoring error", error=str(e))
            
            time.sleep(1)  # Monitor every second
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics if m['cpu_percent'] is not None]
        memory_values = [m['memory_mb'] for m in self.metrics]
        
        return {
            'duration_seconds': len(self.metrics),
            'cpu_usage': {
                'avg': statistics.mean(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory_usage': {
                'avg_mb': statistics.mean(memory_values),
                'max_mb': max(memory_values),
                'min_mb': min(memory_values),
                'peak_percent': max(m['memory_percent'] for m in self.metrics)
            },
            'threads': {
                'avg': statistics.mean(m['threads'] for m in self.metrics),
                'max': max(m['threads'] for m in self.metrics)
            },
            'system_resources': {
                'avg_cpu': statistics.mean(m['system_cpu'] for m in self.metrics),
                'avg_memory': statistics.mean(m['system_memory'] for m in self.metrics)
            }
        }


class DimensionalPerformanceTester:
    """Comprehensive performance and load tester for dimensional processing"""
    
    def __init__(self):
        self.coordinator = DimensionalCoordinator()
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.performance_results = []
        self.load_test_results = []
        self.performance_monitor = PerformanceMonitor()
    
    async def run_performance_and_load_tests(self):
        """Run comprehensive performance and load tests"""
        print("⚡ Starting Dimensional Processing Performance and Load Tests")
        print("=" * 80)
        
        # Initialize coordinator
        await self.coordinator.initialize()
        
        try:
            # Get XML files
            xml_files_dir = Path("../xml_nf")
            if not xml_files_dir.exists():
                xml_files_dir = Path("xml_nf")
            
            if not xml_files_dir.exists():
                print("❌ XML files directory not found")
                return
            
            # Get all XML files (both .xml and .XML extensions)
            xml_files = []
            xml_files.extend(xml_files_dir.glob("*.xml"))
            xml_files.extend(xml_files_dir.glob("*.XML"))
            
            # Remove duplicates by converting to set and back to list
            xml_files = list(set(xml_files))
            
            if not xml_files:
                print("❌ No XML files found")
                return
            
            print(f"📁 Found {len(xml_files)} XML files for performance testing")
            
            # 1. Single Document Performance Tests
            print("\n🚀 Running Single Document Performance Tests...")
            await self._run_single_document_performance_tests(xml_files)
            
            # 2. Concurrent Processing Tests
            print("\n🔄 Running Concurrent Processing Tests...")
            await self._run_concurrent_processing_tests(xml_files)
            
            # 3. Memory Usage Tests
            print("\n💾 Running Memory Usage Tests...")
            await self._run_memory_usage_tests(xml_files)
            
            # 4. Load Testing with Multiple Users
            print("\n👥 Running Load Tests with Multiple Users...")
            await self._run_load_tests(xml_files)
            
            # 5. Stress Testing
            print("\n🔥 Running Stress Tests...")
            await self._run_stress_tests(xml_files)
            
            # Generate comprehensive performance report
            await self._generate_performance_report()
            
            print("\n🎉 Performance and Load Tests Completed!")
            
        finally:
            # Cleanup coordinator
            await self.coordinator.cleanup()
    
    async def _run_single_document_performance_tests(self, xml_files: List[Path]):
        """Test performance characteristics of single document processing"""
        print("   📊 Testing single document processing performance...")
        
        single_doc_results = []
        
        for i, xml_file in enumerate(xml_files[:3], 1):  # Test first 3 files
            print(f"   Processing file {i}: {xml_file.name}")
            
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            # Measure processing time
            start_time = time.time()
            
            try:
                import uuid
                document_id = str(uuid.uuid4())
                
                result = await self.coordinator.process_document_pipeline(
                    xml_content, document_id, 'NFE'
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Stop monitoring
                self.performance_monitor.stop_monitoring()
                performance_summary = self.performance_monitor.get_summary()
                
                single_doc_result = {
                    'filename': xml_file.name,
                    'file_size_bytes': xml_file.stat().st_size,
                    'processing_time_seconds': processing_time,
                    'throughput_bytes_per_second': xml_file.stat().st_size / processing_time,
                    'success': True,
                    'performance_metrics': performance_summary,
                    'pipeline_summary': result.get('summary', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"     ✅ Processed in {processing_time:.2f}s")
                print(f"     📈 Throughput: {single_doc_result['throughput_bytes_per_second']:.0f} bytes/s")
                print(f"     💾 Peak Memory: {performance_summary.get('memory_usage', {}).get('max_mb', 0):.1f} MB")
                
            except Exception as e:
                self.performance_monitor.stop_monitoring()
                single_doc_result = {
                    'filename': xml_file.name,
                    'file_size_bytes': xml_file.stat().st_size,
                    'processing_time_seconds': 0,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"     ❌ Failed: {str(e)}")
            
            single_doc_results.append(single_doc_result)
        
        self.performance_results.extend(single_doc_results)
    
    async def _run_concurrent_processing_tests(self, xml_files: List[Path]):
        """Test concurrent processing performance"""
        print("   🔄 Testing concurrent document processing...")
        
        concurrent_results = []
        concurrency_levels = [2, 3, 5]  # Test different concurrency levels
        
        for concurrency in concurrency_levels:
            print(f"   Testing concurrency level: {concurrency}")
            
            # Select files for concurrent processing
            test_files = xml_files[:concurrency]
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            start_time = time.time()
            
            try:
                # Create tasks for concurrent processing
                tasks = []
                for i, xml_file in enumerate(test_files):
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    
                    import uuid
                    document_id = str(uuid.uuid4())
                    
                    task = self.coordinator.process_document_pipeline(
                        xml_content, document_id, 'NFE'
                    )
                    tasks.append((task, xml_file))
                
                # Execute tasks concurrently
                results = await asyncio.gather(*[task for task, _ in tasks], return_exceptions=True)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Stop monitoring
                self.performance_monitor.stop_monitoring()
                performance_summary = self.performance_monitor.get_summary()
                
                # Analyze results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                failed_results = [r for r in results if isinstance(r, Exception)]
                
                total_bytes = sum(f.stat().st_size for _, f in tasks)
                
                concurrent_result = {
                    'concurrency_level': concurrency,
                    'total_files': len(test_files),
                    'successful_files': len(successful_results),
                    'failed_files': len(failed_results),
                    'total_processing_time_seconds': total_time,
                    'total_bytes_processed': total_bytes,
                    'concurrent_throughput_bytes_per_second': total_bytes / total_time,
                    'average_time_per_file': total_time / len(test_files),
                    'performance_metrics': performance_summary,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"     ✅ Processed {len(successful_results)}/{len(test_files)} files in {total_time:.2f}s")
                print(f"     📈 Concurrent Throughput: {concurrent_result['concurrent_throughput_bytes_per_second']:.0f} bytes/s")
                print(f"     💾 Peak Memory: {performance_summary.get('memory_usage', {}).get('max_mb', 0):.1f} MB")
                
                if failed_results:
                    print(f"     ⚠️  {len(failed_results)} files failed processing")
                
            except Exception as e:
                self.performance_monitor.stop_monitoring()
                concurrent_result = {
                    'concurrency_level': concurrency,
                    'total_files': len(test_files),
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"     ❌ Concurrent processing failed: {str(e)}")
            
            concurrent_results.append(concurrent_result)
        
        self.performance_results.extend(concurrent_results)
    
    async def _run_memory_usage_tests(self, xml_files: List[Path]):
        """Test memory usage patterns during processing"""
        print("   💾 Testing memory usage patterns...")
        
        memory_results = []
        
        # Test with largest file
        largest_file = max(xml_files, key=lambda f: f.stat().st_size)
        print(f"   Testing with largest file: {largest_file.name} ({largest_file.stat().st_size:,} bytes)")
        
        # Read XML content
        with open(largest_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Start detailed memory monitoring
        self.performance_monitor.start_monitoring()
        
        # Get initial memory baseline
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        start_time = time.time()
        
        try:
            import uuid
            document_id = str(uuid.uuid4())
            
            result = await self.coordinator.process_document_pipeline(
                xml_content, document_id, 'NFE'
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Stop monitoring
            self.performance_monitor.stop_monitoring()
            performance_summary = self.performance_monitor.get_summary()
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024
            
            memory_result = {
                'test_type': 'large_file_memory',
                'filename': largest_file.name,
                'file_size_bytes': largest_file.stat().st_size,
                'processing_time_seconds': processing_time,
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'peak_memory_mb': performance_summary.get('memory_usage', {}).get('max_mb', 0),
                'memory_increase_mb': final_memory - initial_memory,
                'memory_efficiency_bytes_per_mb': largest_file.stat().st_size / (performance_summary.get('memory_usage', {}).get('max_mb', 1)),
                'success': True,
                'performance_metrics': performance_summary,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"     ✅ Processed in {processing_time:.2f}s")
            print(f"     📊 Initial Memory: {initial_memory:.1f} MB")
            print(f"     📈 Peak Memory: {memory_result['peak_memory_mb']:.1f} MB")
            print(f"     📉 Final Memory: {final_memory:.1f} MB")
            print(f"     🔄 Memory Increase: {memory_result['memory_increase_mb']:.1f} MB")
            
        except Exception as e:
            self.performance_monitor.stop_monitoring()
            memory_result = {
                'test_type': 'large_file_memory',
                'filename': largest_file.name,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"     ❌ Memory test failed: {str(e)}")
        
        memory_results.append(memory_result)
        
        # Test memory usage with multiple sequential files
        print("   Testing sequential processing memory patterns...")
        
        self.performance_monitor.start_monitoring()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        sequential_start = time.time()
        processed_files = 0
        
        try:
            for i, xml_file in enumerate(xml_files[:3]):  # Process 3 files sequentially
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                import uuid
                document_id = str(uuid.uuid4())
                
                await self.coordinator.process_document_pipeline(
                    xml_content, document_id, 'NFE'
                )
                
                processed_files += 1
            
            sequential_end = time.time()
            sequential_time = sequential_end - sequential_start
            
            self.performance_monitor.stop_monitoring()
            performance_summary = self.performance_monitor.get_summary()
            
            final_memory = process.memory_info().rss / 1024 / 1024
            
            sequential_result = {
                'test_type': 'sequential_memory',
                'files_processed': processed_files,
                'total_processing_time_seconds': sequential_time,
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'peak_memory_mb': performance_summary.get('memory_usage', {}).get('max_mb', 0),
                'memory_increase_mb': final_memory - initial_memory,
                'average_time_per_file': sequential_time / processed_files,
                'success': True,
                'performance_metrics': performance_summary,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"     ✅ Processed {processed_files} files sequentially in {sequential_time:.2f}s")
            print(f"     📊 Memory Growth: {sequential_result['memory_increase_mb']:.1f} MB")
            print(f"     📈 Peak Memory: {sequential_result['peak_memory_mb']:.1f} MB")
            
        except Exception as e:
            self.performance_monitor.stop_monitoring()
            sequential_result = {
                'test_type': 'sequential_memory',
                'files_processed': processed_files,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"     ❌ Sequential memory test failed: {str(e)}")
        
        memory_results.append(sequential_result)
        self.performance_results.extend(memory_results)
    
    async def _run_load_tests(self, xml_files: List[Path]):
        """Test system behavior under load with multiple simulated users"""
        print("   👥 Testing system behavior under load...")
        
        load_results = []
        user_counts = [5, 10, 15]  # Simulate different numbers of concurrent users
        
        for user_count in user_counts:
            print(f"   Testing with {user_count} concurrent users...")
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            start_time = time.time()
            
            try:
                # Create tasks simulating multiple users
                user_tasks = []
                
                for user_id in range(user_count):
                    # Each user processes a random file
                    xml_file = xml_files[user_id % len(xml_files)]
                    
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    
                    import uuid
                    document_id = str(uuid.uuid4())
                    
                    task = self._simulate_user_processing(xml_content, document_id, user_id)
                    user_tasks.append(task)
                
                # Execute all user tasks concurrently
                results = await asyncio.gather(*user_tasks, return_exceptions=True)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Stop monitoring
                self.performance_monitor.stop_monitoring()
                performance_summary = self.performance_monitor.get_summary()
                
                # Analyze results
                successful_users = sum(1 for r in results if not isinstance(r, Exception))
                failed_users = user_count - successful_users
                
                # Calculate response times
                response_times = [r.get('processing_time', 0) for r in results if isinstance(r, dict)]
                
                load_result = {
                    'test_type': 'load_test',
                    'concurrent_users': user_count,
                    'successful_users': successful_users,
                    'failed_users': failed_users,
                    'total_test_time_seconds': total_time,
                    'success_rate': (successful_users / user_count) * 100,
                    'response_times': {
                        'avg_seconds': statistics.mean(response_times) if response_times else 0,
                        'min_seconds': min(response_times) if response_times else 0,
                        'max_seconds': max(response_times) if response_times else 0,
                        'median_seconds': statistics.median(response_times) if response_times else 0
                    },
                    'throughput_users_per_second': successful_users / total_time,
                    'performance_metrics': performance_summary,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"     ✅ {successful_users}/{user_count} users completed successfully")
                print(f"     📈 Success Rate: {load_result['success_rate']:.1f}%")
                print(f"     ⏱️  Average Response Time: {load_result['response_times']['avg_seconds']:.2f}s")
                print(f"     🚀 Throughput: {load_result['throughput_users_per_second']:.2f} users/s")
                print(f"     💾 Peak Memory: {performance_summary.get('memory_usage', {}).get('max_mb', 0):.1f} MB")
                
                if failed_users > 0:
                    print(f"     ⚠️  {failed_users} users failed")
                
            except Exception as e:
                self.performance_monitor.stop_monitoring()
                load_result = {
                    'test_type': 'load_test',
                    'concurrent_users': user_count,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"     ❌ Load test failed: {str(e)}")
            
            load_results.append(load_result)
        
        self.load_test_results.extend(load_results)
    
    async def _simulate_user_processing(self, xml_content: str, document_id: str, user_id: int) -> Dict[str, Any]:
        """Simulate a single user processing a document"""
        try:
            start_time = time.time()
            
            result = await self.coordinator.process_document_pipeline(
                xml_content, document_id, 'NFE'
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            return {
                'user_id': user_id,
                'document_id': document_id,
                'processing_time': processing_time,
                'success': True,
                'result_summary': result.get('summary', {})
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'document_id': document_id,
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }
    
    async def _run_stress_tests(self, xml_files: List[Path]):
        """Run stress tests to find system limits"""
        print("   🔥 Running stress tests to find system limits...")
        
        stress_results = []
        
        # Stress test 1: Rapid sequential processing
        print("   Testing rapid sequential processing...")
        
        self.performance_monitor.start_monitoring()
        
        start_time = time.time()
        processed_count = 0
        errors = []
        
        try:
            # Process files rapidly in sequence
            for i in range(10):  # Try to process 10 documents rapidly
                xml_file = xml_files[i % len(xml_files)]
                
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                import uuid
                document_id = str(uuid.uuid4())
                
                try:
                    await self.coordinator.process_document_pipeline(
                        xml_content, document_id, 'NFE'
                    )
                    processed_count += 1
                    
                except Exception as e:
                    errors.append(str(e))
            
            end_time = time.time()
            total_time = end_time - start_time
            
            self.performance_monitor.stop_monitoring()
            performance_summary = self.performance_monitor.get_summary()
            
            rapid_result = {
                'test_type': 'rapid_sequential_stress',
                'attempted_documents': 10,
                'processed_documents': processed_count,
                'failed_documents': len(errors),
                'total_time_seconds': total_time,
                'processing_rate_docs_per_second': processed_count / total_time,
                'success_rate': (processed_count / 10) * 100,
                'performance_metrics': performance_summary,
                'errors': errors[:5],  # Store first 5 errors
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"     ✅ Processed {processed_count}/10 documents in {total_time:.2f}s")
            print(f"     📈 Processing Rate: {rapid_result['processing_rate_docs_per_second']:.2f} docs/s")
            print(f"     💾 Peak Memory: {performance_summary.get('memory_usage', {}).get('max_mb', 0):.1f} MB")
            
            if errors:
                print(f"     ⚠️  {len(errors)} processing errors occurred")
            
        except Exception as e:
            self.performance_monitor.stop_monitoring()
            rapid_result = {
                'test_type': 'rapid_sequential_stress',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"     ❌ Rapid processing stress test failed: {str(e)}")
        
        stress_results.append(rapid_result)
        
        # Stress test 2: Maximum concurrency test
        print("   Testing maximum concurrency limits...")
        
        max_concurrency = 20  # Try high concurrency
        
        self.performance_monitor.start_monitoring()
        
        start_time = time.time()
        
        try:
            # Create many concurrent tasks
            concurrent_tasks = []
            
            for i in range(max_concurrency):
                xml_file = xml_files[i % len(xml_files)]
                
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                import uuid
                document_id = str(uuid.uuid4())
                
                task = self.coordinator.process_document_pipeline(
                    xml_content, document_id, 'NFE'
                )
                concurrent_tasks.append(task)
            
            # Execute with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*concurrent_tasks, return_exceptions=True),
                    timeout=300  # 5 minute timeout
                )
                
                end_time = time.time()
                total_time = end_time - start_time
                
                successful_results = sum(1 for r in results if not isinstance(r, Exception))
                failed_results = max_concurrency - successful_results
                
                self.performance_monitor.stop_monitoring()
                performance_summary = self.performance_monitor.get_summary()
                
                concurrent_result = {
                    'test_type': 'maximum_concurrency_stress',
                    'max_concurrency_attempted': max_concurrency,
                    'successful_tasks': successful_results,
                    'failed_tasks': failed_results,
                    'total_time_seconds': total_time,
                    'success_rate': (successful_results / max_concurrency) * 100,
                    'concurrent_throughput': successful_results / total_time,
                    'performance_metrics': performance_summary,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"     ✅ {successful_results}/{max_concurrency} concurrent tasks completed")
                print(f"     📈 Success Rate: {concurrent_result['success_rate']:.1f}%")
                print(f"     🚀 Concurrent Throughput: {concurrent_result['concurrent_throughput']:.2f} tasks/s")
                print(f"     💾 Peak Memory: {performance_summary.get('memory_usage', {}).get('max_mb', 0):.1f} MB")
                
            except asyncio.TimeoutError:
                self.performance_monitor.stop_monitoring()
                concurrent_result = {
                    'test_type': 'maximum_concurrency_stress',
                    'max_concurrency_attempted': max_concurrency,
                    'success': False,
                    'error': 'Timeout after 5 minutes',
                    'timestamp': datetime.now().isoformat()
                }
                print(f"     ⏰ Concurrency stress test timed out after 5 minutes")
            
        except Exception as e:
            self.performance_monitor.stop_monitoring()
            concurrent_result = {
                'test_type': 'maximum_concurrency_stress',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"     ❌ Concurrency stress test failed: {str(e)}")
        
        stress_results.append(concurrent_result)
        self.performance_results.extend(stress_results)
    
    async def _generate_performance_report(self):
        """Generate comprehensive performance and load test report"""
        print("\n" + "=" * 80)
        print("⚡ COMPREHENSIVE PERFORMANCE AND LOAD TEST REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_tests = len(self.performance_results) + len(self.load_test_results)
        successful_tests = sum(1 for r in self.performance_results + self.load_test_results if r.get("success", True))
        
        print(f"📊 Total Tests Executed: {total_tests}")
        print(f"✅ Successful Tests: {successful_tests}")
        print(f"❌ Failed Tests: {total_tests - successful_tests}")
        
        # Performance Analysis
        if self.performance_results:
            print(f"\n⚡ Performance Analysis:")
            
            # Single document performance
            single_doc_results = [r for r in self.performance_results if 'throughput_bytes_per_second' in r]
            if single_doc_results:
                processing_times = [r['processing_time_seconds'] for r in single_doc_results if r.get('success')]
                throughputs = [r['throughput_bytes_per_second'] for r in single_doc_results if r.get('success')]
                
                if processing_times:
                    print(f"   Single Document Processing:")
                    print(f"     Average Time: {statistics.mean(processing_times):.2f}s")
                    print(f"     Fastest Time: {min(processing_times):.2f}s")
                    print(f"     Slowest Time: {max(processing_times):.2f}s")
                    print(f"     Average Throughput: {statistics.mean(throughputs):.0f} bytes/s")
            
            # Concurrent processing performance
            concurrent_results = [r for r in self.performance_results if 'concurrency_level' in r]
            if concurrent_results:
                print(f"\n   Concurrent Processing:")
                for result in concurrent_results:
                    if result.get('successful_files', 0) > 0:
                        print(f"     Concurrency {result['concurrency_level']}: {result['successful_files']}/{result['total_files']} files, {result['concurrent_throughput_bytes_per_second']:.0f} bytes/s")
            
            # Memory usage analysis
            memory_results = [r for r in self.performance_results if 'peak_memory_mb' in r]
            if memory_results:
                peak_memories = [r['peak_memory_mb'] for r in memory_results if r.get('success')]
                if peak_memories:
                    print(f"\n   Memory Usage:")
                    print(f"     Average Peak Memory: {statistics.mean(peak_memories):.1f} MB")
                    print(f"     Maximum Peak Memory: {max(peak_memories):.1f} MB")
                    print(f"     Minimum Peak Memory: {min(peak_memories):.1f} MB")
        
        # Load Test Analysis
        if self.load_test_results:
            print(f"\n👥 Load Test Analysis:")
            
            for result in self.load_test_results:
                if result.get('success_rate') is not None:
                    print(f"   {result['concurrent_users']} Users:")
                    print(f"     Success Rate: {result['success_rate']:.1f}%")
                    print(f"     Avg Response Time: {result['response_times']['avg_seconds']:.2f}s")
                    print(f"     Throughput: {result['throughput_users_per_second']:.2f} users/s")
        
        # Performance Recommendations
        print(f"\n💡 Performance Recommendations:")
        
        # Analyze results and provide recommendations
        recommendations = []
        
        # Check processing times
        processing_times = [r.get('processing_time_seconds', 0) for r in self.performance_results if r.get('success')]
        if processing_times:
            avg_time = statistics.mean(processing_times)
            if avg_time > 10:
                recommendations.append("Consider optimizing processing pipeline - average time exceeds 10 seconds")
            elif avg_time < 2:
                recommendations.append("Excellent processing performance - average time under 2 seconds")
        
        # Check memory usage
        peak_memories = [r.get('peak_memory_mb', 0) for r in self.performance_results if r.get('success')]
        if peak_memories:
            max_memory = max(peak_memories)
            if max_memory > 500:
                recommendations.append("High memory usage detected - consider memory optimization")
            elif max_memory < 100:
                recommendations.append("Efficient memory usage - peak memory under 100 MB")
        
        # Check concurrency performance
        concurrent_results = [r for r in self.performance_results if 'concurrency_level' in r and r.get('successful_files', 0) > 0]
        if concurrent_results:
            success_rates = [r['successful_files'] / r['total_files'] for r in concurrent_results]
            avg_success_rate = statistics.mean(success_rates)
            if avg_success_rate < 0.8:
                recommendations.append("Concurrency issues detected - consider connection pooling or rate limiting")
            elif avg_success_rate > 0.95:
                recommendations.append("Excellent concurrency performance - system handles parallel processing well")
        
        # Check load test results
        load_success_rates = [r.get('success_rate', 0) for r in self.load_test_results if r.get('success_rate') is not None]
        if load_success_rates:
            avg_load_success = statistics.mean(load_success_rates)
            if avg_load_success < 80:
                recommendations.append("Load testing shows system stress - consider scaling or optimization")
            elif avg_load_success > 95:
                recommendations.append("System handles load well - good scalability characteristics")
        
        if not recommendations:
            recommendations.append("Performance appears adequate - continue monitoring in production")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dimensional_performance_load_results_{timestamp}.json"
        
        try:
            comprehensive_results = {
                "performance_results": self.performance_results,
                "load_test_results": self.load_test_results,
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": total_tests - successful_tests,
                    "average_processing_time": statistics.mean(processing_times) if processing_times else 0,
                    "peak_memory_usage": max(peak_memories) if peak_memories else 0,
                    "recommendations": recommendations
                },
                "test_timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Comprehensive results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def main():
    """Main test execution"""
    print("⚡ Dimensional Processing Performance and Load Test Suite")
    print("=" * 80)
    
    tester = DimensionalPerformanceTester()
    await tester.run_performance_and_load_tests()


if __name__ == "__main__":
    asyncio.run(main())