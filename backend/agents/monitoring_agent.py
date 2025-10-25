"""
LLM-Enhanced Monitoring Agent for intelligent error logging, predictive monitoring, 
and system health analysis with business context understanding
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog

from .base_agent import BaseAgent
from models.fiscal_data import ProcessingError
from utils.config import settings
from utils.openai_integration import get_openai_service
from utils.llm_error_handler import get_error_handler, ErrorSeverity, ErrorCategory


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemAlert:
    """System alert representation"""
    
    def __init__(self, level: AlertLevel, message: str, source: str, 
                 details: Dict[str, Any] = None):
        self.level = level
        self.message = message
        self.source = source
        self.details = details or {}
        self.timestamp = datetime.now()
        self.alert_id = f"{source}_{int(self.timestamp.timestamp())}"
        self.acknowledged = False
        self.resolved = False


class SystemFailure:
    """System failure representation"""
    
    def __init__(self, component: str, error_type: str, error_message: str,
                 severity: AlertLevel = AlertLevel.ERROR):
        self.component = component
        self.error_type = error_type
        self.error_message = error_message
        self.severity = severity
        self.timestamp = datetime.now()
        self.failure_id = f"{component}_{int(self.timestamp.timestamp())}"
        self.recovery_attempted = False
        self.recovery_successful = False


class HealthStatus:
    """System health status"""
    
    def __init__(self, overall_status: str, components: Dict[str, str],
                 metrics: Dict[str, Any]):
        self.overall_status = overall_status
        self.components = components
        self.metrics = metrics
        self.checked_at = datetime.now()


class PerformanceMetrics:
    """Agent performance metrics"""
    
    def __init__(self, agent_id: str, metrics: Dict[str, Any]):
        self.agent_id = agent_id
        self.metrics = metrics
        self.collected_at = datetime.now()


class MonitoringAgent(BaseAgent):
    """
    LLM-Enhanced Monitoring Agent responsible for intelligent system monitoring, 
    predictive issue detection, and automated performance optimization
    """
    
    def __init__(self):
        super().__init__("MonitoringAgent")
        self.alerts = []
        self.failures = []
        self.performance_history = []
        self.system_metrics = {}
        self.alert_thresholds = {}
        
        # LLM-enhanced capabilities
        self.llm_service = get_openai_service()
        self.error_handler = get_error_handler()
        self.pattern_history = []
        self.predictive_models = {}
        self.optimization_suggestions = []
        self.anomaly_detection_enabled = True
        self.predictive_alerting_enabled = True
        
    async def initialize(self):
        """Initialize Monitoring Agent resources"""
        try:
            # Set up alert thresholds
            await self._setup_alert_thresholds()
            
            # Start monitoring loops
            asyncio.create_task(self._health_monitoring_loop())
            asyncio.create_task(self._performance_monitoring_loop())
            asyncio.create_task(self._alert_cleanup_loop())
            
            self.logger.info("Monitoring Agent initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize Monitoring Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Monitoring Agent cleaned up")
    
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process monitoring request"""
        if isinstance(data, ProcessingError):
            return await self.log_processing_error(data)
        elif isinstance(data, SystemAlert):
            return await self.handle_system_alert(data)
        elif isinstance(data, dict):
            action = data.get('action')
            if action == 'health_check':
                return await self.get_system_health()
            elif action == 'get_alerts':
                return await self.get_active_alerts()
            elif action == 'get_metrics':
                return await self.get_system_metrics()
        
        return {'error': 'Invalid monitoring request'}
    
    async def _setup_alert_thresholds(self):
        """Setup alert thresholds for various metrics"""
        self.alert_thresholds = {
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'disk_usage': {'warning': 85, 'critical': 95},
            'error_rate': {'warning': 5, 'critical': 10},  # errors per minute
            'response_time': {'warning': 5000, 'critical': 10000},  # milliseconds
            'queue_size': {'warning': 100, 'critical': 500},
            'failed_tasks': {'warning': 10, 'critical': 50}  # per hour
        }
        
        self.logger.info("Alert thresholds configured")
    
    async def log_processing_error(self, error: ProcessingError) -> Dict[str, Any]:
        """Log XML processing error"""
        try:
            self.logger.error("Processing error logged",
                            file_path=error.file_path,
                            error_type=error.error_type,
                            error_message=error.error_message,
                            agent=error.agent_name)
            
            # Create system alert for critical errors
            if error.error_type in ['XMLSyntaxError', 'SchemaValidationError']:
                alert = SystemAlert(
                    level=AlertLevel.ERROR,
                    message=f"XML processing failed: {error.error_message}",
                    source=error.agent_name,
                    details={
                        'file_path': error.file_path,
                        'error_type': error.error_type,
                        'timestamp': error.timestamp
                    }
                )
                await self.handle_system_alert(alert)
            
            return {
                'success': True,
                'error_logged': True,
                'alert_created': error.error_type in ['XMLSyntaxError', 'SchemaValidationError']
            }
            
        except Exception as e:
            self.logger.error("Error logging processing error", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def handle_system_alert(self, alert: SystemAlert) -> Dict[str, Any]:
        """Handle system alert"""
        try:
            self.alerts.append(alert)
            
            log_level = self._get_log_level(alert.level)
            if log_level == "critical":
                self.logger.critical("System alert generated",
                                   alert_id=alert.alert_id,
                                   level=alert.level.value,
                                   message=alert.message,
                                   source=alert.source,
                                   details=alert.details)
            elif log_level == "error":
                self.logger.error("System alert generated",
                                alert_id=alert.alert_id,
                                level=alert.level.value,
                                message=alert.message,
                                source=alert.source,
                                details=alert.details)
            elif log_level == "warning":
                self.logger.warning("System alert generated",
                                  alert_id=alert.alert_id,
                                  level=alert.level.value,
                                  message=alert.message,
                                  source=alert.source,
                                  details=alert.details)
            else:
                self.logger.info("System alert generated",
                               alert_id=alert.alert_id,
                               level=alert.level.value,
                               message=alert.message,
                               source=alert.source,
                               details=alert.details)
            
            # Send notifications for critical alerts
            if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                await self.notify_administrators(alert)
            
            # Trigger escalation for critical alerts
            if alert.level == AlertLevel.CRITICAL:
                await self.manage_alert_escalation(alert)
            
            return {
                'success': True,
                'alert_id': alert.alert_id,
                'notification_sent': alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]
            }
            
        except Exception as e:
            self.logger.error("Error handling system alert", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _get_log_level(self, alert_level: AlertLevel) -> str:
        """Convert alert level to log level"""
        mapping = {
            AlertLevel.INFO: "info",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "error",
            AlertLevel.CRITICAL: "critical"
        }
        return mapping.get(alert_level, "info")
    
    async def notify_administrators(self, alert: SystemAlert) -> Dict[str, Any]:
        """Send notifications to administrators"""
        try:
            self.logger.info("Notifying administrators",
                           alert_id=alert.alert_id,
                           level=alert.level.value)
            
            # In a real implementation, this would:
            # 1. Send email notifications
            # 2. Send Slack/Teams messages
            # 3. Send SMS for critical alerts
            # 4. Create tickets in issue tracking system
            
            notification_result = {
                'email_sent': True,
                'slack_sent': True,
                'sms_sent': alert.level == AlertLevel.CRITICAL,
                'ticket_created': alert.level == AlertLevel.CRITICAL,
                'recipients': ['admin@company.com', 'ops-team@company.com'],
                'sent_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'notification_result': notification_result
            }
            
        except Exception as e:
            self.logger.error("Error notifying administrators", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def monitor_system_health(self) -> HealthStatus:
        """Monitor overall system health"""
        try:
            # Check component health
            components = {
                'database': await self._check_database_health(),
                'redis': await self._check_redis_health(),
                'xml_processing': await self._check_xml_processing_health(),
                'agents': await self._check_agents_health(),
                'storage': await self._check_storage_health()
            }
            
            # Calculate overall status
            component_statuses = list(components.values())
            if all(status == 'healthy' for status in component_statuses):
                overall_status = 'healthy'
            elif any(status == 'critical' for status in component_statuses):
                overall_status = 'critical'
            elif any(status == 'degraded' for status in component_statuses):
                overall_status = 'degraded'
            else:
                overall_status = 'unknown'
            
            # Collect system metrics
            metrics = await self._collect_system_metrics()
            
            health_status = HealthStatus(overall_status, components, metrics)
            
            # Generate alerts for unhealthy components
            for component, status in components.items():
                if status in ['degraded', 'critical']:
                    alert = SystemAlert(
                        level=AlertLevel.CRITICAL if status == 'critical' else AlertLevel.WARNING,
                        message=f"Component {component} is {status}",
                        source="MonitoringAgent",
                        details={'component': component, 'status': status}
                    )
                    await self.handle_system_alert(alert)
            
            return health_status
            
        except Exception as e:
            self.logger.error("Error monitoring system health", error=str(e))
            return HealthStatus('unknown', {}, {'error': str(e)})
    
    async def _check_database_health(self) -> str:
        """Check database health"""
        try:
            # In a real implementation, this would check:
            # - Connection pool status
            # - Query response times
            # - Disk space
            # - Active connections
            
            # Placeholder implementation
            return 'healthy'
            
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return 'critical'
    
    async def _check_redis_health(self) -> str:
        """Check Redis health"""
        try:
            # In a real implementation, this would check:
            # - Redis connection
            # - Memory usage
            # - Key count
            # - Response times
            
            # Placeholder implementation
            return 'healthy'
            
        except Exception as e:
            self.logger.error("Redis health check failed", error=str(e))
            return 'critical'
    
    async def _check_xml_processing_health(self) -> str:
        """Check XML processing health"""
        try:
            # Check processing queue size, error rates, etc.
            return 'healthy'
            
        except Exception as e:
            self.logger.error("XML processing health check failed", error=str(e))
            return 'degraded'
    
    async def _check_agents_health(self) -> str:
        """Check all agents health"""
        try:
            # Check if all agents are responsive
            return 'healthy'
            
        except Exception as e:
            self.logger.error("Agents health check failed", error=str(e))
            return 'degraded'
    
    async def _check_storage_health(self) -> str:
        """Check storage health"""
        try:
            # Check disk space, file system health, etc.
            return 'healthy'
            
        except Exception as e:
            self.logger.error("Storage health check failed", error=str(e))
            return 'critical'
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        try:
            # In a real implementation, this would collect:
            # - CPU usage
            # - Memory usage
            # - Disk I/O
            # - Network I/O
            # - Application-specific metrics
            
            metrics = {
                'cpu_usage': 45.2,  # Placeholder
                'memory_usage': 62.8,
                'disk_usage': 34.5,
                'network_io': {'in': 1024, 'out': 2048},
                'active_connections': 15,
                'queue_sizes': {
                    'xml_processing': 5,
                    'report_generation': 2,
                    'scheduled_tasks': 8
                },
                'response_times': {
                    'avg': 250,
                    'p95': 500,
                    'p99': 1200
                },
                'error_rates': {
                    'xml_processing': 0.5,
                    'database': 0.1,
                    'api': 0.2
                }
            }
            
            # Check against thresholds and generate alerts
            await self._check_metric_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error("Error collecting system metrics", error=str(e))
            return {'error': str(e)}
    
    async def _check_metric_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and generate alerts"""
        try:
            for metric_name, value in metrics.items():
                if metric_name in self.alert_thresholds and isinstance(value, (int, float)):
                    thresholds = self.alert_thresholds[metric_name]
                    
                    if value >= thresholds['critical']:
                        alert = SystemAlert(
                            level=AlertLevel.CRITICAL,
                            message=f"{metric_name} is critical: {value}",
                            source="MonitoringAgent",
                            details={'metric': metric_name, 'value': value, 'threshold': thresholds['critical']}
                        )
                        await self.handle_system_alert(alert)
                    
                    elif value >= thresholds['warning']:
                        alert = SystemAlert(
                            level=AlertLevel.WARNING,
                            message=f"{metric_name} is high: {value}",
                            source="MonitoringAgent",
                            details={'metric': metric_name, 'value': value, 'threshold': thresholds['warning']}
                        )
                        await self.handle_system_alert(alert)
            
        except Exception as e:
            self.logger.error("Error checking metric thresholds", error=str(e))
    
    async def track_agent_performance(self, agent_id: str) -> PerformanceMetrics:
        """Track performance metrics for specific agent"""
        try:
            # In a real implementation, this would collect:
            # - Task completion times
            # - Success/failure rates
            # - Resource usage
            # - Queue sizes
            
            metrics = {
                'tasks_completed': 150,
                'tasks_failed': 3,
                'avg_completion_time': 2.5,
                'success_rate': 98.0,
                'cpu_usage': 25.3,
                'memory_usage': 45.7,
                'queue_size': 8
            }
            
            performance_metrics = PerformanceMetrics(agent_id, metrics)
            self.performance_history.append(performance_metrics)
            
            # Keep only recent history (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.performance_history = [
                pm for pm in self.performance_history 
                if pm.collected_at > cutoff_time
            ]
            
            return performance_metrics
            
        except Exception as e:
            self.logger.error("Error tracking agent performance", agent_id=agent_id, error=str(e))
            return PerformanceMetrics(agent_id, {'error': str(e)})
    
    async def manage_alert_escalation(self, alert: SystemAlert) -> Dict[str, Any]:
        """Manage alert escalation procedures"""
        try:
            self.logger.critical("Escalating alert", alert_id=alert.alert_id)
            
            escalation_steps = []
            
            # Step 1: Immediate notification to on-call team
            escalation_steps.append({
                'step': 'immediate_notification',
                'action': 'Notify on-call team',
                'completed': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # Step 2: Create high-priority ticket
            escalation_steps.append({
                'step': 'create_ticket',
                'action': 'Create P1 incident ticket',
                'completed': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # Step 3: Attempt automatic recovery if applicable
            if alert.source in ['XMLProcessingAgent', 'DataLakeAgent']:
                recovery_result = await self._attempt_automatic_recovery(alert)
                escalation_steps.append({
                    'step': 'auto_recovery',
                    'action': 'Attempt automatic recovery',
                    'completed': recovery_result.get('attempted', False),
                    'successful': recovery_result.get('successful', False),
                    'timestamp': datetime.now().isoformat()
                })
            
            return {
                'success': True,
                'alert_id': alert.alert_id,
                'escalation_steps': escalation_steps
            }
            
        except Exception as e:
            self.logger.error("Error managing alert escalation", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _attempt_automatic_recovery(self, alert: SystemAlert) -> Dict[str, Any]:
        """Attempt automatic recovery procedures"""
        try:
            recovery_actions = []
            
            if alert.source == 'XMLProcessingAgent':
                # Restart XML processing queue
                recovery_actions.append('restart_xml_queue')
                
            elif alert.source == 'DataLakeAgent':
                # Check database connections
                recovery_actions.append('check_db_connections')
                
            # Execute recovery actions
            for action in recovery_actions:
                self.logger.info("Executing recovery action", action=action)
                # Placeholder for actual recovery logic
                await asyncio.sleep(1)
            
            return {
                'attempted': True,
                'successful': True,
                'actions': recovery_actions
            }
            
        except Exception as e:
            self.logger.error("Error in automatic recovery", error=str(e))
            return {
                'attempted': True,
                'successful': False,
                'error': str(e)
            }
    
    async def initiate_recovery_procedure(self, failure: SystemFailure) -> Dict[str, Any]:
        """Initiate recovery procedure for system failure"""
        try:
            self.failures.append(failure)
            failure.recovery_attempted = True
            
            self.logger.error("Initiating recovery procedure",
                            failure_id=failure.failure_id,
                            component=failure.component,
                            error_type=failure.error_type)
            
            recovery_result = await self._execute_recovery_procedure(failure)
            failure.recovery_successful = recovery_result.get('successful', False)
            
            return recovery_result
            
        except Exception as e:
            self.logger.error("Error initiating recovery procedure", error=str(e))
            return {'successful': False, 'error': str(e)}
    
    async def _execute_recovery_procedure(self, failure: SystemFailure) -> Dict[str, Any]:
        """Execute specific recovery procedure based on failure type"""
        try:
            if failure.component == 'database':
                return await self._recover_database_failure(failure)
            elif failure.component == 'xml_processing':
                return await self._recover_xml_processing_failure(failure)
            elif failure.component == 'agents':
                return await self._recover_agent_failure(failure)
            else:
                return await self._generic_recovery_procedure(failure)
                
        except Exception as e:
            return {'successful': False, 'error': str(e)}
    
    async def _recover_database_failure(self, failure: SystemFailure) -> Dict[str, Any]:
        """Recover from database failure"""
        # Placeholder for database recovery logic
        return {'successful': True, 'actions': ['reconnect_pool', 'verify_connections']}
    
    async def _recover_xml_processing_failure(self, failure: SystemFailure) -> Dict[str, Any]:
        """Recover from XML processing failure"""
        # Placeholder for XML processing recovery logic
        return {'successful': True, 'actions': ['restart_file_watcher', 'clear_error_queue']}
    
    async def _recover_agent_failure(self, failure: SystemFailure) -> Dict[str, Any]:
        """Recover from agent failure"""
        # Placeholder for agent recovery logic
        return {'successful': True, 'actions': ['restart_agent', 'clear_task_queue']}
    
    async def _generic_recovery_procedure(self, failure: SystemFailure) -> Dict[str, Any]:
        """Generic recovery procedure"""
        return {'successful': False, 'reason': 'No specific recovery procedure available'}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            health_status = await self.monitor_system_health()
            
            return {
                'overall_status': health_status.overall_status,
                'components': health_status.components,
                'metrics': health_status.metrics,
                'checked_at': health_status.checked_at.isoformat(),
                'active_alerts': len([a for a in self.alerts if not a.resolved]),
                'recent_failures': len([f for f in self.failures if f.timestamp > datetime.now() - timedelta(hours=1)])
            }
            
        except Exception as e:
            self.logger.error("Error getting system health", error=str(e))
            return {'error': str(e)}
    
    async def get_active_alerts(self) -> Dict[str, Any]:
        """Get all active alerts"""
        try:
            active_alerts = [a for a in self.alerts if not a.resolved]
            
            alerts_by_level = {
                'critical': [a for a in active_alerts if a.level == AlertLevel.CRITICAL],
                'error': [a for a in active_alerts if a.level == AlertLevel.ERROR],
                'warning': [a for a in active_alerts if a.level == AlertLevel.WARNING],
                'info': [a for a in active_alerts if a.level == AlertLevel.INFO]
            }
            
            return {
                'total_alerts': len(active_alerts),
                'by_level': {
                    level: len(alerts) for level, alerts in alerts_by_level.items()
                },
                'alerts': [
                    {
                        'alert_id': a.alert_id,
                        'level': a.level.value,
                        'message': a.message,
                        'source': a.source,
                        'timestamp': a.timestamp.isoformat(),
                        'acknowledged': a.acknowledged
                    }
                    for a in active_alerts[-50:]  # Last 50 alerts
                ]
            }
            
        except Exception as e:
            self.logger.error("Error getting active alerts", error=str(e))
            return {'error': str(e)}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            metrics = await self._collect_system_metrics()
            
            return {
                'current_metrics': metrics,
                'collected_at': datetime.now().isoformat(),
                'thresholds': self.alert_thresholds
            }
            
        except Exception as e:
            self.logger.error("Error getting system metrics", error=str(e))
            return {'error': str(e)}
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring loop"""
        while True:
            try:
                await self.monitor_system_health()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error("Error in health monitoring loop", error=str(e))
                await asyncio.sleep(300)
    
    async def _performance_monitoring_loop(self):
        """Continuous performance monitoring loop"""
        while True:
            try:
                # Track performance for all known agents
                agent_ids = ['XMLProcessingAgent', 'AICategorization Agent', 'MasterAgent', 
                           'SQLAgent', 'ReportAgent', 'SchedulerAgent', 'DataLakeAgent']
                
                for agent_id in agent_ids:
                    await self.track_agent_performance(agent_id)
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                self.logger.error("Error in performance monitoring loop", error=str(e))
                await asyncio.sleep(600)
    
    async def _alert_cleanup_loop(self):
        """Clean up old resolved alerts"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(days=7)
                
                # Remove old resolved alerts
                self.alerts = [
                    a for a in self.alerts 
                    if not a.resolved or a.timestamp > cutoff_time
                ]
                
                # Remove old failures
                self.failures = [
                    f for f in self.failures 
                    if f.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                self.logger.error("Error in alert cleanup loop", error=str(e))
                await asyncio.sleep(3600)
    
    # ========== LLM-Enhanced Predictive Monitoring Methods ==========
    
    async def analyze_system_patterns_with_llm(self) -> Dict[str, Any]:
        """
        Use LLM to analyze system patterns and detect anomalies
        Implements requirement 8.2: LLM analysis for pattern recognition
        """
        try:
            if len(self.performance_history) < 10:
                return {'patterns': [], 'message': 'Insufficient data for pattern analysis'}
            
            # Prepare data for LLM analysis
            recent_metrics = self._prepare_metrics_for_analysis()
            historical_trends = self._calculate_historical_trends()
            
            llm_context = {
                'current_metrics': recent_metrics,
                'historical_trends': historical_trends,
                'alert_history': self._get_alert_summary(),
                'system_components': ['xml_processing', 'database', 'agents', 'api', 'storage'],
                'business_context': {
                    'peak_hours': '09:00-17:00 BRT',
                    'critical_operations': ['nfe_processing', 'report_generation'],
                    'seasonal_patterns': 'month_end_spike'
                }
            }
            
            llm_response = await self.llm_service.generate_completion(
                "system_pattern_analysis",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.1
            )
            
            pattern_analysis = await self._parse_pattern_analysis(llm_response.content)
            
            # Store pattern for future reference
            self.pattern_history.append({
                'timestamp': datetime.now(),
                'analysis': pattern_analysis,
                'confidence': llm_response.confidence_score
            })
            
            # Generate proactive alerts if needed
            if pattern_analysis.get('anomalies_detected'):
                await self._create_predictive_alerts(pattern_analysis)
            
            self.logger.info("System pattern analysis completed",
                           patterns_detected=len(pattern_analysis.get('patterns', [])),
                           anomalies_detected=len(pattern_analysis.get('anomalies_detected', [])),
                           confidence=llm_response.confidence_score)
            
            return pattern_analysis
            
        except Exception as e:
            self.logger.error("Error in LLM pattern analysis", error=str(e))
            return {'error': str(e), 'patterns': []}
    
    async def predict_system_issues(self) -> Dict[str, Any]:
        """
        Use LLM to predict potential system issues based on current trends
        Implements requirement 8.3: Predictive issue detection and proactive alerting
        """
        try:
            # Collect comprehensive system state
            current_state = await self._get_comprehensive_system_state()
            
            llm_context = {
                'current_system_state': current_state,
                'recent_error_patterns': await self.error_handler.detect_error_patterns(),
                'performance_trends': self._analyze_performance_trends(),
                'resource_utilization': await self._analyze_resource_utilization(),
                'business_calendar': self._get_business_calendar_context(),
                'historical_incidents': self._get_historical_incident_patterns()
            }
            
            llm_response = await self.llm_service.generate_completion(
                "predictive_issue_detection",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.2
            )
            
            predictions = await self._parse_issue_predictions(llm_response.content)
            
            # Create proactive alerts for high-risk predictions
            for prediction in predictions.get('high_risk_issues', []):
                if prediction.get('probability', 0) > 0.7:
                    await self._create_proactive_alert(prediction)
            
            # Generate optimization recommendations
            optimization_suggestions = await self._generate_optimization_suggestions(predictions)
            
            self.logger.info("Predictive issue analysis completed",
                           predictions_count=len(predictions.get('predictions', [])),
                           high_risk_count=len(predictions.get('high_risk_issues', [])),
                           optimization_suggestions=len(optimization_suggestions))
            
            return {
                'predictions': predictions,
                'optimization_suggestions': optimization_suggestions,
                'analysis_timestamp': datetime.now().isoformat(),
                'confidence_score': llm_response.confidence_score
            }
            
        except Exception as e:
            self.logger.error("Error in predictive issue detection", error=str(e))
            return {'error': str(e), 'predictions': []}
    
    async def generate_performance_optimization_suggestions(self) -> Dict[str, Any]:
        """
        Use LLM to generate intelligent performance optimization suggestions
        Implements requirement 8.4: Performance optimization suggestions
        """
        try:
            # Analyze current performance bottlenecks
            bottlenecks = await self._identify_performance_bottlenecks()
            
            llm_context = {
                'performance_bottlenecks': bottlenecks,
                'system_metrics': await self._collect_system_metrics(),
                'resource_constraints': await self._analyze_resource_constraints(),
                'workload_patterns': self._analyze_workload_patterns(),
                'infrastructure_capacity': await self._get_infrastructure_capacity(),
                'business_requirements': {
                    'sla_targets': {'response_time': '< 2s', 'uptime': '99.9%'},
                    'peak_load_handling': 'month_end_processing',
                    'cost_optimization': 'moderate_priority'
                }
            }
            
            llm_response = await self.llm_service.generate_completion(
                "performance_optimization",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.3
            )
            
            optimization_plan = await self._parse_optimization_suggestions(llm_response.content)
            
            # Prioritize suggestions based on impact and feasibility
            prioritized_suggestions = self._prioritize_optimization_suggestions(optimization_plan)
            
            # Store suggestions for tracking implementation
            self.optimization_suggestions.extend(prioritized_suggestions.get('suggestions', []))
            
            self.logger.info("Performance optimization analysis completed",
                           suggestions_count=len(prioritized_suggestions.get('suggestions', [])),
                           high_impact_count=len([s for s in prioritized_suggestions.get('suggestions', []) 
                                                if s.get('impact') == 'high']),
                           confidence=llm_response.confidence_score)
            
            return prioritized_suggestions
            
        except Exception as e:
            self.logger.error("Error generating optimization suggestions", error=str(e))
            return {'error': str(e), 'suggestions': []}
    
    async def analyze_fiscal_data_quality_patterns(self, fiscal_data_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to analyze fiscal data quality patterns and detect business anomalies
        Implements requirement 8.3: Evaluate if patterns indicate data quality issues or business changes
        """
        try:
            llm_context = {
                'fiscal_data_metrics': fiscal_data_metrics,
                'data_quality_indicators': {
                    'xml_validation_errors': fiscal_data_metrics.get('validation_errors', 0),
                    'missing_fields_rate': fiscal_data_metrics.get('missing_fields_rate', 0),
                    'duplicate_documents': fiscal_data_metrics.get('duplicates', 0),
                    'processing_time_variance': fiscal_data_metrics.get('processing_variance', 0)
                },
                'business_context': {
                    'document_types': ['NF-e', 'NFS-e'],
                    'typical_volumes': fiscal_data_metrics.get('typical_volumes', {}),
                    'seasonal_patterns': fiscal_data_metrics.get('seasonal_patterns', {}),
                    'supplier_patterns': fiscal_data_metrics.get('supplier_patterns', {})
                },
                'historical_baselines': self._get_fiscal_data_baselines()
            }
            
            llm_response = await self.llm_service.generate_completion(
                "fiscal_data_quality_analysis",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.1
            )
            
            quality_analysis = await self._parse_data_quality_analysis(llm_response.content)
            
            # Create alerts for significant data quality issues
            if quality_analysis.get('data_quality_issues'):
                for issue in quality_analysis['data_quality_issues']:
                    if issue.get('severity') in ['high', 'critical']:
                        alert = SystemAlert(
                            level=AlertLevel.ERROR if issue['severity'] == 'high' else AlertLevel.CRITICAL,
                            message=f"Data quality issue detected: {issue['description']}",
                            source="MonitoringAgent",
                            details={
                                'issue_type': issue.get('type'),
                                'affected_documents': issue.get('affected_count'),
                                'business_impact': issue.get('business_impact')
                            }
                        )
                        await self.handle_system_alert(alert)
            
            self.logger.info("Fiscal data quality analysis completed",
                           issues_detected=len(quality_analysis.get('data_quality_issues', [])),
                           business_changes_detected=len(quality_analysis.get('business_changes', [])),
                           confidence=llm_response.confidence_score)
            
            return quality_analysis
            
        except Exception as e:
            self.logger.error("Error analyzing fiscal data quality patterns", error=str(e))
            return {'error': str(e), 'analysis': {}}
    
    async def create_intelligent_maintenance_recommendations(self) -> Dict[str, Any]:
        """
        Generate LLM-powered maintenance recommendations and impact assessments
        Implements requirement 8.4: Generate maintenance recommendations and impact evaluations
        """
        try:
            # Collect maintenance-relevant data
            system_health = await self.monitor_system_health()
            
            llm_context = {
                'system_health': {
                    'overall_status': system_health.overall_status,
                    'component_health': system_health.components,
                    'performance_metrics': system_health.metrics
                },
                'maintenance_history': self._get_maintenance_history(),
                'upcoming_business_events': self._get_business_calendar_events(),
                'resource_utilization_trends': self._analyze_resource_trends(),
                'known_technical_debt': self._get_technical_debt_items(),
                'business_constraints': {
                    'maintenance_windows': ['02:00-04:00 BRT daily', 'Saturday 20:00-Sunday 06:00'],
                    'critical_business_periods': ['month_end', 'quarter_end', 'year_end'],
                    'sla_requirements': {'max_downtime': '4 hours/month', 'planned_maintenance': '< 2 hours'}
                }
            }
            
            llm_response = await self.llm_service.generate_completion(
                "maintenance_recommendations",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.2
            )
            
            maintenance_plan = await self._parse_maintenance_recommendations(llm_response.content)
            
            # Assess business impact for each recommendation
            for recommendation in maintenance_plan.get('recommendations', []):
                impact_assessment = await self._assess_maintenance_impact(recommendation)
                recommendation['impact_assessment'] = impact_assessment
            
            self.logger.info("Maintenance recommendations generated",
                           recommendations_count=len(maintenance_plan.get('recommendations', [])),
                           urgent_count=len([r for r in maintenance_plan.get('recommendations', []) 
                                           if r.get('urgency') == 'high']),
                           confidence=llm_response.confidence_score)
            
            return maintenance_plan
            
        except Exception as e:
            self.logger.error("Error generating maintenance recommendations", error=str(e))
            return {'error': str(e), 'recommendations': []}
    
    # ========== Helper Methods for LLM-Enhanced Monitoring ==========
    
    def _prepare_metrics_for_analysis(self) -> Dict[str, Any]:
        """Prepare recent metrics for LLM analysis"""
        recent_metrics = []
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for pm in self.performance_history:
            if pm.collected_at > cutoff_time:
                recent_metrics.append({
                    'timestamp': pm.collected_at.isoformat(),
                    'agent_id': pm.agent_id,
                    'metrics': pm.metrics
                })
        
        return {
            'metrics_count': len(recent_metrics),
            'time_range': '24_hours',
            'metrics_data': recent_metrics[-50:]  # Last 50 metrics
        }
    
    def _calculate_historical_trends(self) -> Dict[str, Any]:
        """Calculate historical trends for pattern analysis"""
        if len(self.performance_history) < 5:
            return {'insufficient_data': True}
        
        # Calculate trends for key metrics
        trends = {}
        
        # Group metrics by agent
        agent_metrics = {}
        for pm in self.performance_history[-100:]:  # Last 100 entries
            if pm.agent_id not in agent_metrics:
                agent_metrics[pm.agent_id] = []
            agent_metrics[pm.agent_id].append(pm)
        
        # Calculate trends for each agent
        for agent_id, metrics_list in agent_metrics.items():
            if len(metrics_list) >= 5:
                trends[agent_id] = self._calculate_agent_trends(metrics_list)
        
        return trends
    
    def _calculate_agent_trends(self, metrics_list: List) -> Dict[str, Any]:
        """Calculate trends for a specific agent"""
        # Simple trend calculation (in real implementation, use more sophisticated analysis)
        recent = metrics_list[-5:]
        older = metrics_list[-10:-5] if len(metrics_list) >= 10 else metrics_list[:-5]
        
        if not older:
            return {'trend': 'insufficient_data'}
        
        # Calculate average metrics for comparison
        recent_avg = self._calculate_average_metrics(recent)
        older_avg = self._calculate_average_metrics(older)
        
        trends = {}
        for metric_name in recent_avg:
            if metric_name in older_avg and isinstance(recent_avg[metric_name], (int, float)):
                change = ((recent_avg[metric_name] - older_avg[metric_name]) / older_avg[metric_name]) * 100
                trends[metric_name] = {
                    'change_percent': round(change, 2),
                    'direction': 'increasing' if change > 5 else 'decreasing' if change < -5 else 'stable'
                }
        
        return trends
    
    def _calculate_average_metrics(self, metrics_list: List) -> Dict[str, Any]:
        """Calculate average metrics from a list of performance metrics"""
        if not metrics_list:
            return {}
        
        # Aggregate numeric metrics
        aggregated = {}
        count = len(metrics_list)
        
        for pm in metrics_list:
            for key, value in pm.metrics.items():
                if isinstance(value, (int, float)):
                    if key not in aggregated:
                        aggregated[key] = 0
                    aggregated[key] += value
        
        # Calculate averages
        return {key: value / count for key, value in aggregated.items()}
    
    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts for pattern analysis"""
        recent_alerts = [a for a in self.alerts if a.timestamp > datetime.now() - timedelta(hours=24)]
        
        return {
            'total_alerts': len(recent_alerts),
            'by_level': {
                'critical': len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
                'error': len([a for a in recent_alerts if a.level == AlertLevel.ERROR]),
                'warning': len([a for a in recent_alerts if a.level == AlertLevel.WARNING]),
                'info': len([a for a in recent_alerts if a.level == AlertLevel.INFO])
            },
            'by_source': self._group_alerts_by_source(recent_alerts),
            'alert_frequency': len(recent_alerts) / 24  # alerts per hour
        }
    
    def _group_alerts_by_source(self, alerts: List[SystemAlert]) -> Dict[str, int]:
        """Group alerts by source for analysis"""
        sources = {}
        for alert in alerts:
            sources[alert.source] = sources.get(alert.source, 0) + 1
        return sources
    
    async def _parse_pattern_analysis(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM pattern analysis response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'patterns': [],
                'anomalies_detected': [],
                'recommendations': [llm_content[:500]],
                'confidence_score': 0.5
            }
    
    async def _create_predictive_alerts(self, pattern_analysis: Dict[str, Any]):
        """Create predictive alerts based on pattern analysis"""
        for anomaly in pattern_analysis.get('anomalies_detected', []):
            alert = SystemAlert(
                level=AlertLevel.WARNING,
                message=f"Predictive anomaly detected: {anomaly.get('description', 'Unknown anomaly')}",
                source="MonitoringAgent_Predictive",
                details={
                    'anomaly_type': anomaly.get('type'),
                    'confidence': anomaly.get('confidence'),
                    'predicted_impact': anomaly.get('predicted_impact'),
                    'recommended_actions': anomaly.get('recommended_actions', [])
                }
            )
            await self.handle_system_alert(alert)
    
    async def _get_comprehensive_system_state(self) -> Dict[str, Any]:
        """Get comprehensive system state for predictive analysis"""
        return {
            'health_status': await self.monitor_system_health(),
            'current_metrics': await self._collect_system_metrics(),
            'active_alerts': len([a for a in self.alerts if not a.resolved]),
            'recent_failures': len([f for f in self.failures if f.timestamp > datetime.now() - timedelta(hours=1)]),
            'agent_performance': self._get_agent_performance_summary(),
            'resource_utilization': await self._get_resource_utilization(),
            'workload_characteristics': self._analyze_current_workload()
        }
    
    def _get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get summary of agent performance"""
        recent_performance = [pm for pm in self.performance_history 
                            if pm.collected_at > datetime.now() - timedelta(hours=1)]
        
        agent_summary = {}
        for pm in recent_performance:
            if pm.agent_id not in agent_summary:
                agent_summary[pm.agent_id] = {
                    'metrics_count': 0,
                    'avg_success_rate': 0,
                    'avg_response_time': 0
                }
            
            summary = agent_summary[pm.agent_id]
            summary['metrics_count'] += 1
            
            # Update averages (simplified)
            if 'success_rate' in pm.metrics:
                summary['avg_success_rate'] = (summary['avg_success_rate'] + pm.metrics['success_rate']) / 2
            if 'avg_completion_time' in pm.metrics:
                summary['avg_response_time'] = (summary['avg_response_time'] + pm.metrics['avg_completion_time']) / 2
        
        return agent_summary
    
    async def _get_resource_utilization(self) -> Dict[str, Any]:
        """Get current resource utilization"""
        # In real implementation, this would collect actual resource metrics
        return {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'disk_usage': 34.5,
            'network_io': {'in_mbps': 10.5, 'out_mbps': 8.3},
            'database_connections': 15,
            'redis_memory': 128.5  # MB
        }
    
    def _analyze_current_workload(self) -> Dict[str, Any]:
        """Analyze current system workload characteristics"""
        return {
            'active_tasks': 25,
            'queue_sizes': {
                'xml_processing': 5,
                'report_generation': 2,
                'scheduled_tasks': 8
            },
            'processing_rates': {
                'documents_per_hour': 150,
                'reports_per_hour': 12
            },
            'peak_load_indicator': 'normal'  # normal, high, critical
        }
    
    async def _parse_issue_predictions(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM issue prediction response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'predictions': [],
                'high_risk_issues': [],
                'recommendations': [llm_content[:500]],
                'confidence_score': 0.5
            }
    
    async def _create_proactive_alert(self, prediction: Dict[str, Any]):
        """Create proactive alert for high-risk predictions"""
        alert = SystemAlert(
            level=AlertLevel.WARNING,
            message=f"Proactive alert: {prediction.get('issue_description', 'Potential issue predicted')}",
            source="MonitoringAgent_Proactive",
            details={
                'prediction_type': prediction.get('type'),
                'probability': prediction.get('probability'),
                'estimated_time_to_occurrence': prediction.get('eta'),
                'preventive_actions': prediction.get('preventive_actions', []),
                'business_impact': prediction.get('business_impact')
            }
        )
        await self.handle_system_alert(alert)
    
    async def _generate_optimization_suggestions(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on predictions"""
        suggestions = []
        
        for prediction in predictions.get('predictions', []):
            if prediction.get('probability', 0) > 0.6:
                suggestion = {
                    'type': 'preventive_optimization',
                    'description': f"Optimize {prediction.get('issue_type')} to prevent predicted issue",
                    'priority': 'high' if prediction.get('probability', 0) > 0.8 else 'medium',
                    'actions': prediction.get('preventive_actions', []),
                    'estimated_impact': prediction.get('business_impact', 'medium')
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends for predictive analysis"""
        if len(self.performance_history) < 10:
            return {'insufficient_data': True}
        
        # Calculate trends over different time periods
        recent_24h = [pm for pm in self.performance_history 
                     if pm.collected_at > datetime.now() - timedelta(hours=24)]
        recent_7d = [pm for pm in self.performance_history 
                    if pm.collected_at > datetime.now() - timedelta(days=7)]
        
        return {
            'short_term_trend': self._calculate_trend_direction(recent_24h),
            'medium_term_trend': self._calculate_trend_direction(recent_7d),
            'performance_degradation': self._detect_performance_degradation(recent_24h),
            'resource_pressure': self._analyze_resource_pressure(recent_24h)
        }
    
    def _calculate_trend_direction(self, metrics_list: List) -> str:
        """Calculate overall trend direction for metrics"""
        if len(metrics_list) < 5:
            return 'insufficient_data'
        
        # Simple trend calculation based on success rates and response times
        first_half = metrics_list[:len(metrics_list)//2]
        second_half = metrics_list[len(metrics_list)//2:]
        
        first_avg = self._calculate_average_metrics(first_half)
        second_avg = self._calculate_average_metrics(second_half)
        
        # Check success rate trend
        if 'success_rate' in first_avg and 'success_rate' in second_avg:
            success_change = second_avg['success_rate'] - first_avg['success_rate']
            if success_change < -5:
                return 'declining'
            elif success_change > 5:
                return 'improving'
        
        return 'stable'
    
    def _detect_performance_degradation(self, recent_metrics: List) -> Dict[str, Any]:
        """Detect performance degradation patterns"""
        if len(recent_metrics) < 5:
            return {'detected': False}
        
        # Check for increasing response times
        response_times = []
        for pm in recent_metrics:
            if 'avg_completion_time' in pm.metrics:
                response_times.append(pm.metrics['avg_completion_time'])
        
        if len(response_times) >= 5:
            recent_avg = sum(response_times[-3:]) / 3
            older_avg = sum(response_times[:3]) / 3
            
            if recent_avg > older_avg * 1.5:  # 50% increase
                return {
                    'detected': True,
                    'type': 'response_time_degradation',
                    'severity': 'high' if recent_avg > older_avg * 2 else 'medium',
                    'change_percent': ((recent_avg - older_avg) / older_avg) * 100
                }
        
        return {'detected': False}
    
    def _analyze_resource_pressure(self, recent_metrics: List) -> Dict[str, Any]:
        """Analyze resource pressure indicators"""
        # In real implementation, this would analyze CPU, memory, disk usage trends
        return {
            'cpu_pressure': 'normal',
            'memory_pressure': 'normal',
            'disk_pressure': 'low',
            'network_pressure': 'low'
        }
    
    async def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        current_resources = await self._get_resource_utilization()
        
        return {
            'current_utilization': current_resources,
            'utilization_trends': self._calculate_resource_trends(),
            'capacity_warnings': self._check_capacity_warnings(current_resources),
            'optimization_opportunities': self._identify_resource_optimization_opportunities(current_resources)
        }
    
    def _calculate_resource_trends(self) -> Dict[str, Any]:
        """Calculate resource utilization trends"""
        # Placeholder for resource trend calculation
        return {
            'cpu_trend': 'stable',
            'memory_trend': 'increasing',
            'disk_trend': 'stable',
            'network_trend': 'stable'
        }
    
    def _check_capacity_warnings(self, resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for capacity warnings"""
        warnings = []
        
        if resources.get('cpu_usage', 0) > 80:
            warnings.append({
                'type': 'cpu_high',
                'current_value': resources['cpu_usage'],
                'threshold': 80,
                'severity': 'high'
            })
        
        if resources.get('memory_usage', 0) > 85:
            warnings.append({
                'type': 'memory_high',
                'current_value': resources['memory_usage'],
                'threshold': 85,
                'severity': 'high'
            })
        
        return warnings
    
    def _identify_resource_optimization_opportunities(self, resources: Dict[str, Any]) -> List[str]:
        """Identify resource optimization opportunities"""
        opportunities = []
        
        if resources.get('cpu_usage', 0) < 30:
            opportunities.append('CPU underutilization - consider resource reallocation')
        
        if resources.get('memory_usage', 0) > 80:
            opportunities.append('Memory optimization needed - review memory-intensive processes')
        
        return opportunities
    
    def _get_business_calendar_context(self) -> Dict[str, Any]:
        """Get business calendar context for predictions"""
        now = datetime.now()
        
        return {
            'current_date': now.isoformat(),
            'day_of_week': now.strftime('%A'),
            'is_month_end': now.day >= 25,
            'is_quarter_end': now.month in [3, 6, 9, 12] and now.day >= 25,
            'is_year_end': now.month == 12 and now.day >= 25,
            'business_hours': '09:00-17:00 BRT',
            'peak_processing_periods': ['month_end', 'quarter_end']
        }
    
    def _get_historical_incident_patterns(self) -> Dict[str, Any]:
        """Get historical incident patterns for prediction"""
        # In real implementation, this would analyze historical incident data
        return {
            'common_failure_patterns': [
                'database_connection_exhaustion',
                'xml_processing_queue_overflow',
                'memory_leaks_in_long_running_processes'
            ],
            'seasonal_incidents': {
                'month_end': ['high_load_database_timeouts', 'report_generation_delays'],
                'quarter_end': ['storage_capacity_issues', 'backup_failures']
            },
            'time_based_patterns': {
                'monday_morning': 'high_error_rates',
                'friday_evening': 'maintenance_window_issues'
            }
        }
    
    async def _identify_performance_bottlenecks(self) -> Dict[str, Any]:
        """Identify current performance bottlenecks"""
        current_metrics = await self._collect_system_metrics()
        
        bottlenecks = []
        
        # Check response time bottlenecks
        if current_metrics.get('response_times', {}).get('avg', 0) > 1000:
            bottlenecks.append({
                'type': 'response_time',
                'component': 'api',
                'severity': 'high',
                'current_value': current_metrics['response_times']['avg'],
                'threshold': 1000
            })
        
        # Check queue size bottlenecks
        for queue_name, size in current_metrics.get('queue_sizes', {}).items():
            if size > 50:
                bottlenecks.append({
                    'type': 'queue_overflow',
                    'component': queue_name,
                    'severity': 'medium',
                    'current_value': size,
                    'threshold': 50
                })
        
        return {
            'bottlenecks': bottlenecks,
            'bottleneck_count': len(bottlenecks),
            'most_critical': bottlenecks[0] if bottlenecks else None
        }
    
    async def _analyze_resource_constraints(self) -> Dict[str, Any]:
        """Analyze current resource constraints"""
        return {
            'cpu_constraint': 'none',  # none, moderate, severe
            'memory_constraint': 'moderate',
            'disk_constraint': 'none',
            'network_constraint': 'none',
            'database_connection_constraint': 'none',
            'constraint_summary': 'Memory usage approaching limits'
        }
    
    def _analyze_workload_patterns(self) -> Dict[str, Any]:
        """Analyze workload patterns"""
        return {
            'current_workload_type': 'normal',  # light, normal, heavy, peak
            'workload_distribution': {
                'xml_processing': 60,
                'report_generation': 25,
                'api_requests': 15
            },
            'peak_hours': '09:00-11:00, 14:00-16:00',
            'workload_predictability': 'high'  # high, medium, low
        }
    
    async def _get_infrastructure_capacity(self) -> Dict[str, Any]:
        """Get infrastructure capacity information"""
        return {
            'cpu_capacity': {'total_cores': 8, 'available_cores': 4.5},
            'memory_capacity': {'total_gb': 32, 'available_gb': 12},
            'disk_capacity': {'total_gb': 500, 'available_gb': 325},
            'network_capacity': {'max_mbps': 1000, 'current_utilization': 15},
            'scaling_options': ['horizontal_scaling', 'vertical_scaling'],
            'capacity_planning_horizon': '6_months'
        }
    
    async def _parse_optimization_suggestions(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM optimization suggestions response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'immediate_optimizations': [],
                'medium_term_improvements': [],
                'long_term_investments': [],
                'priority_ranking': [llm_content[:200]],
                'confidence_score': 0.5
            }
    
    def _prioritize_optimization_suggestions(self, optimization_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize optimization suggestions based on impact and feasibility"""
        all_suggestions = []
        
        # Add immediate optimizations with high priority
        for opt in optimization_plan.get('immediate_optimizations', []):
            opt['category'] = 'immediate'
            opt['priority_score'] = self._calculate_priority_score(opt['impact'], opt['effort'])
            all_suggestions.append(opt)
        
        # Add medium-term improvements
        for imp in optimization_plan.get('medium_term_improvements', []):
            imp['category'] = 'medium_term'
            imp['priority_score'] = self._calculate_priority_score(imp['impact'], imp['effort'])
            all_suggestions.append(imp)
        
        # Sort by priority score
        all_suggestions.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return {
            'suggestions': all_suggestions,
            'high_priority_count': len([s for s in all_suggestions if s.get('priority_score', 0) > 7]),
            'total_suggestions': len(all_suggestions),
            'prioritization_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_priority_score(self, impact: str, effort: str) -> int:
        """Calculate priority score based on impact and effort"""
        impact_scores = {'high': 9, 'medium': 6, 'low': 3}
        effort_scores = {'low': 3, 'medium': 2, 'high': 1}
        
        return impact_scores.get(impact, 6) + effort_scores.get(effort, 2)
    
    def _get_fiscal_data_baselines(self) -> Dict[str, Any]:
        """Get fiscal data quality baselines"""
        return {
            'validation_error_baseline': 2.5,  # percentage
            'missing_fields_baseline': 1.0,    # percentage
            'duplicate_rate_baseline': 0.5,    # percentage
            'processing_time_baseline': 2.5,   # seconds average
            'baseline_period': 'last_30_days'
        }
    
    async def _parse_data_quality_analysis(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM data quality analysis response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'data_quality_assessment': {'overall_score': 75, 'quality_trend': 'stable'},
                'data_quality_issues': [],
                'business_changes': [],
                'improvement_recommendations': [llm_content[:200]],
                'confidence_score': 0.5
            }
    
    def _get_maintenance_history(self) -> Dict[str, Any]:
        """Get maintenance history for planning"""
        return {
            'last_major_maintenance': '2024-10-01',
            'last_minor_maintenance': '2024-10-15',
            'maintenance_frequency': 'monthly',
            'average_downtime': '1.5_hours',
            'maintenance_success_rate': 95.0,
            'common_maintenance_issues': ['database_optimization', 'log_cleanup', 'security_updates']
        }
    
    def _get_business_calendar_events(self) -> List[Dict[str, Any]]:
        """Get upcoming business events that might affect maintenance scheduling"""
        return [
            {
                'event': 'month_end_processing',
                'date': '2024-11-30',
                'impact': 'high_load',
                'maintenance_restriction': True
            },
            {
                'event': 'quarter_end_reporting',
                'date': '2024-12-31',
                'impact': 'critical_load',
                'maintenance_restriction': True
            },
            {
                'event': 'holiday_period',
                'date_range': '2024-12-20 to 2025-01-05',
                'impact': 'reduced_support',
                'maintenance_restriction': True
            }
        ]
    
    def _analyze_resource_trends(self) -> Dict[str, Any]:
        """Analyze resource utilization trends"""
        return {
            'cpu_trend': {'direction': 'stable', 'change_rate': 2.5},
            'memory_trend': {'direction': 'increasing', 'change_rate': 8.3},
            'disk_trend': {'direction': 'increasing', 'change_rate': 5.1},
            'network_trend': {'direction': 'stable', 'change_rate': 1.2}
        }
    
    def _get_technical_debt_items(self) -> List[Dict[str, Any]]:
        """Get known technical debt items"""
        return [
            {
                'item': 'Legacy XML parser optimization',
                'priority': 'high',
                'estimated_effort': '2 weeks',
                'business_impact': 'Performance improvement for NF-e processing'
            },
            {
                'item': 'Database index optimization',
                'priority': 'medium',
                'estimated_effort': '1 week',
                'business_impact': 'Faster report generation'
            },
            {
                'item': 'API rate limiting implementation',
                'priority': 'medium',
                'estimated_effort': '1 week',
                'business_impact': 'Better resource protection'
            }
        ]
    
    async def _parse_maintenance_recommendations(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM maintenance recommendations response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'urgent_maintenance': [],
                'preventive_maintenance': [],
                'planned_improvements': [],
                'recommended_schedule': [],
                'confidence_score': 0.5
            }
    
    async def _assess_maintenance_impact(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business impact of maintenance recommendation"""
        return {
            'downtime_estimate': recommendation.get('estimated_downtime', 'unknown'),
            'affected_services': ['xml_processing', 'api'],
            'user_impact': 'minimal' if recommendation.get('urgency') == 'low' else 'moderate',
            'business_risk': 'low',
            'mitigation_strategies': ['schedule_during_maintenance_window', 'notify_users_in_advance']
        }