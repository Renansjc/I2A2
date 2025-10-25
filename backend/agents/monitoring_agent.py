"""
Monitoring Agent for error logging, notifications, and system health monitoring
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog

from .base_agent import BaseAgent
from models.fiscal_data import ProcessingError
from utils.config import settings


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
    """Agent responsible for system monitoring and error handling"""
    
    def __init__(self):
        super().__init__("MonitoringAgent")
        self.alerts = []
        self.failures = []
        self.performance_history = []
        self.system_metrics = {}
        self.alert_thresholds = {}
        
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
            
            self.logger.log(
                self._get_log_level(alert.level),
                "System alert generated",
                alert_id=alert.alert_id,
                level=alert.level.value,
                message=alert.message,
                source=alert.source,
                details=alert.details
            )
            
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