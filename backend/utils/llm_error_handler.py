"""
LLM-Enhanced Error Handler for intelligent error analysis and recovery suggestions
"""

import asyncio
import json
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog

from .openai_integration import get_openai_service, LLMResponse
from .config import settings

logger = structlog.get_logger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    SYSTEM = "system"
    DATABASE = "database"
    XML_PROCESSING = "xml_processing"
    AGENT_COMMUNICATION = "agent_communication"
    API = "api"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    LLM_SERVICE = "llm_service"

@dataclass
class ErrorContext:
    """Context information for error analysis"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    stack_trace: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
    operation: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    business_context: Optional[Dict[str, Any]] = None

@dataclass
class ErrorAnalysis:
    """Result of LLM-powered error analysis"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    root_cause: str
    business_impact: str
    technical_diagnosis: str
    recovery_suggestions: List[str]
    prevention_recommendations: List[str]
    user_friendly_message: str
    admin_alert_message: str
    confidence_score: float
    similar_errors: List[str]
    escalation_required: bool

class LLMEnhancedErrorHandler:
    """
    LLM-Enhanced Error Handler for intelligent error analysis and recovery suggestions
    
    This class provides:
    - Intelligent error analysis using LLMs
    - Contextual error diagnosis and solution suggestions
    - Business-appropriate error message translation
    - Pattern recognition for predictive error detection
    - Automated recovery suggestions
    """
    
    def __init__(self):
        self.llm_service = get_openai_service()
        self.error_history: List[ErrorContext] = []
        self.error_patterns: Dict[str, List[ErrorContext]] = {}
        self.max_history_size = 1000
        self.pattern_analysis_threshold = 5
        
        # Error message templates in Portuguese
        self.user_message_templates = {
            ErrorCategory.XML_PROCESSING: "Houve um problema ao processar o documento fiscal. Nossa equipe foi notificada e está trabalhando na solução.",
            ErrorCategory.DATABASE: "Ocorreu um problema temporário com o banco de dados. Tente novamente em alguns minutos.",
            ErrorCategory.API: "Serviço temporariamente indisponível. Tente novamente em alguns instantes.",
            ErrorCategory.AUTHENTICATION: "Problema de autenticação. Verifique suas credenciais e tente novamente.",
            ErrorCategory.VALIDATION: "Os dados fornecidos não estão no formato correto. Verifique e tente novamente.",
            ErrorCategory.LLM_SERVICE: "Serviço de análise inteligente temporariamente indisponível. Funcionalidades básicas continuam disponíveis.",
            ErrorCategory.BUSINESS_LOGIC: "Não foi possível processar a solicitação devido a regras de negócio. Entre em contato com o suporte.",
            ErrorCategory.EXTERNAL_SERVICE: "Serviço externo temporariamente indisponível. Tente novamente mais tarde.",
            ErrorCategory.AGENT_COMMUNICATION: "Problema de comunicação entre serviços. Nossa equipe foi notificada.",
            ErrorCategory.SYSTEM: "Erro interno do sistema. Nossa equipe técnica foi notificada automaticamente."
        }
        
        logger.info("LLM Enhanced Error Handler initialized")
    
    async def analyze_error(self, error_context: ErrorContext) -> ErrorAnalysis:
        """
        Analyze error using LLM for intelligent diagnosis and suggestions
        """
        try:
            # Add to error history
            self._add_to_history(error_context)
            
            # Get similar errors for pattern analysis
            similar_errors = self._find_similar_errors(error_context)
            
            # Prepare context for LLM analysis
            llm_context = await self._prepare_llm_context(error_context, similar_errors)
            
            # Generate LLM analysis
            llm_response = await self.llm_service.generate_completion(
                "error_analysis",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.1
            )
            
            # Parse LLM response
            analysis_data = await self._parse_llm_analysis(llm_response.content)
            
            # Create error analysis
            analysis = ErrorAnalysis(
                error_id=error_context.error_id,
                category=ErrorCategory(analysis_data.get('category', 'system')),
                severity=ErrorSeverity(analysis_data.get('severity', 'medium')),
                root_cause=analysis_data.get('root_cause', 'Causa não identificada'),
                business_impact=analysis_data.get('business_impact', 'Impacto sendo avaliado'),
                technical_diagnosis=analysis_data.get('technical_diagnosis', 'Diagnóstico em andamento'),
                recovery_suggestions=analysis_data.get('recovery_suggestions', []),
                prevention_recommendations=analysis_data.get('prevention_recommendations', []),
                user_friendly_message=analysis_data.get('user_friendly_message', ''),
                admin_alert_message=analysis_data.get('admin_alert_message', ''),
                confidence_score=analysis_data.get('confidence_score', llm_response.confidence_score),
                similar_errors=[e.error_id for e in similar_errors],
                escalation_required=analysis_data.get('escalation_required', False)
            )
            
            # Enhance with business-appropriate messages if not provided by LLM
            if not analysis.user_friendly_message:
                analysis.user_friendly_message = self._generate_user_friendly_message(analysis.category)
            
            # Log analysis
            logger.info("Error analysis completed",
                       error_id=error_context.error_id,
                       category=analysis.category.value,
                       severity=analysis.severity.value,
                       confidence=analysis.confidence_score)
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to analyze error with LLM", 
                        error_id=error_context.error_id,
                        analysis_error=str(e))
            
            # Fallback analysis without LLM
            return self._create_fallback_analysis(error_context)
    
    async def create_admin_alert(self, error_analysis: ErrorAnalysis) -> Dict[str, Any]:
        """
        Create contextual and actionable alert message for administrators
        """
        try:
            # Get system context
            system_context = await self._get_system_context_for_alert()
            
            llm_context = {
                'error_analysis': {
                    'error_id': error_analysis.error_id,
                    'category': error_analysis.category.value,
                    'severity': error_analysis.severity.value,
                    'root_cause': error_analysis.root_cause,
                    'business_impact': error_analysis.business_impact,
                    'technical_diagnosis': error_analysis.technical_diagnosis,
                    'escalation_required': error_analysis.escalation_required
                },
                'system_context': system_context,
                'similar_errors_count': len(error_analysis.similar_errors),
                'alert_urgency': self._calculate_alert_urgency(error_analysis)
            }
            
            llm_response = await self.llm_service.generate_completion(
                "admin_alert_generation",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.1
            )
            
            alert_data = await self._parse_admin_alert(llm_response.content)
            
            # Enhance with metadata
            alert = {
                'alert_id': f"alert_{error_analysis.error_id}_{int(datetime.now().timestamp())}",
                'timestamp': datetime.now().isoformat(),
                'severity': error_analysis.severity.value,
                'category': error_analysis.category.value,
                'title': alert_data.get('title', f'Erro {error_analysis.severity.value.upper()} detectado'),
                'message': alert_data.get('message', error_analysis.admin_alert_message),
                'technical_details': alert_data.get('technical_details', error_analysis.technical_diagnosis),
                'recommended_actions': alert_data.get('recommended_actions', error_analysis.recovery_suggestions),
                'business_impact': alert_data.get('business_impact', error_analysis.business_impact),
                'escalation_required': error_analysis.escalation_required,
                'related_errors': error_analysis.similar_errors,
                'confidence_score': error_analysis.confidence_score
            }
            
            logger.info("Admin alert created",
                       alert_id=alert['alert_id'],
                       severity=alert['severity'],
                       escalation_required=alert['escalation_required'])
            
            return alert
            
        except Exception as e:
            logger.error("Failed to create admin alert", 
                        error_id=error_analysis.error_id,
                        error=str(e))
            return self._create_basic_admin_alert(error_analysis)
    
    def _add_to_history(self, error_context: ErrorContext):
        """Add error to history and maintain size limit"""
        self.error_history.append(error_context)
        
        # Maintain history size
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        
        # Update pattern tracking
        pattern_key = f"{error_context.error_type}_{error_context.agent_name}"
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = []
        self.error_patterns[pattern_key].append(error_context)
    
    def _find_similar_errors(self, error_context: ErrorContext, limit: int = 5) -> List[ErrorContext]:
        """Find similar errors for pattern analysis"""
        similar = []
        
        for historical_error in reversed(self.error_history[-50:]):
            if historical_error.error_id == error_context.error_id:
                continue
            
            similarity_score = self._calculate_error_similarity(error_context, historical_error)
            if similarity_score > 0.7:
                similar.append(historical_error)
                if len(similar) >= limit:
                    break
        
        return similar
    
    def _calculate_error_similarity(self, error1: ErrorContext, error2: ErrorContext) -> float:
        """Calculate similarity score between two errors"""
        score = 0.0
        
        if error1.error_type == error2.error_type:
            score += 0.4
        
        if error1.agent_name == error2.agent_name:
            score += 0.3
        
        if error1.operation == error2.operation:
            score += 0.2
        
        if error1.error_message and error2.error_message:
            common_words = set(error1.error_message.lower().split()) & set(error2.error_message.lower().split())
            if len(common_words) > 2:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _prepare_llm_context(self, error_context: ErrorContext, similar_errors: List[ErrorContext]) -> Dict[str, Any]:
        """Prepare context for LLM error analysis"""
        return {
            'error_details': {
                'error_type': error_context.error_type,
                'error_message': error_context.error_message,
                'stack_trace': error_context.stack_trace[:2000],
                'agent_name': error_context.agent_name,
                'operation': error_context.operation,
                'timestamp': error_context.timestamp.isoformat()
            },
            'system_context': {
                'input_data': error_context.input_data,
                'system_state': error_context.system_state,
                'business_context': error_context.business_context
            },
            'historical_context': {
                'similar_errors_count': len(similar_errors),
                'recent_error_rate': len(self.error_history[-10:]),
                'error_patterns': list(self.error_patterns.keys())
            },
            'system_capabilities': {
                'available_agents': ['master', 'xml_processing', 'categorization', 'sql', 'report'],
                'recovery_mechanisms': ['restart_agent', 'clear_cache', 'retry_operation', 'fallback_mode'],
                'monitoring_tools': ['health_check', 'performance_metrics', 'log_analysis']
            }
        }
    
    async def _parse_llm_analysis(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'category': 'system',
                'severity': 'medium',
                'root_cause': 'Análise automática não disponível',
                'business_impact': 'Impacto sendo avaliado',
                'technical_diagnosis': llm_content[:500],
                'recovery_suggestions': ['Verificar logs do sistema', 'Reiniciar serviços afetados'],
                'prevention_recommendations': ['Monitorar métricas de sistema'],
                'confidence_score': 0.5,
                'escalation_required': False
            }
    
    def _generate_user_friendly_message(self, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        return self.user_message_templates.get(
            category, 
            "Ocorreu um problema temporário. Nossa equipe foi notificada e está trabalhando na solução."
        )
    
    def _create_fallback_analysis(self, error_context: ErrorContext) -> ErrorAnalysis:
        """Create basic error analysis when LLM is unavailable"""
        category = self._categorize_error_simple(error_context.error_type, error_context.error_message)
        severity = self._assess_severity_simple(error_context.error_type)
        
        return ErrorAnalysis(
            error_id=error_context.error_id,
            category=category,
            severity=severity,
            root_cause="Análise automática não disponível",
            business_impact="Impacto sendo avaliado pela equipe técnica",
            technical_diagnosis=f"Erro: {error_context.error_message}",
            recovery_suggestions=["Verificar logs do sistema", "Reiniciar serviços afetados"],
            prevention_recommendations=["Monitorar métricas de sistema"],
            user_friendly_message=self._generate_user_friendly_message(category),
            admin_alert_message=f"Erro {severity.value} detectado: {error_context.error_message}",
            confidence_score=0.6,
            similar_errors=[],
            escalation_required=severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        )
    
    def _categorize_error_simple(self, error_type: str, error_message: str) -> ErrorCategory:
        """Simple rule-based error categorization"""
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower() if error_message else ""
        
        if 'database' in error_type_lower or 'sql' in error_message_lower:
            return ErrorCategory.DATABASE
        elif 'xml' in error_type_lower or 'parse' in error_message_lower:
            return ErrorCategory.XML_PROCESSING
        elif 'auth' in error_type_lower or 'permission' in error_message_lower:
            return ErrorCategory.AUTHENTICATION
        elif 'validation' in error_type_lower or 'invalid' in error_message_lower:
            return ErrorCategory.VALIDATION
        elif 'http' in error_type_lower or 'api' in error_type_lower or 'endpoint' in error_message_lower:
            return ErrorCategory.API
        elif 'openai' in error_type_lower or 'llm' in error_message_lower or 'rate limit' in error_message_lower:
            return ErrorCategory.LLM_SERVICE
        else:
            return ErrorCategory.SYSTEM
    
    def _assess_severity_simple(self, error_type: str) -> ErrorSeverity:
        """Simple rule-based severity assessment"""
        error_type_lower = error_type.lower()
        
        if any(keyword in error_type_lower for keyword in ['critical', 'fatal', 'security']):
            return ErrorSeverity.CRITICAL
        elif any(keyword in error_type_lower for keyword in ['error', 'exception', 'failed']):
            return ErrorSeverity.HIGH
        elif any(keyword in error_type_lower for keyword in ['warning', 'timeout']):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def _get_system_context_for_alert(self) -> Dict[str, Any]:
        """Get system context for alert generation"""
        return {
            'current_time': datetime.now().isoformat(),
            'system_load': 'normal',
            'active_users': 10,
            'recent_error_count': len(self.error_history[-10:]),
            'system_uptime': '99.5%',
            'last_maintenance': datetime.now() - timedelta(days=7)
        }
    
    def _calculate_alert_urgency(self, error_analysis: ErrorAnalysis) -> str:
        """Calculate alert urgency level"""
        if error_analysis.severity == ErrorSeverity.CRITICAL:
            return 'immediate'
        elif error_analysis.severity == ErrorSeverity.HIGH:
            return 'high'
        elif len(error_analysis.similar_errors) > 3:
            return 'medium'
        else:
            return 'low'
    
    async def _parse_admin_alert(self, llm_content: str) -> Dict[str, Any]:
        """Parse admin alert from LLM response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'title': 'Erro detectado no sistema',
                'message': llm_content[:500],
                'technical_details': 'Detalhes técnicos não disponíveis',
                'recommended_actions': ['Verificar logs', 'Reiniciar serviços'],
                'business_impact': 'Impacto sendo avaliado'
            }
    
    def _create_basic_admin_alert(self, error_analysis: ErrorAnalysis) -> Dict[str, Any]:
        """Create basic admin alert without LLM"""
        return {
            'alert_id': f"alert_{error_analysis.error_id}_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'severity': error_analysis.severity.value,
            'category': error_analysis.category.value,
            'title': f'Erro {error_analysis.severity.value.upper()} - {error_analysis.category.value}',
            'message': f'Erro detectado: {error_analysis.root_cause}',
            'technical_details': error_analysis.technical_diagnosis,
            'recommended_actions': error_analysis.recovery_suggestions,
            'business_impact': error_analysis.business_impact,
            'escalation_required': error_analysis.escalation_required,
            'related_errors': error_analysis.similar_errors,
            'confidence_score': error_analysis.confidence_score
        }
    
    async def generate_recovery_plan(self, error_analysis: ErrorAnalysis) -> Dict[str, Any]:
        """
        Generate automated recovery plan using LLM
        """
        try:
            llm_context = {
                'error_analysis': {
                    'category': error_analysis.category.value,
                    'severity': error_analysis.severity.value,
                    'root_cause': error_analysis.root_cause,
                    'technical_diagnosis': error_analysis.technical_diagnosis,
                    'recovery_suggestions': error_analysis.recovery_suggestions
                },
                'system_capabilities': await self._get_system_capabilities(),
                'current_system_state': await self._get_current_system_state(),
                'business_constraints': await self._get_business_constraints()
            }
            
            llm_response = await self.llm_service.generate_completion(
                "recovery_plan_generation",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.2
            )
            
            recovery_plan = await self._parse_recovery_plan(llm_response.content)
            
            logger.info("Recovery plan generated",
                       error_id=error_analysis.error_id,
                       automated_steps=len(recovery_plan.get('automated_steps', [])),
                       manual_steps=len(recovery_plan.get('manual_steps', [])))
            
            return recovery_plan
            
        except Exception as e:
            logger.error("Failed to generate recovery plan", 
                        error_id=error_analysis.error_id,
                        error=str(e))
            return self._create_basic_recovery_plan(error_analysis)
    
    async def detect_error_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect error patterns using LLM analysis for predictive monitoring
        """
        try:
            if len(self.error_history) < self.pattern_analysis_threshold:
                return []
            
            # Group errors by type and time windows
            pattern_groups = self._group_errors_for_pattern_analysis()
            
            patterns = []
            for group_key, errors in pattern_groups.items():
                if len(errors) >= self.pattern_analysis_threshold:
                    pattern = await self._analyze_error_pattern(group_key, errors)
                    if pattern:
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error("Failed to detect error patterns", error=str(e))
            return []
    
    async def _get_system_capabilities(self) -> Dict[str, Any]:
        """Get current system capabilities for recovery planning"""
        return {
            'automated_recovery': ['restart_agent', 'clear_cache', 'retry_operation'],
            'monitoring_tools': ['health_check', 'performance_metrics'],
            'backup_systems': ['fallback_mode', 'manual_processing'],
            'notification_channels': ['admin_alert', 'email', 'slack']
        }
    
    async def _get_current_system_state(self) -> Dict[str, Any]:
        """Get current system state for recovery planning"""
        return {
            'system_load': 'normal',
            'available_resources': 'sufficient',
            'active_agents': 8,
            'error_rate': len(self.error_history[-10:]) / 10,
            'last_backup': datetime.now() - timedelta(hours=1)
        }
    
    async def _get_business_constraints(self) -> Dict[str, Any]:
        """Get business constraints for recovery planning"""
        return {
            'business_hours': '08:00-18:00 BRT',
            'critical_operations': ['xml_processing', 'report_generation'],
            'maintenance_windows': ['02:00-04:00 BRT'],
            'sla_requirements': {'uptime': '99.5%', 'response_time': '< 5s'}
        }
    
    async def _parse_recovery_plan(self, llm_content: str) -> Dict[str, Any]:
        """Parse recovery plan from LLM response"""
        try:
            return json.loads(llm_content)
        except json.JSONDecodeError:
            return {
                'automated_steps': ['Verificar status dos serviços', 'Reiniciar agentes afetados'],
                'manual_steps': ['Verificar logs detalhados', 'Contatar suporte se necessário'],
                'estimated_recovery_time': '5-10 minutos',
                'success_probability': 0.8
            }
    
    def _create_basic_recovery_plan(self, error_analysis: ErrorAnalysis) -> Dict[str, Any]:
        """Create basic recovery plan without LLM"""
        return {
            'automated_steps': [
                'Verificar status dos serviços',
                'Reiniciar agentes afetados',
                'Limpar cache se necessário'
            ],
            'manual_steps': [
                'Verificar logs detalhados',
                'Analisar causa raiz',
                'Implementar correção permanente'
            ],
            'estimated_recovery_time': '10-15 minutos',
            'success_probability': 0.7,
            'escalation_required': error_analysis.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        }
    
    def _group_errors_for_pattern_analysis(self) -> Dict[str, List[ErrorContext]]:
        """Group errors for pattern analysis"""
        groups = {}
        
        # Group by error type and time window (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for error in self.error_history:
            if error.timestamp < cutoff_time:
                continue
            
            group_key = f"{error.error_type}_{error.agent_name}"
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(error)
        
        return groups
    
    async def _analyze_error_pattern(self, group_key: str, errors: List[ErrorContext]) -> Optional[Dict[str, Any]]:
        """Analyze a group of errors for patterns"""
        try:
            llm_context = {
                'pattern_group': group_key,
                'error_count': len(errors),
                'time_span': (errors[-1].timestamp - errors[0].timestamp).total_seconds() / 3600,  # hours
                'error_details': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'message': e.error_message,
                        'operation': e.operation
                    }
                    for e in errors[-10:]  # Last 10 errors in pattern
                ]
            }
            
            llm_response = await self.llm_service.generate_completion(
                "error_pattern_analysis",
                llm_context,
                model=settings.OPENAI_DEFAULT_MODEL,
                temperature=0.1
            )
            
            pattern_data = json.loads(llm_response.content)
            
            return {
                'pattern_id': f"pattern_{group_key}_{int(datetime.now().timestamp())}",
                'pattern_type': pattern_data.get('pattern_type', 'recurring_error'),
                'description': pattern_data.get('description', f'Padrão detectado em {group_key}'),
                'frequency': len(errors),
                'severity': pattern_data.get('severity', 'medium'),
                'predicted_impact': pattern_data.get('predicted_impact', 'Impacto sendo avaliado'),
                'prevention_recommendations': pattern_data.get('prevention_recommendations', []),
                'confidence_score': pattern_data.get('confidence_score', llm_response.confidence_score)
            }
            
        except Exception as e:
            logger.error("Failed to analyze error pattern", pattern=group_key, error=str(e))
            return None

# Global instance
error_handler = None

def get_error_handler() -> LLMEnhancedErrorHandler:
    """Get global error handler instance"""
    global error_handler
    if error_handler is None:
        error_handler = LLMEnhancedErrorHandler()
    return error_handler

# Convenience functions for easy integration
async def analyze_and_handle_error(
    error: Exception,
    context: Dict[str, Any] = None,
    user_id: str = None,
    agent_name: str = None,
    operation: str = None
) -> ErrorAnalysis:
    """
    Convenience function to analyze and handle an error
    """
    handler = get_error_handler()
    
    error_context = ErrorContext(
        error_id=f"error_{int(datetime.now().timestamp())}_{hash(str(error)) % 10000}",
        timestamp=datetime.now(),
        error_type=type(error).__name__,
        error_message=str(error),
        stack_trace=traceback.format_exc(),
        user_id=user_id,
        agent_name=agent_name,
        operation=operation,
        input_data=context.get('input_data') if context else None,
        system_state=context.get('system_state') if context else None,
        business_context=context.get('business_context') if context else None
    )
    
    return await handler.analyze_error(error_context)

async def create_user_friendly_error_response(error_analysis: ErrorAnalysis) -> Dict[str, Any]:
    """
    Create user-friendly error response for API endpoints
    """
    return {
        'error': True,
        'error_id': error_analysis.error_id,
        'message': error_analysis.user_friendly_message,
        'severity': error_analysis.severity.value,
        'timestamp': datetime.now().isoformat(),
        'support_available': True,
        'retry_recommended': error_analysis.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
    }