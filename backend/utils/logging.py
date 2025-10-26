"""
Logging utilities for the AI Agents system
"""

import structlog
from typing import Any

def get_agent_logger(agent_name: str) -> Any:
    """Get a logger for an agent"""
    return structlog.get_logger().bind(agent=agent_name)