"""
Agentes IA para processamento de documentos fiscais
Adaptado do projeto alternativo com integração Supabase
"""

from .xml_processing_agent import XMLProcessingAgent
from .categorization_agent import CategorizationAgent
from .insights_agent import InsightsAgent

__all__ = [
    'XMLProcessingAgent',
    'CategorizationAgent', 
    'InsightsAgent'
]