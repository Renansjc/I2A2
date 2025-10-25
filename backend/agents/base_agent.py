"""
Base agent class for the AI Agents Invoice Analysis System
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import asyncio
from utils.logging import get_agent_logger
from utils.config import settings

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_agent_logger(agent_name)
        self.is_active = False
        self.status = "initialized"
        self._tasks = []
    
    async def start(self):
        """Start the agent"""
        self.logger.info("Starting agent")
        self.is_active = True
        self.status = "active"
        await self.initialize()
    
    async def stop(self):
        """Stop the agent"""
        self.logger.info("Stopping agent")
        self.is_active = False
        self.status = "stopped"
        await self.cleanup()
    
    @abstractmethod
    async def initialize(self):
        """Initialize agent-specific resources"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup agent-specific resources"""
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """Process data - main agent functionality"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.agent_name,
            "status": self.status,
            "is_active": self.is_active,
            "tasks_count": len(self._tasks)
        }
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            # Basic health check - can be overridden by specific agents
            return self.is_active and self.status == "active"
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return False
    
    def add_task(self, task_id: str, task_data: Dict[str, Any]):
        """Add task to agent queue"""
        self._tasks.append({"id": task_id, "data": task_data, "status": "queued"})
        self.logger.info("Task added", task_id=task_id)
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get status of specific task"""
        for task in self._tasks:
            if task["id"] == task_id:
                return task["status"]
        return None
    
    def update_task_status(self, task_id: str, status: str):
        """Update task status"""
        for task in self._tasks:
            if task["id"] == task_id:
                task["status"] = status
                self.logger.info("Task status updated", task_id=task_id, status=status)
                break