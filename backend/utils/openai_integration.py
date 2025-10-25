"""
Serviço de integração OpenAI para o sistema de análise de notas fiscais
Fornece capacidades LLM centralizadas para todos os agentes
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import openai
from openai import AsyncOpenAI
import redis.asyncio as redis
from pydantic import BaseModel, Field

from .config import settings
from .llm_config import (
    ConfiguracoesLLM, ModeloLLM, TipoPrompt, 
    configuracoes_llm_padrao
)


# Configurar logging
logger = logging.getLogger(__name__)


class StatusResposta(str, Enum):
    """Status da resposta LLM"""
    SUCESSO = "sucesso"
    ERRO = "erro"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    FALLBACK = "fallback"


@dataclass
class EstatisticasProcessamento:
    """Estatísticas de processamento LLM"""
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    tempo_processamento: float
    modelo_usado: str
    custo_estimado: float
    tentativas: int
    cache_hit: bool


@dataclass
class RespostaLLM:
    """Resposta padronizada do LLM"""
    conteudo: str
    status: StatusResposta
    modelo_usado: str
    estatisticas: EstatisticasProcessamento
    contexto_id: str
    timestamp: datetime
    confianca: float = 0.0
    metadados: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "conteudo": self.conteudo,
            "status": self.status.value,
            "modelo_usado": self.modelo_usado,
            "estatisticas": asdict(self.estatisticas),
            "contexto_id": self.contexto_id,
            "timestamp": self.timestamp.isoformat(),
            "confianca": self.confianca,
            "metadados": self.metadados or {}
        }


class AnaliseDocumento(BaseModel):
    """Resultado da análise de documento"""
    tipo_documento: str
    contexto_empresarial: Dict[str, Any]
    insights_principais: List[str]
    anomalias_detectadas: List[str]
    score_confianca: float
    recomendacoes: List[str]


class TraducaoSQL(BaseModel):
    """Resultado da tradução para SQL"""
    consulta_sql: str
    explicacao_logica: str
    score_confianca: float
    sugestoes_otimizacao: List[str]
    problemas_potenciais: List[str]
    metricas_estimadas: Dict[str, Any]


class InsightsEmpresariais(BaseModel):
    """Insights empresariais gerados"""
    descobertas_principais: List[str]
    tendencias_identificadas: List[str]
    impacto_empresarial: Dict[str, Any]
    implicacoes_estrategicas: List[str]
    nivel_confianca: float
    dados_suporte: Dict[str, Any]


class ResultadoCategorizacao(BaseModel):
    """Resultado da categorização inteligente"""
    itens_categorizados: List[Dict[str, Any]]
    categorias_criadas: List[str]
    score_confianca: float
    justificativas: Dict[str, str]
    sugestoes_melhoria: List[str]


class GerenciadorRateLimit:
    """Gerenciador de rate limiting para OpenAI"""
    
    def __init__(self, redis_client: redis.Redis, config: ConfiguracoesLLM):
        self.redis = redis_client
        self.config = config
        self.chave_requests = "openai:rate_limit:requests"
        self.chave_tokens = "openai:rate_limit:tokens"
    
    async def verificar_limite(self, tokens_estimados: int) -> Tuple[bool, float]:
        """
        Verifica se a requisição pode ser feita dentro dos limites
        Retorna (pode_fazer_requisicao, tempo_espera)
        """
        agora = time.time()
        janela = 60  # 1 minuto
        
        # Verificar limite de requests
        requests_atuais = await self._contar_requests_janela(agora, janela)
        if requests_atuais >= self.config.rate_limiting.requests_per_minute:
            tempo_espera = await self._calcular_tempo_espera_requests(agora, janela)
            return False, tempo_espera
        
        # Verificar limite de tokens
        tokens_atuais = await self._contar_tokens_janela(agora, janela)
        if tokens_atuais + tokens_estimados > self.config.rate_limiting.tokens_per_minute:
            tempo_espera = await self._calcular_tempo_espera_tokens(agora, janela)
            return False, tempo_espera
        
        return True, 0.0
    
    async def registrar_uso(self, tokens_usados: int):
        """Registra uso de tokens e requests"""
        agora = time.time()
        
        # Registrar request
        await self.redis.zadd(
            self.chave_requests, 
            {str(agora): agora}
        )
        
        # Registrar tokens
        await self.redis.zadd(
            self.chave_tokens,
            {f"{agora}:{tokens_usados}": agora}
        )
        
        # Limpar dados antigos (mais de 1 hora)
        limite_tempo = agora - 3600
        await self.redis.zremrangebyscore(self.chave_requests, 0, limite_tempo)
        await self.redis.zremrangebyscore(self.chave_tokens, 0, limite_tempo)
    
    async def _contar_requests_janela(self, agora: float, janela: int) -> int:
        """Conta requests na janela de tempo"""
        inicio_janela = agora - janela
        return await self.redis.zcount(self.chave_requests, inicio_janela, agora)
    
    async def _contar_tokens_janela(self, agora: float, janela: int) -> int:
        """Conta tokens na janela de tempo"""
        inicio_janela = agora - janela
        registros = await self.redis.zrangebyscore(
            self.chave_tokens, inicio_janela, agora
        )
        
        total_tokens = 0
        for registro in registros:
            try:
                _, tokens_str = registro.decode().split(':', 1)
                total_tokens += int(tokens_str)
            except (ValueError, IndexError):
                continue
        
        return total_tokens
    
    async def _calcular_tempo_espera_requests(self, agora: float, janela: int) -> float:
        """Calcula tempo de espera para requests"""
        inicio_janela = agora - janela
        primeiro_request = await self.redis.zrangebyscore(
            self.chave_requests, inicio_janela, agora, start=0, num=1
        )
        
        if primeiro_request:
            primeiro_timestamp = float(primeiro_request[0].decode())
            return max(0, (primeiro_timestamp + janela) - agora)
        
        return 0.0
    
    async def _calcular_tempo_espera_tokens(self, agora: float, janela: int) -> float:
        """Calcula tempo de espera para tokens"""
        inicio_janela = agora - janela
        primeiro_registro = await self.redis.zrangebyscore(
            self.chave_tokens, inicio_janela, agora, start=0, num=1
        )
        
        if primeiro_registro:
            timestamp_str = primeiro_registro[0].decode().split(':', 1)[0]
            primeiro_timestamp = float(timestamp_str)
            return max(0, (primeiro_timestamp + janela) - agora)
        
        return 0.0


class GerenciadorCache:
    """Gerenciador de cache para respostas LLM"""
    
    def __init__(self, redis_client: redis.Redis, config: ConfiguracoesLLM):
        self.redis = redis_client
        self.config = config
        self.prefixo_cache = "openai:cache"
    
    def _gerar_chave_cache(self, prompt: str, parametros: Dict[str, Any]) -> str:
        """Gera chave única para cache baseada no prompt e parâmetros"""
        conteudo = f"{prompt}:{json.dumps(parametros, sort_keys=True)}"
        hash_conteudo = hashlib.sha256(conteudo.encode()).hexdigest()
        return f"{self.prefixo_cache}:{hash_conteudo}"
    
    async def obter_cache(self, prompt: str, parametros: Dict[str, Any]) -> Optional[RespostaLLM]:
        """Obtém resposta do cache se disponível"""
        if not self.config.cache.habilitado:
            return None
        
        chave = self._gerar_chave_cache(prompt, parametros)
        
        try:
            dados_cache = await self.redis.get(chave)
            if dados_cache:
                dados = json.loads(dados_cache.decode())
                
                # Reconstruir RespostaLLM
                estatisticas = EstatisticasProcessamento(**dados['estatisticas'])
                estatisticas.cache_hit = True
                
                return RespostaLLM(
                    conteudo=dados['conteudo'],
                    status=StatusResposta(dados['status']),
                    modelo_usado=dados['modelo_usado'],
                    estatisticas=estatisticas,
                    contexto_id=dados['contexto_id'],
                    timestamp=datetime.fromisoformat(dados['timestamp']),
                    confianca=dados.get('confianca', 0.0),
                    metadados=dados.get('metadados', {})
                )
        except Exception as e:
            logger.warning(f"Erro ao obter cache: {e}")
        
        return None
    
    async def salvar_cache(
        self, 
        prompt: str, 
        parametros: Dict[str, Any], 
        resposta: RespostaLLM,
        tipo_prompt: Optional[TipoPrompt] = None
    ):
        """Salva resposta no cache"""
        if not self.config.cache.habilitado:
            return
        
        chave = self._gerar_chave_cache(prompt, parametros)
        ttl = self.config.obter_ttl_cache(tipo_prompt) if tipo_prompt else self.config.cache.ttl_segundos
        
        try:
            dados_cache = json.dumps(resposta.to_dict())
            await self.redis.setex(chave, ttl, dados_cache)
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {e}")


class ServicoIntegracaoOpenAI:
    """Serviço principal de integração com OpenAI"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        config: Optional[ConfiguracoesLLM] = None,
        redis_url: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.config = config or configuracoes_llm_padrao
        
        # Inicializar cliente OpenAI
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Inicializar Redis para cache e rate limiting
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client = None
        
        # Gerenciadores
        self.rate_limiter = None
        self.cache_manager = None
        
        # Métricas
        self.metricas = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_custo": 0.0,
            "cache_hits": 0,
            "erros": 0
        }
    
    async def inicializar(self):
        """Inicializa conexões assíncronas"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            self.rate_limiter = GerenciadorRateLimit(self.redis_client, self.config)
            self.cache_manager = GerenciadorCache(self.redis_client, self.config)
            
            logger.info("Serviço OpenAI inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço OpenAI: {e}")
            raise
    
    async def finalizar(self):
        """Finaliza conexões"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def gerar_completion(
        self,
        prompt: str,
        contexto: Dict[str, Any],
        modelo: Optional[ModeloLLM] = None,
        tipo_prompt: Optional[TipoPrompt] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> RespostaLLM:
        """
        Gera completion usando OpenAI com gerenciamento completo
        """
        modelo_usado = modelo or self.config.modelo_padrao
        config_modelo = self.config.obter_configuracao_modelo(modelo_usado)
        
        # Parâmetros da requisição
        parametros = {
            "modelo": modelo_usado.value,
            "max_tokens": max_tokens or config_modelo.max_tokens,
            "temperature": temperature or config_modelo.temperature,
            "contexto": contexto
        }
        
        # Verificar cache primeiro
        resposta_cache = await self.cache_manager.obter_cache(prompt, parametros)
        if resposta_cache:
            self.metricas["cache_hits"] += 1
            return resposta_cache
        
        # Estimar tokens para rate limiting
        tokens_estimados = self._estimar_tokens(prompt, contexto)
        
        # Verificar rate limiting
        pode_fazer, tempo_espera = await self.rate_limiter.verificar_limite(tokens_estimados)
        if not pode_fazer:
            if tempo_espera > 0:
                await asyncio.sleep(min(tempo_espera, 60))  # Máximo 1 minuto de espera
        
        # Fazer requisição
        try:
            resposta = await self._fazer_requisicao_openai(
                prompt, contexto, config_modelo, parametros
            )
            
            # Salvar no cache
            await self.cache_manager.salvar_cache(prompt, parametros, resposta, tipo_prompt)
            
            # Registrar uso
            await self.rate_limiter.registrar_uso(resposta.estatisticas.tokens_total)
            
            # Atualizar métricas
            self._atualizar_metricas(resposta)
            
            return resposta
            
        except Exception as e:
            logger.error(f"Erro na requisição OpenAI: {e}")
            self.metricas["erros"] += 1
            
            # Tentar fallback se configurado
            if self.config.usar_fallback_automatico and modelo_usado != self.config.modelo_fallback:
                logger.info(f"Tentando fallback para {self.config.modelo_fallback}")
                return await self.gerar_completion(
                    prompt, contexto, self.config.modelo_fallback, tipo_prompt, max_tokens, temperature
                )
            
            # Retornar erro
            return RespostaLLM(
                conteudo=f"Erro na geração: {str(e)}",
                status=StatusResposta.ERRO,
                modelo_usado=modelo_usado.value,
                estatisticas=EstatisticasProcessamento(
                    tokens_prompt=0, tokens_completion=0, tokens_total=0,
                    tempo_processamento=0.0, modelo_usado=modelo_usado.value,
                    custo_estimado=0.0, tentativas=1, cache_hit=False
                ),
                contexto_id=self._gerar_contexto_id(),
                timestamp=datetime.now()
            )
    
    async def analisar_documento(
        self,
        conteudo_documento: str,
        tipo_analise: str,
        contexto: Optional[Dict[str, Any]] = None
    ) -> AnaliseDocumento:
        """Analisa documentos usando prompts especializados"""
        contexto_completo = {
            "documento": conteudo_documento,
            "tipo_analise": tipo_analise,
            "contexto_adicional": contexto or {}
        }
        
        # Usar prompt específico para análise de documentos
        prompt = self._obter_prompt_analise_documento(tipo_analise)
        
        resposta = await self.gerar_completion(
            prompt, 
            contexto_completo, 
            tipo_prompt=TipoPrompt.ANALISE_SEMANTICA_XML
        )
        
        # Processar resposta em formato estruturado
        return self._processar_resposta_analise_documento(resposta)
    
    async def traduzir_para_sql(
        self,
        consulta_natural: str,
        contexto_schema: Dict[str, Any],
        exemplos: Optional[List[str]] = None
    ) -> TraducaoSQL:
        """Converte consulta em linguagem natural para SQL"""
        contexto_completo = {
            "consulta_natural": consulta_natural,
            "schema": contexto_schema,
            "exemplos": exemplos or [],
            "contexto_brasileiro": self.config.contexto_brasileiro.model_dump()
        }
        
        prompt = self._obter_prompt_traducao_sql()
        
        resposta = await self.gerar_completion(
            prompt,
            contexto_completo,
            tipo_prompt=TipoPrompt.TRADUCAO_SQL
        )
        
        return self._processar_resposta_traducao_sql(resposta)
    
    async def gerar_insights(
        self,
        dados: Dict[str, Any],
        tipo_insight: str,
        audiencia: str = "executivo"
    ) -> InsightsEmpresariais:
        """Gera insights empresariais a partir de dados"""
        contexto_completo = {
            "dados": dados,
            "tipo_insight": tipo_insight,
            "audiencia": audiencia,
            "contexto_brasileiro": self.config.contexto_brasileiro.model_dump()
        }
        
        prompt = self._obter_prompt_geracao_insights(tipo_insight, audiencia)
        
        resposta = await self.gerar_completion(
            prompt,
            contexto_completo,
            tipo_prompt=TipoPrompt.GERACAO_RELATORIO
        )
        
        return self._processar_resposta_insights(resposta)
    
    async def categorizar_com_contexto(
        self,
        itens: List[str],
        tipo_categoria: str,
        contexto_empresarial: Dict[str, Any]
    ) -> ResultadoCategorizacao:
        """Categorização inteligente com compreensão empresarial"""
        contexto_completo = {
            "itens": itens,
            "tipo_categoria": tipo_categoria,
            "contexto_empresarial": contexto_empresarial,
            "categorias_padrao": self.config.contexto_brasileiro.categorias_produto_padrao
        }
        
        prompt = self._obter_prompt_categorizacao(tipo_categoria)
        
        resposta = await self.gerar_completion(
            prompt,
            contexto_completo,
            tipo_prompt=TipoPrompt.CATEGORIZACAO_PRODUTOS
        )
        
        return self._processar_resposta_categorizacao(resposta)
    
    def obter_metricas(self) -> Dict[str, Any]:
        """Obtém métricas de uso do serviço"""
        return {
            **self.metricas,
            "cache_hit_rate": (
                self.metricas["cache_hits"] / max(self.metricas["total_requests"], 1)
            ),
            "error_rate": (
                self.metricas["erros"] / max(self.metricas["total_requests"], 1)
            )
        }
    
    # Métodos privados de apoio
    
    def _estimar_tokens(self, prompt: str, contexto: Dict[str, Any]) -> int:
        """Estima número de tokens baseado no conteúdo"""
        conteudo_total = prompt + json.dumps(contexto, ensure_ascii=False)
        # Estimativa aproximada: 1 token ≈ 4 caracteres para português
        return len(conteudo_total) // 3
    
    def _gerar_contexto_id(self) -> str:
        """Gera ID único para contexto"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    async def _fazer_requisicao_openai(
        self,
        prompt: str,
        contexto: Dict[str, Any],
        config_modelo,
        parametros: Dict[str, Any]
    ) -> RespostaLLM:
        """Faz requisição real para OpenAI"""
        inicio = time.time()
        
        # Preparar mensagens
        mensagens = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user", 
                "content": json.dumps(contexto, ensure_ascii=False, indent=2)
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=config_modelo.modelo.value,
                messages=mensagens,
                max_tokens=parametros["max_tokens"],
                temperature=parametros["temperature"],
                top_p=config_modelo.top_p,
                frequency_penalty=config_modelo.frequency_penalty,
                presence_penalty=config_modelo.presence_penalty
            )
            
            tempo_processamento = time.time() - inicio
            
            # Extrair informações da resposta
            choice = response.choices[0]
            usage = response.usage
            
            # Calcular custo estimado (valores aproximados)
            custo_estimado = self._calcular_custo(
                config_modelo.modelo, usage.prompt_tokens, usage.completion_tokens
            )
            
            estatisticas = EstatisticasProcessamento(
                tokens_prompt=usage.prompt_tokens,
                tokens_completion=usage.completion_tokens,
                tokens_total=usage.total_tokens,
                tempo_processamento=tempo_processamento,
                modelo_usado=config_modelo.modelo.value,
                custo_estimado=custo_estimado,
                tentativas=1,
                cache_hit=False
            )
            
            return RespostaLLM(
                conteudo=choice.message.content,
                status=StatusResposta.SUCESSO,
                modelo_usado=config_modelo.modelo.value,
                estatisticas=estatisticas,
                contexto_id=self._gerar_contexto_id(),
                timestamp=datetime.now(),
                confianca=0.8,  # Score padrão, pode ser refinado
                metadados={"finish_reason": choice.finish_reason}
            )
            
        except Exception as e:
            tempo_processamento = time.time() - inicio
            raise e
    
    def _calcular_custo(self, modelo: ModeloLLM, tokens_prompt: int, tokens_completion: int) -> float:
        """Calcula custo estimado baseado no modelo e tokens"""
        # Preços aproximados em USD (podem variar)
        precos = {
            ModeloLLM.GPT_4: {"prompt": 0.03, "completion": 0.06},
            ModeloLLM.GPT_4_TURBO: {"prompt": 0.01, "completion": 0.03},
            ModeloLLM.GPT_3_5_TURBO: {"prompt": 0.0015, "completion": 0.002}
        }
        
        preco_modelo = precos.get(modelo, precos[ModeloLLM.GPT_3_5_TURBO])
        
        custo_prompt = (tokens_prompt / 1000) * preco_modelo["prompt"]
        custo_completion = (tokens_completion / 1000) * preco_modelo["completion"]
        
        return custo_prompt + custo_completion
    
    def _atualizar_metricas(self, resposta: RespostaLLM):
        """Atualiza métricas internas"""
        self.metricas["total_requests"] += 1
        self.metricas["total_tokens"] += resposta.estatisticas.tokens_total
        self.metricas["total_custo"] += resposta.estatisticas.custo_estimado
    
    # Métodos para obter prompts usando o PromptManager
    def _obter_prompt_analise_documento(self, tipo_analise: str) -> str:
        """Obtém prompt para análise de documento"""
        from .prompt_manager import gerenciador_prompts
        template = gerenciador_prompts.obter_template("xml_analise_semantica")
        return template.template if template else "Erro: Template não encontrado"
    
    def _obter_prompt_traducao_sql(self) -> str:
        """Obtém prompt para tradução SQL"""
        from .prompt_manager import gerenciador_prompts
        template = gerenciador_prompts.obter_template("traducao_sql")
        return template.template if template else "Erro: Template não encontrado"
    
    def _obter_prompt_geracao_insights(self, tipo_insight: str, audiencia: str) -> str:
        """Obtém prompt para geração de insights"""
        from .prompt_manager import gerenciador_prompts
        template = gerenciador_prompts.obter_template("relatorio_executivo")
        return template.template if template else "Erro: Template não encontrado"
    
    def _obter_prompt_categorizacao(self, tipo_categoria: str) -> str:
        """Obtém prompt para categorização"""
        from .prompt_manager import gerenciador_prompts
        template = gerenciador_prompts.obter_template("categorizacao_produtos")
        return template.template if template else "Erro: Template não encontrado"
    
    # Métodos para processar respostas (implementação básica)
    def _processar_resposta_analise_documento(self, resposta: RespostaLLM) -> AnaliseDocumento:
        """Processa resposta de análise de documento"""
        try:
            dados = json.loads(resposta.conteudo)
            return AnaliseDocumento(**dados)
        except:
            return AnaliseDocumento(
                tipo_documento="desconhecido",
                contexto_empresarial={},
                insights_principais=[resposta.conteudo],
                anomalias_detectadas=[],
                score_confianca=resposta.confianca,
                recomendacoes=[]
            )
    
    def _processar_resposta_traducao_sql(self, resposta: RespostaLLM) -> TraducaoSQL:
        """Processa resposta de tradução SQL"""
        try:
            dados = json.loads(resposta.conteudo)
            return TraducaoSQL(**dados)
        except:
            return TraducaoSQL(
                consulta_sql=resposta.conteudo,
                explicacao_logica="Tradução gerada automaticamente",
                score_confianca=resposta.confianca,
                sugestoes_otimizacao=[],
                problemas_potenciais=[],
                metricas_estimadas={}
            )
    
    def _processar_resposta_insights(self, resposta: RespostaLLM) -> InsightsEmpresariais:
        """Processa resposta de insights"""
        try:
            dados = json.loads(resposta.conteudo)
            return InsightsEmpresariais(**dados)
        except:
            return InsightsEmpresariais(
                descobertas_principais=[resposta.conteudo],
                tendencias_identificadas=[],
                impacto_empresarial={},
                implicacoes_estrategicas=[],
                nivel_confianca=resposta.confianca,
                dados_suporte={}
            )
    
    def _processar_resposta_categorizacao(self, resposta: RespostaLLM) -> ResultadoCategorizacao:
        """Processa resposta de categorização"""
        try:
            dados = json.loads(resposta.conteudo)
            return ResultadoCategorizacao(**dados)
        except:
            return ResultadoCategorizacao(
                itens_categorizados=[],
                categorias_criadas=[],
                score_confianca=resposta.confianca,
                justificativas={},
                sugestoes_melhoria=[]
            )


# Instância global do serviço (será inicializada na aplicação)
servico_openai: Optional[ServicoIntegracaoOpenAI] = None


async def obter_servico_openai() -> ServicoIntegracaoOpenAI:
    """Obtém instância do serviço OpenAI (singleton)"""
    global servico_openai
    
    if servico_openai is None:
        servico_openai = ServicoIntegracaoOpenAI()
        await servico_openai.inicializar()
    
    return servico_openai