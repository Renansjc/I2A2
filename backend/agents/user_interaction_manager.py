"""
User Interaction Management System
Gerencia interações com usuários executivos, incluindo confirmações e feedback
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class InteractionType(Enum):
    """Tipos de interação com usuário"""
    CONFIRMACAO_WORKFLOW = "confirmacao_workflow"
    ESCOLHA_PARAMETROS = "escolha_parametros"
    APROVACAO_RELATORIO = "aprovacao_relatorio"
    FEEDBACK_RESULTADO = "feedback_resultado"
    ESCLARECIMENTO_CONSULTA = "esclarecimento_consulta"
    CONFIGURACAO_PREFERENCIAS = "configuracao_preferencias"


class InteractionStatus(Enum):
    """Status de interações"""
    PENDENTE = "pendente"
    AGUARDANDO_RESPOSTA = "aguardando_resposta"
    RESPONDIDA = "respondida"
    EXPIRADA = "expirada"
    CANCELADA = "cancelada"


@dataclass
class InteractionOption:
    """Opção de resposta para interação"""
    id: str
    label: str
    value: Any
    description: Optional[str] = None
    is_default: bool = False


@dataclass
class UserInteraction:
    """Representa uma interação com usuário"""
    id: str
    user_id: str
    type: InteractionType
    title: str
    message: str
    options: List[InteractionOption] = field(default_factory=list)
    status: InteractionStatus = InteractionStatus.PENDENTE
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response: Optional[Any] = None
    context: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None


class UserInteractionManager:
    """
    Gerenciador de interações com usuários executivos
    Implementa sistema de confirmações, escolhas e feedback
    """
    
    def __init__(self, master_agent):
        self.master_agent = master_agent
        self.active_interactions: Dict[str, UserInteraction] = {}
        self.interaction_history: Dict[str, List[UserInteraction]] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.default_timeout_minutes = 15
        self.is_running = False
        
    async def initialize(self):
        """Inicializa o gerenciador de interações"""
        try:
            logger.info("Inicializando gerenciador de interações...")
            
            # Carrega preferências padrão
            await self._load_default_preferences()
            
            # Inicia loop de limpeza de interações expiradas
            self.is_running = True
            asyncio.create_task(self._cleanup_expired_interactions())
            
            logger.info("Gerenciador de interações inicializado")
            
        except Exception as e:
            logger.error("Erro ao inicializar gerenciador de interações", error=str(e))
            raise
    
    async def shutdown(self):
        """Finaliza o gerenciador"""
        try:
            self.is_running = False
            
            # Cancela interações pendentes
            for interaction in list(self.active_interactions.values()):
                if interaction.status in [InteractionStatus.PENDENTE, InteractionStatus.AGUARDANDO_RESPOSTA]:
                    interaction.status = InteractionStatus.CANCELADA
            
            logger.info("Gerenciador de interações finalizado")
            
        except Exception as e:
            logger.error("Erro ao finalizar gerenciador", error=str(e))
    
    async def _load_default_preferences(self):
        """Carrega preferências padrão para usuários executivos"""
        self.default_user_preferences = {
            'timeout_interacao_minutos': 15,
            'formato_relatorio_padrao': 'pdf',
            'nivel_detalhe': 'executivo',
            'notificacoes_ativas': True,
            'confirmacao_automatica': False,
            'idioma': 'pt-br',
            'fuso_horario': 'America/Sao_Paulo'
        }
    
    async def create_workflow_confirmation(self, user_id: str, workflow_id: str, 
                                         preview: Dict[str, Any]) -> str:
        """Cria interação de confirmação de workflow"""
        try:
            interaction_id = f"confirm_{workflow_id}"
            
            # Prepara opções de confirmação
            options = [
                InteractionOption(
                    id="confirm",
                    label="✅ Confirmar e Executar",
                    value=True,
                    description="Executar consulta conforme interpretado",
                    is_default=True
                ),
                InteractionOption(
                    id="cancel",
                    label="❌ Cancelar",
                    value=False,
                    description="Cancelar esta consulta"
                ),
                InteractionOption(
                    id="modify",
                    label="✏️ Modificar Parâmetros",
                    value="modify",
                    description="Ajustar parâmetros antes de executar"
                ),
                InteractionOption(
                    id="details",
                    label="ℹ️ Mais Detalhes",
                    value="details",
                    description="Ver mais informações sobre a consulta"
                )
            ]
            
            # Cria mensagem executiva
            message = self._format_executive_confirmation_message(preview)
            
            interaction = UserInteraction(
                id=interaction_id,
                user_id=user_id,
                type=InteractionType.CONFIRMACAO_WORKFLOW,
                title="Confirmação de Consulta Fiscal",
                message=message,
                options=options,
                expires_at=datetime.now() + timedelta(minutes=self._get_user_timeout(user_id)),
                context={
                    'workflow_id': workflow_id,
                    'preview': preview
                }
            )
            
            self.active_interactions[interaction_id] = interaction
            
            logger.info("Confirmação de workflow criada", 
                       interaction_id=interaction_id,
                       user_id=user_id,
                       workflow_id=workflow_id)
            
            return interaction_id
            
        except Exception as e:
            logger.error("Erro ao criar confirmação de workflow", error=str(e))
            raise
    
    def _format_executive_confirmation_message(self, preview: Dict[str, Any]) -> str:
        """Formata mensagem de confirmação para nível executivo"""
        intent = preview.get('intent_detectado', 'Operação')
        confidence = preview.get('confianca', '0%')
        interpretation = preview.get('interpretacao', 'Consulta fiscal')
        estimated_time = preview.get('tempo_estimado', 'Não estimado')
        
        message = f"""
**{interpretation}**

**Confiança da Interpretação:** {confidence}

**Parâmetros Identificados:**
"""
        
        # Adiciona parâmetros extraídos
        params = preview.get('parametros_extraidos', {})
        if params:
            for key, value in params.items():
                message += f"• **{key.replace('_', ' ').title()}:** {value}\n"
        else:
            message += "• Nenhum parâmetro específico identificado\n"
        
        # Adiciona entidades encontradas
        entities = preview.get('entidades_encontradas', [])
        if entities:
            message += f"\n**Entidades Reconhecidas:**\n"
            for entity in entities:
                message += f"• {entity}\n"
        
        # Adiciona passos planejados
        steps = preview.get('passos_planejados', [])
        if steps:
            message += f"\n**Execução Planejada:**\n"
            for step in steps:
                message += f"• {step}\n"
        
        message += f"\n**Tempo Estimado:** {estimated_time}"
        
        message += f"\n\n*Confirme se a interpretação está correta antes de prosseguir.*"
        
        return message
    
    async def create_parameter_choice(self, user_id: str, parameter_name: str, 
                                    options: List[Dict[str, Any]], 
                                    context: Dict[str, Any] = None) -> str:
        """Cria interação para escolha de parâmetros"""
        try:
            interaction_id = f"param_{parameter_name}_{datetime.now().timestamp()}"
            
            # Converte opções para InteractionOption
            interaction_options = []
            for i, option in enumerate(options):
                interaction_options.append(
                    InteractionOption(
                        id=f"option_{i}",
                        label=option.get('label', str(option.get('value', f'Opção {i+1}'))),
                        value=option.get('value'),
                        description=option.get('description'),
                        is_default=option.get('is_default', False)
                    )
                )
            
            message = f"**Escolha o valor para {parameter_name.replace('_', ' ').title()}:**\n\n"
            message += "Selecione uma das opções abaixo para continuar com a consulta."
            
            interaction = UserInteraction(
                id=interaction_id,
                user_id=user_id,
                type=InteractionType.ESCOLHA_PARAMETROS,
                title=f"Escolha de Parâmetro: {parameter_name.replace('_', ' ').title()}",
                message=message,
                options=interaction_options,
                expires_at=datetime.now() + timedelta(minutes=self._get_user_timeout(user_id)),
                context=context or {}
            )
            
            self.active_interactions[interaction_id] = interaction
            
            logger.info("Escolha de parâmetro criada", 
                       interaction_id=interaction_id,
                       parameter=parameter_name)
            
            return interaction_id
            
        except Exception as e:
            logger.error("Erro ao criar escolha de parâmetro", error=str(e))
            raise
    
    async def create_report_approval(self, user_id: str, report_info: Dict[str, Any]) -> str:
        """Cria interação para aprovação de relatório"""
        try:
            interaction_id = f"approve_report_{datetime.now().timestamp()}"
            
            options = [
                InteractionOption(
                    id="approve",
                    label="✅ Aprovar e Baixar",
                    value="approve",
                    description="Aprovar relatório e disponibilizar para download",
                    is_default=True
                ),
                InteractionOption(
                    id="regenerate",
                    label="🔄 Regenerar",
                    value="regenerate",
                    description="Regenerar relatório com ajustes"
                ),
                InteractionOption(
                    id="modify_format",
                    label="📄 Alterar Formato",
                    value="modify_format",
                    description="Alterar formato do relatório (PDF, Excel, Word)"
                ),
                InteractionOption(
                    id="reject",
                    label="❌ Rejeitar",
                    value="reject",
                    description="Rejeitar relatório"
                )
            ]
            
            message = f"""
**Relatório Gerado com Sucesso**

**Detalhes do Relatório:**
• **Formato:** {report_info.get('format', 'N/A')}
• **Tamanho:** {report_info.get('size', 'N/A')}
• **Páginas:** {report_info.get('pages', 'N/A')}

O relatório foi gerado e está pronto para aprovação.
"""
            
            interaction = UserInteraction(
                id=interaction_id,
                user_id=user_id,
                type=InteractionType.APROVACAO_RELATORIO,
                title="Aprovação de Relatório",
                message=message,
                options=options,
                expires_at=datetime.now() + timedelta(minutes=self._get_user_timeout(user_id)),
                context={'report_info': report_info}
            )
            
            self.active_interactions[interaction_id] = interaction
            
            logger.info("Aprovação de relatório criada", interaction_id=interaction_id)
            
            return interaction_id
            
        except Exception as e:
            logger.error("Erro ao criar aprovação de relatório", error=str(e))
            raise
    
    async def provide_response(self, interaction_id: str, response_value: Any) -> Dict[str, Any]:
        """Fornece resposta para interação"""
        try:
            if interaction_id not in self.active_interactions:
                return {
                    'erro': 'Interação não encontrada',
                    'interaction_id': interaction_id
                }
            
            interaction = self.active_interactions[interaction_id]
            
            # Verifica se interação ainda está válida
            if interaction.status != InteractionStatus.AGUARDANDO_RESPOSTA:
                if interaction.status == InteractionStatus.PENDENTE:
                    interaction.status = InteractionStatus.AGUARDANDO_RESPOSTA
                else:
                    return {
                        'erro': f'Interação não está aguardando resposta (status: {interaction.status.value})',
                        'interaction_id': interaction_id
                    }
            
            # Verifica expiração
            if interaction.expires_at and datetime.now() > interaction.expires_at:
                interaction.status = InteractionStatus.EXPIRADA
                return {
                    'erro': 'Interação expirou',
                    'interaction_id': interaction_id
                }
            
            # Registra resposta
            interaction.response = response_value
            interaction.responded_at = datetime.now()
            interaction.status = InteractionStatus.RESPONDIDA
            
            # Move para histórico
            await self._move_to_history(interaction)
            
            # Executa callback se existir
            if interaction.callback:
                try:
                    await interaction.callback(interaction)
                except Exception as e:
                    logger.error("Erro no callback da interação", 
                               interaction_id=interaction_id, error=str(e))
            
            logger.info("Resposta fornecida para interação", 
                       interaction_id=interaction_id,
                       response=response_value)
            
            return {
                'interaction_id': interaction_id,
                'status': 'respondida',
                'response': response_value,
                'message': 'Resposta registrada com sucesso'
            }
            
        except Exception as e:
            logger.error("Erro ao fornecer resposta", 
                        interaction_id=interaction_id, error=str(e))
            return {'erro': str(e)}
    
    async def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de uma interação"""
        try:
            if interaction_id not in self.active_interactions:
                return None
            
            interaction = self.active_interactions[interaction_id]
            
            return {
                'id': interaction.id,
                'user_id': interaction.user_id,
                'type': interaction.type.value,
                'title': interaction.title,
                'message': interaction.message,
                'options': [
                    {
                        'id': opt.id,
                        'label': opt.label,
                        'value': opt.value,
                        'description': opt.description,
                        'is_default': opt.is_default
                    }
                    for opt in interaction.options
                ],
                'status': interaction.status.value,
                'created_at': interaction.created_at.isoformat(),
                'expires_at': interaction.expires_at.isoformat() if interaction.expires_at else None,
                'context': interaction.context
            }
            
        except Exception as e:
            logger.error("Erro ao obter interação", interaction_id=interaction_id, error=str(e))
            return None
    
    async def get_user_interactions(self, user_id: str, 
                                  include_history: bool = False) -> List[Dict[str, Any]]:
        """Obtém interações de um usuário"""
        try:
            interactions = []
            
            # Interações ativas
            for interaction in self.active_interactions.values():
                if interaction.user_id == user_id:
                    interaction_data = await self.get_interaction(interaction.id)
                    if interaction_data:
                        interactions.append(interaction_data)
            
            # Histórico se solicitado
            if include_history and user_id in self.interaction_history:
                for historical_interaction in self.interaction_history[user_id][-10:]:  # Últimas 10
                    interactions.append({
                        'id': historical_interaction.id,
                        'type': historical_interaction.type.value,
                        'title': historical_interaction.title,
                        'status': historical_interaction.status.value,
                        'created_at': historical_interaction.created_at.isoformat(),
                        'responded_at': historical_interaction.responded_at.isoformat() if historical_interaction.responded_at else None,
                        'response': historical_interaction.response
                    })
            
            return interactions
            
        except Exception as e:
            logger.error("Erro ao obter interações do usuário", user_id=user_id, error=str(e))
            return []
    
    async def cancel_interaction(self, interaction_id: str) -> Dict[str, Any]:
        """Cancela uma interação"""
        try:
            if interaction_id not in self.active_interactions:
                return {
                    'erro': 'Interação não encontrada',
                    'interaction_id': interaction_id
                }
            
            interaction = self.active_interactions[interaction_id]
            interaction.status = InteractionStatus.CANCELADA
            
            await self._move_to_history(interaction)
            
            logger.info("Interação cancelada", interaction_id=interaction_id)
            
            return {
                'interaction_id': interaction_id,
                'status': 'cancelada',
                'message': 'Interação cancelada com sucesso'
            }
            
        except Exception as e:
            logger.error("Erro ao cancelar interação", interaction_id=interaction_id, error=str(e))
            return {'erro': str(e)}
    
    async def _move_to_history(self, interaction: UserInteraction):
        """Move interação para histórico"""
        try:
            # Remove das interações ativas
            if interaction.id in self.active_interactions:
                del self.active_interactions[interaction.id]
            
            # Adiciona ao histórico
            if interaction.user_id not in self.interaction_history:
                self.interaction_history[interaction.user_id] = []
            
            self.interaction_history[interaction.user_id].append(interaction)
            
            # Mantém apenas últimas 50 interações por usuário
            if len(self.interaction_history[interaction.user_id]) > 50:
                self.interaction_history[interaction.user_id] = \
                    self.interaction_history[interaction.user_id][-50:]
            
        except Exception as e:
            logger.error("Erro ao mover interação para histórico", error=str(e))
    
    async def _cleanup_expired_interactions(self):
        """Loop de limpeza de interações expiradas"""
        while self.is_running:
            try:
                current_time = datetime.now()
                expired_interactions = []
                
                for interaction_id, interaction in self.active_interactions.items():
                    if (interaction.expires_at and 
                        current_time > interaction.expires_at and
                        interaction.status in [InteractionStatus.PENDENTE, InteractionStatus.AGUARDANDO_RESPOSTA]):
                        
                        expired_interactions.append(interaction)
                
                # Marca como expiradas
                for interaction in expired_interactions:
                    interaction.status = InteractionStatus.EXPIRADA
                    await self._move_to_history(interaction)
                    
                    logger.info("Interação expirada", interaction_id=interaction.id)
                
                # Aguarda antes da próxima verificação
                await asyncio.sleep(60)  # Verifica a cada minuto
                
            except Exception as e:
                logger.error("Erro na limpeza de interações expiradas", error=str(e))
                await asyncio.sleep(60)
    
    def _get_user_timeout(self, user_id: str) -> int:
        """Obtém timeout configurado para usuário"""
        user_prefs = self.user_preferences.get(user_id, {})
        return user_prefs.get('timeout_interacao_minutos', self.default_timeout_minutes)
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza preferências do usuário"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = self.default_user_preferences.copy()
            
            self.user_preferences[user_id].update(preferences)
            
            logger.info("Preferências de usuário atualizadas", 
                       user_id=user_id, preferences=preferences)
            
            return {
                'user_id': user_id,
                'status': 'atualizado',
                'preferences': self.user_preferences[user_id]
            }
            
        except Exception as e:
            logger.error("Erro ao atualizar preferências", user_id=user_id, error=str(e))
            return {'erro': str(e)}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema de interações"""
        try:
            active_by_type = {}
            for interaction in self.active_interactions.values():
                interaction_type = interaction.type.value
                active_by_type[interaction_type] = active_by_type.get(interaction_type, 0) + 1
            
            return {
                'interacoes_ativas': len(self.active_interactions),
                'usuarios_com_historico': len(self.interaction_history),
                'interacoes_por_tipo': active_by_type,
                'timeout_padrao_minutos': self.default_timeout_minutes,
                'sistema_ativo': self.is_running,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Erro ao obter métricas do sistema", error=str(e))
            return {'erro': str(e)}