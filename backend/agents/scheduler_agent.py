"""
Scheduler Agent for managing automated recurring tasks and CronJobs
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog
import uuid

from .base_agent import BaseAgent
from utils.config import settings


class TaskFrequency(Enum):
    """Task frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """Task execution status"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledTask:
    """Scheduled task representation"""
    
    def __init__(self, task_id: str, name: str, frequency: TaskFrequency, 
                 query: str, recipients: List[str], format: str = "pdf"):
        self.task_id = task_id
        self.name = name
        self.frequency = frequency
        self.query = query
        self.recipients = recipients
        self.format = format
        self.created_at = datetime.now()
        self.next_run = None
        self.last_run = None
        self.status = TaskStatus.SCHEDULED
        self.cron_expression = ""
        self.execution_count = 0
        self.failure_count = 0


class SchedulerAgent(BaseAgent):
    """Agent responsible for managing automated recurring tasks"""
    
    def __init__(self):
        super().__init__("SchedulerAgent")
        self.scheduled_tasks = {}
        self.running_tasks = {}
        self.task_history = []
        
    async def initialize(self):
        """Initialize Scheduler Agent resources"""
        try:
            # Start the scheduler loop
            asyncio.create_task(self._scheduler_loop())
            
            self.logger.info("Scheduler Agent initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize Scheduler Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        # Cancel all running tasks
        for task_id in list(self.running_tasks.keys()):
            await self._cancel_task(task_id)
        
        self.logger.info("Scheduler Agent cleaned up")
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process scheduling request"""
        if isinstance(data, dict):
            action = data.get('action')
            
            if action == 'create_schedule':
                return await self.create_recurring_task(
                    query=data.get('query'),
                    frequency=data.get('frequency', 'monthly'),
                    recipients=data.get('recipients', []),
                    name=data.get('name', 'Relatório Automatizado'),
                    format=data.get('format', 'pdf')
                )
            elif action == 'cancel_schedule':
                return await self.cancel_task(data.get('task_id'))
            elif action == 'list_schedules':
                return await self.list_scheduled_tasks()
            elif action == 'get_status':
                return await self.get_task_status(data.get('task_id'))
        
        return {'error': 'Invalid request'}
    
    async def create_recurring_task(self, query: str, frequency: str, recipients: List[str],
                                  name: str = "Relatório Automatizado", format: str = "pdf") -> Dict[str, Any]:
        """Create a new recurring task"""
        try:
            task_id = str(uuid.uuid4())
            freq_enum = TaskFrequency(frequency.lower())
            
            # Create scheduled task
            task = ScheduledTask(
                task_id=task_id,
                name=name,
                frequency=freq_enum,
                query=query,
                recipients=recipients,
                format=format
            )
            
            # Generate cron expression
            task.cron_expression = await self.generate_cron_expression(freq_enum)
            
            # Calculate next run time
            task.next_run = await self._calculate_next_run(freq_enum)
            
            # Store task
            self.scheduled_tasks[task_id] = task
            
            self.logger.info("Recurring task created", 
                           task_id=task_id, 
                           frequency=frequency,
                           next_run=task.next_run.isoformat())
            
            return {
                'task_id': task_id,
                'name': name,
                'frequency': frequency,
                'cron_expression': task.cron_expression,
                'next_run': task.next_run.isoformat(),
                'recipients': recipients,
                'status': 'scheduled'
            }
            
        except Exception as e:
            self.logger.error("Error creating recurring task", error=str(e))
            return {'error': str(e)}
    
    async def generate_cron_expression(self, frequency: TaskFrequency) -> str:
        """Generate cron expression for specified frequency"""
        
        cron_expressions = {
            TaskFrequency.DAILY: "0 9 * * *",        # Daily at 9 AM
            TaskFrequency.WEEKLY: "0 9 * * 1",       # Weekly on Monday at 9 AM
            TaskFrequency.MONTHLY: "0 9 1 * *",      # Monthly on 1st at 9 AM
            TaskFrequency.QUARTERLY: "0 9 1 */3 *",  # Quarterly on 1st at 9 AM
            TaskFrequency.YEARLY: "0 9 1 1 *"        # Yearly on Jan 1st at 9 AM
        }
        
        return cron_expressions.get(frequency, "0 9 1 * *")
    
    async def _calculate_next_run(self, frequency: TaskFrequency) -> datetime:
        """Calculate next run time based on frequency"""
        now = datetime.now()
        
        if frequency == TaskFrequency.DAILY:
            next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif frequency == TaskFrequency.WEEKLY:
            # Next Monday at 9 AM
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=9, minute=0, second=0, microsecond=0)
        
        elif frequency == TaskFrequency.MONTHLY:
            # First day of next month at 9 AM
            if now.day == 1 and now.hour < 9:
                next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, day=1, 
                                         hour=9, minute=0, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month + 1, day=1, 
                                         hour=9, minute=0, second=0, microsecond=0)
        
        elif frequency == TaskFrequency.QUARTERLY:
            # First day of next quarter at 9 AM
            current_quarter = (now.month - 1) // 3 + 1
            next_quarter_month = current_quarter * 3 + 1
            if next_quarter_month > 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1,
                                     hour=9, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=next_quarter_month, day=1,
                                     hour=9, minute=0, second=0, microsecond=0)
        
        elif frequency == TaskFrequency.YEARLY:
            # January 1st of next year at 9 AM
            next_run = now.replace(year=now.year + 1, month=1, day=1,
                                 hour=9, minute=0, second=0, microsecond=0)
        
        else:
            # Default to next day
            next_run = now + timedelta(days=1)
            next_run = next_run.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return next_run
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks for tasks to execute"""
        while True:
            try:
                await self._check_and_execute_tasks()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error("Error in scheduler loop", error=str(e))
                await asyncio.sleep(60)
    
    async def _check_and_execute_tasks(self):
        """Check for tasks that need to be executed"""
        now = datetime.now()
        
        for task_id, task in list(self.scheduled_tasks.items()):
            if (task.status == TaskStatus.SCHEDULED and 
                task.next_run and 
                task.next_run <= now):
                
                # Execute task
                await self._execute_task(task)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            self.logger.info("Executing scheduled task", task_id=task.task_id, name=task.name)
            
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()
            self.running_tasks[task.task_id] = task
            
            # Execute the task (generate report and deliver)
            result = await self.execute_scheduled_task(task)
            
            if result.get('success', False):
                task.status = TaskStatus.COMPLETED
                task.execution_count += 1
                
                # Deliver report to recipients
                await self.deliver_scheduled_report(result.get('report'), task.recipients)
                
                self.logger.info("Scheduled task completed successfully", 
                               task_id=task.task_id)
            else:
                task.status = TaskStatus.FAILED
                task.failure_count += 1
                
                self.logger.error("Scheduled task failed", 
                                task_id=task.task_id, 
                                error=result.get('error'))
            
            # Calculate next run time
            task.next_run = await self._calculate_next_run(task.frequency)
            task.status = TaskStatus.SCHEDULED
            
            # Remove from running tasks
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            
            # Add to history
            self.task_history.append({
                'task_id': task.task_id,
                'name': task.name,
                'executed_at': task.last_run,
                'status': TaskStatus.COMPLETED if result.get('success') else TaskStatus.FAILED,
                'result': result
            })
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.failure_count += 1
            
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            
            self.logger.error("Error executing scheduled task", 
                            task_id=task.task_id, error=str(e))
    
    async def execute_scheduled_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute the actual task (query + report generation)"""
        try:
            # This would integrate with other agents to:
            # 1. Execute the SQL query via SQL Agent
            # 2. Generate report via Report Agent
            # 3. Return the result
            
            # Placeholder implementation
            result = {
                'success': True,
                'report': {
                    'title': task.name,
                    'format': task.format,
                    'file_path': f'/tmp/report_{task.task_id}.{task.format}',
                    'generated_at': datetime.now().isoformat()
                },
                'query_result': {
                    'rows': 100,
                    'execution_time': 2.5
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deliver_scheduled_report(self, report: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Deliver scheduled report to recipients"""
        try:
            self.logger.info("Delivering scheduled report", 
                           recipients=recipients, 
                           report_title=report.get('title'))
            
            # In a real implementation, this would:
            # 1. Send email with report attachment
            # 2. Upload to shared storage
            # 3. Send notifications
            
            delivery_results = []
            for recipient in recipients:
                # Placeholder delivery
                delivery_results.append({
                    'recipient': recipient,
                    'status': 'delivered',
                    'delivered_at': datetime.now().isoformat()
                })
            
            return {
                'success': True,
                'deliveries': delivery_results
            }
            
        except Exception as e:
            self.logger.error("Error delivering scheduled report", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a scheduled task"""
        try:
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                
                # Remove from running tasks if currently running
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                
                self.logger.info("Task cancelled", task_id=task_id)
                
                return {
                    'success': True,
                    'task_id': task_id,
                    'status': 'cancelled'
                }
            else:
                return {
                    'success': False,
                    'error': 'Task not found'
                }
                
        except Exception as e:
            self.logger.error("Error cancelling task", task_id=task_id, error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _cancel_task(self, task_id: str):
        """Internal method to cancel task"""
        await self.cancel_task(task_id)
    
    async def list_scheduled_tasks(self) -> Dict[str, Any]:
        """List all scheduled tasks"""
        try:
            tasks = []
            
            for task_id, task in self.scheduled_tasks.items():
                tasks.append({
                    'task_id': task_id,
                    'name': task.name,
                    'frequency': task.frequency.value,
                    'status': task.status.value,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'execution_count': task.execution_count,
                    'failure_count': task.failure_count,
                    'recipients': task.recipients,
                    'format': task.format
                })
            
            return {
                'success': True,
                'tasks': tasks,
                'total_tasks': len(tasks),
                'running_tasks': len(self.running_tasks)
            }
            
        except Exception as e:
            self.logger.error("Error listing scheduled tasks", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of specific task"""
        try:
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                
                return {
                    'success': True,
                    'task_id': task_id,
                    'name': task.name,
                    'status': task.status.value,
                    'frequency': task.frequency.value,
                    'cron_expression': task.cron_expression,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'execution_count': task.execution_count,
                    'failure_count': task.failure_count,
                    'created_at': task.created_at.isoformat(),
                    'recipients': task.recipients,
                    'format': task.format,
                    'query': task.query
                }
            else:
                return {
                    'success': False,
                    'error': 'Task not found'
                }
                
        except Exception as e:
            self.logger.error("Error getting task status", task_id=task_id, error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_task_history(self, task_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get task execution history"""
        try:
            history = self.task_history
            
            if task_id:
                history = [h for h in history if h['task_id'] == task_id]
            
            # Sort by execution time (most recent first)
            history = sorted(history, key=lambda x: x['executed_at'], reverse=True)
            
            # Limit results
            history = history[:limit]
            
            return {
                'success': True,
                'history': history,
                'total_executions': len(history)
            }
            
        except Exception as e:
            self.logger.error("Error getting task history", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def manage_task_lifecycle(self, task: ScheduledTask) -> Dict[str, Any]:
        """Manage complete task lifecycle"""
        try:
            # Check if task should be retired (too many failures, etc.)
            if task.failure_count > 5:
                task.status = TaskStatus.CANCELLED
                self.logger.warning("Task cancelled due to excessive failures", 
                                  task_id=task.task_id, 
                                  failures=task.failure_count)
                return {'action': 'cancelled', 'reason': 'excessive_failures'}
            
            # Check if task is stale (hasn't run in a long time)
            if (task.last_run and 
                datetime.now() - task.last_run > timedelta(days=30) and
                task.frequency in [TaskFrequency.DAILY, TaskFrequency.WEEKLY]):
                
                self.logger.warning("Task appears stale", 
                                  task_id=task.task_id, 
                                  last_run=task.last_run)
                return {'action': 'flagged', 'reason': 'stale_task'}
            
            return {'action': 'continue', 'status': 'healthy'}
            
        except Exception as e:
            self.logger.error("Error managing task lifecycle", error=str(e))
            return {'action': 'error', 'error': str(e)}