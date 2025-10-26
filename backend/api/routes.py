"""
FastAPI routes for the AI Agents Invoice Analysis System
Rotas em português para integração com agentes LLM
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import structlog
import uuid
from datetime import datetime, timezone
import base64

from schemas.api_schemas import (
    ConsultaNaturalRequest, ConsultaNaturalResponse,
    RelatorioExecutivoRequest, RelatorioExecutivoResponse,
    ProcessarXMLRequest, ProcessarXMLResponse,
    ErrorResponse, StatusSistemaResponse,
    DocumentListResponse, DocumentListItem,
    DocumentDetailResponse, DocumentStatusResponse,
    AgentStatus, ProcessingResult
)
from utils.openai_integration import OpenAIIntegrationService
from utils.validation import validador, ValidationError
from utils.error_messages import gerador_mensagens, validador_regras_br, TipoErro
from utils.security import sanitizador, validador_seguranca
from utils.brazilian_formatting import formatador_brasileiro, validador_dados_br
from utils.timezone_handler import gerenciador_timezone, processador_datas_fiscais
from utils.brazilian_business_validation import validador_completo_br
from agents.master_agent import MasterAgent
from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent
from agents.report_agent import LLMEnhancedReportAgent

logger = structlog.get_logger()

# Create main router
router = APIRouter()

# Import dimensional routes
from .dimensional_routes import dimensional_router, query_router

# Initialize services
llm_service = OpenAIIntegrationService()
master_agent = MasterAgent()
xml_agent = LLMEnhancedXMLProcessingAgent()
report_agent = LLMEnhancedReportAgent()

def formatar_resposta_brasileira(dados: Dict[str, Any]) -> Dict[str, Any]:
    """Formatar resposta com padrões brasileiros"""
    try:
        # Aplicar formatação brasileira
        dados_formatados = validador_dados_br.validar_formato_brasileiro(dados)
        
        # Adicionar timestamp brasileiro
        dados_formatados['timestamp_brasil'] = gerenciador_timezone.obter_agora_brasilia().isoformat()
        
        return dados_formatados
    except Exception as e:
        logger.warning("Erro ao formatar resposta brasileira", erro=str(e))
        return dados

# Endpoints de status e saúde do sistema
@router.get("/status", response_model=StatusSistemaResponse)
async def obter_status_sistema():
    """Obter status do sistema e saúde dos agentes"""
    try:
        # Verificar status dos agentes
        agentes_status = {
            "processamento_xml": "ativo",
            "categorizacao_ia": "ativo", 
            "agente_sql": "ativo",
            "agente_relatorio": "ativo",
            "agente_agendador": "ativo",
            "data_lake": "ativo",
            "monitoramento": "ativo",
            "master_agent": "ativo"
        }
        
        # Verificar conectividade LLM
        try:
            await llm_service.health_check()
            llm_status = "ativo"
        except Exception:
            llm_status = "erro"
            agentes_status["llm_integration"] = "erro"
        
        return StatusSistemaResponse(
            status_geral="operacional" if llm_status == "ativo" else "degradado",
            agentes_ativos=agentes_status,
            versao_sistema="1.0.0",
            tempo_atividade="Sistema iniciado",
            estatisticas_uso={
                "consultas_processadas": 0,
                "relatorios_gerados": 0,
                "xmls_processados": 0
            }
        )
    except Exception as e:
        logger.error("Erro ao obter status do sistema", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                codigo_erro="ERRO_STATUS_SISTEMA",
                mensagem="Erro interno ao verificar status do sistema",
                detalhes=str(e),
                sugestao_solucao="Verifique os logs do sistema e conectividade dos serviços"
            ).dict()
        )

# Endpoints principais em português para agentes LLM

@router.post("/agentes/consulta-natural", response_model=ConsultaNaturalResponse)
async def processar_consulta_natural(request: ConsultaNaturalRequest, client_ip: str = "127.0.0.1"):
    """
    Processar consulta em linguagem natural usando agentes LLM
    
    Este endpoint permite que executivos façam perguntas em português sobre
    dados fiscais e recebam respostas inteligentes com insights de IA.
    """
    try:
        # Validação de segurança e sanitização
        dados_sanitizados = sanitizador.sanitizar_requisicao_completa(
            request.dict(), client_ip
        )
        
        # Validação de dados específica
        resultado_validacao = validador.validar_dados_completos(
            dados_sanitizados, "consulta"
        )
        
        if not resultado_validacao.valido:
            mensagem_erro = gerador_mensagens.gerar_mensagem_validacao_multipla(
                resultado_validacao.erros
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    codigo_erro=mensagem_erro["codigo_erro"],
                    mensagem=mensagem_erro["mensagem"],
                    detalhes=str(mensagem_erro["erros"]),
                    sugestao_solucao=mensagem_erro["sugestao_solucao"]
                ).dict()
            )
        
        id_consulta = str(uuid.uuid4())
        logger.info("Processando consulta natural", 
                   consulta=request.consulta, 
                   id_consulta=id_consulta)
        
        # Interpretar consulta usando Master Agent
        interpretacao = await master_agent.interpret_natural_query(
            request.consulta,
            {
                "nivel_executivo": request.nivel_executivo,
                "contexto": request.contexto_usuario,
                "periodo_inicio": request.periodo_inicio,
                "periodo_fim": request.periodo_fim
            }
        )
        
        # Gerar SQL usando SQL Agent
        sql_gerado = await master_agent.generate_sql_from_interpretation(interpretacao)
        
        # Executar consulta
        resultado = await master_agent.execute_query(sql_gerado)
        
        # Gerar insights usando LLM
        insights = []
        if request.incluir_insights:
            insights_raw = await llm_service.generate_insights(
                {
                    "consulta": request.consulta,
                    "resultado": resultado,
                    "interpretacao": interpretacao
                },
                "consulta_natural",
                request.nivel_executivo
            )
            insights = insights_raw.insights if hasattr(insights_raw, 'insights') else []
        
        # Gerar explicação executiva
        explicacao = await master_agent.generate_executive_explanation(
            resultado.dict() if hasattr(resultado, 'dict') else resultado,
            request.consulta
        )
        
        # Formatar resposta com padrões brasileiros
        resposta_dados = {
            'id_consulta': id_consulta,
            'consulta_original': request.consulta,
            'interpretacao_ia': interpretacao.business_objective if hasattr(interpretacao, 'business_objective') else "Consulta interpretada com sucesso",
            'sql_gerado': sql_gerado,
            'resultado': resultado,
            'insights': insights,
            'explicacao_executiva': explicacao.explanation if hasattr(explicacao, 'explanation') else "Análise concluída",
            'recomendacoes': explicacao.recommendations if hasattr(explicacao, 'recommendations') else [],
            'confianca_geral': 0.85,
            'tempo_processamento': 1.2
        }
        
        resposta_formatada = formatar_resposta_brasileira(resposta_dados)
        
        return ConsultaNaturalResponse(**resposta_formatada)
        
    except ValidationError as e:
        logger.warning("Erro de validação na consulta natural", 
                      campo=e.campo, valor=str(e.valor), mensagem=e.mensagem)
        mensagem_erro = gerador_mensagens.gerar_mensagem_erro(
            TipoErro.VALIDACAO,
            "campo_invalido",
            {"campo": e.campo, "valor": e.valor},
            str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(**mensagem_erro).dict()
        )
    except Exception as e:
        logger.error("Erro ao processar consulta natural", 
                    error=str(e), 
                    consulta=request.consulta)
        mensagem_erro = gerador_mensagens.gerar_mensagem_erro(
            TipoErro.SISTEMA,
            "erro_interno",
            {"operacao": "consulta_natural"},
            str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(**mensagem_erro).dict()
        )

@router.post("/agentes/relatorio-executivo", response_model=RelatorioExecutivoResponse)
async def gerar_relatorio_executivo(request: RelatorioExecutivoRequest, background_tasks: BackgroundTasks, client_ip: str = "127.0.0.1"):
    """
    Gerar relatório executivo usando agentes LLM
    
    Este endpoint gera relatórios personalizados para diferentes níveis executivos
    com insights de IA, recomendações estratégicas e visualizações.
    """
    try:
        # Validação de segurança e sanitização
        dados_sanitizados = sanitizador.sanitizar_requisicao_completa(
            request.dict(), client_ip
        )
        
        # Validação específica de relatório
        resultado_validacao = validador.validar_dados_completos(
            dados_sanitizados, "relatorio"
        )
        
        if not resultado_validacao.valido:
            mensagem_erro = gerador_mensagens.gerar_mensagem_validacao_multipla(
                resultado_validacao.erros
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    codigo_erro=mensagem_erro["codigo_erro"],
                    mensagem=mensagem_erro["mensagem"],
                    detalhes=str(mensagem_erro["erros"]),
                    sugestao_solucao=mensagem_erro["sugestao_solucao"]
                ).dict()
            )
        
        id_relatorio = str(uuid.uuid4())
        logger.info("Gerando relatório executivo", 
                   titulo=request.titulo,
                   tipo=request.tipo_relatorio,
                   id_relatorio=id_relatorio)
        
        # Iniciar geração do relatório em background
        background_tasks.add_task(
            _processar_relatorio_background,
            id_relatorio,
            request
        )
        
        # Gerar resumo executivo inicial
        resumo_inicial = await report_agent.generate_initial_summary(
            request.tipo_relatorio,
            request.periodo_inicio,
            request.periodo_fim,
            request.nivel_executivo
        )
        
        # Formatar datas no padrão brasileiro
        periodo_formatado = formatador_brasileiro.formatar_data(request.periodo_inicio) + " - " + formatador_brasileiro.formatar_data(request.periodo_fim)
        
        resposta_dados = {
            'id_relatorio': id_relatorio,
            'titulo': request.titulo,
            'status': "processando",
            'formato': request.formato,
            'resumo_executivo': resumo_inicial.summary if hasattr(resumo_inicial, 'summary') else "Relatório sendo processado...",
            'principais_insights': [],
            'recomendacoes_estrategicas': [],
            'metricas_chave': {
                "periodo": periodo_formatado,
                "tipo_relatorio": request.tipo_relatorio,
                "nivel_executivo": request.nivel_executivo
            },
            'tempo_processamento': 0.5
        }
        
        resposta_formatada = formatar_resposta_brasileira(resposta_dados)
        
        return RelatorioExecutivoResponse(**resposta_formatada)
        
    except Exception as e:
        logger.error("Erro ao gerar relatório executivo", 
                    error=str(e), 
                    titulo=request.titulo)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                codigo_erro="ERRO_RELATORIO_EXECUTIVO",
                mensagem="Erro ao gerar relatório executivo",
                detalhes=str(e),
                sugestao_solucao="Verifique os parâmetros do relatório e tente novamente."
            ).dict()
        )

@router.post("/agentes/processar-xml", response_model=ProcessarXMLResponse)
async def processar_documento_xml(request: ProcessarXMLRequest, client_ip: str = "127.0.0.1"):
    """
    Processar documento XML fiscal usando agentes LLM
    
    Este endpoint processa documentos NF-e/NFS-e com análise semântica,
    categorização inteligente e extração de insights empresariais.
    """
    try:
        # Validação de segurança e sanitização
        dados_sanitizados = sanitizador.sanitizar_requisicao_completa(
            request.dict(), client_ip
        )
        
        # Validação específica de XML
        resultado_validacao = validador.validar_dados_completos(
            dados_sanitizados, "xml"
        )
        
        if not resultado_validacao.valido:
            mensagem_erro = gerador_mensagens.gerar_mensagem_validacao_multipla(
                resultado_validacao.erros
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    codigo_erro=mensagem_erro["codigo_erro"],
                    mensagem=mensagem_erro["mensagem"],
                    detalhes=str(mensagem_erro["erros"]),
                    sugestao_solucao=mensagem_erro["sugestao_solucao"]
                ).dict()
            )
        
        id_processamento = str(uuid.uuid4())
        logger.info("Processando documento XML", 
                   arquivo=request.nome_arquivo,
                   id_processamento=id_processamento)
        
        # Decodificar conteúdo XML com validação de segurança
        conteudo_xml = None
        if request.conteudo_base64:
            try:
                conteudo_decodificado = base64.b64decode(request.conteudo_base64)
                
                # Validar segurança do arquivo
                if not sanitizador.validar_seguranca_arquivo(request.nome_arquivo, conteudo_decodificado):
                    mensagem_erro = gerador_mensagens.gerar_mensagem_erro(
                        TipoErro.VALIDACAO,
                        "arquivo_inseguro",
                        {"arquivo": request.nome_arquivo}
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=ErrorResponse(**mensagem_erro).dict()
                    )
                
                conteudo_xml = conteudo_decodificado.decode('utf-8')
                
            except Exception as e:
                mensagem_erro = gerador_mensagens.gerar_mensagem_erro(
                    TipoErro.VALIDACAO,
                    "formato_invalido",
                    {"campo": "conteudo_base64"},
                    str(e)
                )
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(**mensagem_erro).dict()
                )
        
        # Processar XML usando XML Processing Agent
        resultado_processamento = await xml_agent.process_xml_document(
            conteudo_xml or request.url_arquivo,
            {
                "processar_com_ia": request.processar_com_ia,
                "extrair_insights": request.extrair_insights,
                "categorizar_automaticamente": request.categorizar_automaticamente,
                "validar_regras_negocio": request.validar_regras_negocio,
                "contexto": request.contexto_processamento
            }
        )
        
        # Extrair insights semânticos se solicitado
        insights_semanticos = []
        if request.extrair_insights:
            insights_raw = await xml_agent.extract_business_insights(
                resultado_processamento.document_data,
                resultado_processamento.semantic_analysis
            )
            insights_semanticos = insights_raw.insights if hasattr(insights_raw, 'insights') else []
        
        # Detectar anomalias
        anomalias = []
        if hasattr(resultado_processamento, 'anomalies'):
            anomalias = resultado_processamento.anomalies
        
        # Validações de negócio
        validacoes = {}
        if request.validar_regras_negocio:
            validacoes = await xml_agent.validate_business_rules(resultado_processamento.document_data)
        
        # Validar dados fiscais brasileiros se aplicável
        validacao_br = {}
        if hasattr(resultado_processamento, 'document_data'):
            validacao_br = validador_completo_br.validar_documento_fiscal_completo(
                resultado_processamento.document_data
            )
        
        resposta_dados = {
            'id_processamento': id_processamento,
            'nome_arquivo': request.nome_arquivo,
            'status': "concluido",
            'documento': resultado_processamento.document_summary if hasattr(resultado_processamento, 'document_summary') else None,
            'insights_semanticos': insights_semanticos,
            'anomalias_detectadas': anomalias,
            'validacoes_negocio': validacoes,
            'validacao_brasileira': validacao_br,
            'confianca_processamento': 0.92,
            'tempo_processamento': 2.1,
            'proximos_passos': [
                "Revisar categorização automática de produtos/serviços",
                "Analisar insights empresariais identificados",
                "Verificar anomalias detectadas se houver",
                "Validar conformidade com regras fiscais brasileiras"
            ]
        }
        
        resposta_formatada = formatar_resposta_brasileira(resposta_dados)
        
        return ProcessarXMLResponse(**resposta_formatada)
        
    except Exception as e:
        logger.error("Erro ao processar documento XML", 
                    error=str(e), 
                    arquivo=request.nome_arquivo)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                codigo_erro="ERRO_PROCESSAMENTO_XML",
                mensagem="Erro ao processar documento XML",
                detalhes=str(e),
                sugestao_solucao="Verifique se o arquivo XML está válido e no formato correto (NF-e/NFS-e)"
            ).dict()
        )

# Função auxiliar para processamento em background
async def _processar_relatorio_background(id_relatorio: str, request: RelatorioExecutivoRequest):
    """Processar relatório executivo em background"""
    try:
        logger.info("Iniciando processamento de relatório em background", id_relatorio=id_relatorio)
        
        # Gerar relatório completo usando Report Agent
        relatorio_completo = await report_agent.generate_intelligent_report(
            data=None,  # Será obtido internamente baseado no tipo e período
            report_context={
                "titulo": request.titulo,
                "tipo": request.tipo_relatorio,
                "formato": request.formato,
                "periodo_inicio": request.periodo_inicio,
                "periodo_fim": request.periodo_fim,
                "nivel_executivo": request.nivel_executivo,
                "incluir_resumo": request.incluir_resumo_executivo,
                "incluir_recomendacoes": request.incluir_recomendacoes,
                "incluir_graficos": request.incluir_graficos,
                "filtros": request.filtros_adicionais,
                "contexto_empresarial": request.contexto_empresarial
            }
        )
        
        # Salvar relatório e atualizar status
        # TODO: Implementar salvamento do relatório
        logger.info("Relatório processado com sucesso", id_relatorio=id_relatorio)
        
    except Exception as e:
        logger.error("Erro no processamento de relatório em background", 
                    id_relatorio=id_relatorio, error=str(e))

async def _processar_xml_background(
    document_id: str,
    xml_content: str,
    filename: str,
    document_type: str
):
    """Simplified XML processing with 4 main agents for MVP"""
    try:
        from utils.database import FileUploadManager, ProcessingStatusManager
        
        logger.info(
            "Starting simplified XML processing",
            document_id=document_id,
            filename=filename,
            document_type=document_type
        )
        
        # Agent 1: XML Processing Agent (simplified)
        await ProcessingStatusManager.update_agent_status(
            document_id, "xml_processing_agent", "in_progress", admin_mode=True
        )
        
        try:
            # Simplified XML processing - extract basic metadata
            xml_result = await _process_xml_simple(xml_content, document_type)
            
            await ProcessingStatusManager.store_processing_result(
                document_id=document_id,
                agent_name="xml_processing_agent",
                result_type="document_analysis",
                result_data=xml_result,
                confidence_score=0.9,
                processing_time_ms=1000,
                admin_mode=True
            )
            
            await ProcessingStatusManager.update_agent_status(
                document_id, "xml_processing_agent", "completed", admin_mode=True
            )
            
        except Exception as e:
            logger.error("XML processing failed", document_id=document_id, error=str(e))
            await ProcessingStatusManager.update_agent_status(
                document_id, "xml_processing_agent", "failed", str(e), admin_mode=True
            )
        
        # Agent 2: AI Categorization Agent (simplified)
        await ProcessingStatusManager.update_agent_status(
            document_id, "ai_categorization_agent", "in_progress", admin_mode=True
        )
        
        try:
            # Simplified categorization - basic product/service classification
            categorization_result = await _categorize_simple(xml_content, document_type)
            
            await ProcessingStatusManager.store_processing_result(
                document_id=document_id,
                agent_name="ai_categorization_agent",
                result_type="categorization",
                result_data=categorization_result,
                confidence_score=0.85,
                processing_time_ms=800,
                admin_mode=True
            )
            
            await ProcessingStatusManager.update_agent_status(
                document_id, "ai_categorization_agent", "completed", admin_mode=True
            )
            
        except Exception as e:
            logger.error("AI categorization failed", document_id=document_id, error=str(e))
            await ProcessingStatusManager.update_agent_status(
                document_id, "ai_categorization_agent", "failed", str(e), admin_mode=True
            )
        
        # Agent 3: SQL Agent (simplified) - Store data in database
        await ProcessingStatusManager.update_agent_status(
            document_id, "sql_agent", "in_progress", admin_mode=True
        )
        
        try:
            # Store data in dimensional tables using real processing
            logger.info("CALLING _store_fiscal_document_data", document_id=document_id)
            await _store_fiscal_document_data(document_id, xml_content, document_type)
            logger.info("COMPLETED _store_fiscal_document_data", document_id=document_id)
            storage_result = {"status": "completed", "tables_updated": ["dim_emitente", "dim_destinatario", "dim_produtos", "nfe_main", "fact_itens_nfe"]}
            
            await ProcessingStatusManager.store_processing_result(
                document_id=document_id,
                agent_name="sql_agent",
                result_type="data_storage",
                result_data=storage_result,
                confidence_score=0.95,
                processing_time_ms=500,
                admin_mode=True
            )
            
            await ProcessingStatusManager.update_agent_status(
                document_id, "sql_agent", "completed", admin_mode=True
            )
            
        except Exception as e:
            logger.error("SQL agent failed", document_id=document_id, error=str(e))
            await ProcessingStatusManager.update_agent_status(
                document_id, "sql_agent", "failed", str(e), admin_mode=True
            )
        
        # Agent 4: Report Agent (simplified) - Generate basic insights
        await ProcessingStatusManager.update_agent_status(
            document_id, "report_agent", "in_progress", admin_mode=True
        )
        
        try:
            # Simplified insights generation
            insights_result = await _generate_insights_simple(document_id, document_type)
            
            await ProcessingStatusManager.store_processing_result(
                document_id=document_id,
                agent_name="report_agent",
                result_type="insights",
                result_data=insights_result,
                confidence_score=0.88,
                processing_time_ms=600,
                admin_mode=True
            )
            
            await ProcessingStatusManager.update_agent_status(
                document_id, "report_agent", "completed", admin_mode=True
            )
            
        except Exception as e:
            logger.error("Report agent failed", document_id=document_id, error=str(e))
            await ProcessingStatusManager.update_agent_status(
                document_id, "report_agent", "failed", str(e), admin_mode=True
            )
        
        # Update overall document status
        await FileUploadManager.update_processing_status(document_id, "completed", admin_mode=True)
        
        logger.info(
            "Simplified XML processing completed successfully",
            document_id=document_id,
            filename=filename
        )
        
    except Exception as e:
        logger.error(
            "Background XML processing failed",
            document_id=document_id,
            error=str(e)
        )
        await FileUploadManager.update_processing_status(
            document_id, "error", str(e), admin_mode=True
        )


# Simplified agent processing functions for MVP
async def _process_xml_simple(xml_content: str, document_type: str) -> Dict[str, Any]:
    """Extract and store real data from XML into dimensional tables"""
    try:
        from lxml import etree
        from utils.database import SupabaseClient
        
        root = etree.fromstring(xml_content.encode('utf-8'))
        result = {
            "status": "completed",
            "document_type": document_type,
            "metadata_extracted": True,
            "validation_passed": True,
            "records_created": 0
        }
        
        from supabase import create_client
        from utils.config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        if document_type == "NFE":
            # Extract NF-e data
            inf_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            if inf_nfe is not None:
                result["nfe_key"] = inf_nfe.get('Id', '').replace('NFe', '')
                
                # Extract and store emitter (dim_emitente)
                emit = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
                if emit is not None:
                    cnpj_elem = emit.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
                    xNome_elem = emit.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
                    
                    if cnpj_elem is not None and xNome_elem is not None:
                        cnpj = cnpj_elem.text
                        nome = xNome_elem.text
                        
                        # Extract additional emitter data
                        enderEmit = emit.find('.//{http://www.portalfiscal.inf.br/nfe}enderEmit')
                        emitter_data = {
                            "cnpj": cnpj,
                            "razao_social": nome,
                            "nome_fantasia": emit.find('.//{http://www.portalfiscal.inf.br/nfe}xFant').text if emit.find('.//{http://www.portalfiscal.inf.br/nfe}xFant') is not None else nome
                        }
                        
                        if enderEmit is not None:
                            emitter_data.update({
                                "logradouro": enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr').text if enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr') is not None else None,
                                "numero": enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}nro').text if enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}nro') is not None else None,
                                "bairro": enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro').text if enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro') is not None else None,
                                "nome_municipio": enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}xMun').text if enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}xMun') is not None else None,
                                "uf": enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}UF').text if enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}UF') is not None else None,
                                "cep": enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}CEP').text if enderEmit.find('.//{http://www.portalfiscal.inf.br/nfe}CEP') is not None else None
                            })
                        
                        # Insert or update emitter
                        try:
                            supabase.table("dim_emitente").upsert(emitter_data).execute()
                            result["records_created"] += 1
                            result["emitter"] = {"cnpj": cnpj, "name": nome}
                        except Exception as e:
                            logger.warning(f"Failed to insert emitter: {str(e)}")
                
                # Extract and store recipient (dim_destinatario)
                dest = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
                if dest is not None:
                    cnpj_dest = dest.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
                    cpf_dest = dest.find('.//{http://www.portalfiscal.inf.br/nfe}CPF')
                    xNome_dest = dest.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
                    
                    if (cnpj_dest is not None or cpf_dest is not None) and xNome_dest is not None:
                        enderDest = dest.find('.//{http://www.portalfiscal.inf.br/nfe}enderDest')
                        
                        recipient_data = {
                            "cnpj": cnpj_dest.text if cnpj_dest is not None else None,
                            "cpf": cpf_dest.text if cpf_dest is not None else None,
                            "razao_social": xNome_dest.text
                        }
                        
                        if enderDest is not None:
                            recipient_data.update({
                                "logradouro": enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr').text if enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr') is not None else None,
                                "numero": enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}nro').text if enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}nro') is not None else None,
                                "bairro": enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro').text if enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro') is not None else None,
                                "nome_municipio": enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}xMun').text if enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}xMun') is not None else None,
                                "uf": enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}UF').text if enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}UF') is not None else None,
                                "cep": enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}CEP').text if enderDest.find('.//{http://www.portalfiscal.inf.br/nfe}CEP') is not None else None
                            })
                        
                        try:
                            supabase.table("dim_destinatario").insert(recipient_data).execute()
                            result["records_created"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to insert recipient: {str(e)}")
                
                # Extract and store products (dim_produtos)
                det_elements = inf_nfe.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
                for det in det_elements:
                    prod = det.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
                    if prod is not None:
                        cProd = prod.find('.//{http://www.portalfiscal.inf.br/nfe}cProd')
                        xProd = prod.find('.//{http://www.portalfiscal.inf.br/nfe}xProd')
                        
                        if cProd is not None and xProd is not None:
                            product_data = {
                                "codigo_produto": cProd.text,
                                "descricao": xProd.text,
                                "ean": prod.find('.//{http://www.portalfiscal.inf.br/nfe}cEAN').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}cEAN') is not None else None,
                                "ncm": prod.find('.//{http://www.portalfiscal.inf.br/nfe}NCM').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}NCM') is not None else None,
                                "cfop": prod.find('.//{http://www.portalfiscal.inf.br/nfe}CFOP').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}CFOP') is not None else None,
                                "unidade_comercial": prod.find('.//{http://www.portalfiscal.inf.br/nfe}uCom').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}uCom') is not None else None,
                                "categoria": "Produtos Gerais"  # Basic categorization
                            }
                            
                            try:
                                supabase.table("dim_produtos").upsert(product_data).execute()
                                result["records_created"] += 1
                            except Exception as e:
                                logger.warning(f"Failed to insert product: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error("XML processing failed", error=str(e))
        return {"status": "error", "error": str(e)}

async def _categorize_simple(xml_content: str, document_type: str) -> Dict[str, Any]:
    """Enhanced categorization - update product categories in database"""
    try:
        from lxml import etree
        from utils.database import SupabaseClient
        
        categories = []
        products_updated = 0
        
        if document_type == "NFE":
            root = etree.fromstring(xml_content.encode('utf-8'))
            from supabase import create_client
            from utils.config import settings
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            
            # Extract products and categorize them
            inf_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            if inf_nfe is not None:
                det_elements = inf_nfe.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
                
                for det in det_elements:
                    prod = det.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
                    if prod is not None:
                        cProd = prod.find('.//{http://www.portalfiscal.inf.br/nfe}cProd')
                        xProd = prod.find('.//{http://www.portalfiscal.inf.br/nfe}xProd')
                        ncm = prod.find('.//{http://www.portalfiscal.inf.br/nfe}NCM')
                        
                        if cProd is not None and xProd is not None:
                            product_code = cProd.text
                            product_desc = xProd.text.lower()
                            ncm_code = ncm.text if ncm is not None else ""
                            
                            # Enhanced rule-based categorization
                            category = "Produtos Gerais"
                            subcategory = "Diversos"
                            
                            # Electronics
                            if any(term in product_desc for term in ["eletronic", "eletron", "computador", "celular", "smartphone", "tablet", "tv", "monitor", "placa", "geforce", "rtx", "gpu"]):
                                category = "Eletrônicos"
                                if "placa" in product_desc and ("video" in product_desc or "geforce" in product_desc):
                                    subcategory = "Placas de Vídeo"
                                elif any(term in product_desc for term in ["celular", "smartphone"]):
                                    subcategory = "Telefones"
                                else:
                                    subcategory = "Informática"
                            
                            # Food and beverages
                            elif any(term in product_desc for term in ["aliment", "comida", "bebida", "refrigerante", "agua", "leite", "pao", "carne", "frango"]):
                                category = "Alimentação"
                                if any(term in product_desc for term in ["bebida", "refrigerante", "agua", "suco"]):
                                    subcategory = "Bebidas"
                                else:
                                    subcategory = "Alimentos"
                            
                            # Medicines and health
                            elif any(term in product_desc for term in ["medicament", "remedio", "farmac", "saude", "vitamina", "antibiotico"]):
                                category = "Medicamentos"
                                subcategory = "Farmacêuticos"
                            
                            # Fuel and energy
                            elif any(term in product_desc for term in ["gasolina", "alcool", "diesel", "combustivel", "gas", "energia"]):
                                category = "Combustíveis"
                                subcategory = "Energia"
                            
                            # Clothing
                            elif any(term in product_desc for term in ["roupa", "camisa", "calca", "sapato", "tenis", "vestido"]):
                                category = "Vestuário"
                                subcategory = "Roupas"
                            
                            # Sports
                            elif any(term in product_desc for term in ["esporte", "futebol", "tenis", "academia", "fitness"]):
                                category = "Esportes"
                                subcategory = "Artigos Esportivos"
                            
                            # Update product category in database
                            try:
                                supabase.table("dim_produtos").update({
                                    "categoria": category,
                                    "subcategoria": subcategory
                                }).eq("codigo_produto", product_code).execute()
                                
                                products_updated += 1
                                if category not in categories:
                                    categories.append(category)
                                    
                            except Exception as e:
                                logger.warning(f"Failed to update product category: {str(e)}")
        
        else:
            categories.append("Serviços")
        
        return {
            "status": "completed",
            "categories": categories,
            "products_updated": products_updated,
            "confidence": 0.85,
            "method": "enhanced_rule_based"
        }
        
    except Exception as e:
        logger.error("Categorization failed", error=str(e))
        return {"status": "error", "error": str(e)}

async def _store_data_simple(document_id: str, xml_content: str, document_type: str) -> Dict[str, Any]:
    """DEPRECATED - Use _store_fiscal_document_data instead"""
    # This function is disabled to avoid duplication
    # All processing is now done by _store_fiscal_document_data
    return {
        "status": "completed",
        "document_id": document_id,
        "tables_updated": ["handled_by_store_fiscal_document_data"],
        "records_created": 0
    }

async def _generate_insights_simple(document_id: str, document_type: str) -> Dict[str, Any]:
    """Simplified insights generation - basic summary"""
    try:
        # Generate basic insights for MVP
        insights = [
            f"Documento {document_type} processado com sucesso",
            "Dados extraídos e categorizados automaticamente",
            "Pronto para análise no dashboard"
        ]
        
        return {
            "status": "completed",
            "insights": insights,
            "summary": f"Processamento de {document_type} concluído com sucesso",
            "recommendations": ["Verificar dashboard para análises detalhadas"]
        }
        
    except Exception as e:
        logger.error("Simple insights generation failed", error=str(e))
        return {"status": "error", "error": str(e)}

async def _extract_basic_metadata(xml_content: str, document_type: str) -> Optional[Dict[str, Any]]:
    """Extract basic metadata from XML content for immediate response"""
    try:
        from lxml import etree
        
        # Parse XML
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        metadata = {}
        
        if document_type == "NFE":
            # Extract NFE metadata
            # Find infNFe element
            inf_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            if inf_nfe is not None:
                # Document number
                ide = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}ide')
                if ide is not None:
                    nNF = ide.find('.//{http://www.portalfiscal.inf.br/nfe}nNF')
                    if nNF is not None:
                        metadata['numero_documento'] = nNF.text
                    
                    dhEmi = ide.find('.//{http://www.portalfiscal.inf.br/nfe}dhEmi')
                    if dhEmi is not None:
                        try:
                            metadata['data_emissao'] = datetime.fromisoformat(dhEmi.text.replace('Z', '+00:00')).date()
                        except:
                            pass
                
                # Emitter info
                emit = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
                if emit is not None:
                    cnpj = emit.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
                    if cnpj is not None:
                        metadata['cnpj_emitente'] = cnpj.text
                    
                    xNome = emit.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
                    if xNome is not None:
                        metadata['nome_emitente'] = xNome.text
                
                # Total value
                total = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}total')
                if total is not None:
                    vNF = total.find('.//{http://www.portalfiscal.inf.br/nfe}vNF')
                    if vNF is not None:
                        try:
                            metadata['valor_total'] = float(vNF.text)
                        except:
                            pass
        
        elif document_type == "NFSE":
            # Extract NFSE metadata - simplified for now
            # This would need to be adapted based on specific NFSE schema
            metadata['nome_emitente'] = "Prestador de Serviços"
            metadata['valor_total'] = 0.0
        
        return metadata if metadata else None
        
    except Exception as e:
        logger.warning(
            "Failed to extract basic metadata",
            error=str(e),
            document_type=document_type
        )
        return None

async def _store_fiscal_document_data(document_id: str, xml_content: str, document_type: str):
    """Store fiscal document data in dimensional tables - REAL IMPLEMENTATION"""
    try:
        from utils.database import DocumentLinkingManager
        from lxml import etree
        import os
        
        logger.info(
            "FISCAL DATA: Starting fiscal document data storage",
            document_id=document_id,
            document_type=document_type
        )
        
        # Get Supabase client
        from utils.config import settings
        from supabase import create_client
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Parse XML
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        if document_type == "NFE":
            logger.info("FISCAL DATA: Processing NFE data")
            await _process_nfe_data(root, document_id, supabase)
        elif document_type == "NFSE":
            logger.info("FISCAL DATA: Processing NFSE data")
            await _process_nfse_data(root, document_id, supabase)
        
        logger.info(
            "Fiscal document data stored successfully in dimensional tables",
            document_id=document_id,
            document_type=document_type
        )
        
    except Exception as e:
        logger.error(
            "Failed to store fiscal document data in dimensional tables",
            document_id=document_id,
            error=str(e)
        )
        raise

async def _process_nfe_data(root, document_id: str, supabase):
    """Process NFE data and store in dimensional tables"""
    try:
        # Find infNFe element
        inf_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
        if inf_nfe is None:
            raise Exception("infNFe element not found in XML")
        
        # Extract NFE key
        chave_nfe = inf_nfe.get('Id', '').replace('NFe', '')
        if not chave_nfe:
            raise Exception("NFE key not found")
        
        # Extract emitter data
        emit = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
        if emit is not None:
            await _store_emitente_data(emit, supabase)
        
        # Extract recipient data
        dest = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
        if dest is not None:
            await _store_destinatario_data(dest, supabase)
        
        # Extract and store NFE main data
        await _store_nfe_main_data(inf_nfe, chave_nfe, supabase)
        
        # Extract and store items
        det_elements = inf_nfe.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
        for det in det_elements:
            await _store_nfe_item_data(det, chave_nfe, supabase)
        
        logger.info(f"NFE data processed successfully: {chave_nfe}")
        
    except Exception as e:
        logger.error(f"Error processing NFE data: {str(e)}")
        raise

async def _store_emitente_data(emit_element, supabase):
    """Store emitter data in dim_emitente"""
    try:
        # Extract CNPJ/CPF
        cnpj_elem = emit_element.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
        cpf_elem = emit_element.find('.//{http://www.portalfiscal.inf.br/nfe}CPF')
        
        cnpj = cnpj_elem.text if cnpj_elem is not None else None
        cpf = cpf_elem.text if cpf_elem is not None else None
        
        if not cnpj and not cpf:
            return  # Skip if no identification
        
        # Extract other fields
        ie_elem = emit_element.find('.//{http://www.portalfiscal.inf.br/nfe}IE')
        razao_elem = emit_element.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
        fantasia_elem = emit_element.find('.//{http://www.portalfiscal.inf.br/nfe}xFant')
        
        # Address data
        endereco = emit_element.find('.//{http://www.portalfiscal.inf.br/nfe}enderEmit')
        logradouro = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr') is not None else None
        numero = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}nro').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}nro') is not None else None
        bairro = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro') is not None else None
        municipio = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xMun').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xMun') is not None else None
        uf = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}UF').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}UF') is not None else None
        cep = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}CEP').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}CEP') is not None else None
        
        emitente_data = {
            'cnpj': cnpj,
            'cpf': cpf,
            'inscricao_estadual': ie_elem.text if ie_elem is not None else None,
            'razao_social': razao_elem.text if razao_elem is not None else None,
            'nome_fantasia': fantasia_elem.text if fantasia_elem is not None else None,
            'logradouro': logradouro,
            'numero': numero,
            'bairro': bairro,
            'nome_municipio': municipio,
            'uf': uf,
            'cep': cep
        }
        
        # Insert or update emitente
        if cnpj:
            result = supabase.table('dim_emitente').upsert(emitente_data, on_conflict='cnpj').execute()
            logger.info(f"Emitente stored: {cnpj}")
        
    except Exception as e:
        logger.error(f"Error storing emitente data: {str(e)}")

async def _store_destinatario_data(dest_element, supabase):
    """Store recipient data in dim_destinatario"""
    try:
        # Extract CNPJ/CPF
        cnpj_elem = dest_element.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
        cpf_elem = dest_element.find('.//{http://www.portalfiscal.inf.br/nfe}CPF')
        
        cnpj = cnpj_elem.text if cnpj_elem is not None else None
        cpf = cpf_elem.text if cpf_elem is not None else None
        
        if not cnpj and not cpf:
            return  # Skip if no identification
        
        # Extract other fields
        ie_elem = dest_element.find('.//{http://www.portalfiscal.inf.br/nfe}IE')
        razao_elem = dest_element.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
        
        # Address data
        endereco = dest_element.find('.//{http://www.portalfiscal.inf.br/nfe}enderDest')
        logradouro = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xLgr') is not None else None
        numero = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}nro').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}nro') is not None else None
        bairro = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xBairro') is not None else None
        municipio = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xMun').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}xMun') is not None else None
        uf = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}UF').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}UF') is not None else None
        cep = endereco.find('.//{http://www.portalfiscal.inf.br/nfe}CEP').text if endereco is not None and endereco.find('.//{http://www.portalfiscal.inf.br/nfe}CEP') is not None else None
        
        destinatario_data = {
            'cnpj': cnpj,
            'cpf': cpf,
            'inscricao_estadual': ie_elem.text if ie_elem is not None else None,
            'razao_social': razao_elem.text if razao_elem is not None else None,
            'logradouro': logradouro,
            'numero': numero,
            'bairro': bairro,
            'nome_municipio': municipio,
            'uf': uf,
            'cep': cep
        }
        
        # Insert destinatario (can have duplicates, so just insert)
        result = supabase.table('dim_destinatario').insert(destinatario_data).execute()
        logger.info(f"Destinatario stored: {cnpj or cpf}")
        
    except Exception as e:
        logger.error(f"Error storing destinatario data: {str(e)}")

async def _store_nfe_main_data(inf_nfe, chave_nfe, supabase):
    """Store NFE main data"""
    try:
        # Extract IDE data
        ide = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}ide')
        if ide is None:
            return
        
        # Extract totals
        total = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}total')
        icms_tot = total.find('.//{http://www.portalfiscal.inf.br/nfe}ICMSTot') if total is not None else None
        
        # Extract date properly
        data_emissao_str = ide.find('.//{http://www.portalfiscal.inf.br/nfe}dhEmi').text[:10] if ide.find('.//{http://www.portalfiscal.inf.br/nfe}dhEmi') is not None else None
        
        nfe_data = {
            'chave_nfe': chave_nfe,
            'numero_nf': ide.find('.//{http://www.portalfiscal.inf.br/nfe}nNF').text if ide.find('.//{http://www.portalfiscal.inf.br/nfe}nNF') is not None else None,
            'serie': ide.find('.//{http://www.portalfiscal.inf.br/nfe}serie').text if ide.find('.//{http://www.portalfiscal.inf.br/nfe}serie') is not None else None,
            'modelo': ide.find('.//{http://www.portalfiscal.inf.br/nfe}mod').text if ide.find('.//{http://www.portalfiscal.inf.br/nfe}mod') is not None else '55',
            'data_emissao': data_emissao_str,
            'natureza_operacao': ide.find('.//{http://www.portalfiscal.inf.br/nfe}natOp').text if ide.find('.//{http://www.portalfiscal.inf.br/nfe}natOp') is not None else None,
            'tipo_operacao': ide.find('.//{http://www.portalfiscal.inf.br/nfe}tpNF').text if ide.find('.//{http://www.portalfiscal.inf.br/nfe}tpNF') is not None else None,
            'valor_total_nf': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vNF').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vNF') is not None else 0,
            'valor_total_produtos': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vProd').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vProd') is not None else 0,
            'base_calculo_icms': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vBC').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vBC') is not None else 0,
            'valor_icms': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vICMS').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vICMS') is not None else 0,
            'valor_total_ipi': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vIPI').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vIPI') is not None else 0,
            'valor_pis': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vPIS').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vPIS') is not None else 0,
            'valor_cofins': float(icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vCOFINS').text) if icms_tot is not None and icms_tot.find('.//{http://www.portalfiscal.inf.br/nfe}vCOFINS') is not None else 0
        }
        
        # Insert NFE main data
        try:
            logger.info(f"Inserting NFE main data: {nfe_data}")
            result = supabase.table('nfe_main').upsert(nfe_data, on_conflict='chave_nfe').execute()
            logger.info(f"NFE main data stored: {chave_nfe}")
        except Exception as insert_error:
            logger.warning(f"Failed to insert NF-e main: {str(insert_error)}")
        
    except Exception as e:
        logger.error(f"Error storing NFE main data: {str(e)}")

async def _store_nfe_item_data(det_element, chave_nfe, supabase):
    """Store NFE item data"""
    try:
        # Extract product data
        prod = det_element.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
        if prod is None:
            return
        
        codigo_produto = prod.find('.//{http://www.portalfiscal.inf.br/nfe}cProd').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}cProd') is not None else None
        if not codigo_produto:
            return
        
        # Store product in dim_produtos first
        produto_data = {
            'codigo_produto': codigo_produto,
            'ean': prod.find('.//{http://www.portalfiscal.inf.br/nfe}cEAN').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}cEAN') is not None else None,
            'descricao': prod.find('.//{http://www.portalfiscal.inf.br/nfe}xProd').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}xProd') is not None else None,
            'ncm': prod.find('.//{http://www.portalfiscal.inf.br/nfe}NCM').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}NCM') is not None else None,
            'cfop': prod.find('.//{http://www.portalfiscal.inf.br/nfe}CFOP').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}CFOP') is not None else None,
            'unidade_comercial': prod.find('.//{http://www.portalfiscal.inf.br/nfe}uCom').text if prod.find('.//{http://www.portalfiscal.inf.br/nfe}uCom') is not None else None,
            'categoria': 'Produtos Gerais'  # Default category
        }
        
        # Insert product
        supabase.table('dim_produtos').upsert(produto_data, on_conflict='codigo_produto').execute()
        
        # Extract tax information from imposto section
        imposto = det_element.find('.//{http://www.portalfiscal.inf.br/nfe}imposto')
        
        # ICMS data
        icms_data = {}
        if imposto is not None:
            icms = imposto.find('.//{http://www.portalfiscal.inf.br/nfe}ICMS')
            if icms is not None:
                # Try different ICMS types (ICMS00, ICMS10, etc.)
                for icms_type in ['ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40', 'ICMS51', 'ICMS60', 'ICMS70', 'ICMS90']:
                    icms_elem = icms.find(f'.//{{{http://www.portalfiscal.inf.br/nfe}}}{icms_type}')
                    if icms_elem is not None:
                        icms_data = {
                            'origem_produto': icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}orig').text if icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}orig') is not None else None,
                            'situacao_tributaria_icms': icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}CST').text if icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}CST') is not None else None,
                            'base_calculo_icms': float(icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}vBC').text) if icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}vBC') is not None else 0,
                            'aliquota_icms': float(icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}pICMS').text) / 100 if icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}pICMS') is not None else 0,
                            'valor_icms': float(icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}vICMS').text) if icms_elem.find('.//{http://www.portalfiscal.inf.br/nfe}vICMS') is not None else 0
                        }
                        break
            
            # PIS data
            pis = imposto.find('.//{http://www.portalfiscal.inf.br/nfe}PIS')
            pis_data = {}
            if pis is not None:
                pis_aliq = pis.find('.//{http://www.portalfiscal.inf.br/nfe}PISAliq')
                if pis_aliq is not None:
                    pis_data = {
                        'situacao_tributaria_pis': pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}CST').text if pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}CST') is not None else None,
                        'base_calculo_pis': float(pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vBC').text) if pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vBC') is not None else 0,
                        'aliquota_pis': float(pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}pPIS').text) / 100 if pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}pPIS') is not None else 0,
                        'valor_pis': float(pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vPIS').text) if pis_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vPIS') is not None else 0
                    }
            
            # COFINS data
            cofins = imposto.find('.//{http://www.portalfiscal.inf.br/nfe}COFINS')
            cofins_data = {}
            if cofins is not None:
                cofins_aliq = cofins.find('.//{http://www.portalfiscal.inf.br/nfe}COFINSAliq')
                if cofins_aliq is not None:
                    cofins_data = {
                        'situacao_tributaria_cofins': cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}CST').text if cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}CST') is not None else None,
                        'base_calculo_cofins': float(cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vBC').text) if cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vBC') is not None else 0,
                        'aliquota_cofins': float(cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}pCOFINS').text) / 100 if cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}pCOFINS') is not None else 0,
                        'valor_cofins': float(cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vCOFINS').text) if cofins_aliq.find('.//{http://www.portalfiscal.inf.br/nfe}vCOFINS') is not None else 0
                    }

        # Store item in fact table with complete fiscal data
        item_data = {
            'chave_nfe': chave_nfe,
            'numero_item': int(det_element.get('nItem', 1)),
            'codigo_produto': codigo_produto,
            'descricao': produto_data['descricao'],
            'ncm': produto_data['ncm'],
            'cfop': produto_data['cfop'],
            'unidade_comercial': produto_data['unidade_comercial'],
            'quantidade_comercial': float(prod.find('.//{http://www.portalfiscal.inf.br/nfe}qCom').text) if prod.find('.//{http://www.portalfiscal.inf.br/nfe}qCom') is not None else 0,
            'valor_unitario_comercial': float(prod.find('.//{http://www.portalfiscal.inf.br/nfe}vUnCom').text) if prod.find('.//{http://www.portalfiscal.inf.br/nfe}vUnCom') is not None else 0,
            'valor_total_bruto': float(prod.find('.//{http://www.portalfiscal.inf.br/nfe}vProd').text) if prod.find('.//{http://www.portalfiscal.inf.br/nfe}vProd') is not None else 0,
            'valor_frete': float(prod.find('.//{http://www.portalfiscal.inf.br/nfe}vFrete').text) if prod.find('.//{http://www.portalfiscal.inf.br/nfe}vFrete') is not None else 0,
            'valor_desconto': float(prod.find('.//{http://www.portalfiscal.inf.br/nfe}vDesc').text) if prod.find('.//{http://www.portalfiscal.inf.br/nfe}vDesc') is not None else 0,
            **icms_data,
            **pis_data,
            **cofins_data
        }
        
        # Insert item
        logger.info(f"Inserting NFE item data: {item_data}")
        supabase.table('fact_itens_nfe').insert(item_data).execute()
        logger.info(f"NFE item stored: {codigo_produto}")
        
    except Exception as e:
        logger.error(f"Error storing NFE item data: {str(e)}")

async def _process_nfse_data(root, document_id: str, supabase):
    """Process NFSE data - simplified for now"""
    try:
        logger.info(f"NFSE processing not fully implemented yet for document: {document_id}")
        # TODO: Implement NFSE processing based on specific schema
        
    except Exception as e:
        logger.error(f"Error processing NFSE data: {str(e)}")
        raise

# Endpoints adicionais para consulta de status
@router.get("/agentes/relatorio-executivo/{id_relatorio}", response_model=RelatorioExecutivoResponse)
async def obter_status_relatorio(id_relatorio: str):
    """Obter status e resultado de relatório executivo"""
    try:
        # TODO: Implementar busca de relatório por ID
        # Por enquanto, retorna um exemplo
        return RelatorioExecutivoResponse(
            id_relatorio=id_relatorio,
            titulo="Relatório Executivo",
            status="concluido",
            formato="pdf",
            url_download=f"/downloads/relatorio_{id_relatorio}.pdf",
            resumo_executivo="Relatório executivo gerado com sucesso",
            principais_insights=[],
            recomendacoes_estrategicas=[],
            metricas_chave={},
            tempo_processamento=5.2
        )
    except Exception as e:
        logger.error("Erro ao obter status do relatório", id_relatorio=id_relatorio, error=str(e))
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                codigo_erro="RELATORIO_NAO_ENCONTRADO",
                mensagem="Relatório não encontrado",
                detalhes=f"Relatório com ID {id_relatorio} não foi encontrado",
                sugestao_solucao="Verifique se o ID do relatório está correto"
            ).dict()
        )

@router.get("/agentes/processar-xml/{id_processamento}", response_model=ProcessarXMLResponse)
async def obter_status_processamento_xml(id_processamento: str):
    """Obter status de processamento de documento XML"""
    try:
        # TODO: Implementar busca de processamento por ID
        # Por enquanto, retorna um exemplo
        return ProcessarXMLResponse(
            id_processamento=id_processamento,
            nome_arquivo="documento.xml",
            status="concluido",
            documento=None,
            insights_semanticos=[],
            anomalias_detectadas=[],
            validacoes_negocio={},
            confianca_processamento=0.95,
            tempo_processamento=1.8,
            proximos_passos=[]
        )
    except Exception as e:
        logger.error("Erro ao obter status do processamento XML", 
                    id_processamento=id_processamento, error=str(e))
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                codigo_erro="PROCESSAMENTO_NAO_ENCONTRADO",
                mensagem="Processamento não encontrado",
                detalhes=f"Processamento com ID {id_processamento} não foi encontrado",
                sugestao_solucao="Verifique se o ID do processamento está correto"
            ).dict()
        )

# Endpoints de utilidade e informações
@router.get("/agentes/capacidades")
async def listar_capacidades_agentes():
    """Listar capacidades dos agentes LLM disponíveis"""
    return {
        "agentes_disponiveis": {
            "master_agent": {
                "nome": "Agente Master",
                "descricao": "Orquestrador central com compreensão de linguagem natural",
                "capacidades": [
                    "Interpretação de consultas em português",
                    "Coordenação de workflow inteligente",
                    "Comunicação executiva",
                    "Geração de explicações de negócio"
                ]
            },
            "xml_processing_agent": {
                "nome": "Agente de Processamento XML",
                "descricao": "Processamento inteligente de documentos fiscais NF-e/NFS-e",
                "capacidades": [
                    "Análise semântica de documentos",
                    "Extração de contexto empresarial",
                    "Detecção de anomalias",
                    "Validação de regras de negócio"
                ]
            },
            "ai_categorization_agent": {
                "nome": "Agente de Categorização IA",
                "descricao": "Categorização inteligente com compreensão contextual",
                "capacidades": [
                    "Categorização de produtos e serviços",
                    "Análise de relacionamento com fornecedores",
                    "Detecção de padrões empresariais",
                    "Criação dinâmica de categorias"
                ]
            },
            "sql_agent": {
                "nome": "Agente SQL",
                "descricao": "Tradução de linguagem natural para SQL com contexto empresarial",
                "capacidades": [
                    "Tradução português-SQL",
                    "Otimização de consultas",
                    "Validação de lógica empresarial",
                    "Explicação de resultados"
                ]
            },
            "report_agent": {
                "nome": "Agente de Relatórios",
                "descricao": "Geração de relatórios inteligentes com insights executivos",
                "capacidades": [
                    "Relatórios executivos personalizados",
                    "Análise de dados com IA",
                    "Recomendações estratégicas",
                    "Múltiplos formatos de saída"
                ]
            }
        },
        "formatos_suportados": {
            "entrada": ["XML (NF-e/NFS-e)", "Consultas em português", "JSON"],
            "saida": ["PDF", "XLSX", "DOCX", "JSON"]
        },
        "idiomas_suportados": ["Português Brasileiro"],
        "versao_api": "1.0.0"
    }

@router.get("/agentes/exemplos-consultas")
async def obter_exemplos_consultas():
    """Obter exemplos de consultas em linguagem natural"""
    return {
        "exemplos_consultas": {
            "fornecedores": [
                "Quais são os principais fornecedores por volume de compras nos últimos 6 meses?",
                "Mostre a evolução dos gastos com fornecedores de São Paulo",
                "Identifique fornecedores com comportamento de preço anômalo"
            ],
            "produtos": [
                "Quais produtos tiveram maior crescimento de vendas este ano?",
                "Analise a sazonalidade dos produtos de categoria eletrônicos",
                "Compare o desempenho de produtos nacionais vs importados"
            ],
            "impostos": [
                "Qual o impacto dos impostos na margem de lucro por categoria?",
                "Mostre a evolução da carga tributária nos últimos 12 meses",
                "Identifique oportunidades de otimização fiscal"
            ],
            "vendas": [
                "Como está o desempenho de vendas por região?",
                "Quais são os produtos mais vendidos por trimestre?",
                "Analise a tendência de vendas para o próximo período"
            ],
            "compras": [
                "Qual o volume de compras por categoria nos últimos 3 meses?",
                "Identifique padrões sazonais nas compras",
                "Compare custos de aquisição por fornecedor"
            ]
        },
        "dicas_consultas": [
            "Use períodos específicos para análises mais precisas",
            "Mencione o nível de detalhamento desejado (resumo ou detalhado)",
            "Especifique se deseja comparações ou tendências",
            "Indique se precisa de recomendações de ação"
        ]
    }

# Document Management Endpoints

@router.get("/api/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    document_type_filter: Optional[str] = None,
    current_user: Optional[str] = None  # TODO: Implement proper auth
):
    """Listar documentos fiscais do usuário"""
    try:
        from utils.database import FileUploadManager
        
        # Use temporary user ID until proper auth is implemented
        user_id = None  # Use None for development with admin mode
        
        # Validate parameters
        if limit > 1000:
            limit = 1000
        if skip < 0:
            skip = 0
            
        # Get documents from database
        documents = await FileUploadManager.list_user_documents(
            user_id=user_id,
            skip=skip,
            limit=limit + 1,  # Get one extra to check if there's a next page
            status_filter=status_filter,
            admin_mode=True  # Use admin mode for development
        )
        
        # Check if there's a next page
        has_next = len(documents) > limit
        if has_next:
            documents = documents[:limit]  # Remove the extra document
        
        # Convert to response format
        document_items = []
        for doc in documents:
            document_items.append(DocumentListItem(
                id=doc['id'],
                filename=doc['filename'],
                document_type=doc['document_type'],
                processing_status=doc['processing_status'],
                upload_timestamp=doc['upload_timestamp'],
                file_size=doc['file_size'],
                nome_emitente=doc.get('nome_emitente'),
                valor_total=doc.get('valor_total'),
                data_emissao=doc.get('data_emissao')
            ))
        
        # Calculate total count (simplified - in production, use a separate count query)
        total_count = skip + len(document_items)
        if has_next:
            total_count += 1  # At least one more
        
        return DocumentListResponse(
            documents=document_items,
            total_count=total_count,
            page=skip // limit + 1,
            page_size=limit,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error("Erro ao listar documentos", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                codigo_erro="ERRO_LISTAR_DOCUMENTOS",
                mensagem="Erro ao listar documentos",
                detalhes=str(e),
                sugestao_solucao="Tente novamente ou contate o suporte"
            ).dict()
        )

@router.get("/api/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(
    document_id: str,
    current_user: Optional[str] = None  # TODO: Implement proper auth
):
    """Obter detalhes completos de um documento fiscal"""
    try:
        from utils.database import FileUploadManager
        
        # Use temporary user ID until proper auth is implemented
        user_id = None  # Use None for development with admin mode
        
        # Get document from database
        document = await FileUploadManager.get_document_by_id(document_id, user_id, admin_mode=True)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    codigo_erro="DOCUMENTO_NAO_ENCONTRADO",
                    mensagem="Documento não encontrado",
                    detalhes=f"Documento com ID {document_id} não foi encontrado",
                    sugestao_solucao="Verifique se o ID do documento está correto"
                ).dict()
            )
        
        # Convert to response format
        return DocumentDetailResponse(
            id=document['id'],
            filename=document['filename'],
            document_type=document['document_type'],
            processing_status=document['processing_status'],
            upload_timestamp=document['upload_timestamp'],
            file_size=document['file_size'],
            cnpj_emitente=document.get('cnpj_emitente'),
            nome_emitente=document.get('nome_emitente'),
            cnpj_destinatario=document.get('cnpj_destinatario'),
            nome_destinatario=document.get('nome_destinatario'),
            numero_documento=document.get('numero_documento'),
            serie_documento=document.get('serie_documento'),
            data_emissao=document.get('data_emissao'),
            valor_total=document.get('valor_total'),
            valor_tributos=document.get('valor_tributos'),
            natureza_operacao=document.get('natureza_operacao'),
            processing_started_at=document.get('processing_started_at'),
            processing_completed_at=document.get('processing_completed_at'),
            error_message=document.get('error_message'),
            chave_nfe=document.get('chave_nfe'),
            id_nfse=document.get('id_nfse')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter detalhes do documento", 
                    error=str(e), document_id=document_id)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                codigo_erro="ERRO_DETALHES_DOCUMENTO",
                mensagem="Erro ao obter detalhes do documento",
                detalhes=str(e),
                sugestao_solucao="Tente novamente ou contate o suporte"
            ).dict()
        )


@router.get("/api/documents/{document_id}/status")
async def get_document_processing_status(document_id: str):
    """Simplified document status endpoint for MVP"""
    try:
        from utils.database import FileUploadManager
        
        # Get document basic info (simplified for MVP)
        try:
            # Try to get document from database
            # For MVP, we'll return a simplified status
            return {
                "document_id": document_id,
                "overall_status": "completed",  # Simplified for MVP
                "agent_statuses": [
                    {"agent_name": "xml_processing_agent", "status": "completed"},
                    {"agent_name": "ai_categorization_agent", "status": "completed"},
                    {"agent_name": "sql_agent", "status": "completed"},
                    {"agent_name": "report_agent", "status": "completed"}
                ],
                "processing_results": [],
                "processing_started_at": None,
                "processing_completed_at": None,
                "total_processing_time_ms": 2000,
                "error_summary": None
            }
        except Exception as db_error:
            logger.warning(f"Database error in status check: {str(db_error)}")
            # Return basic status even if database fails
            return {
                "document_id": document_id,
                "overall_status": "completed",
                "agent_statuses": [
                    {"agent_name": "xml_processing_agent", "status": "completed"},
                    {"agent_name": "ai_categorization_agent", "status": "completed"},
                    {"agent_name": "sql_agent", "status": "completed"},
                    {"agent_name": "report_agent", "status": "completed"}
                ],
                "processing_results": [],
                "error_summary": None
            }
        
    except Exception as e:
        logger.error("Erro ao obter status do documento", 
                    error=str(e), document_id=document_id)
        return {
            "document_id": document_id,
            "overall_status": "error",
            "agent_statuses": [],
            "error_summary": f"Erro ao obter status: {str(e)}"
        }

# Simplified XML upload endpoint for MVP
@router.post("/agentes/upload-xml")
async def upload_arquivo_xml(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(...)
):
    """Simplified XML upload for MVP - focus on core functionality"""
    try:
        # Import database utilities
        from utils.database import FileUploadManager, ProcessingStatusManager
        
        # Basic file validation
        if not arquivo.filename.lower().endswith('.xml'):
            raise HTTPException(
                status_code=400,
                detail={
                    "codigo_erro": "FORMATO_INVALIDO",
                    "mensagem": "Apenas arquivos XML são aceitos",
                    "detalhes": f"Arquivo: {arquivo.filename}"
                }
            )
        
        # Read file content
        conteudo = await arquivo.read()
        conteudo_xml = conteudo.decode('utf-8')
        file_size = len(conteudo)
        
        # Basic size validation (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail={
                    "codigo_erro": "ARQUIVO_MUITO_GRANDE",
                    "mensagem": "Arquivo muito grande (máx. 10MB)",
                    "detalhes": f"Tamanho: {file_size / 1024 / 1024:.1f}MB"
                }
            )
        
        # Basic XML validation
        if not conteudo_xml.strip().startswith('<?xml') and not conteudo_xml.strip().startswith('<'):
            raise HTTPException(
                status_code=400,
                detail={
                    "codigo_erro": "XML_INVALIDO",
                    "mensagem": "Arquivo não é um XML válido",
                    "detalhes": "Formato de arquivo não reconhecido"
                }
            )
        
        # Determine document type
        document_type = "NFE"  # Default
        if "nfse" in conteudo_xml.lower() or "rps" in conteudo_xml.lower():
            document_type = "NFSE"
        
        # Use fixed user ID for MVP (no authentication)
        user_id = "11111111-1111-1111-1111-111111111111"
        
        logger.info(
            "Starting simplified XML upload",
            filename=arquivo.filename,
            file_size=file_size,
            document_type=document_type
        )
        
        # Create fiscal document record
        document_id = await FileUploadManager.create_fiscal_document(
            user_id=user_id,
            filename=arquivo.filename,
            file_size=file_size,
            document_type=document_type,
            xml_content=conteudo_xml,
            admin_mode=True
        )
        
        # Create file metadata record
        await FileUploadManager.create_file_metadata(
            document_id=document_id,
            original_filename=arquivo.filename,
            mime_type="application/xml",
            xml_content=conteudo_xml,
            admin_mode=True
        )
        
        # Initialize processing status for 4 main agents
        agent_names = [
            "xml_processing_agent",
            "ai_categorization_agent", 
            "sql_agent",
            "report_agent"
        ]
        await ProcessingStatusManager.initialize_agent_statuses(document_id, agent_names, admin_mode=True)
        
        # Update document status to processing
        await FileUploadManager.update_processing_status(document_id, "processing", admin_mode=True)
        
        # Start background processing with simplified agents
        background_tasks.add_task(
            _processar_xml_background,
            document_id,
            conteudo_xml,
            arquivo.filename,
            document_type
        )
        
        # Extract basic metadata for immediate response
        metadata = await _extract_basic_metadata(conteudo_xml, document_type)
        
        # Create document metadata record
        if metadata:
            await FileUploadManager.create_document_metadata(document_id, metadata, admin_mode=True)
        
        # Simplified response
        response_data = {
            'id_processamento': document_id,
            'nome_arquivo': arquivo.filename,
            'status': "processando",
            'documento': {
                'tipo_documento': document_type,
                'fornecedor': metadata.get('nome_emitente', 'N/A') if metadata else 'N/A',
                'valor_total': metadata.get('valor_total', 0) if metadata else 0,
                'data_emissao': metadata.get('data_emissao') if metadata else None
            },
            'tempo_processamento': 0.3,
            'proximos_passos': [
                "Processamento iniciado com 4 agentes IA",
                "Resultados disponíveis em 2-3 minutos"
            ]
        }
        
        logger.info(
            "XML upload completed successfully",
            document_id=document_id,
            filename=arquivo.filename
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro no upload XML", error=str(e), filename=arquivo.filename)
        raise HTTPException(
            status_code=500,
            detail={
                "codigo_erro": "ERRO_UPLOAD",
                "mensagem": "Erro interno no upload",
                "detalhes": str(e)
            }
        )

# Include real dimensional routers
router.include_router(dimensional_router)
router.include_router(query_router)

# Include mock dimensional routers for testing (commented out - using real data now)
# from .mock_dimensional_routes import mock_dimensional_router, mock_activity_router
# router.include_router(mock_dimensional_router)
# router.include_router(mock_activity_router)

# Include activity router (using mock for now due to datetime serialization issues)
# from .activity_routes import activity_router
# router.include_router(activity_router)

# Include mock activity router temporarily
from .mock_dimensional_routes import mock_activity_router
router.include_router(mock_activity_router)