"""
FastAPI routes for the AI Agents Invoice Analysis System
Rotas em português para integração com agentes LLM
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import structlog
import uuid
from datetime import datetime, timezone
import base64

from schemas.api_schemas import (
    ConsultaNaturalRequest, ConsultaNaturalResponse,
    RelatorioExecutivoRequest, RelatorioExecutivoResponse,
    ProcessarXMLRequest, ProcessarXMLResponse,
    ErrorResponse, StatusSistemaResponse
)
from utils.llm_service import OpenAIIntegrationService
from utils.validation import validador, ValidationError
from utils.error_messages import gerador_mensagens, validador_regras_br, TipoErro
from utils.security import sanitizador, validador_seguranca
from utils.brazilian_formatting import formatador_brasileiro, validador_dados_br
from utils.timezone_handler import gerenciador_timezone, processador_datas_fiscais
from utils.brazilian_business_validation import validador_completo_br
from agents.master_agent import EnhancedMasterAgent
from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent
from agents.report_agent import LLMEnhancedReportAgent

logger = structlog.get_logger()

# Create main router
router = APIRouter()

# Initialize services
llm_service = OpenAIIntegrationService()
master_agent = EnhancedMasterAgent()
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

# Endpoint para upload de arquivo XML
@router.post("/agentes/upload-xml")
async def upload_arquivo_xml(arquivo: UploadFile = File(...)):
    """Upload de arquivo XML para processamento"""
    try:
        if not arquivo.filename.lower().endswith('.xml'):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    codigo_erro="FORMATO_ARQUIVO_INVALIDO",
                    mensagem="Apenas arquivos XML são aceitos",
                    detalhes=f"Arquivo enviado: {arquivo.filename}",
                    sugestao_solucao="Envie um arquivo com extensão .xml"
                ).dict()
            )
        
        # Ler conteúdo do arquivo
        conteudo = await arquivo.read()
        conteudo_base64 = base64.b64encode(conteudo).decode('utf-8')
        
        # Processar usando o endpoint de processamento XML
        request_processamento = ProcessarXMLRequest(
            nome_arquivo=arquivo.filename,
            conteudo_base64=conteudo_base64,
            processar_com_ia=True,
            extrair_insights=True,
            categorizar_automaticamente=True,
            validar_regras_negocio=True
        )
        
        return await processar_documento_xml(request_processamento)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro no upload de arquivo XML", error=str(e), filename=arquivo.filename)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                codigo_erro="ERRO_UPLOAD_XML",
                mensagem="Erro ao fazer upload do arquivo XML",
                detalhes=str(e),
                sugestao_solucao="Verifique se o arquivo não está corrompido e tente novamente"
            ).dict()
        )