"""
Dimensional Coordinator for orchestrating the dimensional processing pipeline
"""

import structlog
from typing import Dict, Any, Optional
from datetime import datetime

from .dimensional_processing_agent import DimensionalProcessingAgent
from .xml_processing_agent import LLMEnhancedXMLProcessingAgent
from .ai_categorization_agent import LLMEnhancedAICategorizationAgent
from utils.database import ProcessingStatusManager

logger = structlog.get_logger()


class DimensionalCoordinator:
    """
    Coordinator for the dimensional processing pipeline:
    XML Processing → AI Categorization → Dimensional Processing → Storage
    """
    
    def __init__(self):
        self.xml_agent = LLMEnhancedXMLProcessingAgent()
        self.categorization_agent = LLMEnhancedAICategorizationAgent()
        self.dimensional_agent = DimensionalProcessingAgent()
        
    async def initialize(self):
        """Initialize all agents"""
        await self.xml_agent.initialize()
        await self.categorization_agent.initialize()
        await self.dimensional_agent.initialize()
        
        logger.info("Dimensional coordinator initialized")
    
    async def cleanup(self):
        """Cleanup all agents"""
        await self.xml_agent.cleanup()
        await self.categorization_agent.cleanup()
        await self.dimensional_agent.cleanup()
        
        logger.info("Dimensional coordinator cleaned up")
    
    async def process_document_pipeline(
        self, 
        xml_content: str, 
        document_id: str, 
        document_type: str = "NFE"
    ) -> Dict[str, Any]:
        """
        Execute the complete dimensional processing pipeline
        
        Args:
            xml_content: Raw XML content
            document_id: Document identifier
            document_type: Type of document (NFE or NFSE)
            
        Returns:
            Combined results from all processing stages
        """
        try:
            logger.info(
                "Starting dimensional processing pipeline",
                document_id=document_id,
                document_type=document_type
            )
            
            # Initialize agent statuses
            agent_names = [
                "xml_processing_agent",
                "ai_categorization_agent", 
                "dimensional_processing_agent"
            ]
            
            await ProcessingStatusManager.initialize_agent_statuses(
                document_id, agent_names, admin_mode=True
            )
            
            context = {
                'document_id': document_id,
                'document_type': document_type,
                'pipeline_stage': 'dimensional_processing'
            }
            
            # Stage 1: XML Processing and Extraction
            logger.info("Stage 1: XML Processing", document_id=document_id)
            xml_results = await self._execute_xml_processing(xml_content, context)
            
            # Stage 2: AI Categorization and Enrichment
            logger.info("Stage 2: AI Categorization", document_id=document_id)
            categorization_results = await self._execute_categorization(xml_content, context)
            
            # Stage 3: Dimensional Processing and Storage
            logger.info("Stage 3: Dimensional Processing", document_id=document_id)
            dimensional_results = await self._execute_dimensional_processing(xml_content, context)
            
            # Combine results
            pipeline_results = {
                "document_id": document_id,
                "document_type": document_type,
                "pipeline_status": "completed",
                "stages": {
                    "xml_processing": xml_results,
                    "ai_categorization": categorization_results,
                    "dimensional_processing": dimensional_results
                },
                "summary": {
                    "emitente_processed": dimensional_results.get("emitente_id") is not None,
                    "destinatario_processed": dimensional_results.get("destinatario_id") is not None,
                    "produtos_count": dimensional_results.get("produtos_processed", 0),
                    "servicos_count": dimensional_results.get("servicos_processed", 0),
                    "fact_records_count": dimensional_results.get("fact_records_created", 0),
                    "categorization_items": categorization_results.get("total_items", 0),
                    "integrity_check": dimensional_results.get("integrity_check", {})
                },
                "processing_time": datetime.now().isoformat()
            }
            
            logger.info(
                "Dimensional processing pipeline completed successfully",
                document_id=document_id,
                summary=pipeline_results["summary"]
            )
            
            return pipeline_results
            
        except Exception as e:
            logger.error(
                "Dimensional processing pipeline failed",
                document_id=document_id,
                error=str(e)
            )
            
            # Update all agent statuses to failed
            for agent_name in agent_names:
                await ProcessingStatusManager.update_agent_status(
                    document_id, agent_name, "failed", str(e), admin_mode=True
                )
            
            raise
    
    async def _execute_xml_processing(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute XML processing stage with error recovery"""
        try:
            data = {
                'xml_content': xml_content,
                'context': context
            }
            
            result = await self.xml_agent.process(data)
            
            logger.info(
                "XML processing stage completed",
                document_id=context.get('document_id'),
                status=result.get('processing_status')
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "XML processing stage failed",
                document_id=context.get('document_id'),
                error=str(e)
            )
            
            # Attempt recovery with basic extraction
            recovery_result = await self._recover_xml_processing(xml_content, context)
            return recovery_result
    
    async def _execute_categorization(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI categorization stage with error recovery"""
        try:
            data = {
                'xml_content': xml_content,
                'context': context
            }
            
            result = await self.categorization_agent.process(data)
            
            logger.info(
                "AI categorization stage completed",
                document_id=context.get('document_id'),
                items_categorized=result.get('total_items', 0)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "AI categorization stage failed",
                document_id=context.get('document_id'),
                error=str(e)
            )
            
            # Attempt recovery with basic categorization
            recovery_result = await self._recover_categorization(xml_content, context)
            return recovery_result
    
    async def _execute_dimensional_processing(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dimensional processing stage"""
        try:
            data = {
                'xml_content': xml_content,
                'context': context
            }
            
            result = await self.dimensional_agent.process(data)
            
            logger.info(
                "Dimensional processing stage completed",
                document_id=context.get('document_id'),
                emitente_id=result.get('emitente_id'),
                produtos_processed=result.get('produtos_processed', 0)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Dimensional processing stage failed",
                document_id=context.get('document_id'),
                error=str(e)
            )
            raise  # Don't recover from dimensional processing failures
    
    async def _recover_xml_processing(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Recovery mechanism for XML processing failures"""
        try:
            logger.info("Attempting XML processing recovery", document_id=context.get('document_id'))
            
            # Basic recovery - extract minimal required data
            from lxml import etree
            
            root = etree.fromstring(xml_content.encode('utf-8'))
            document_type = context.get('document_type', 'NFE')
            
            # Basic document summary
            recovery_result = {
                "document_type": document_type,
                "document_summary": {
                    "supplier": "Fornecedor (recuperação)",
                    "total_value": 0.0,
                    "emission_date": datetime.now().isoformat(),
                    "document_key": f"RECOVERY_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                },
                "semantic_analysis": {
                    "document_structure": "recovered",
                    "confidence": 0.5,
                    "recovery_mode": True
                },
                "business_insights": [
                    {
                        "type": "recovery_mode",
                        "description": "Documento processado em modo de recuperação",
                        "confidence": 0.5
                    }
                ],
                "anomalies": ["Processamento em modo de recuperação"],
                "business_validation": {"recovery_mode": True},
                "processing_status": "recovered"
            }
            
            logger.info("XML processing recovery completed", document_id=context.get('document_id'))
            return recovery_result
            
        except Exception as e:
            logger.error("XML processing recovery failed", error=str(e))
            raise
    
    async def _recover_categorization(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Recovery mechanism for categorization failures"""
        try:
            logger.info("Attempting categorization recovery", document_id=context.get('document_id'))
            
            # Basic recovery - provide default categorization
            recovery_result = {
                "categorized_items": [
                    {
                        "code": "RECOVERY_001",
                        "description": "Item processado em modo de recuperação",
                        "category": "Outros",
                        "subcategory": "Recuperação",
                        "confidence": 0.3,
                        "categorization_method": "recovery_mode"
                    }
                ],
                "category_insights": [
                    {
                        "type": "recovery_mode",
                        "description": "Categorização realizada em modo de recuperação",
                        "confidence": 0.3
                    }
                ],
                "patterns_detected": [
                    {
                        "type": "recovery_processing",
                        "description": "Documento processado com categorização de recuperação",
                        "confidence": 0.3
                    }
                ],
                "total_items": 1,
                "unique_categories": 1,
                "confidence": 0.3,
                "processing_status": "recovered"
            }
            
            logger.info("Categorization recovery completed", document_id=context.get('document_id'))
            return recovery_result
            
        except Exception as e:
            logger.error("Categorization recovery failed", error=str(e))
            raise
    
    async def get_pipeline_status(self, document_id: str) -> Dict[str, Any]:
        """Get current status of the dimensional processing pipeline"""
        try:
            # Get processing status for all agents
            statuses = await ProcessingStatusManager.get_document_processing_status(
                document_id, admin_mode=True
            )
            
            # Get processing results
            results = await ProcessingStatusManager.get_processing_results(
                document_id, admin_mode=True
            )
            
            pipeline_status = {
                "document_id": document_id,
                "agent_statuses": {status['agent_name']: status for status in statuses},
                "processing_results": results,
                "overall_status": self._determine_overall_status(statuses)
            }
            
            return pipeline_status
            
        except Exception as e:
            logger.error("Failed to get pipeline status", error=str(e))
            return {"document_id": document_id, "error": str(e)}
    
    def _determine_overall_status(self, agent_statuses: list) -> str:
        """Determine overall pipeline status from individual agent statuses"""
        if not agent_statuses:
            return "pending"
        
        status_counts = {}
        for status in agent_statuses:
            agent_status = status.get('status', 'unknown')
            status_counts[agent_status] = status_counts.get(agent_status, 0) + 1
        
        # Determine overall status
        if status_counts.get('failed', 0) > 0:
            return "failed"
        elif status_counts.get('in_progress', 0) > 0:
            return "in_progress"
        elif status_counts.get('completed', 0) == len(agent_statuses):
            return "completed"
        else:
            return "pending"