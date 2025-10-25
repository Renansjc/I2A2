"""
Serviço LLM integrado - ponto de entrada principal para capacidades LLM
Combina OpenAI Integration, Prompt Manager e Context Manager
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .openai_integration import (
    ServicoIntegracaoOpenAI, obter_servico_openai,
    AnaliseDocumento, TraducaoSQL, InsightsEmpresariais, ResultadoCategorizacao
)
from .context_manager import (
    GerenciadorContexto, obter_gerenciador_contexto,
    TipoInteracao, ContextoEmpresarial, PreferenciasUsuario
)
from .prompt_manager import gerenciador_prompts
from .llm_config import TipoPrompt, ModeloLLM, configuracoes_llm_padrao

logger = logging.getLogger(__name__)


class ServicoLLMIntegrado:
    """
    Serviço principal que integra todas as capacidades LLM
    Fornece interface unificada para todos os agentes
    """
    
    def __init__(self):
        self.servico_openai: Optional[ServicoIntegracaoOpenAI] = None
        self.gerenciador_contexto: Optional[GerenciadorContexto] = None
        self.inicializado = False
    
    async def inicializar(self):
        """Inicializa todos os componentes LLM"""
        try:
            # Inicializar serviços
            self.servico_openai = await obter_servico_openai()
            self.gerenciador_contexto = await obter_gerenciador_contexto()
            
            self.inicializado = True
            logger.info("Serviço LLM integrado inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço LLM: {e}")
            raise
    
    async def finalizar(self):
        """Finaliza todos os componentes"""
        if self.servico_openai:
            await self.servico_openai.finalizar()
        
        if self.gerenciador_contexto:
            await self.gerenciador_contexto.finalizar()
        
        self.inicializado = False
        logger.info("Serviço LLM finalizado")
    
    def _verificar_inicializacao(self):
        """Verifica se o serviço foi inicializado"""
        if not self.inicializado:
            raise RuntimeError("Serviço LLM não foi inicializado. Chame inicializar() primeiro.")
    
    # Métodos de sessão e contexto
    
    async def criar_sessao_usuario(
        self,
        usuario_id: str,
        contexto_empresarial: Optional[Dict[str, Any]] = None,
        preferencias: Optional[Dict[str, Any]] = None
    ) -> str:
        """Cria nova sessão para usuário"""
        self._verificar_inicializacao()
        
        # Converter dicionários para objetos se fornecidos
        ctx_empresarial = None
        if contexto_empresarial:
            ctx_empresarial = ContextoEmpresarial(**contexto_empresarial)
        
        prefs_usuario = None
        if preferencias:
            prefs_usuario = PreferenciasUsuario(**preferencias)
        
        return await self.gerenciador_contexto.criar_sessao(
            usuario_id, ctx_empresarial, prefs_usuario
        )
    
    async def encerrar_sessao_usuario(self, sessao_id: str) -> bool:
        """Encerra sessão do usuário"""
        self._verificar_inicializacao()
        return await self.gerenciador_contexto.encerrar_sessao(sessao_id)
    
    # Métodos principais de processamento LLM
    
    async def processar_consulta_natural(
        self,
        sessao_id: str,
        consulta: str,
        cargo_usuario: str = "Executivo",
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa consulta em linguagem natural usando Master Agent
        """
        self._verificar_inicializacao()
        
        try:
            # Obter contexto da sessão
            contexto_sessao = await self.gerenciador_contexto.obter_contexto_para_llm(sessao_id)
            
            # Preparar contexto para o LLM
            contexto_llm = {
                "consulta": consulta,
                "cargo_usuario": cargo_usuario,
                "contexto_empresarial": contexto_sessao.get("contexto_empresarial", {}),
                "dados_disponiveis": "Dados fiscais, fornecedores, produtos e relatórios",
                "historico_conversa": contexto_sessao.get("historico_conversa", [])
            }
            
            if contexto_adicional:
                contexto_llm.update(contexto_adicional)
            
            # Renderizar template
            template_renderizado, erros = gerenciador_prompts.renderizar_template(
                "master_agent_interpretacao_consulta", contexto_llm
            )
            
            if erros:
                logger.error(f"Erros no template: {erros}")
                return {"erro": "Erro ao processar template", "detalhes": erros}
            
            # Gerar resposta usando OpenAI
            resposta = await self.servico_openai.gerar_completion(
                template_renderizado,
                contexto_llm,
                tipo_prompt=TipoPrompt.INTERPRETACAO_CONSULTA
            )
            
            # Registrar interação
            await self.gerenciador_contexto.adicionar_interacao(
                sessao_id=sessao_id,
                tipo_interacao=TipoInteracao.CONSULTA_NATURAL,
                entrada_usuario=consulta,
                resposta_sistema=resposta.conteudo,
                contexto_usado=contexto_llm,
                tokens_usados=resposta.estatisticas.tokens_total,
                custo_estimado=resposta.estatisticas.custo_estimado,
                tempo_processamento=resposta.estatisticas.tempo_processamento
            )
            
            return {
                "interpretacao": resposta.conteudo,
                "status": resposta.status.value,
                "confianca": resposta.confianca,
                "modelo_usado": resposta.modelo_usado,
                "estatisticas": resposta.estatisticas.__dict__
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar consulta natural: {e}")
            return {"erro": str(e)}
    
    async def analisar_documento_fiscal(
        self,
        sessao_id: str,
        conteudo_xml: str,
        tipo_documento: str,
        info_fornecedor: Dict[str, Any],
        itens: List[Dict[str, Any]],
        valor_total: float,
        info_tributaria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analisa documento fiscal usando XML Processing Agent
        """
        self._verificar_inicializacao()
        
        try:
            # Obter contexto da sessão
            contexto_sessao = await self.gerenciador_contexto.obter_contexto_para_llm(sessao_id)
            
            # Preparar contexto para análise
            contexto_analise = {
                "tipo_documento": tipo_documento,
                "info_fornecedor": info_fornecedor,
                "itens": itens,
                "valor_total": valor_total,
                "info_tributaria": info_tributaria or {},
                "contexto_empresarial": contexto_sessao.get("contexto_empresarial", {})
            }
            
            # Usar serviço OpenAI para análise
            analise = await self.servico_openai.analisar_documento(
                conteudo_xml, "semantica", contexto_analise
            )
            
            # Registrar interação
            await self.gerenciador_contexto.adicionar_interacao(
                sessao_id=sessao_id,
                tipo_interacao=TipoInteracao.ANALISE_DOCUMENTO,
                entrada_usuario=f"Análise de {tipo_documento}",
                resposta_sistema=str(analise.insights_principais),
                contexto_usado=contexto_analise
            )
            
            return {
                "analise": analise.model_dump(),
                "status": "sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar documento: {e}")
            return {"erro": str(e)}
    
    async def categorizar_produtos_inteligente(
        self,
        sessao_id: str,
        produtos: List[str],
        contexto_empresarial: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Categoriza produtos usando AI Categorization Agent
        """
        self._verificar_inicializacao()
        
        try:
            # Obter contexto da sessão
            contexto_sessao = await self.gerenciador_contexto.obter_contexto_para_llm(sessao_id)
            
            # Usar contexto empresarial da sessão se não fornecido
            if not contexto_empresarial:
                contexto_empresarial = contexto_sessao.get("contexto_empresarial", {})
            
            # Categorizar usando OpenAI
            resultado = await self.servico_openai.categorizar_com_contexto(
                produtos, "produto", contexto_empresarial
            )
            
            # Registrar interação
            await self.gerenciador_contexto.adicionar_interacao(
                sessao_id=sessao_id,
                tipo_interacao=TipoInteracao.CATEGORIZACAO,
                entrada_usuario=f"Categorização de {len(produtos)} produtos",
                resposta_sistema=f"Produtos categorizados com {resultado.score_confianca:.2f} de confiança",
                contexto_usado={"produtos": produtos, "contexto": contexto_empresarial}
            )
            
            return {
                "categorizacao": resultado.model_dump(),
                "status": "sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro ao categorizar produtos: {e}")
            return {"erro": str(e)}
    
    async def traduzir_consulta_sql(
        self,
        sessao_id: str,
        consulta_natural: str,
        schema_banco: Dict[str, Any],
        exemplos: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Traduz consulta natural para SQL usando SQL Agent
        """
        self._verificar_inicializacao()
        
        try:
            # Obter contexto da sessão
            contexto_sessao = await self.gerenciador_contexto.obter_contexto_para_llm(sessao_id)
            
            # Traduzir usando OpenAI
            traducao = await self.servico_openai.traduzir_para_sql(
                consulta_natural, schema_banco, exemplos
            )
            
            # Registrar interação
            await self.gerenciador_contexto.adicionar_interacao(
                sessao_id=sessao_id,
                tipo_interacao=TipoInteracao.TRADUCAO_SQL,
                entrada_usuario=consulta_natural,
                resposta_sistema=traducao.consulta_sql,
                contexto_usado={"schema": schema_banco, "exemplos": exemplos or []}
            )
            
            return {
                "traducao": traducao.model_dump(),
                "status": "sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro ao traduzir consulta SQL: {e}")
            return {"erro": str(e)}
    
    async def gerar_relatorio_executivo(
        self,
        sessao_id: str,
        dados_analise: Dict[str, Any],
        publico_alvo: str = "CEO",
        periodo_analise: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera relatório executivo usando Report Agent
        """
        self._verificar_inicializacao()
        
        try:
            # Obter contexto da sessão
            contexto_sessao = await self.gerenciador_contexto.obter_contexto_para_llm(sessao_id)
            
            # Gerar insights usando OpenAI
            insights = await self.servico_openai.gerar_insights(
                dados_analise, "relatorio_executivo", publico_alvo
            )
            
            # Registrar interação
            await self.gerenciador_contexto.adicionar_interacao(
                sessao_id=sessao_id,
                tipo_interacao=TipoInteracao.GERACAO_RELATORIO,
                entrada_usuario=f"Relatório para {publico_alvo}",
                resposta_sistema=f"Relatório gerado com {len(insights.descobertas_principais)} descobertas principais",
                contexto_usado={"dados": dados_analise, "publico": publico_alvo}
            )
            
            return {
                "relatorio": insights.model_dump(),
                "status": "sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {"erro": str(e)}
    
    # Métodos de feedback e métricas
    
    async def adicionar_feedback_interacao(
        self,
        sessao_id: str,
        interacao_id: str,
        score_satisfacao: float,
        feedback_texto: Optional[str] = None
    ) -> bool:
        """Adiciona feedback do usuário"""
        self._verificar_inicializacao()
        
        return await self.gerenciador_contexto.adicionar_feedback(
            sessao_id, interacao_id, score_satisfacao, feedback_texto
        )
    
    def obter_metricas_servico(self) -> Dict[str, Any]:
        """Obtém métricas gerais do serviço"""
        self._verificar_inicializacao()
        
        metricas_openai = self.servico_openai.obter_metricas()
        
        return {
            "servico_inicializado": self.inicializado,
            "metricas_openai": metricas_openai,
            "templates_disponiveis": len(gerenciador_prompts.templates),
            "configuracao_llm": {
                "modelo_padrao": configuracoes_llm_padrao.modelo_padrao.value,
                "cache_habilitado": configuracoes_llm_padrao.cache.habilitado,
                "rate_limit_rpm": configuracoes_llm_padrao.rate_limiting.requests_per_minute
            }
        }
    
    def obter_estatisticas_sessao(self, sessao_id: str) -> Dict[str, Any]:
        """Obtém estatísticas de uma sessão"""
        self._verificar_inicializacao()
        
        return self.gerenciador_contexto.obter_estatisticas_sessao(sessao_id)
    
    # Métodos de manutenção
    
    async def limpar_cache_expirado(self):
        """Limpa cache e sessões expiradas"""
        self._verificar_inicializacao()
        
        await self.gerenciador_contexto.limpar_sessoes_expiradas()
        logger.info("Cache e sessões expiradas limpas")
    
    def validar_configuracao(self) -> Dict[str, Any]:
        """Valida configuração do serviço"""
        problemas = configuracoes_llm_padrao.validar_configuracao()
        
        return {
            "configuracao_valida": len(problemas) == 0,
            "problemas_encontrados": problemas,
            "servico_inicializado": self.inicializado
        }


# Instância global do serviço
servico_llm_integrado: Optional[ServicoLLMIntegrado] = None


async def obter_servico_llm() -> ServicoLLMIntegrado:
    """Obtém instância do serviço LLM integrado (singleton)"""
    global servico_llm_integrado
    
    if servico_llm_integrado is None:
        servico_llm_integrado = ServicoLLMIntegrado()
        await servico_llm_integrado.inicializar()
    
    return servico_llm_integrado


async def inicializar_servicos_llm():
    """Inicializa todos os serviços LLM na aplicação"""
    try:
        servico = await obter_servico_llm()
        logger.info("Todos os serviços LLM inicializados com sucesso")
        return servico
    except Exception as e:
        logger.error(f"Erro ao inicializar serviços LLM: {e}")
        raise


async def finalizar_servicos_llm():
    """Finaliza todos os serviços LLM"""
    global servico_llm_integrado
    
    if servico_llm_integrado:
        await servico_llm_integrado.finalizar()
        servico_llm_integrado = None
        logger.info("Serviços LLM finalizados")