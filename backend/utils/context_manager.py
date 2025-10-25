"""
Sistema de gerenciamento de contexto e conversação para LLM
Mantém histórico, preferências e contexto empresarial
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
from collections import deque

import redis.asyncio as redis
from pydantic import BaseModel, Field

from .config import settings
from .llm_config import ConfiguracoesLLM, configuracoes_llm_padrao

logger = logging.getLogger(__name__)


class TipoInteracao(str, Enum):
    """Tipos de interação do usuário"""
    CONSULTA_NATURAL = "consulta_natural"
    ANALISE_DOCUMENTO = "analise_documento"
    GERACAO_RELATORIO = "geracao_relatorio"
    CATEGORIZACAO = "categorizacao"
    TRADUCAO_SQL = "traducao_sql"
    FEEDBACK = "feedback"
    ESCLARECIMENTO = "esclarecimento"


class StatusSessao(str, Enum):
    """Status da sessão de conversa"""
    ATIVA = "ativa"
    PAUSADA = "pausada"
    ENCERRADA = "encerrada"
    EXPIRADA = "expirada"


@dataclass
class InteracaoUsuario:
    """Registro de uma interação do usuário"""
    id_interacao: str
    timestamp: datetime
    tipo: TipoInteracao
    entrada_usuario: str
    resposta_sistema: str
    contexto_usado: Dict[str, Any]
    metadados: Dict[str, Any]
    score_satisfacao: Optional[float] = None
    feedback_usuario: Optional[str] = None
    tempo_processamento: float = 0.0
    tokens_usados: int = 0
    custo_estimado: float = 0.0


@dataclass
class PreferenciasUsuario:
    """Preferências do usuário"""
    idioma_preferido: str = "pt-BR"
    nivel_detalhamento: str = "executivo"  # executivo, gerencial, técnico
    formato_numeros: str = "brasileiro"
    formato_datas: str = "dd/mm/yyyy"
    tipos_relatorio_preferidos: List[str] = None
    categorias_interesse: List[str] = None
    frequencia_atualizacoes: str = "diaria"
    notificacoes_ativas: bool = True
    tema_interface: str = "claro"
    
    def __post_init__(self):
        if self.tipos_relatorio_preferidos is None:
            self.tipos_relatorio_preferidos = ["executivo", "financeiro"]
        if self.categorias_interesse is None:
            self.categorias_interesse = ["fornecedores", "produtos", "custos"]


@dataclass
class ContextoEmpresarial:
    """Contexto empresarial do usuário"""
    empresa_id: str
    setor_atuacao: str
    porte_empresa: str  # micro, pequena, media, grande
    regioes_operacao: List[str]
    principais_fornecedores: List[str]
    categorias_produtos: List[str]
    sazonalidades: Dict[str, Any]
    metas_empresariais: Dict[str, Any]
    restricoes_orcamentarias: Dict[str, Any]
    compliance_requirements: List[str]
    
    def __post_init__(self):
        if not self.regioes_operacao:
            self.regioes_operacao = ["Brasil"]
        if not self.compliance_requirements:
            self.compliance_requirements = ["SPED", "NFe", "NFSe"]


class ContextoConversa(BaseModel):
    """Contexto atual da conversa"""
    sessao_id: str
    usuario_id: str
    status: StatusSessao = StatusSessao.ATIVA
    data_inicio: datetime
    data_ultima_atividade: datetime
    
    # Histórico de interações
    historico_interacoes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Contexto acumulado
    entidades_mencionadas: Dict[str, List[str]] = Field(default_factory=dict)
    topicos_discutidos: List[str] = Field(default_factory=list)
    decisoes_tomadas: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Estado da conversa
    ultimo_tipo_interacao: Optional[TipoInteracao] = None
    aguardando_esclarecimento: bool = False
    perguntas_pendentes: List[str] = Field(default_factory=list)
    
    # Métricas da sessão
    total_interacoes: int = 0
    total_tokens_usados: int = 0
    custo_total_sessao: float = 0.0
    score_satisfacao_medio: float = 0.0
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompressorContexto:
    """Compressor de contexto para otimizar uso de tokens"""
    
    def __init__(self, config: ConfiguracoesLLM):
        self.config = config
        self.max_interacoes_historico = 10
        self.max_tokens_contexto = 2000
    
    def comprimir_historico(self, historico: List[InteracaoUsuario]) -> List[Dict[str, Any]]:
        """Comprime histórico mantendo informações essenciais"""
        if len(historico) <= self.max_interacoes_historico:
            return [self._resumir_interacao(interacao) for interacao in historico]
        
        # Manter interações mais recentes e mais relevantes
        historico_ordenado = sorted(historico, key=lambda x: x.timestamp, reverse=True)
        
        # Sempre manter as 5 mais recentes
        historico_comprimido = historico_ordenado[:5]
        
        # Adicionar interações relevantes mais antigas
        historico_antigo = historico_ordenado[5:]
        interacoes_relevantes = self._selecionar_interacoes_relevantes(
            historico_antigo, 
            self.max_interacoes_historico - 5
        )
        
        historico_comprimido.extend(interacoes_relevantes)
        
        return [self._resumir_interacao(interacao) for interacao in historico_comprimido]
    
    def _resumir_interacao(self, interacao: InteracaoUsuario) -> Dict[str, Any]:
        """Resume uma interação para economizar tokens"""
        return {
            "timestamp": interacao.timestamp.isoformat(),
            "tipo": interacao.tipo.value,
            "entrada_resumida": self._resumir_texto(interacao.entrada_usuario, 100),
            "resposta_resumida": self._resumir_texto(interacao.resposta_sistema, 150),
            "entidades_chave": self._extrair_entidades_chave(interacao.contexto_usado),
            "score_satisfacao": interacao.score_satisfacao
        }
    
    def _resumir_texto(self, texto: str, max_chars: int) -> str:
        """Resume texto mantendo informações essenciais"""
        if len(texto) <= max_chars:
            return texto
        
        # Estratégia simples: manter início e fim
        inicio = texto[:max_chars//2]
        fim = texto[-(max_chars//2):]
        return f"{inicio}...{fim}"
    
    def _extrair_entidades_chave(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai entidades chave do contexto"""
        entidades = {}
        
        # Extrair informações importantes
        campos_importantes = [
            "fornecedores", "produtos", "categorias", "valores", 
            "periodos", "regioes", "tipos_documento"
        ]
        
        for campo in campos_importantes:
            if campo in contexto:
                entidades[campo] = contexto[campo]
        
        return entidades
    
    def _selecionar_interacoes_relevantes(
        self, 
        historico: List[InteracaoUsuario], 
        max_selecoes: int
    ) -> List[InteracaoUsuario]:
        """Seleciona interações mais relevantes do histórico antigo"""
        # Critérios de relevância
        def calcular_relevancia(interacao: InteracaoUsuario) -> float:
            score = 0.0
            
            # Score por satisfação do usuário
            if interacao.score_satisfacao:
                score += interacao.score_satisfacao * 0.3
            
            # Score por tipo de interação (alguns são mais importantes)
            tipos_importantes = {
                TipoInteracao.CONSULTA_NATURAL: 0.8,
                TipoInteracao.GERACAO_RELATORIO: 0.9,
                TipoInteracao.ANALISE_DOCUMENTO: 0.7,
                TipoInteracao.CATEGORIZACAO: 0.6,
                TipoInteracao.TRADUCAO_SQL: 0.7,
                TipoInteracao.FEEDBACK: 0.5
            }
            score += tipos_importantes.get(interacao.tipo, 0.4) * 0.4
            
            # Score por presença de entidades importantes
            entidades_importantes = ["fornecedores", "produtos", "valores", "categorias"]
            for entidade in entidades_importantes:
                if entidade in str(interacao.contexto_usado):
                    score += 0.1
            
            # Penalizar por idade (interações muito antigas são menos relevantes)
            dias_atras = (datetime.now() - interacao.timestamp).days
            if dias_atras > 7:
                score *= 0.8
            if dias_atras > 30:
                score *= 0.6
            
            return score
        
        # Ordenar por relevância e selecionar as melhores
        historico_com_score = [
            (interacao, calcular_relevancia(interacao)) 
            for interacao in historico
        ]
        historico_com_score.sort(key=lambda x: x[1], reverse=True)
        
        return [interacao for interacao, _ in historico_com_score[:max_selecoes]]


class GerenciadorMemoria:
    """Gerenciador de memória de longo prazo"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefixo_memoria = "llm:memoria"
        self.ttl_memoria_curto_prazo = 3600  # 1 hora
        self.ttl_memoria_medio_prazo = 86400 * 7  # 1 semana
        self.ttl_memoria_longo_prazo = 86400 * 30  # 1 mês
    
    async def salvar_memoria_curto_prazo(
        self, 
        usuario_id: str, 
        chave: str, 
        dados: Dict[str, Any]
    ):
        """Salva informação na memória de curto prazo"""
        chave_redis = f"{self.prefixo_memoria}:curto:{usuario_id}:{chave}"
        await self.redis.setex(
            chave_redis, 
            self.ttl_memoria_curto_prazo, 
            json.dumps(dados, default=str)
        )
    
    async def salvar_memoria_medio_prazo(
        self, 
        usuario_id: str, 
        chave: str, 
        dados: Dict[str, Any]
    ):
        """Salva informação na memória de médio prazo"""
        chave_redis = f"{self.prefixo_memoria}:medio:{usuario_id}:{chave}"
        await self.redis.setex(
            chave_redis, 
            self.ttl_memoria_medio_prazo, 
            json.dumps(dados, default=str)
        )
    
    async def salvar_memoria_longo_prazo(
        self, 
        usuario_id: str, 
        chave: str, 
        dados: Dict[str, Any]
    ):
        """Salva informação na memória de longo prazo"""
        chave_redis = f"{self.prefixo_memoria}:longo:{usuario_id}:{chave}"
        await self.redis.setex(
            chave_redis, 
            self.ttl_memoria_longo_prazo, 
            json.dumps(dados, default=str)
        )
    
    async def recuperar_memoria(
        self, 
        usuario_id: str, 
        chave: str, 
        tipo: str = "todos"
    ) -> Dict[str, Any]:
        """Recupera informações da memória"""
        memorias = {}
        
        tipos_busca = ["curto", "medio", "longo"] if tipo == "todos" else [tipo]
        
        for tipo_memoria in tipos_busca:
            chave_redis = f"{self.prefixo_memoria}:{tipo_memoria}:{usuario_id}:{chave}"
            dados = await self.redis.get(chave_redis)
            
            if dados:
                try:
                    memorias[tipo_memoria] = json.loads(dados.decode())
                except json.JSONDecodeError:
                    logger.warning(f"Erro ao decodificar memória: {chave_redis}")
        
        return memorias
    
    async def consolidar_memorias(self, usuario_id: str):
        """Consolida memórias movendo informações importantes para longo prazo"""
        # Buscar padrões nas memórias de curto e médio prazo
        padroes = await self._identificar_padroes_usuario(usuario_id)
        
        # Salvar padrões importantes na memória de longo prazo
        if padroes:
            await self.salvar_memoria_longo_prazo(
                usuario_id, 
                "padroes_comportamento", 
                padroes
            )
    
    async def _identificar_padroes_usuario(self, usuario_id: str) -> Dict[str, Any]:
        """Identifica padrões de comportamento do usuário"""
        # Implementação simplificada - pode ser expandida com ML
        padroes = {
            "tipos_consulta_frequentes": [],
            "horarios_uso": [],
            "categorias_interesse": [],
            "fornecedores_frequentes": [],
            "padroes_sazonais": {}
        }
        
        # Buscar dados de médio prazo para análise
        chaves_busca = [
            "interacoes_recentes", "consultas_frequentes", 
            "categorias_acessadas", "fornecedores_consultados"
        ]
        
        for chave in chaves_busca:
            memoria = await self.recuperar_memoria(usuario_id, chave, "medio")
            if memoria:
                # Analisar e extrair padrões (implementação básica)
                padroes = self._analisar_padroes_memoria(memoria, padroes)
        
        return padroes
    
    def _analisar_padroes_memoria(
        self, 
        memoria: Dict[str, Any], 
        padroes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analisa memória para extrair padrões"""
        # Implementação básica - pode ser melhorada com algoritmos de ML
        for tipo_memoria, dados in memoria.items():
            if isinstance(dados, dict):
                for chave, valor in dados.items():
                    if "consulta" in chave and isinstance(valor, list):
                        padroes["tipos_consulta_frequentes"].extend(valor)
                    elif "categoria" in chave and isinstance(valor, list):
                        padroes["categorias_interesse"].extend(valor)
                    elif "fornecedor" in chave and isinstance(valor, list):
                        padroes["fornecedores_frequentes"].extend(valor)
        
        return padroes


class GerenciadorContexto:
    """Gerenciador principal de contexto e conversação"""
    
    def __init__(
        self, 
        redis_url: Optional[str] = None,
        config: Optional[ConfiguracoesLLM] = None
    ):
        self.redis_url = redis_url or settings.REDIS_URL
        self.config = config or configuracoes_llm_padrao
        self.redis_client = None
        
        # Componentes
        self.compressor = CompressorContexto(self.config)
        self.gerenciador_memoria = None
        
        # Cache local de sessões ativas
        self.sessoes_ativas: Dict[str, ContextoConversa] = {}
        
        # Configurações
        self.max_sessoes_cache = 100
        self.ttl_sessao_inativa = 3600  # 1 hora
        self.ttl_sessao_ativa = 86400 * 7  # 1 semana
    
    async def inicializar(self):
        """Inicializa conexões e componentes"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            self.gerenciador_memoria = GerenciadorMemoria(self.redis_client)
            
            logger.info("Gerenciador de contexto inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador de contexto: {e}")
            raise
    
    async def finalizar(self):
        """Finaliza conexões"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def criar_sessao(
        self, 
        usuario_id: str,
        contexto_empresarial: Optional[ContextoEmpresarial] = None,
        preferencias: Optional[PreferenciasUsuario] = None
    ) -> str:
        """Cria nova sessão de conversa"""
        sessao_id = str(uuid.uuid4())
        agora = datetime.now()
        
        contexto = ContextoConversa(
            sessao_id=sessao_id,
            usuario_id=usuario_id,
            data_inicio=agora,
            data_ultima_atividade=agora
        )
        
        # Salvar no cache local e Redis
        self.sessoes_ativas[sessao_id] = contexto
        await self._salvar_sessao_redis(contexto)
        
        # Salvar contexto empresarial e preferências se fornecidos
        if contexto_empresarial:
            await self._salvar_contexto_empresarial(usuario_id, contexto_empresarial)
        
        if preferencias:
            await self._salvar_preferencias_usuario(usuario_id, preferencias)
        
        logger.info(f"Sessão criada: {sessao_id} para usuário {usuario_id}")
        return sessao_id
    
    async def obter_sessao(self, sessao_id: str) -> Optional[ContextoConversa]:
        """Obtém sessão de conversa"""
        # Verificar cache local primeiro
        if sessao_id in self.sessoes_ativas:
            return self.sessoes_ativas[sessao_id]
        
        # Buscar no Redis
        contexto = await self._carregar_sessao_redis(sessao_id)
        if contexto:
            # Adicionar ao cache local se há espaço
            if len(self.sessoes_ativas) < self.max_sessoes_cache:
                self.sessoes_ativas[sessao_id] = contexto
        
        return contexto
    
    async def adicionar_interacao(
        self,
        sessao_id: str,
        tipo_interacao: TipoInteracao,
        entrada_usuario: str,
        resposta_sistema: str,
        contexto_usado: Dict[str, Any],
        metadados: Optional[Dict[str, Any]] = None,
        tokens_usados: int = 0,
        custo_estimado: float = 0.0,
        tempo_processamento: float = 0.0
    ) -> bool:
        """Adiciona nova interação ao contexto"""
        try:
            contexto = await self.obter_sessao(sessao_id)
            if not contexto:
                logger.error(f"Sessão não encontrada: {sessao_id}")
                return False
            
            # Criar registro da interação
            interacao = InteracaoUsuario(
                id_interacao=str(uuid.uuid4()),
                timestamp=datetime.now(),
                tipo=tipo_interacao,
                entrada_usuario=entrada_usuario,
                resposta_sistema=resposta_sistema,
                contexto_usado=contexto_usado,
                metadados=metadados or {},
                tokens_usados=tokens_usados,
                custo_estimado=custo_estimado,
                tempo_processamento=tempo_processamento
            )
            
            # Atualizar contexto
            contexto.historico_interacoes.append(asdict(interacao))
            contexto.ultimo_tipo_interacao = tipo_interacao
            contexto.data_ultima_atividade = datetime.now()
            contexto.total_interacoes += 1
            contexto.total_tokens_usados += tokens_usados
            contexto.custo_total_sessao += custo_estimado
            
            # Extrair e atualizar entidades mencionadas
            self._atualizar_entidades_mencionadas(contexto, contexto_usado)
            
            # Atualizar tópicos discutidos
            self._atualizar_topicos_discutidos(contexto, tipo_interacao, entrada_usuario)
            
            # Salvar contexto atualizado
            await self._salvar_sessao_redis(contexto)
            
            # Salvar na memória de curto prazo
            await self.gerenciador_memoria.salvar_memoria_curto_prazo(
                contexto.usuario_id,
                f"interacao_{interacao.id_interacao}",
                asdict(interacao)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar interação: {e}")
            return False
    
    async def obter_contexto_para_llm(
        self, 
        sessao_id: str,
        incluir_historico: bool = True,
        incluir_preferencias: bool = True,
        incluir_contexto_empresarial: bool = True
    ) -> Dict[str, Any]:
        """Obtém contexto formatado para uso em LLM"""
        contexto = await self.obter_sessao(sessao_id)
        if not contexto:
            return {}
        
        contexto_llm = {
            "sessao_id": sessao_id,
            "usuario_id": contexto.usuario_id,
            "data_sessao": contexto.data_inicio.isoformat(),
            "total_interacoes": contexto.total_interacoes
        }
        
        # Incluir histórico comprimido
        if incluir_historico and contexto.historico_interacoes:
            historico_objetos = [
                InteracaoUsuario(**interacao) 
                for interacao in contexto.historico_interacoes
            ]
            contexto_llm["historico_conversa"] = self.compressor.comprimir_historico(
                historico_objetos
            )
        
        # Incluir entidades e tópicos
        contexto_llm["entidades_mencionadas"] = contexto.entidades_mencionadas
        contexto_llm["topicos_discutidos"] = contexto.topicos_discutidos
        contexto_llm["decisoes_tomadas"] = contexto.decisoes_tomadas
        
        # Incluir preferências do usuário
        if incluir_preferencias:
            preferencias = await self._carregar_preferencias_usuario(contexto.usuario_id)
            if preferencias:
                contexto_llm["preferencias_usuario"] = asdict(preferencias)
        
        # Incluir contexto empresarial
        if incluir_contexto_empresarial:
            ctx_empresarial = await self._carregar_contexto_empresarial(contexto.usuario_id)
            if ctx_empresarial:
                contexto_llm["contexto_empresarial"] = asdict(ctx_empresarial)
        
        # Incluir memórias relevantes
        memorias = await self.gerenciador_memoria.recuperar_memoria(
            contexto.usuario_id, "padroes_comportamento"
        )
        if memorias:
            contexto_llm["padroes_usuario"] = memorias
        
        return contexto_llm
    
    async def adicionar_feedback(
        self, 
        sessao_id: str, 
        interacao_id: str, 
        score_satisfacao: float,
        feedback_texto: Optional[str] = None
    ) -> bool:
        """Adiciona feedback do usuário a uma interação"""
        try:
            contexto = await self.obter_sessao(sessao_id)
            if not contexto:
                return False
            
            # Encontrar e atualizar a interação
            for interacao_dict in contexto.historico_interacoes:
                if interacao_dict.get("id_interacao") == interacao_id:
                    interacao_dict["score_satisfacao"] = score_satisfacao
                    interacao_dict["feedback_usuario"] = feedback_texto
                    break
            
            # Atualizar score médio da sessão
            scores = [
                i.get("score_satisfacao", 0) 
                for i in contexto.historico_interacoes 
                if i.get("score_satisfacao") is not None
            ]
            if scores:
                contexto.score_satisfacao_medio = sum(scores) / len(scores)
            
            # Salvar contexto atualizado
            await self._salvar_sessao_redis(contexto)
            
            # Salvar feedback na memória de médio prazo
            await self.gerenciador_memoria.salvar_memoria_medio_prazo(
                contexto.usuario_id,
                f"feedback_{interacao_id}",
                {
                    "score": score_satisfacao,
                    "feedback": feedback_texto,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar feedback: {e}")
            return False
    
    async def encerrar_sessao(self, sessao_id: str) -> bool:
        """Encerra sessão de conversa"""
        try:
            contexto = await self.obter_sessao(sessao_id)
            if not contexto:
                return False
            
            contexto.status = StatusSessao.ENCERRADA
            contexto.data_ultima_atividade = datetime.now()
            
            # Salvar no Redis com TTL menor
            await self._salvar_sessao_redis(contexto, ttl=self.ttl_sessao_inativa)
            
            # Remover do cache local
            if sessao_id in self.sessoes_ativas:
                del self.sessoes_ativas[sessao_id]
            
            # Consolidar memórias da sessão
            await self.gerenciador_memoria.consolidar_memorias(contexto.usuario_id)
            
            logger.info(f"Sessão encerrada: {sessao_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao encerrar sessão: {e}")
            return False
    
    async def limpar_sessoes_expiradas(self):
        """Remove sessões expiradas do cache"""
        agora = datetime.now()
        sessoes_para_remover = []
        
        for sessao_id, contexto in self.sessoes_ativas.items():
            tempo_inativo = agora - contexto.data_ultima_atividade
            
            if tempo_inativo.total_seconds() > self.ttl_sessao_inativa:
                sessoes_para_remover.append(sessao_id)
        
        for sessao_id in sessoes_para_remover:
            await self.encerrar_sessao(sessao_id)
    
    def obter_estatisticas_sessao(self, sessao_id: str) -> Dict[str, Any]:
        """Obtém estatísticas da sessão"""
        if sessao_id not in self.sessoes_ativas:
            return {}
        
        contexto = self.sessoes_ativas[sessao_id]
        
        return {
            "sessao_id": sessao_id,
            "usuario_id": contexto.usuario_id,
            "status": contexto.status.value,
            "duracao_sessao": (
                contexto.data_ultima_atividade - contexto.data_inicio
            ).total_seconds(),
            "total_interacoes": contexto.total_interacoes,
            "total_tokens": contexto.total_tokens_usados,
            "custo_total": contexto.custo_total_sessao,
            "score_satisfacao": contexto.score_satisfacao_medio,
            "tipos_interacao": list(set([
                i.get("tipo") for i in contexto.historico_interacoes
            ])),
            "entidades_unicas": sum(len(v) for v in contexto.entidades_mencionadas.values()),
            "topicos_discutidos": len(contexto.topicos_discutidos)
        }
    
    # Métodos privados de apoio
    
    async def _salvar_sessao_redis(
        self, 
        contexto: ContextoConversa, 
        ttl: Optional[int] = None
    ):
        """Salva sessão no Redis"""
        chave = f"sessao:{contexto.sessao_id}"
        dados = contexto.model_dump_json()
        ttl_usado = ttl or self.ttl_sessao_ativa
        
        await self.redis_client.setex(chave, ttl_usado, dados)
    
    async def _carregar_sessao_redis(self, sessao_id: str) -> Optional[ContextoConversa]:
        """Carrega sessão do Redis"""
        chave = f"sessao:{sessao_id}"
        dados = await self.redis_client.get(chave)
        
        if dados:
            try:
                return ContextoConversa.model_validate_json(dados.decode())
            except Exception as e:
                logger.error(f"Erro ao carregar sessão {sessao_id}: {e}")
        
        return None
    
    async def _salvar_contexto_empresarial(
        self, 
        usuario_id: str, 
        contexto: ContextoEmpresarial
    ):
        """Salva contexto empresarial do usuário"""
        chave = f"contexto_empresarial:{usuario_id}"
        dados = json.dumps(asdict(contexto), default=str)
        await self.redis_client.setex(chave, self.ttl_sessao_ativa * 7, dados)  # 1 semana
    
    async def _carregar_contexto_empresarial(
        self, 
        usuario_id: str
    ) -> Optional[ContextoEmpresarial]:
        """Carrega contexto empresarial do usuário"""
        chave = f"contexto_empresarial:{usuario_id}"
        dados = await self.redis_client.get(chave)
        
        if dados:
            try:
                dados_dict = json.loads(dados.decode())
                return ContextoEmpresarial(**dados_dict)
            except Exception as e:
                logger.error(f"Erro ao carregar contexto empresarial: {e}")
        
        return None
    
    async def _salvar_preferencias_usuario(
        self, 
        usuario_id: str, 
        preferencias: PreferenciasUsuario
    ):
        """Salva preferências do usuário"""
        chave = f"preferencias:{usuario_id}"
        dados = json.dumps(asdict(preferencias), default=str)
        await self.redis_client.setex(chave, self.ttl_sessao_ativa * 7, dados)  # 1 semana
    
    async def _carregar_preferencias_usuario(
        self, 
        usuario_id: str
    ) -> Optional[PreferenciasUsuario]:
        """Carrega preferências do usuário"""
        chave = f"preferencias:{usuario_id}"
        dados = await self.redis_client.get(chave)
        
        if dados:
            try:
                dados_dict = json.loads(dados.decode())
                return PreferenciasUsuario(**dados_dict)
            except Exception as e:
                logger.error(f"Erro ao carregar preferências: {e}")
        
        return None
    
    def _atualizar_entidades_mencionadas(
        self, 
        contexto: ContextoConversa, 
        contexto_usado: Dict[str, Any]
    ):
        """Atualiza entidades mencionadas no contexto"""
        entidades_importantes = [
            "fornecedores", "produtos", "categorias", "valores", 
            "periodos", "regioes", "documentos"
        ]
        
        for entidade in entidades_importantes:
            if entidade in contexto_usado:
                valor = contexto_usado[entidade]
                if isinstance(valor, list):
                    if entidade not in contexto.entidades_mencionadas:
                        contexto.entidades_mencionadas[entidade] = []
                    contexto.entidades_mencionadas[entidade].extend(valor)
                elif isinstance(valor, str) and valor:
                    if entidade not in contexto.entidades_mencionadas:
                        contexto.entidades_mencionadas[entidade] = []
                    contexto.entidades_mencionadas[entidade].append(valor)
        
        # Manter apenas valores únicos e limitar tamanho
        for entidade in contexto.entidades_mencionadas:
            contexto.entidades_mencionadas[entidade] = list(set(
                contexto.entidades_mencionadas[entidade]
            ))[:20]  # Máximo 20 itens por entidade
    
    def _atualizar_topicos_discutidos(
        self, 
        contexto: ContextoConversa, 
        tipo_interacao: TipoInteracao,
        entrada_usuario: str
    ):
        """Atualiza tópicos discutidos baseado na interação"""
        # Mapear tipos de interação para tópicos
        mapa_topicos = {
            TipoInteracao.CONSULTA_NATURAL: "consultas_gerais",
            TipoInteracao.ANALISE_DOCUMENTO: "analise_documentos",
            TipoInteracao.GERACAO_RELATORIO: "relatorios",
            TipoInteracao.CATEGORIZACAO: "categorizacao",
            TipoInteracao.TRADUCAO_SQL: "consultas_dados",
            TipoInteracao.FEEDBACK: "feedback"
        }
        
        topico = mapa_topicos.get(tipo_interacao, "outros")
        if topico not in contexto.topicos_discutidos:
            contexto.topicos_discutidos.append(topico)
        
        # Identificar tópicos específicos na entrada do usuário
        palavras_chave_topicos = {
            "fornecedor": "gestao_fornecedores",
            "produto": "gestao_produtos", 
            "custo": "analise_custos",
            "relatorio": "relatorios",
            "categoria": "categorizacao",
            "fiscal": "documentos_fiscais",
            "nfe": "notas_fiscais",
            "nfse": "notas_servico"
        }
        
        entrada_lower = entrada_usuario.lower()
        for palavra, topico_especifico in palavras_chave_topicos.items():
            if palavra in entrada_lower and topico_especifico not in contexto.topicos_discutidos:
                contexto.topicos_discutidos.append(topico_especifico)
        
        # Limitar número de tópicos
        contexto.topicos_discutidos = contexto.topicos_discutidos[-15:]


# Instância global do gerenciador
gerenciador_contexto: Optional[GerenciadorContexto] = None


async def obter_gerenciador_contexto() -> GerenciadorContexto:
    """Obtém instância do gerenciador de contexto (singleton)"""
    global gerenciador_contexto
    
    if gerenciador_contexto is None:
        gerenciador_contexto = GerenciadorContexto()
        await gerenciador_contexto.inicializar()
    
    return gerenciador_contexto