"""
Master Agent - Central orchestrator for the AI Agents Invoice Analysis System
"""

import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
import structlog

from .base_agent import BaseAgent
from models.fiscal_data import FiscalDocument
from utils.config import settings


class Intent(Enum):
    """User intent types"""
    QUERY_DATA = "query_data"
    GENERATE_REPORT = "generate_report"
    SCHEDULE_TASK = "schedule_task"
    ANALYZE_TRENDS = "analyze_trends"
    UNKNOWN = "unknown"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MasterAgent(BaseAgent):
    """Master Agent responsible for orchestrating all other agents"""
    
    def __init__(self):
        super().__init__("MasterAgent")
        self.active_workflows = {}
        self.agent_registry = {}
        self.intent_patterns = {}
        
    async def initialize(self):
        """Initialize Master Agent resources"""
        try:
            # Initialize intent recognition patterns
            await self._load_intent_patterns()
            
            # Register other agents (would be done dynamically in real implementation)
            await self._register_agents()
            
            self.logger.info("Master Agent initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize Master Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        # Cancel any active workflows
        for workflow_id in list(self.active_workflows.keys()):
            await self._cancel_workflow(workflow_id)
        
        self.logger.info("Master Agent cleaned up")
    
    async def process(self, data: str) -> Dict[str, Any]:
        """Process natural language query from user"""
        if isinstance(data, str):
            return await self.interpret_query(data)
        return {"error": "Invalid input type"}
    
    async def _load_intent_patterns(self):
        """Load intent recognition patterns"""
        try:
            # Simple keyword-based intent recognition
            # In a real implementation, this would use NLP models
            self.intent_patterns = {
                Intent.QUERY_DATA: [
                    'quanto', 'qual', 'quais', 'como', 'quando', 'onde',
                    'mostrar', 'listar', 'buscar', 'encontrar', 'consultar',
                    'fornecedor', 'produto', 'serviço', 'valor', 'total'
                ],
                Intent.GENERATE_REPORT: [
                    'relatório', 'report', 'gerar', 'criar', 'exportar',
                    'pdf', 'excel', 'xlsx', 'word', 'docx'
                ],
                Intent.SCHEDULE_TASK: [
                    'agendar', 'programar', 'automatizar', 'recorrente',
                    'diário', 'semanal', 'mensal', 'schedule'
                ],
                Intent.ANALYZE_TRENDS: [
                    'tendência', 'padrão', 'análise', 'comparar',
                    'crescimento', 'redução', 'evolução', 'histórico'
                ]
            }
            
            self.logger.info("Intent patterns loaded")
            
        except Exception as e:
            self.logger.error("Error loading intent patterns", error=str(e))
    
    async def _register_agents(self):
        """Register other agents in the system"""
        try:
            # In a real implementation, this would discover and register agents dynamically
            self.agent_registry = {
                'xml_processing': 'XMLProcessingAgent',
                'ai_categorization': 'AICategorization Agent',
                'sql': 'SQLAgent',
                'report': 'ReportAgent',
                'scheduler': 'SchedulerAgent',
                'data_lake': 'DataLakeAgent',
                'monitoring': 'MonitoringAgent'
            }
            
            self.logger.info("Agents registered", agents=list(self.agent_registry.keys()))
            
        except Exception as e:
            self.logger.error("Error registering agents", error=str(e))
    
    async def interpret_query(self, natural_language_query: str) -> Dict[str, Any]:
        """Interpret user's natural language query"""
        try:
            self.logger.info("Interpreting query", query=natural_language_query)
            
            # Detect intent
            intent = await self._detect_intent(natural_language_query)
            
            # Extract entities and parameters
            entities = await self._extract_entities(natural_language_query)
            
            # Create workflow based on intent
            workflow_id = await self._create_workflow(intent, entities, natural_language_query)
            
            # Execute workflow
            result = await self._execute_workflow(workflow_id)
            
            return {
                'workflow_id': workflow_id,
                'intent': intent.value,
                'entities': entities,
                'result': result,
                'status': 'completed'
            }
            
        except Exception as e:
            self.logger.error("Error interpreting query", error=str(e))
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    async def _detect_intent(self, query: str) -> Intent:
        """Detect user intent from natural language query"""
        query_lower = query.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            self.logger.info("Intent detected", intent=best_intent.value, score=intent_scores[best_intent])
            return best_intent
        
        return Intent.UNKNOWN
    
    async def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from natural language query"""
        entities = {}
        query_lower = query.lower()
        
        # Simple entity extraction (in reality, would use NLP models)
        
        # Time periods
        if 'mês' in query_lower or 'mensal' in query_lower:
            entities['time_period'] = 'monthly'
        elif 'ano' in query_lower or 'anual' in query_lower:
            entities['time_period'] = 'yearly'
        elif 'semana' in query_lower or 'semanal' in query_lower:
            entities['time_period'] = 'weekly'
        
        # Document types
        if 'nfe' in query_lower or 'nota fiscal eletrônica' in query_lower:
            entities['document_type'] = 'NFE'
        elif 'nfse' in query_lower or 'nota fiscal de serviço' in query_lower:
            entities['document_type'] = 'NFSE'
        
        # Report formats
        if 'pdf' in query_lower:
            entities['format'] = 'pdf'
        elif 'excel' in query_lower or 'xlsx' in query_lower:
            entities['format'] = 'xlsx'
        elif 'word' in query_lower or 'docx' in query_lower:
            entities['format'] = 'docx'
        
        # Suppliers/Products (would be more sophisticated in reality)
        if 'fornecedor' in query_lower:
            entities['entity_type'] = 'supplier'
        elif 'produto' in query_lower:
            entities['entity_type'] = 'product'
        elif 'serviço' in query_lower:
            entities['entity_type'] = 'service'
        
        return entities
    
    async def _create_workflow(self, intent: Intent, entities: Dict[str, Any], original_query: str) -> str:
        """Create workflow based on intent and entities"""
        import uuid
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            'id': workflow_id,
            'intent': intent,
            'entities': entities,
            'original_query': original_query,
            'status': WorkflowStatus.PENDING,
            'steps': [],
            'results': {}
        }
        
        # Define workflow steps based on intent
        if intent == Intent.QUERY_DATA:
            workflow['steps'] = [
                {'agent': 'sql', 'action': 'generate_query', 'data': {'query': original_query, 'entities': entities}},
                {'agent': 'data_lake', 'action': 'execute_query', 'data': None},  # Will be filled by previous step
                {'agent': 'master', 'action': 'format_response', 'data': None}
            ]
        
        elif intent == Intent.GENERATE_REPORT:
            workflow['steps'] = [
                {'agent': 'sql', 'action': 'generate_query', 'data': {'query': original_query, 'entities': entities}},
                {'agent': 'data_lake', 'action': 'execute_query', 'data': None},
                {'agent': 'report', 'action': 'generate_report', 'data': {'format': entities.get('format', 'pdf')}},
                {'agent': 'master', 'action': 'present_report', 'data': None}
            ]
        
        elif intent == Intent.SCHEDULE_TASK:
            workflow['steps'] = [
                {'agent': 'sql', 'action': 'generate_query', 'data': {'query': original_query, 'entities': entities}},
                {'agent': 'scheduler', 'action': 'create_schedule', 'data': {'frequency': entities.get('time_period', 'monthly')}},
                {'agent': 'master', 'action': 'confirm_schedule', 'data': None}
            ]
        
        elif intent == Intent.ANALYZE_TRENDS:
            workflow['steps'] = [
                {'agent': 'sql', 'action': 'generate_analytics_query', 'data': {'query': original_query, 'entities': entities}},
                {'agent': 'data_lake', 'action': 'execute_analytics', 'data': None},
                {'agent': 'ai_categorization', 'action': 'analyze_patterns', 'data': None},
                {'agent': 'master', 'action': 'present_analysis', 'data': None}
            ]
        
        else:
            workflow['steps'] = [
                {'agent': 'master', 'action': 'handle_unknown_intent', 'data': {'query': original_query}}
            ]
        
        self.active_workflows[workflow_id] = workflow
        
        self.logger.info("Workflow created", workflow_id=workflow_id, intent=intent.value, steps=len(workflow['steps']))
        
        return workflow_id
    
    async def _execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute workflow steps"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow['status'] = WorkflowStatus.IN_PROGRESS
        
        try:
            self.logger.info("Executing workflow", workflow_id=workflow_id)
            
            for i, step in enumerate(workflow['steps']):
                self.logger.info("Executing step", workflow_id=workflow_id, step=i+1, agent=step['agent'])
                
                # Execute step (in reality, this would route to actual agents)
                step_result = await self._execute_step(step, workflow['results'])
                workflow['results'][f'step_{i+1}'] = step_result
                
                # Update data for next step if needed
                if i < len(workflow['steps']) - 1:
                    next_step = workflow['steps'][i + 1]
                    if next_step['data'] is None:
                        next_step['data'] = step_result
            
            workflow['status'] = WorkflowStatus.COMPLETED
            
            # Generate final result
            final_result = await self._generate_final_result(workflow)
            
            self.logger.info("Workflow completed", workflow_id=workflow_id)
            
            return final_result
            
        except Exception as e:
            workflow['status'] = WorkflowStatus.FAILED
            self.logger.error("Workflow execution failed", workflow_id=workflow_id, error=str(e))
            raise
    
    async def _execute_step(self, step: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        agent = step['agent']
        action = step['action']
        data = step['data']
        
        # This is a placeholder implementation
        # In reality, this would route to actual agent instances
        
        if agent == 'sql':
            if action == 'generate_query':
                return {
                    'sql_query': f"SELECT * FROM fiscal_documents WHERE {data.get('entities', {})}",
                    'query_type': 'data_query'
                }
            elif action == 'generate_analytics_query':
                return {
                    'sql_query': "SELECT supplier, SUM(total_value) FROM fiscal_documents GROUP BY supplier",
                    'query_type': 'analytics_query'
                }
        
        elif agent == 'data_lake':
            if action == 'execute_query':
                return {
                    'data': [{'supplier': 'Fornecedor A', 'total': 10000}],
                    'row_count': 1
                }
            elif action == 'execute_analytics':
                return {
                    'analytics_data': [{'period': '2024-01', 'value': 50000}],
                    'trends': ['increasing']
                }
        
        elif agent == 'report':
            if action == 'generate_report':
                return {
                    'report_path': '/tmp/report.pdf',
                    'format': data.get('format', 'pdf'),
                    'size': '2.5MB'
                }
        
        elif agent == 'scheduler':
            if action == 'create_schedule':
                return {
                    'schedule_id': 'sched_123',
                    'frequency': data.get('frequency', 'monthly'),
                    'next_run': '2024-02-01 09:00:00'
                }
        
        elif agent == 'ai_categorization':
            if action == 'analyze_patterns':
                return {
                    'patterns': ['seasonal_increase', 'new_supplier_trend'],
                    'confidence': 0.85
                }
        
        elif agent == 'master':
            return await self._handle_master_action(action, data, previous_results)
        
        return {'status': 'completed', 'agent': agent, 'action': action}
    
    async def _handle_master_action(self, action: str, data: Any, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Master Agent specific actions"""
        if action == 'format_response':
            return {
                'formatted_response': "Aqui estão os dados solicitados:",
                'data_summary': previous_results
            }
        
        elif action == 'present_report':
            return {
                'message': "Relatório gerado com sucesso!",
                'download_link': "/api/reports/download/123"
            }
        
        elif action == 'confirm_schedule':
            return {
                'message': "Tarefa agendada com sucesso!",
                'schedule_details': previous_results
            }
        
        elif action == 'present_analysis':
            return {
                'analysis_summary': "Análise de tendências concluída",
                'insights': previous_results
            }
        
        elif action == 'handle_unknown_intent':
            return {
                'message': "Desculpe, não consegui entender sua solicitação. Pode reformular?",
                'suggestions': [
                    "Gerar relatório mensal de fornecedores",
                    "Mostrar produtos mais comprados",
                    "Agendar relatório semanal"
                ]
            }
        
        return {'status': 'completed'}
    
    async def _generate_final_result(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final result from workflow execution"""
        intent = workflow['intent']
        results = workflow['results']
        
        # Get the last step result as the primary result
        last_step_key = f"step_{len(workflow['steps'])}"
        primary_result = results.get(last_step_key, {})
        
        return {
            'intent': intent.value,
            'workflow_id': workflow['id'],
            'status': 'completed',
            'result': primary_result,
            'execution_summary': {
                'steps_executed': len(workflow['steps']),
                'total_time': '2.3s',  # Placeholder
                'agents_involved': list(set(step['agent'] for step in workflow['steps']))
            }
        }
    
    async def _cancel_workflow(self, workflow_id: str):
        """Cancel an active workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['status'] = WorkflowStatus.FAILED
            self.logger.info("Workflow cancelled", workflow_id=workflow_id)
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow"""
        if workflow_id not in self.active_workflows:
            return {'error': 'Workflow not found'}
        
        workflow = self.active_workflows[workflow_id]
        return {
            'workflow_id': workflow_id,
            'status': workflow['status'].value,
            'intent': workflow['intent'].value,
            'steps_completed': len([r for r in workflow['results'].values() if r]),
            'total_steps': len(workflow['steps'])
        }
    
    async def route_to_agent(self, agent_name: str, action: str, data: Any) -> Dict[str, Any]:
        """Route request to specific agent"""
        try:
            self.logger.info("Routing to agent", agent=agent_name, action=action)
            
            # In a real implementation, this would route to actual agent instances
            # For now, return a placeholder response
            
            return {
                'agent': agent_name,
                'action': action,
                'status': 'completed',
                'result': f"Action {action} completed by {agent_name}"
            }
            
        except Exception as e:
            self.logger.error("Error routing to agent", agent=agent_name, error=str(e))
            return {'error': str(e)}
    
    async def coordinate_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Coordinate complex multi-agent workflow"""
        try:
            workflow_id = await self._create_custom_workflow(workflow_steps)
            return await self._execute_workflow(workflow_id)
        except Exception as e:
            self.logger.error("Error coordinating workflow", error=str(e))
            return {'error': str(e)}
    
    async def _create_custom_workflow(self, steps: List[Dict[str, Any]]) -> str:
        """Create custom workflow from provided steps"""
        import uuid
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            'id': workflow_id,
            'intent': Intent.UNKNOWN,
            'entities': {},
            'original_query': 'Custom workflow',
            'status': WorkflowStatus.PENDING,
            'steps': steps,
            'results': {}
        }
        
        self.active_workflows[workflow_id] = workflow
        return workflow_id