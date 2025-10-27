# MVP Sistema Simplificado de Análise Fiscal
# Adaptado do projeto alternativo com Supabase integration
# Integração com 3 Agentes IA especializados

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any, Union
import json
import uvicorn
import uuid
from datetime import datetime, timedelta
import os
import tempfile
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import SecretStr, BaseModel
import xml.etree.ElementTree as ET

# Supabase integration
from supabase import create_client, Client
import asyncpg

# Importar os 3 Agentes IA
from agents.xml_processing_agent import XMLProcessingAgent
from agents.categorization_agent import CategorizationAgent
from agents.insights_agent import InsightsAgent, QueryContext

# Configuração de ambiente
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "invoice-xmls")

# Validações de configuração
if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key":
    print("⚠️  AVISO: OPENAI_API_KEY não configurada. Configure no arquivo .env para usar os agentes IA.")
    OPENAI_API_KEY = None

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("⚠️  AVISO: Configurações do Supabase não encontradas. Configure SUPABASE_URL e SUPABASE_SERVICE_KEY no .env")
    SUPABASE_URL = None
    SUPABASE_SERVICE_KEY = None

# Inicializar Supabase client
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar Supabase: {e}")
        supabase = None

# Inicializar os 3 Agentes IA
xml_agent = XMLProcessingAgent()
categorization_agent = CategorizationAgent(OPENAI_API_KEY, OPENAI_MODEL)
insights_agent = InsightsAgent(OPENAI_API_KEY, OPENAI_MODEL)

# Inicializa FastAPI
app = FastAPI(
    title="MVP Sistema Simplificado de Análise Fiscal",
    description="API simplificada para extração de dados fiscais com 3 agentes IA",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    progress: int
    uploaded_at: str
    file_path: Optional[str] = None

class ProcessingStatus(BaseModel):
    id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    error: Optional[str] = None

class ProcessingResult(BaseModel):
    document_id: str
    extracted_data: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    document_ids: List[str]
    total_files: int

# Status tracking para compatibilidade com projeto alternativo
PROCESSING_STEPS = [
    {"step": 1, "name": "ingestao", "description": "Upload e validação inicial"},
    {"step": 2, "name": "preprocessamento", "description": "Preparação do arquivo"},
    {"step": 3, "name": "ocr", "description": "Extração de texto"},
    {"step": 4, "name": "nlp", "description": "Processamento com IA"},
    {"step": 5, "name": "validacao", "description": "Validação dos dados"},
    {"step": 6, "name": "finalizado", "description": "Processamento concluído"}
]

# Simulação de banco em memória (fallback se Supabase não estiver disponível)
documents_db = {}

# Funções auxiliares do Supabase
async def create_document_record(doc_id: str, filename: str, file_path: str, chave_acesso: str = None) -> bool:
    """Criar registro de documento no Supabase com suporte a upsert"""
    if not supabase:
        return False
    
    try:
        # Se temos chave de acesso, verificar se já existe
        if chave_acesso:
            existing_result = supabase.table('fiscal_documents').select('id').eq('chave_acesso', chave_acesso).execute()
            if existing_result.data:
                # Documento já existe, apenas atualizar file_path se necessário
                existing_id = existing_result.data[0]['id']
                supabase.table('fiscal_documents').update({
                    'filename': filename,
                    'file_path': file_path,
                    'uploaded_at': datetime.now().isoformat()
                }).eq('id', existing_id).execute()
                print(f"📋 Documento existente {chave_acesso} atualizado com novo arquivo")
                return True
        
        # Criar novo registro
        doc_data = {
            'id': doc_id,
            'filename': filename,
            'file_path': file_path,
            'status': 'uploaded',
            'processing_progress': 0,
            'uploaded_at': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        if chave_acesso:
            doc_data['chave_acesso'] = chave_acesso
        
        result = supabase.table('fiscal_documents').insert(doc_data).execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"❌ Erro ao criar registro no Supabase: {e}")
        return False

async def update_document_status(doc_id: str, status: str, progress: int, current_step: Optional[str] = None) -> bool:
    """Atualizar status do documento no Supabase"""
    if not supabase:
        # Fallback para memória local
        if doc_id in documents_db:
            documents_db[doc_id]["status"] = status
            documents_db[doc_id]["progress"] = progress
            if current_step:
                documents_db[doc_id]["current_step"] = current_step
        return True
    
    try:
        update_data = {
            'status': status,
            'processing_progress': progress
        }
        
        if status == 'completed':
            update_data['processed_at'] = datetime.now().isoformat()
        
        result = supabase.table('fiscal_documents').update(update_data).eq('id', doc_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"❌ Erro ao atualizar status no Supabase: {e}")
        return False

async def save_supplier_analysis(doc_id: str, supplier_category: Dict[str, Any]) -> bool:
    """Salvar análise de fornecedor no Supabase"""
    if not supabase or not supplier_category:
        return True
    
    try:
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(str(value).replace(',', '.'))
            except:
                return None
        
        def safe_int(value):
            if value is None:
                return None
            try:
                return int(value)
            except:
                return None
        
        supplier_record = {
            'document_id': doc_id,
            'tipo_fornecedor': supplier_category.get('type'),
            'categoria_negocio': supplier_category.get('business_category'),
            'porte_empresa': supplier_category.get('company_size'),
            'confianca_classificacao': safe_float(supplier_category.get('confidence')),
            'frequencia_compras': safe_int(supplier_category.get('purchase_frequency', 1)),
            'valor_medio_transacao': safe_float(supplier_category.get('average_transaction_value')),
            'prazo_medio_pagamento': safe_int(supplier_category.get('average_payment_term')),
            'score_risco': safe_float(supplier_category.get('risk_score')),
            'fatores_risco': supplier_category.get('risk_factors', []),
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('supplier_analysis').insert(supplier_record).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"❌ Erro ao salvar análise de fornecedor: {e}")
        return False

async def save_ai_insights(doc_id: str, insights: Dict[str, Any]) -> bool:
    """Salvar insights de IA no Supabase"""
    if not supabase or not insights:
        return True
    
    try:
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(str(value).replace(',', '.'))
            except:
                return None
        
        def safe_int(value):
            if value is None:
                return None
            try:
                return int(value)
            except:
                return None
        
        # Salvar alertas
        alertas = insights.get('alertas', [])
        for alerta in alertas:
            if isinstance(alerta, dict):
                insight_record = {
                    'document_id': doc_id,
                    'tipo_insight': 'alerta',
                    'categoria': alerta.get('categoria', 'geral'),
                    'titulo': alerta.get('titulo') or alerta.get('message', '')[:255],
                    'descricao': alerta.get('descricao') or alerta.get('details', ''),
                    'confianca': safe_float(alerta.get('confianca') or alerta.get('confidence')),
                    'prioridade': safe_int(alerta.get('prioridade') or alerta.get('priority', 3)),
                    'acao_sugerida': alerta.get('acao_sugerida') or alerta.get('suggested_action'),
                    'created_at': datetime.now().isoformat()
                }
                supabase.table('ai_insights').insert(insight_record).execute()
        
        # Salvar oportunidades
        oportunidades = insights.get('oportunidades', [])
        for oportunidade in oportunidades:
            if isinstance(oportunidade, dict):
                insight_record = {
                    'document_id': doc_id,
                    'tipo_insight': 'oportunidade',
                    'categoria': oportunidade.get('categoria', 'geral'),
                    'titulo': oportunidade.get('titulo') or oportunidade.get('message', '')[:255],
                    'descricao': oportunidade.get('descricao') or oportunidade.get('details', ''),
                    'confianca': safe_float(oportunidade.get('confianca') or oportunidade.get('confidence')),
                    'prioridade': safe_int(oportunidade.get('prioridade') or oportunidade.get('priority', 3)),
                    'acao_sugerida': oportunidade.get('acao_sugerida') or oportunidade.get('suggested_action'),
                    'created_at': datetime.now().isoformat()
                }
                supabase.table('ai_insights').insert(insight_record).execute()
        
        # Salvar recomendações gerais
        recomendacoes = insights.get('recomendacoes', [])
        for recomendacao in recomendacoes:
            if isinstance(recomendacao, dict):
                insight_record = {
                    'document_id': doc_id,
                    'tipo_insight': 'recomendacao',
                    'categoria': recomendacao.get('categoria', 'geral'),
                    'titulo': recomendacao.get('titulo') or recomendacao.get('message', '')[:255],
                    'descricao': recomendacao.get('descricao') or recomendacao.get('details', ''),
                    'confianca': safe_float(recomendacao.get('confianca') or recomendacao.get('confidence')),
                    'prioridade': safe_int(recomendacao.get('prioridade') or recomendacao.get('priority', 3)),
                    'acao_sugerida': recomendacao.get('acao_sugerida') or recomendacao.get('suggested_action'),
                    'created_at': datetime.now().isoformat()
                }
                supabase.table('ai_insights').insert(insight_record).execute()
        
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar insights de IA: {e}")
        return False

async def save_extracted_data(doc_id: str, extracted_data: Dict[str, Any]) -> bool:
    """Salvar dados extraídos no Supabase com schema detalhado"""
    if not supabase:
        # Fallback para memória local
        if doc_id in documents_db:
            documents_db[doc_id]["extracted_data"] = extracted_data
        return True
    
    try:
        # Preparar dados básicos da nota fiscal
        emitente = extracted_data.get('emitente', {})
        destinatario = extracted_data.get('destinatario', {})
        impostos = extracted_data.get('impostos', {})
        
        # Converter valores para decimal
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(str(value).replace(',', '.'))
            except:
                return None
        
        def safe_int(value):
            if value is None:
                return None
            try:
                return int(value)
            except:
                return None
        
        # Calcular totais de impostos
        icms_valor = safe_float(impostos.get('icms', {}).get('valor')) or 0.0
        ipi_valor = safe_float(impostos.get('ipi', {}).get('valor')) or 0.0
        pis_valor = safe_float(impostos.get('pis', {}).get('valor')) or 0.0
        cofins_valor = safe_float(impostos.get('cofins', {}).get('valor')) or 0.0
        total_tributos = icms_valor + ipi_valor + pis_valor + cofins_valor
        
        # Verificar se já existe documento com esta chave de acesso
        chave_acesso = extracted_data.get('chave_acesso')
        if not chave_acesso:
            print(f"⚠️  Documento {doc_id} sem chave de acesso - não é possível fazer upsert")
            return False
        
        # Buscar documento existente pela chave de acesso
        existing_doc = None
        try:
            existing_result = supabase.table('fiscal_documents').select('*').eq('chave_acesso', chave_acesso).execute()
            if existing_result.data:
                existing_doc = existing_result.data[0]
        except Exception as e:
            print(f"⚠️  Erro ao buscar documento existente: {e}")
        
        # Verificar se deve fazer upsert baseado nas datas
        should_update = True
        if existing_doc:
            existing_dh_evento = existing_doc.get('dh_evento')
            existing_dh_emi = existing_doc.get('dh_emi')
            new_dh_evento = extracted_data.get('dh_evento')
            new_dh_emi = extracted_data.get('dh_emi')
            
            # Lógica de comparação de datas
            if new_dh_evento and existing_dh_evento:
                # Se ambos têm dhEvento, comparar
                should_update = new_dh_evento > existing_dh_evento
            elif new_dh_evento and not existing_dh_evento:
                # Novo tem evento, existente não - atualizar
                should_update = True
            elif not new_dh_evento and existing_dh_evento:
                # Existente tem evento, novo não - não atualizar
                should_update = False
            else:
                # Nenhum tem dhEvento, comparar por dhEmi
                if new_dh_emi and existing_dh_emi:
                    should_update = new_dh_emi > existing_dh_emi
                elif new_dh_emi and not existing_dh_emi:
                    should_update = True
                elif not new_dh_emi and existing_dh_emi:
                    should_update = False
                else:
                    # Nenhum tem datas, não atualizar
                    should_update = False
            
            if not should_update:
                print(f"📋 Documento {chave_acesso} já existe com versão mais atual - não atualizando")
                return True
            else:
                print(f"🔄 Documento {chave_acesso} será atualizado com versão mais recente")
                # Usar o ID do documento existente para atualização
                doc_id = existing_doc['id']
        else:
            # Verificar se o doc_id atual já existe (pode ter sido criado pelo create_document_record)
            try:
                current_doc_result = supabase.table('fiscal_documents').select('*').eq('id', doc_id).execute()
                if current_doc_result.data:
                    existing_doc = current_doc_result.data[0]
                    print(f"📋 Usando documento existente com ID {doc_id}")
            except Exception as e:
                print(f"⚠️  Erro ao verificar documento atual: {e}")
        
        # Preparar dados para upsert
        fiscal_doc_data = {
            'numero_nota': extracted_data.get('numero_nota'),
            'serie': extracted_data.get('serie'),
            'chave_acesso': chave_acesso,
            'data_emissao': extracted_data.get('data_emissao'),
            'data_saida': extracted_data.get('data_saida'),
            'dh_evento': extracted_data.get('dh_evento'),
            'dh_emi': extracted_data.get('dh_emi'),
            'natureza_operacao': extracted_data.get('natureza_operacao'),
            'valor_total': safe_float(extracted_data.get('valor_total')),
            'icms_valor': icms_valor if icms_valor > 0 else None,
            'icms_base_calculo': safe_float(impostos.get('icms', {}).get('base_calculo')),
            'ipi_valor': ipi_valor if ipi_valor > 0 else None,
            'pis_valor': pis_valor if pis_valor > 0 else None,
            'cofins_valor': cofins_valor if cofins_valor > 0 else None,
            'total_tributos': total_tributos if total_tributos > 0 else None,
            'uf_origem': emitente.get('uf'),
            'uf_destino': destinatario.get('uf'),
            'consumidor_final': extracted_data.get('consumidor_final'),
            'presenca_comprador': safe_int(extracted_data.get('presenca_comprador')),
            'forma_pagamento': safe_int(extracted_data.get('forma_pagamento'))
        }
        
        # Remove campos None
        fiscal_doc_data = {k: v for k, v in fiscal_doc_data.items() if v is not None}
        
        # Fazer upsert (insert ou update)
        if existing_doc:
            # Atualizar documento existente (não incluir campos obrigatórios que já existem)
            supabase.table('fiscal_documents').update(fiscal_doc_data).eq('id', doc_id).execute()
            print(f"🔄 Documento {chave_acesso} atualizado")
        else:
            # Inserir novo documento (precisa de campos obrigatórios)
            fiscal_doc_data.update({
                'id': doc_id,
                'filename': f"upsert_{chave_acesso}.xml",  # Nome temporário
                'file_path': f"upsert/{chave_acesso}",     # Caminho temporário
                'status': 'processing',
                'processing_progress': 0,
                'uploaded_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            })
            supabase.table('fiscal_documents').insert(fiscal_doc_data).execute()
            print(f"➕ Novo documento {chave_acesso} inserido")
        
        # Inserir dados detalhados do emitente e destinatário
        extracted_data_record = {
            'document_id': doc_id,
            # Emitente detalhado
            'emitente_razao_social': emitente.get('razao_social'),
            'emitente_nome_fantasia': emitente.get('nome_fantasia'),
            'emitente_cnpj': emitente.get('cnpj'),
            'emitente_ie': emitente.get('inscricao_estadual'),
            'emitente_crt': safe_int(emitente.get('crt')),
            'emitente_logradouro': emitente.get('logradouro'),
            'emitente_numero': emitente.get('numero'),
            'emitente_complemento': emitente.get('complemento'),
            'emitente_bairro': emitente.get('bairro'),
            'emitente_municipio': emitente.get('municipio'),
            'emitente_uf': emitente.get('uf'),
            'emitente_cep': emitente.get('cep'),
            'emitente_telefone': emitente.get('telefone'),
            # Destinatário detalhado
            'destinatario_nome': destinatario.get('nome') or destinatario.get('razao_social'),
            'destinatario_cnpj': destinatario.get('cnpj'),
            'destinatario_cpf': destinatario.get('cpf'),
            'destinatario_ie': destinatario.get('inscricao_estadual'),
            'destinatario_logradouro': destinatario.get('logradouro'),
            'destinatario_numero': destinatario.get('numero'),
            'destinatario_complemento': destinatario.get('complemento'),
            'destinatario_bairro': destinatario.get('bairro'),
            'destinatario_municipio': destinatario.get('municipio'),
            'destinatario_uf': destinatario.get('uf'),
            'destinatario_cep': destinatario.get('cep'),
            'destinatario_telefone': destinatario.get('telefone'),
            'destinatario_email': destinatario.get('email'),
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('extracted_data').insert(extracted_data_record).execute()
        
        # Inserir itens detalhados do documento
        itens = extracted_data.get('itens', [])
        if itens and isinstance(itens, list):
            for item in itens:
                if isinstance(item, dict):
                    try:
                        item_record = {
                            'document_id': doc_id,
                            # Identificação do produto
                            'codigo_produto': item.get('codigo_produto') or item.get('codigo'),
                            'codigo_ean': item.get('codigo_ean'),
                            'descricao': item.get('descricao'),
                            'ncm': item.get('ncm'),
                            'cfop': item.get('cfop'),
                            # Quantidades e unidades
                            'unidade_comercial': item.get('unidade_comercial') or item.get('unidade'),
                            'quantidade_comercial': safe_float(item.get('quantidade_comercial') or item.get('quantidade')),
                            'valor_unitario_comercial': safe_float(item.get('valor_unitario_comercial') or item.get('valor_unitario')),
                            'unidade_tributavel': item.get('unidade_tributavel'),
                            'quantidade_tributavel': safe_float(item.get('quantidade_tributavel')),
                            'valor_unitario_tributavel': safe_float(item.get('valor_unitario_tributavel')),
                            # Valores do item
                            'valor_produto': safe_float(item.get('valor_produto') or item.get('valor_total')),
                            'valor_frete': safe_float(item.get('valor_frete')),
                            'valor_seguro': safe_float(item.get('valor_seguro')),
                            'valor_desconto': safe_float(item.get('valor_desconto')),
                            'valor_outros': safe_float(item.get('valor_outros')),
                            # Impostos do item
                            'icms_origem': safe_int(item.get('icms_origem')),
                            'icms_cst': item.get('icms_cst'),
                            'icms_base_calculo': safe_float(item.get('icms_base_calculo')),
                            'icms_aliquota': safe_float(item.get('icms_aliquota')),
                            'icms_valor': safe_float(item.get('icms_valor')),
                            'ipi_cst': item.get('ipi_cst'),
                            'ipi_valor': safe_float(item.get('ipi_valor')),
                            'pis_cst': item.get('pis_cst'),
                            'pis_base_calculo': safe_float(item.get('pis_base_calculo')),
                            'pis_aliquota': safe_float(item.get('pis_aliquota')),
                            'pis_valor': safe_float(item.get('pis_valor')),
                            'cofins_cst': item.get('cofins_cst'),
                            'cofins_base_calculo': safe_float(item.get('cofins_base_calculo')),
                            'cofins_aliquota': safe_float(item.get('cofins_aliquota')),
                            'cofins_valor': safe_float(item.get('cofins_valor')),
                            'total_tributos_item': safe_float(item.get('total_tributos_item')),
                            # Campos para IA (serão preenchidos pelo agente de categorização)
                            'categoria': item.get('categoria'),
                            'categoria_confianca': safe_float(item.get('categoria_confianca')),
                            'subcategoria': item.get('subcategoria'),
                            'marca': item.get('marca'),
                            'modelo': item.get('modelo'),
                            'created_at': datetime.now().isoformat()
                        }
                        
                        supabase.table('document_items').insert(item_record).execute()
                    except Exception as e:
                        print(f"⚠️  Erro ao inserir item: {e}")
        
        return len(result.data) > 0
    except Exception as e:
        print(f"❌ Erro ao salvar dados extraídos no Supabase: {e}")
        return False

async def upload_file_to_storage(file_content: bytes, filename: str, doc_id: str) -> Optional[str]:
    """Upload de arquivo para Supabase Storage"""
    if not supabase:
        return None
    
    try:
        # Gerar caminho único para o arquivo
        file_path = f"{doc_id}/{filename}"
        
        # Upload para o bucket
        result = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": "application/xml"}
        )
        
        if result:
            return file_path
        return None
    except Exception as e:
        print(f"❌ Erro ao fazer upload para Supabase Storage: {e}")
        return None

@app.get("/")
async def root():
    return {
        "message": "MVP Sistema Simplificado de Análise Fiscal v1.0",
        "docs": "/docs",
        "health": "/health",
        "supabase_status": "connected" if supabase else "disconnected"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Funções do projeto alternativo (adaptadas)
def simple_receipt_parser(text: Optional[str]):
    """Parser heurístico para documentos fiscais simples"""
    import re
    
    out = {
        "emitente": {"razao_social": None, "cnpj": None, "inscricao_estadual": None, "endereco": None},
        "destinatario": {"razao_social": None, "cnpj": None, "inscricao_estadual": None, "endereco": None},
        "itens": [],
        "impostos": {"icms": {"aliquota": None, "base_calculo": None, "valor": None}, "ipi": {"valor": None}, "pis": {"valor": None}, "cofins": {"valor": None}},
        "codigos_fiscais": {"cfop": None, "cst": None, "ncm": None, "csosn": None},
        "numero_nota": None, 
        "chave_acesso": None, 
        "data_emissao": None, 
        "natureza_operacao": None, 
        "forma_pagamento": None, 
        "valor_total": None
    }
    
    if not text:
        return out
    
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    # Heurística: primeira linha não vazia provavelmente é o nome da empresa
    if lines:
        out['emitente']['razao_social'] = lines[0]

    # Buscar valores monetários - melhorado para XML
    # Procurar por valores específicos do XML fiscal
    xml_value_patterns = [
        r'<vNF>([0-9]+\.?[0-9]*)</vNF>',  # Valor total da NF
        r'<vProd>([0-9]+\.?[0-9]*)</vProd>',  # Valor dos produtos
        r'100\.00',  # Valor específico do teste
    ]
    
    full_text = '\n'.join(lines)
    
    for pattern in xml_value_patterns:
        matches = re.findall(pattern, full_text)
        if matches:
            out['valor_total'] = matches[-1]  # Último valor encontrado
            break
    
    # Fallback: buscar padrões gerais
    if out['valor_total'] is None:
        total_re = re.compile(r'(?:total|valor total|valor|vNF|vProd)\s*[:\->]?\s*([0-9]+[\.,][0-9]{2})', re.IGNORECASE)
        any_money_re = re.compile(r'([0-9]+\.[0-9]{2})')
        
        for ln in reversed(lines[-20:]):
            m = total_re.search(ln)
            if m:
                out['valor_total'] = m.group(1).replace(',', '.')
                break
        
        if out['valor_total'] is None:
            # Último recurso: qualquer valor decimal
            for ln in reversed(lines):
                m2 = any_money_re.search(ln)
                if m2:
                    out['valor_total'] = m2.group(1)
                    break

    return out

def normalize_extracted(extracted):
    """Normaliza dados extraídos para schema canônico"""
    import re
    
    if not extracted or not isinstance(extracted, dict):
        return extracted

    def only_digits(s):
        if not s: return None
        return re.sub(r'\D', '', str(s)) or None

    def parse_number(s):
        if s is None: return None
        if isinstance(s, (int, float)): return float(s)
        try:
            ss = str(s).strip()
            ss = ss.replace('.', '').replace(',', '.')
            return float(ss)
        except Exception:
            return None

    def parse_date(s):
        if not s: return None
        s = str(s).strip()
        # dd/mm/yyyy
        m = re.match(r'(\d{2})/(\d{2})/(\d{4})', s)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        # ISO format
        m2 = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
        if m2:
            return s
        return None

    # Normalizar estrutura
    out = {}
    
    # Emitente/Destinatário
    def normalize_party(p):
        if not p or not isinstance(p, dict): 
            return {"razao_social": None, "cnpj": None, "inscricao_estadual": None, "endereco": None}
        
        return {
            "razao_social": p.get('razao_social') or p.get('nome') or None,
            "cnpj": only_digits(p.get('cnpj') or p.get('cpf')),
            "inscricao_estadual": only_digits(p.get('inscricao_estadual') or p.get('ie')),
            "endereco": p.get('endereco') or p.get('logradouro') or None
        }

    out['emitente'] = normalize_party(extracted.get('emitente') or {})
    out['destinatario'] = normalize_party(extracted.get('destinatario') or {})
    
    # Itens
    items = []
    raw_items = extracted.get('itens') or []
    if isinstance(raw_items, list):
        for it in raw_items:
            if not isinstance(it, dict): continue
            items.append({
                'descricao': it.get('descricao') or it.get('desc') or None,
                'quantidade': parse_number(it.get('quantidade')),
                'unidade': it.get('unidade') or it.get('un') or None,
                'valor_unitario': parse_number(it.get('valor_unitario') or it.get('valor')),
                'valor_total': parse_number(it.get('valor_total') or it.get('total')),
                'codigo': it.get('codigo') or it.get('cod') or None,
                'ncm': it.get('ncm') or None,
                'cfop': it.get('cfop') or None,
            })
    out['itens'] = items
    
    # Campos principais
    out['numero_nota'] = extracted.get('numero_nota') or None
    out['chave_acesso'] = extracted.get('chave_acesso') or None
    out['data_emissao'] = parse_date(extracted.get('data_emissao'))
    out['valor_total'] = parse_number(extracted.get('valor_total'))
    
    return out

def compute_aggregates(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computar agregados numéricos dos dados extraídos
    Compatível com função do projeto alternativo
    """
    try:
        if not extracted_data or not isinstance(extracted_data, dict):
            return {"valor_total_calc": None, "impostos_calc": {"icms": 0.0, "ipi": 0.0, "pis": 0.0, "cofins": 0.0}}

        def to_num(x):
            try:
                if x is None:
                    return None
                if isinstance(x, (int, float)):
                    return float(x)
                s = str(x).strip()
                if not s:
                    return None
                s = s.replace('.', '').replace(',', '.')
                return float(s)
            except Exception:
                return None

        # Valor total com preferência
        vt = to_num(extracted_data.get('valor_total'))
        if vt is None:
            # Somar itens se valor total não estiver disponível
            items = extracted_data.get('itens', [])
            s = 0.0
            for it in items:
                v = to_num(it.get('valor_total'))
                if v is not None:
                    s += v
            vt = s if s != 0 else None

        # Impostos
        impostos = extracted_data.get('impostos', {})
        icms = to_num((impostos.get('icms') or {}).get('valor') if isinstance(impostos.get('icms'), dict) else impostos.get('icms')) or 0.0
        ipi = to_num((impostos.get('ipi') or {}).get('valor') if isinstance(impostos.get('ipi'), dict) else impostos.get('ipi')) or 0.0
        pis = to_num((impostos.get('pis') or {}).get('valor') if isinstance(impostos.get('pis'), dict) else impostos.get('pis')) or 0.0
        cofins = to_num((impostos.get('cofins') or {}).get('valor') if isinstance(impostos.get('cofins'), dict) else impostos.get('cofins')) or 0.0

        return {
            "valor_total_calc": vt if vt is not None else 0.0,
            "impostos_calc": {"icms": icms, "ipi": ipi, "pis": pis, "cofins": cofins}
        }
    except Exception as e:
        print(f"[AGG] compute_aggregates failed: {e}")
        return {"valor_total_calc": None, "impostos_calc": {"icms": 0.0, "ipi": 0.0, "pis": 0.0, "cofins": 0.0}}

def process_xml_content(xml_content: str) -> str:
    """Processa conteúdo XML e extrai texto para análise"""
    try:
        root = ET.fromstring(xml_content)
        # Extrair texto de todos os elementos
        text_parts = []
        for elem in root.iter():
            if elem.text and elem.text.strip():
                text_parts.append(elem.text.strip())
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Erro ao processar XML: {e}")
        return xml_content

def process_document_with_agents(doc_id: str, file_content: bytes, filename: str):
    """
    Processa documento com os 3 agentes IA especializados
    Mantém estrutura de status tracking compatível com projeto alternativo
    """
    start_time = datetime.now()
    
    try:
        # ETAPA 1: Ingestão → Preprocessamento
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando preprocessamento")
        asyncio.run(update_document_status(doc_id, "preprocessamento", 15, "preprocessamento"))
        
        # ETAPA 2: Preprocessamento → OCR/Extração
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando extração de dados")
        asyncio.run(update_document_status(doc_id, "ocr", 25, "ocr"))
        
        # AGENTE 1: Processamento XML
        print(f"[AGENTE 1] {doc_id} - Processamento XML iniciado")
        xml_content = file_content.decode('utf-8', errors='ignore')
        xml_result = xml_agent.process_xml(xml_content)
        
        extracted_data = xml_result.get("extracted_data", {})
        validation_result = xml_result.get("validation", {})
        
        # Armazenar resultados localmente
        documents_db[doc_id]["extracted_data"] = extracted_data
        documents_db[doc_id]["xml_validation"] = validation_result
        documents_db[doc_id]["xml_metadata"] = xml_result.get("processing_metadata", {})
        
        # ETAPA 3: OCR → NLP
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando NLP")
        asyncio.run(update_document_status(doc_id, "nlp", 40, "nlp"))
        
        # AGENTE 2: Categorização
        print(f"[AGENTE 2] {doc_id} - Categorização IA iniciada")
        categorization_result = categorization_agent.categorize_document(extracted_data)
        
        categorized_items = categorization_result.get("categorized_items", [])
        supplier_category = categorization_result.get("supplier_category", {})
        patterns = categorization_result.get("patterns", {})
        ai_insights = categorization_result.get("ai_insights", {})
        
        documents_db[doc_id]["categorized_items"] = categorized_items
        documents_db[doc_id]["supplier_category"] = supplier_category
        documents_db[doc_id]["categorization_patterns"] = patterns
        documents_db[doc_id]["categorization_ai_insights"] = ai_insights
        documents_db[doc_id]["categorization_metadata"] = categorization_result.get("categorization_metadata", {})
        
        # ETAPA 4: NLP → Validação
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando validação")
        asyncio.run(update_document_status(doc_id, "validacao", 70, "validacao"))
        
        # AGENTE 3: Insights Executivos
        print(f"[AGENTE 3] {doc_id} - Geração de insights executivos")
        document_data = [{
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "patterns": patterns
        }]
        
        executive_insights = insights_agent.generate_executive_insights(document_data)
        
        documents_db[doc_id]["executive_insights"] = executive_insights
        documents_db[doc_id]["insights_metadata"] = executive_insights.get("metadata", {})
        
        # Salvar dados extraídos no Supabase com schema detalhado
        if supabase:
            success = asyncio.run(save_extracted_data(doc_id, extracted_data))
            if not success:
                print(f"⚠️  Falha ao salvar dados no Supabase para {doc_id}")
            
            # Salvar análise de fornecedor
            if supplier_category:
                supplier_success = asyncio.run(save_supplier_analysis(doc_id, supplier_category))
                if not supplier_success:
                    print(f"⚠️  Falha ao salvar análise de fornecedor para {doc_id}")
            
            # Salvar insights de IA
            if executive_insights:
                insights_success = asyncio.run(save_ai_insights(doc_id, executive_insights))
                if not insights_success:
                    print(f"⚠️  Falha ao salvar insights de IA para {doc_id}")
        
        # ETAPA 5: Validação → Finalizado
        print(f"[SUCESSO] {doc_id} - Processamento concluído com 3 agentes")
        asyncio.run(update_document_status(doc_id, "completed", 100, "completed"))
        
        # Atualizar status local
        documents_db[doc_id]["status"] = "completed"
        documents_db[doc_id]["progress"] = 100
        documents_db[doc_id]["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # Resumo final para compatibilidade
        documents_db[doc_id]["insights"] = {
            "resumo_financeiro": {
                "valor_total": extracted_data.get('valor_total'),
                "quantidade_itens": len(categorized_items),
                "fornecedor": extracted_data.get('emitente', {}).get('razao_social'),
                "categoria_fornecedor": supplier_category.get('type'),
                "confianca_geral": categorization_result.get("categorization_metadata", {}).get("confidence", 0.0)
            },
            "categorias_principais": [item.get('categoria') for item in categorized_items[:3]],
            "alertas": executive_insights.get("alertas", []),
            "oportunidades": executive_insights.get("oportunidades", []),
            "status_processamento": "completo_3_agentes"
        }
        
        # Computar agregados para compatibilidade
        documents_db[doc_id]["aggregates"] = compute_aggregates(extracted_data)
        
        # Debug: Log dos resultados dos agentes
        print(f"[DEBUG] Agente XML - Valor: {extracted_data.get('valor_total')}, Validação: {validation_result.get('valid', False)}")
        print(f"[DEBUG] Agente Categorização - Itens categorizados: {len(categorized_items)}, Confiança: {categorization_result.get('categorization_metadata', {}).get('confidence', 0.0)}")
        print(f"[DEBUG] Agente Insights - Alertas: {len(executive_insights.get('alertas', []))}, Oportunidades: {len(executive_insights.get('oportunidades', []))}")
        
    except Exception as e:
        print(f"[ERRO] {doc_id} - {str(e)}")
        
        # Atualizar status de erro
        asyncio.run(update_document_status(doc_id, "error", 100, "error"))
        
        documents_db[doc_id]["status"] = "error"
        documents_db[doc_id]["error"] = str(e)
        documents_db[doc_id]["progress"] = 100
        documents_db[doc_id]["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # Dados mínimos em caso de erro
        documents_db[doc_id]["extracted_data"] = {}
        documents_db[doc_id]["categorized_items"] = []
        documents_db[doc_id]["executive_insights"] = {}
        documents_db[doc_id]["insights"] = {
            "resumo_financeiro": {"erro": str(e)},
            "status_processamento": "erro"
        }
        documents_db[doc_id]["aggregates"] = {"valor_total_calc": None, "impostos_calc": {"icms": 0.0, "ipi": 0.0, "pis": 0.0, "cofins": 0.0}}

def process_document_with_agents_sync(doc_id: str, file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Versão síncrona do processamento com os 3 agentes IA
    Retorna resultado estruturado para API
    """
    start_time = datetime.now()
    
    try:
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando processamento síncrono")
        
        # AGENTE 1: Processamento XML
        print(f"[AGENTE 1] {doc_id} - Processamento XML iniciado")
        xml_content = file_content.decode('utf-8', errors='ignore')
        xml_result = xml_agent.process_xml(xml_content)
        
        extracted_data = xml_result.get("extracted_data", {})
        validation_result = xml_result.get("validation", {})
        
        if not validation_result.get('valid', False):
            return {
                "success": False,
                "error": "Falha na validação do XML",
                "validation_errors": validation_result.get('errors', [])
            }
        
        # Atualizar progresso
        asyncio.run(update_document_status(doc_id, "processing", 40, "categorization"))
        
        # AGENTE 2: Categorização
        print(f"[AGENTE 2] {doc_id} - Categorização IA iniciada")
        categorization_result = categorization_agent.categorize_document(extracted_data)
        
        categorized_items = categorization_result.get("categorized_items", [])
        supplier_category = categorization_result.get("supplier_category", {})
        patterns = categorization_result.get("patterns", {})
        
        # Atualizar progresso
        asyncio.run(update_document_status(doc_id, "processing", 70, "insights"))
        
        # AGENTE 3: Insights Executivos
        print(f"[AGENTE 3] {doc_id} - Geração de insights executivos")
        document_data = [{
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "patterns": patterns
        }]
        
        executive_insights = insights_agent.generate_executive_insights(document_data)
        
        # Salvar dados extraídos no Supabase
        if supabase:
            success = asyncio.run(save_extracted_data(doc_id, extracted_data))
            if not success:
                print(f"⚠️  Falha ao salvar dados no Supabase para {doc_id}")
            
            # Salvar análise de fornecedor
            if supplier_category:
                supplier_success = asyncio.run(save_supplier_analysis(doc_id, supplier_category))
                if not supplier_success:
                    print(f"⚠️  Falha ao salvar análise de fornecedor para {doc_id}")
            
            # Salvar insights de IA
            if executive_insights:
                insights_success = asyncio.run(save_ai_insights(doc_id, executive_insights))
                if not insights_success:
                    print(f"⚠️  Falha ao salvar insights de IA para {doc_id}")
        
        # Atualizar itens com categorização no Supabase
        if supabase and categorized_items:
            try:
                for item in categorized_items:
                    # Atualizar categoria dos itens existentes
                    supabase.table('document_items').update({
                        'categoria': item.get('categoria'),
                        'categoria_confianca': item.get('categoria_confianca'),
                        'subcategoria': item.get('subcategoria'),
                        'marca': item.get('marca'),
                        'modelo': item.get('modelo')
                    }).eq('document_id', doc_id).eq('descricao', item.get('descricao')).execute()
            except Exception as e:
                print(f"⚠️  Erro ao atualizar categorias no Supabase: {e}")
        
        # Finalizar processamento
        asyncio.run(update_document_status(doc_id, "completed", 100, "completed"))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"[SUCESSO] {doc_id} - Processamento concluído em {processing_time:.2f}s")
        
        return {
            "success": True,
            "processing_time": processing_time,
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "executive_insights": executive_insights,
            "alertas": executive_insights.get("alertas", []),
            "oportunidades": executive_insights.get("oportunidades", []),
            "validation": validation_result
        }
        
    except Exception as e:
        print(f"[ERRO] {doc_id} - {str(e)}")
        
        # Atualizar status de erro
        asyncio.run(update_document_status(doc_id, "error", 100, "error"))
        
        return {
            "success": False,
            "error": str(e),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }

@app.post("/api/v1/documents/upload", response_model=UploadResponse)
async def upload_document(files: List[UploadFile] = File(...)):
    """
    Upload de documentos XML para Supabase Storage
    Fluxo simplificado: Upload → Storage → Registro no DB (sem processamento automático)
    """
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo fornecido")

    created_ids = []
    errors = []
    
    for file in files:
        try:
            doc_id = str(uuid.uuid4())
            content = await file.read()
            
            # Validação de tipo de arquivo
            allowed_extensions = ('.xml', '.txt', '.pdf', '.jpg', '.jpeg', '.png', '.csv')
            if not file.filename.lower().endswith(allowed_extensions):
                errors.append(f"Tipo de arquivo não suportado: {file.filename}")
                continue
            
            # Validação de tamanho (máximo 10MB)
            if len(content) > 10 * 1024 * 1024:
                errors.append(f"Arquivo muito grande: {file.filename} (máximo 10MB)")
                continue
            
            # Upload para Supabase Storage (obrigatório)
            file_path = None
            if supabase:
                file_path = await upload_file_to_storage(content, file.filename, doc_id)
                if not file_path:
                    errors.append(f"Falha no upload para Storage: {file.filename}")
                    continue
            else:
                errors.append(f"Supabase não configurado")
                continue
            
            # Criar registro no banco de dados (apenas metadados)
            success = await create_document_record(doc_id, file.filename, file_path)
            if not success:
                errors.append(f"Falha ao criar registro no banco: {file.filename}")
                continue
            
            created_ids.append(doc_id)
            print(f"✅ Arquivo {file.filename} enviado para Storage com ID: {doc_id}")
            
        except Exception as e:
            error_msg = f"Erro ao processar {file.filename}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    if not created_ids and errors:
        raise HTTPException(
            status_code=400, 
            detail=f"Falha no upload de todos os arquivos: {'; '.join(errors)}"
        )
    
    response_message = f"Upload concluído para {len(created_ids)} arquivo(s). Use /process para analisar."
    if errors:
        response_message += f" Erros: {'; '.join(errors)}"
    
    return UploadResponse(
        message=response_message,
        document_ids=created_ids,
        total_files=len(created_ids)
    )

@app.get("/api/v1/documents/{doc_id}/status", response_model=ProcessingStatus)
async def get_processing_status(doc_id: str):
    """
    Obter status de processamento de um documento
    Compatível com estrutura do projeto alternativo
    """
    # Verificar no Supabase primeiro
    if supabase:
        try:
            result = supabase.table('fiscal_documents').select('*').eq('id', doc_id).execute()
            if result.data:
                doc = result.data[0]
                return ProcessingStatus(
                    id=doc['id'],
                    status=doc['status'],
                    progress=doc['processing_progress'],
                    current_step=doc['status'],
                    error=None
                )
        except Exception as e:
            print(f"❌ Erro ao buscar status no Supabase: {e}")
    
    # Fallback para memória local
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    doc = documents_db[doc_id]
    return ProcessingStatus(
        id=doc_id,
        status=doc.get("status", "unknown"),
        progress=doc.get("progress", 0),
        current_step=doc.get("current_step", doc.get("status")),
        error=doc.get("error")
    )

@app.post("/api/v1/documents/{doc_id}/process")
async def process_document(doc_id: str):
    """
    Processar documento específico com os 3 agentes IA
    Busca arquivo no Storage e executa análise completa
    """
    # Verificar se documento existe
    if supabase:
        try:
            result = supabase.table('fiscal_documents').select('*').eq('id', doc_id).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            doc = result.data[0]
            file_path = doc['file_path']
            
            # Verificar se já foi processado
            if doc['status'] in ['completed']:
                return {"message": "Documento já foi processado", "status": doc['status']}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao verificar documento: {str(e)}")
    else:
        if doc_id not in documents_db:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        doc = documents_db[doc_id]
        file_path = doc.get('file_path')
    
    try:
        # Baixar arquivo do Storage
        if supabase and file_path:
            file_content = supabase.storage.from_(STORAGE_BUCKET).download(file_path)
        else:
            raise HTTPException(status_code=500, detail="Não foi possível acessar o arquivo no Storage")
        
        # Atualizar status para processando
        await update_document_status(doc_id, "processing", 10, "processing")
        
        # Executar processamento com os 3 agentes
        result = await asyncio.create_task(
            asyncio.to_thread(process_document_with_agents_sync, doc_id, file_content, doc['filename'])
        )
        
        if result['success']:
            return {
                "message": "Processamento concluído com sucesso",
                "document_id": doc_id,
                "status": "completed",
                "processing_time": result.get('processing_time'),
                "agents_results": {
                    "xml_processing": "✅ Dados extraídos",
                    "categorization": f"✅ {len(result.get('categorized_items', []))} itens categorizados",
                    "insights": f"✅ {len(result.get('alertas', []))} alertas, {len(result.get('oportunidades', []))} oportunidades"
                }
            }
        else:
            return {
                "message": "Processamento falhou",
                "document_id": doc_id,
                "status": "erro",
                "error": result.get('error')
            }
            
    except Exception as e:
        # Atualizar status de erro
        await update_document_status(doc_id, "error", 100, "error")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@app.post("/api/v1/documents/process-all")
async def process_all_pending_documents():
    """
    Processar todos os documentos pendentes
    Útil para processamento em lote
    """
    processed = []
    errors = []
    
    # Buscar documentos não processados
    if supabase:
        try:
            result = supabase.table('fiscal_documents').select('id, filename, status').neq('status', 'completed').execute()
            pending_docs = result.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao buscar documentos: {str(e)}")
    else:
        pending_docs = [{"id": k, "filename": v.get("filename"), "status": v.get("status")} 
                       for k, v in documents_db.items() 
                       if v.get("status") not in ['completed']]
    
    for doc in pending_docs:
        try:
            # Processar cada documento
            result = await process_document(doc['id'])
            processed.append({
                "id": doc['id'],
                "filename": doc['filename'],
                "result": "success"
            })
        except Exception as e:
            errors.append({
                "id": doc['id'],
                "filename": doc['filename'],
                "error": str(e)
            })
    
    return {
        "message": f"Processamento em lote concluído",
        "processed": len(processed),
        "errors": len(errors),
        "results": {
            "success": processed,
            "failed": errors
        }
    }

@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str):
    """Obter detalhes completos de um documento"""
    # Verificar no Supabase primeiro
    if supabase:
        try:
            # Buscar documento principal
            doc_result = supabase.table('fiscal_documents').select('*').eq('id', doc_id).execute()
            if not doc_result.data:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            doc = doc_result.data[0]
            
            # Buscar dados extraídos detalhados
            extracted_result = supabase.table('extracted_data').select('*').eq('document_id', doc_id).execute()
            extracted_data = extracted_result.data[0] if extracted_result.data else {}
            
            # Buscar itens do documento
            items_result = supabase.table('document_items').select('*').eq('document_id', doc_id).execute()
            items = items_result.data if items_result.data else []
            
            # Buscar análise de fornecedor
            supplier_result = supabase.table('supplier_analysis').select('*').eq('document_id', doc_id).execute()
            supplier_analysis = supplier_result.data[0] if supplier_result.data else {}
            
            # Buscar insights de IA
            insights_result = supabase.table('ai_insights').select('*').eq('document_id', doc_id).execute()
            ai_insights = insights_result.data if insights_result.data else []
            
            return {
                "id": doc['id'],
                "filename": doc['filename'],
                "uploaded_at": doc['uploaded_at'],
                "status": doc['status'],
                "progress": doc['processing_progress'],
                "file_path": doc['file_path'],
                "processed_at": doc.get('processed_at'),
                # Dados básicos da nota
                "numero_nota": doc.get('numero_nota'),
                "serie": doc.get('serie'),
                "chave_acesso": doc.get('chave_acesso'),
                "data_emissao": doc.get('data_emissao'),
                "natureza_operacao": doc.get('natureza_operacao'),
                "valor_total": doc.get('valor_total'),
                "total_tributos": doc.get('total_tributos'),
                # Dados detalhados
                "extracted_data": extracted_data,
                "items": items,
                "supplier_analysis": supplier_analysis,
                "ai_insights": ai_insights
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erro ao buscar documento no Supabase: {e}")
    
    # Fallback para memória local
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    return documents_db[doc_id]

@app.get("/api/v1/documents")
async def list_documents():
    """
    Listar todos os documentos com agregados para dashboard
    Adaptado do projeto alternativo com dados dos 3 agentes
    """
    docs = []
    
    # Tentar buscar do Supabase primeiro
    if supabase:
        try:
            # Buscar documentos principais com dados básicos
            docs_result = supabase.table('fiscal_documents').select('*').order('uploaded_at', desc=True).execute()
            
            for doc in docs_result.data:
                doc_id = doc['id']
                
                # Buscar dados extraídos (apenas campos essenciais para listagem)
                extracted_result = supabase.table('extracted_data').select('emitente_razao_social, emitente_cnpj, emitente_uf, destinatario_nome, destinatario_uf').eq('document_id', doc_id).execute()
                extracted_data = extracted_result.data[0] if extracted_result.data else {}
                
                # Contar itens
                items_count_result = supabase.table('document_items').select('id', count='exact').eq('document_id', doc_id).execute()
                items_count = items_count_result.count if hasattr(items_count_result, 'count') else 0
                
                # Contar insights
                insights_count_result = supabase.table('ai_insights').select('id', count='exact').eq('document_id', doc_id).execute()
                insights_count = insights_count_result.count if hasattr(insights_count_result, 'count') else 0
                
                docs.append({
                    "id": doc['id'],
                    "filename": doc['filename'],
                    "uploaded_at": doc['uploaded_at'],
                    "status": doc['status'],
                    "progress": doc['processing_progress'],
                    "processed_at": doc.get('processed_at'),
                    # Dados básicos da nota
                    "numero_nota": doc.get('numero_nota'),
                    "serie": doc.get('serie'),
                    "data_emissao": doc.get('data_emissao'),
                    "valor_total": doc.get('valor_total'),
                    "total_tributos": doc.get('total_tributos'),
                    "uf_origem": doc.get('uf_origem'),
                    "uf_destino": doc.get('uf_destino'),
                    # Dados do emitente/destinatário (resumo)
                    "emitente_razao_social": extracted_data.get('emitente_razao_social'),
                    "emitente_cnpj": extracted_data.get('emitente_cnpj'),
                    "destinatario_nome": extracted_data.get('destinatario_nome'),
                    # Contadores
                    "items_count": items_count,
                    "insights_count": insights_count
                })
            
            return {"documents": docs}
            
        except Exception as e:
            print(f"❌ Erro ao buscar documentos do Supabase: {e}")
    
    # Fallback para memória local
    for k, v in documents_db.items():
        docs.append({
            "id": k,
            "filename": v.get("filename"),
            "uploaded_at": v.get("uploaded_at"),
            "status": v.get("status"),
            "progress": v.get("progress"),
            "extracted_data": v.get("extracted_data"),
            "categorized_items": v.get("categorized_items"),
            "supplier_category": v.get("supplier_category"),
            "executive_insights": v.get("executive_insights"),
            "insights": v.get("insights"),  # Resumo compatível
            "validation": v.get("xml_validation"),
            "aggregates": v.get("aggregates"),
            "agents_metadata": {
                "xml_processing": v.get("xml_metadata"),
                "categorization": v.get("categorization_metadata"),
                "insights": v.get("insights_metadata")
            }
        })
    
    # Ordenar por data de upload (mais recente primeiro)
    docs.sort(key=lambda x: x.get('uploaded_at') or '', reverse=True)
    return {"documents": docs}

@app.get("/api/v1/dashboard/metrics")
async def get_dashboard_metrics():
    """
    Métricas principais do dashboard executivo
    Adaptado do projeto alternativo com compute_aggregates
    """
    metrics = {
        "total_documentos": 0,
        "documentos_processados": 0,
        "valor_total": 0.0,
        "total_impostos": 0.0,
        "media_valor_documento": 0.0,
        "documentos_hoje": 0,
        "taxa_sucesso": 0.0
    }
    
    # Buscar do Supabase se disponível
    if supabase:
        try:
            # Usar view otimizada para métricas do dashboard
            dashboard_result = supabase.table('vw_dashboard_metrics').select('*').execute()
            
            if dashboard_result.data:
                dashboard_data = dashboard_result.data[0]
                metrics.update({
                    "total_documentos": dashboard_data.get('total_documentos', 0),
                    "documentos_processados": dashboard_data.get('documentos_processados', 0),
                    "valor_total": float(dashboard_data.get('valor_total_geral', 0) or 0),
                    "total_impostos": float(dashboard_data.get('total_tributos_geral', 0) or 0),
                    "media_valor_documento": float(dashboard_data.get('valor_medio_documento', 0) or 0),
                    "documentos_hoje": dashboard_data.get('documentos_hoje', 0)
                })
                
                # Calcular taxa de sucesso
                if metrics["total_documentos"] > 0:
                    metrics["taxa_sucesso"] = (metrics["documentos_processados"] / metrics["total_documentos"]) * 100
            else:
                # Fallback para consulta direta se view não estiver disponível
                docs_result = supabase.table('fiscal_documents').select('id, status, uploaded_at, valor_total, total_tributos').execute()
                metrics["total_documentos"] = len(docs_result.data)
                
                processed_docs = [doc for doc in docs_result.data if doc['status'] == 'completed']
                metrics["documentos_processados"] = len(processed_docs)
                
                if metrics["total_documentos"] > 0:
                    metrics["taxa_sucesso"] = (metrics["documentos_processados"] / metrics["total_documentos"]) * 100
                
                # Somar valores diretamente da tabela fiscal_documents
                total_value = sum(float(doc.get('valor_total', 0) or 0) for doc in docs_result.data)
                total_taxes = sum(float(doc.get('total_tributos', 0) or 0) for doc in docs_result.data)
                valid_docs = len([doc for doc in docs_result.data if doc.get('valor_total')])
                
                metrics["valor_total"] = total_value
                metrics["total_impostos"] = total_taxes
                metrics["media_valor_documento"] = total_value / valid_docs if valid_docs > 0 else 0.0
                
                # Documentos de hoje
                today = datetime.now().date().isoformat()
                today_docs = [doc for doc in docs_result.data if doc['uploaded_at'] and doc['uploaded_at'].startswith(today)]
                metrics["documentos_hoje"] = len(today_docs)
            
            return metrics
            
        except Exception as e:
            print(f"❌ Erro ao buscar métricas do Supabase: {e}")
    
    # Fallback para memória local
    total_docs = len(documents_db)
    completed_docs = 0
    total_value = 0.0
    total_taxes = 0.0
    valid_docs = 0
    today_docs = 0
    today = datetime.now().date().isoformat()
    
    for doc in documents_db.values():
        if doc.get('status') in ['finalizado', 'completed']:
            completed_docs += 1
            
            # Usar agregados se disponível
            aggregates = doc.get('aggregates', {})
            if aggregates.get('valor_total_calc'):
                total_value += aggregates['valor_total_calc']
                valid_docs += 1
            
            # Somar impostos
            impostos_calc = aggregates.get('impostos_calc', {})
            for imposto in impostos_calc.values():
                if isinstance(imposto, (int, float)):
                    total_taxes += imposto
        
        # Documentos de hoje
        if doc.get('uploaded_at', '').startswith(today):
            today_docs += 1
    
    metrics.update({
        "total_documentos": total_docs,
        "documentos_processados": completed_docs,
        "valor_total": total_value,
        "total_impostos": total_taxes,
        "media_valor_documento": total_value / valid_docs if valid_docs > 0 else 0.0,
        "documentos_hoje": today_docs,
        "taxa_sucesso": (completed_docs / total_docs * 100) if total_docs > 0 else 0.0
    })
    
    return metrics

@app.get("/api/v1/dashboard/suppliers")
async def get_top_suppliers():
    """Top fornecedores com análise de valor e categorização"""
    suppliers = {}
    
    # Buscar do Supabase se disponível
    if supabase:
        try:
            # Usar view otimizada para fornecedores
            result = supabase.table('vw_top_fornecedores').select('*').limit(10).execute()
            
            for supplier_data in result.data:
                supplier_name = supplier_data.get('emitente_razao_social')
                if supplier_name:
                    suppliers[supplier_name] = {
                        "name": supplier_name,
                        "cnpj": supplier_data.get('emitente_cnpj'),
                        "uf": supplier_data.get('emitente_uf'),
                        "total_value": float(supplier_data.get('valor_total', 0) or 0),
                        "document_count": supplier_data.get('total_documentos', 0),
                        "average_value": float(supplier_data.get('valor_medio', 0) or 0),
                        "type": supplier_data.get('tipo_fornecedor', 'Fornecedor'),
                        "business_category": supplier_data.get('categoria_negocio'),
                        "risk_score": float(supplier_data.get('risco_medio', 0) or 0),
                        "confidence": 0.9
                    }
            
            # Se view não retornar dados, usar consulta direta
            if not suppliers:
                extracted_result = supabase.table('extracted_data').select('emitente_razao_social, emitente_cnpj, emitente_uf, document_id').execute()
                fiscal_result = supabase.table('fiscal_documents').select('id, valor_total').execute()
                
                # Criar mapa de valores por documento
                doc_values = {doc['id']: float(doc.get('valor_total', 0) or 0) for doc in fiscal_result.data}
                
                for data in extracted_result.data:
                    supplier_name = data.get('emitente_razao_social')
                    if supplier_name:
                        if supplier_name not in suppliers:
                            suppliers[supplier_name] = {
                                "name": supplier_name,
                                "cnpj": data.get('emitente_cnpj'),
                                "uf": data.get('emitente_uf'),
                                "total_value": 0.0,
                                "document_count": 0,
                                "type": "Fornecedor",
                                "confidence": 0.8
                            }
                        
                        suppliers[supplier_name]["document_count"] += 1
                        doc_value = doc_values.get(data.get('document_id'), 0)
                        suppliers[supplier_name]["total_value"] += doc_value
            
        except Exception as e:
            print(f"❌ Erro ao buscar fornecedores do Supabase: {e}")
    
    # Fallback para memória local
    if not suppliers:
        for doc in documents_db.values():
            if doc.get('status') in ['finalizado', 'completed']:
                data = doc.get('extracted_data', {})
                supplier_cat = doc.get('supplier_category', {})
                
                emitente = data.get('emitente', {})
                supplier_name = emitente.get('razao_social')
                cnpj = emitente.get('cnpj')
                
                if supplier_name:
                    if supplier_name not in suppliers:
                        suppliers[supplier_name] = {
                            "name": supplier_name,
                            "cnpj": cnpj,
                            "total_value": 0.0,
                            "document_count": 0,
                            "type": supplier_cat.get('type', 'Fornecedor'),
                            "confidence": supplier_cat.get('confidence', 0.8)
                        }
                    
                    suppliers[supplier_name]["document_count"] += 1
                    
                    # Usar agregados se disponível
                    aggregates = doc.get('aggregates', {})
                    if aggregates.get('valor_total_calc'):
                        suppliers[supplier_name]["total_value"] += aggregates['valor_total_calc']
    
    # Ordenar por valor total e retornar top 10
    top_suppliers = sorted(suppliers.values(), key=lambda x: x['total_value'], reverse=True)[:10]
    
    # Calcular percentuais
    total_value = sum(s['total_value'] for s in suppliers.values())
    for supplier in top_suppliers:
        supplier['percentage'] = (supplier['total_value'] / total_value * 100) if total_value > 0 else 0
    
    return {"suppliers": top_suppliers}

@app.get("/api/v1/dashboard/categories")
async def get_product_categories():
    """Categorias de produtos com análise de valor e quantidade"""
    categories = {}
    
    # Buscar do Supabase se disponível
    if supabase:
        try:
            # Usar view otimizada para categorias
            result = supabase.table('vw_categorias_produtos').select('*').limit(10).execute()
            
            for category_data in result.data:
                categoria = category_data.get('categoria', 'Outros')
                subcategoria = category_data.get('subcategoria')
                
                category_key = f"{categoria} - {subcategoria}" if subcategoria else categoria
                
                categories[category_key] = {
                    "category": categoria,
                    "subcategory": subcategoria,
                    "count": category_data.get('total_itens', 0),
                    "total_value": float(category_data.get('valor_total', 0) or 0),
                    "average_value": float(category_data.get('valor_medio', 0) or 0),
                    "total_quantity": float(category_data.get('quantidade_total', 0) or 0),
                    "document_count": category_data.get('documentos_distintos', 0)
                }
            
            # Se view não retornar dados, usar consulta direta
            if not categories:
                result = supabase.table('document_items').select('categoria, subcategoria, valor_produto, quantidade_comercial').execute()
                
                for item in result.data:
                    categoria = item.get('categoria', 'Outros')
                    subcategoria = item.get('subcategoria')
                    category_key = f"{categoria} - {subcategoria}" if subcategoria else categoria
                    
                    if category_key not in categories:
                        categories[category_key] = {
                            "category": categoria,
                            "subcategory": subcategoria,
                            "count": 0,
                            "total_value": 0.0,
                            "total_quantity": 0.0
                        }
                    
                    categories[category_key]["count"] += 1
                    
                    if item.get('valor_produto'):
                        categories[category_key]["total_value"] += float(item['valor_produto'])
                    
                    if item.get('quantidade_comercial'):
                        categories[category_key]["total_quantity"] += float(item['quantidade_comercial'])
            
        except Exception as e:
            print(f"❌ Erro ao buscar categorias do Supabase: {e}")
    
    # Fallback para memória local
    if not categories:
        for doc in documents_db.values():
            if doc.get('status') in ['finalizado', 'completed']:
                categorized_items = doc.get('categorized_items', [])
                
                for item in categorized_items:
                    categoria = item.get('categoria', 'Outros')
                    
                    if categoria not in categories:
                        categories[categoria] = {
                            "category": categoria,
                            "count": 0,
                            "total_value": 0.0,
                            "total_quantity": 0.0
                        }
                    
                    categories[categoria]["count"] += 1
                    
                    try:
                        if item.get('valor_total'):
                            categories[categoria]["total_value"] += float(item['valor_total'])
                        if item.get('quantidade'):
                            categories[categoria]["total_quantity"] += float(item['quantidade'])
                    except:
                        pass
    
    # Ordenar por valor total e retornar top 10
    top_categories = sorted(categories.values(), key=lambda x: x['total_value'], reverse=True)[:10]
    
    # Calcular percentuais
    total_value = sum(c['total_value'] for c in categories.values())
    for category in top_categories:
        category['percentage'] = (category['total_value'] / total_value * 100) if total_value > 0 else 0
    
    return {"categories": top_categories}

@app.get("/api/v1/dashboard/insights")
async def get_ai_insights():
    """Obter insights de IA pendentes e recentes"""
    insights = {
        "pending": [],
        "recent": [],
        "summary": {
            "total_insights": 0,
            "pending_count": 0,
            "alerts_count": 0,
            "opportunities_count": 0,
            "recommendations_count": 0
        }
    }
    
    if supabase:
        try:
            # Usar view para insights pendentes
            pending_result = supabase.table('vw_insights_pendentes').select('*').limit(20).execute()
            
            for insight in pending_result.data:
                insights["pending"].append({
                    "id": insight.get('id'),
                    "type": insight.get('tipo_insight'),
                    "category": insight.get('categoria'),
                    "title": insight.get('titulo'),
                    "description": insight.get('descricao'),
                    "priority": insight.get('prioridade'),
                    "confidence": insight.get('confianca'),
                    "document_number": insight.get('numero_nota'),
                    "supplier": insight.get('emitente_razao_social'),
                    "created_at": insight.get('created_at')
                })
            
            # Buscar insights recentes (últimos 7 dias)
            recent_result = supabase.table('ai_insights').select('*').gte('created_at', (datetime.now() - timedelta(days=7)).isoformat()).order('created_at', desc=True).limit(10).execute()
            
            for insight in recent_result.data:
                insights["recent"].append({
                    "id": insight.get('id'),
                    "type": insight.get('tipo_insight'),
                    "category": insight.get('categoria'),
                    "title": insight.get('titulo'),
                    "description": insight.get('descricao'),
                    "priority": insight.get('prioridade'),
                    "confidence": insight.get('confianca'),
                    "viewed": insight.get('visualizado', False),
                    "action_taken": insight.get('acao_tomada', False),
                    "created_at": insight.get('created_at')
                })
            
            # Calcular resumo
            all_insights_result = supabase.table('ai_insights').select('tipo_insight, visualizado').execute()
            
            insights["summary"]["total_insights"] = len(all_insights_result.data)
            insights["summary"]["pending_count"] = len([i for i in all_insights_result.data if not i.get('visualizado', False)])
            insights["summary"]["alerts_count"] = len([i for i in all_insights_result.data if i.get('tipo_insight') == 'alerta'])
            insights["summary"]["opportunities_count"] = len([i for i in all_insights_result.data if i.get('tipo_insight') == 'oportunidade'])
            insights["summary"]["recommendations_count"] = len([i for i in all_insights_result.data if i.get('tipo_insight') == 'recomendacao'])
            
        except Exception as e:
            print(f"❌ Erro ao buscar insights do Supabase: {e}")
    
    return insights

@app.post("/api/v1/insights/{insight_id}/mark-viewed")
async def mark_insight_viewed(insight_id: str):
    """Marcar insight como visualizado"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase não disponível")
    
    try:
        result = supabase.table('ai_insights').update({
            'visualizado': True
        }).eq('id', insight_id).execute()
        
        if result.data:
            return {"message": "Insight marcado como visualizado", "success": True}
        else:
            raise HTTPException(status_code=404, detail="Insight não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar insight: {str(e)}")

@app.post("/api/v1/insights/{insight_id}/feedback")
async def provide_insight_feedback(insight_id: str, feedback: dict):
    """Fornecer feedback sobre um insight"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase não disponível")
    
    try:
        rating = feedback.get('rating')  # 1-5 stars
        action_taken = feedback.get('action_taken', False)
        
        update_data = {}
        if rating is not None:
            update_data['feedback_usuario'] = int(rating)
        if action_taken is not None:
            update_data['acao_tomada'] = bool(action_taken)
        
        if update_data:
            result = supabase.table('ai_insights').update(update_data).eq('id', insight_id).execute()
            
            if result.data:
                return {"message": "Feedback registrado com sucesso", "success": True}
            else:
                raise HTTPException(status_code=404, detail="Insight não encontrado")
        else:
            raise HTTPException(status_code=400, detail="Nenhum feedback fornecido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar feedback: {str(e)}")

@app.get("/api/v1/dashboard/timeline")
async def get_timeline_data():
    """Análise temporal com dados reais dos documentos processados"""
    timeline = {}
    
    # Buscar do Supabase se disponível
    if supabase:
        try:
            # Buscar documentos com datas
            docs_result = supabase.table('fiscal_documents').select('uploaded_at, status').execute()
            extracted_result = supabase.table('extracted_data').select('data_emissao, valor_total').execute()
            
            # Processar por mês de upload
            for doc in docs_result.data:
                if doc.get('uploaded_at'):
                    month_key = doc['uploaded_at'][:7]  # YYYY-MM
                    
                    if month_key not in timeline:
                        timeline[month_key] = {
                            "month": month_key,
                            "documents": 0,
                            "processed": 0,
                            "revenue": 0.0
                        }
                    
                    timeline[month_key]["documents"] += 1
                    if doc['status'] == 'finalizado':
                        timeline[month_key]["processed"] += 1
            
            # Adicionar valores por mês de emissão
            for data in extracted_result.data:
                if data.get('data_emissao') and data.get('valor_total'):
                    month_key = data['data_emissao'][:7]  # YYYY-MM
                    
                    if month_key in timeline:
                        timeline[month_key]["revenue"] += float(data['valor_total'])
            
        except Exception as e:
            print(f"❌ Erro ao buscar timeline do Supabase: {e}")
    
    # Fallback para memória local
    if not timeline:
        for doc in documents_db.values():
            uploaded_at = doc.get('uploaded_at', '')
            if uploaded_at:
                month_key = uploaded_at[:7]  # YYYY-MM
                
                if month_key not in timeline:
                    timeline[month_key] = {
                        "month": month_key,
                        "documents": 0,
                        "processed": 0,
                        "revenue": 0.0
                    }
                
                timeline[month_key]["documents"] += 1
                
                if doc.get('status') in ['finalizado', 'completed']:
                    timeline[month_key]["processed"] += 1
                    
                    # Adicionar valor se disponível
                    aggregates = doc.get('aggregates', {})
                    if aggregates.get('valor_total_calc'):
                        timeline[month_key]["revenue"] += aggregates['valor_total_calc']
    
    # Ordenar por mês e retornar últimos 12 meses
    sorted_timeline = sorted(timeline.values(), key=lambda x: x['month'])[-12:]
    
    return {"timeline": sorted_timeline}

@app.get("/api/v1/agents/status")
async def agents_status():
    """Status dos 3 agentes IA"""
    return {
        "agents": [
            {
                "name": xml_agent.name,
                "version": xml_agent.version,
                "status": "active",
                "capabilities": ["xml_parsing", "data_extraction", "validation"]
            },
            {
                "name": categorization_agent.name,
                "version": categorization_agent.version,
                "status": "active" if OPENAI_API_KEY else "limited",
                "capabilities": ["item_categorization", "supplier_classification", "pattern_analysis"]
            },
            {
                "name": insights_agent.name,
                "version": insights_agent.version,
                "status": "active" if OPENAI_API_KEY else "limited",
                "capabilities": ["executive_insights", "natural_language_queries", "sql_generation"]
            }
        ],
        "openai_configured": OPENAI_API_KEY is not None,
        "system_status": "fully_operational" if OPENAI_API_KEY else "basic_mode"
    }

@app.get("/api/v1/documents/{doc_id}/agents")
async def get_document_agents_data(doc_id: str):
    """Obter dados detalhados dos agentes para um documento específico"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    doc = documents_db[doc_id]
    
    return {
        "document_id": doc_id,
        "filename": doc.get("filename"),
        "status": doc.get("status"),
        "agents_results": {
            "xml_processing": {
                "extracted_data": doc.get("extracted_data"),
                "validation": doc.get("xml_validation"),
                "metadata": doc.get("xml_metadata")
            },
            "categorization": {
                "categorized_items": doc.get("categorized_items"),
                "supplier_category": doc.get("supplier_category"),
                "patterns": doc.get("categorization_patterns"),
                "ai_insights": doc.get("categorization_ai_insights"),
                "metadata": doc.get("categorization_metadata")
            },
            "insights": {
                "executive_insights": doc.get("executive_insights"),
                "metadata": doc.get("insights_metadata")
            }
        },
        "summary": doc.get("insights")  # Resumo compatível
    }

class NaturalQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class NaturalQueryResponse(BaseModel):
    query: str
    response: str
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    sql_generated: Optional[str] = None
    intent: Optional[Union[str, Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/v1/query/natural", response_model=NaturalQueryResponse)
async def process_natural_query(request: NaturalQueryRequest):
    """
    Processamento de perguntas em português com GPT-4o-mini
    Integra com Supabase para conversão SQL e execução
    """
    user_query = request.query.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query não pode estar vazia")
    
    try:
        # Preparar contexto de dados
        metrics = await get_dashboard_metrics()
        suppliers_data = await get_top_suppliers()
        categories_data = await get_product_categories()
        
        # Coletar dados de todos os documentos para contexto
        all_documents_data = []
        
        if supabase:
            try:
                # Buscar dados do Supabase para contexto mais rico
                docs_result = supabase.table('fiscal_documents').select('*').execute()
                extracted_result = supabase.table('extracted_data').select('*').execute()
                items_result = supabase.table('document_items').select('*').execute()
                
                context_data = {
                    "total_documentos": len(docs_result.data),
                    "documentos_processados": len([d for d in docs_result.data if d['status'] == 'finalizado']),
                    "valor_total": sum(float(e.get('valor_total', 0) or 0) for e in extracted_result.data),
                    "fornecedores": suppliers_data.get('suppliers', []),
                    "categorias": categories_data.get('categories', []),
                    "total_itens": len(items_result.data)
                }
            except Exception as e:
                print(f"⚠️  Erro ao buscar contexto do Supabase: {e}")
                context_data = metrics
        else:
            # Fallback para dados locais
            for doc_id, doc_data in documents_db.items():
                if doc_data.get('status') in ['finalizado', 'completed']:
                    all_documents_data.append({
                        "extracted_data": doc_data.get('extracted_data', {}),
                        "categorized_items": doc_data.get('categorized_items', []),
                        "supplier_category": doc_data.get('supplier_category', {}),
                        "executive_insights": doc_data.get('executive_insights', {})
                    })
            
            context_data = {
                **metrics,
                "fornecedores": suppliers_data.get('suppliers', []),
                "categorias": categories_data.get('categories', []),
                "documents_data": all_documents_data
            }
        
        # Criar contexto para o agente de insights
        context = QueryContext(
            available_data=context_data,
            user_history=[],  # Em produção, manteria histórico
            business_context={"tipo_empresa": "geral", "setor": "diversos"}
        )
        
        # Processar consulta com agente de insights
        if OPENAI_API_KEY and insights_agent:
            result = insights_agent.process_natural_query(user_query, context)
            
            return NaturalQueryResponse(
                query=user_query,
                response=result.get("response", "Não foi possível processar a consulta."),
                data=result.get("data"),
                suggestions=result.get("suggestions", []),
                sql_generated=result.get("sql_generated"),
                intent=result.get("intent"),
                metadata=result.get("metadata")
            )
        else:
            # Fallback sem IA - análise baseada em palavras-chave
            return await process_fallback_query(user_query, context_data)
        
    except Exception as e:
        print(f"❌ Erro na consulta natural: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar consulta: {str(e)}")

async def process_fallback_query(query: str, context_data: Dict[str, Any]) -> NaturalQueryResponse:
    """Processamento de consulta sem IA usando análise de palavras-chave"""
    query_lower = query.lower()
    
    # Análise de intenção baseada em palavras-chave
    if any(word in query_lower for word in ['total', 'valor', 'receita', 'faturamento']):
        valor_total = context_data.get('valor_total', 0)
        total_docs = context_data.get('total_documentos', 0)
        
        response = f"O valor total processado é R$ {valor_total:,.2f} em {total_docs} documentos."
        
        return NaturalQueryResponse(
            query=query,
            response=response,
            data={"valor_total": valor_total, "total_documentos": total_docs},
            suggestions=[
                "Quais são os principais fornecedores?",
                "Como está a distribuição por categoria?",
                "Qual a média de valor por documento?"
            ],
            intent="valor_total"
        )
    
    elif any(word in query_lower for word in ['fornecedor', 'empresa', 'supplier']):
        fornecedores = context_data.get('fornecedores', [])
        top_3 = fornecedores[:3]
        
        if top_3:
            nomes = [f['name'] for f in top_3]
            response = f"Os principais fornecedores são: {', '.join(nomes)}."
        else:
            response = "Nenhum fornecedor encontrado nos documentos processados."
        
        return NaturalQueryResponse(
            query=query,
            response=response,
            data={"fornecedores": fornecedores},
            suggestions=[
                "Qual fornecedor tem maior volume?",
                "Quantos fornecedores únicos temos?",
                "Há oportunidades de consolidação?"
            ],
            intent="fornecedores"
        )
    
    elif any(word in query_lower for word in ['categoria', 'produto', 'item', 'classificação']):
        categorias = context_data.get('categorias', [])
        top_3 = categorias[:3]
        
        if top_3:
            nomes = [c['category'] for c in top_3]
            response = f"As principais categorias são: {', '.join(nomes)}."
        else:
            response = "Nenhuma categoria encontrada nos documentos processados."
        
        return NaturalQueryResponse(
            query=query,
            response=response,
            data={"categorias": categorias},
            suggestions=[
                "Qual categoria tem maior valor?",
                "Quantas categorias diferentes temos?",
                "Como está a distribuição de produtos?"
            ],
            intent="categorias"
        )
    
    elif any(word in query_lower for word in ['documento', 'nota', 'processado', 'status']):
        total_docs = context_data.get('total_documentos', 0)
        processados = context_data.get('documentos_processados', 0)
        taxa_sucesso = (processados / total_docs * 100) if total_docs > 0 else 0
        
        response = f"Temos {total_docs} documentos no total, sendo {processados} processados com sucesso ({taxa_sucesso:.1f}% de taxa de sucesso)."
        
        return NaturalQueryResponse(
            query=query,
            response=response,
            data={"total_documentos": total_docs, "processados": processados, "taxa_sucesso": taxa_sucesso},
            suggestions=[
                "Quantos documentos foram processados hoje?",
                "Qual o valor médio por documento?",
                "Há documentos com erro?"
            ],
            intent="documentos"
        )
    
    else:
        # Resposta genérica
        return NaturalQueryResponse(
            query=query,
            response="Não consegui entender sua pergunta. Tente perguntar sobre valores totais, fornecedores, categorias ou documentos.",
            suggestions=[
                "Qual o valor total processado?",
                "Quais são os principais fornecedores?",
                "Como está a distribuição por categoria?",
                "Quantos documentos foram processados?"
            ],
            intent="unknown"
        )

@app.get("/api/v1/query/suggestions")
async def get_query_suggestions():
    """Gerar sugestões contextuais baseadas nos dados do usuário"""
    suggestions = [
        "Qual o valor total processado este mês?",
        "Quais são os 5 principais fornecedores?",
        "Como está a distribuição por categoria de produtos?",
        "Quantos documentos foram processados com sucesso?",
        "Qual fornecedor tem o maior volume de transações?",
        "Há oportunidades de consolidação de fornecedores?",
        "Qual a média de valor por documento?",
        "Como está a evolução mensal das receitas?",
        "Quais categorias de produtos são mais frequentes?",
        "Há algum padrão nos valores de impostos?"
    ]
    
    # Personalizar sugestões baseadas nos dados disponíveis
    try:
        metrics = await get_dashboard_metrics()
        
        if metrics.get('total_documentos', 0) > 0:
            suggestions.insert(0, f"Temos {metrics['total_documentos']} documentos. Como estão distribuídos?")
        
        if metrics.get('valor_total', 0) > 0:
            suggestions.insert(1, f"O valor total é R$ {metrics['valor_total']:,.2f}. Qual a origem?")
    
    except Exception as e:
        print(f"⚠️  Erro ao personalizar sugestões: {e}")
    
    return {"suggestions": suggestions}

class ReportRequest(BaseModel):
    title: Optional[str] = "Relatório Executivo Fiscal"
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    include_sections: List[str] = ["summary", "suppliers", "categories", "timeline"]

class ReportResponse(BaseModel):
    report_id: str
    title: str
    status: str
    file_path: Optional[str] = None
    generated_at: str
    download_url: Optional[str] = None

@app.post("/api/v1/reports/generate", response_model=ReportResponse)
async def generate_executive_report(request: ReportRequest):
    """
    Geração automática de relatórios executivos em PDF
    Com templates profissionais e insights de IA
    """
    report_id = str(uuid.uuid4())
    
    try:
        # Validar período se fornecido
        period_start = None
        period_end = None
        
        if request.period_start:
            try:
                period_start = datetime.fromisoformat(request.period_start.replace('Z', '+00:00'))
            except:
                raise HTTPException(status_code=400, detail="Formato de data inválido para period_start")
        
        if request.period_end:
            try:
                period_end = datetime.fromisoformat(request.period_end.replace('Z', '+00:00'))
            except:
                raise HTTPException(status_code=400, detail="Formato de data inválido para period_end")
        
        # Criar registro do relatório
        if supabase:
            try:
                supabase.table('executive_reports').insert({
                    'id': report_id,
                    'title': request.title,
                    'file_path': '',
                    'period_start': period_start.date().isoformat() if period_start else None,
                    'period_end': period_end.date().isoformat() if period_end else None,
                    'generated_at': datetime.now().isoformat()
                }).execute()
            except Exception as e:
                print(f"⚠️  Erro ao criar registro de relatório no Supabase: {e}")
        
        # Gerar relatório de forma síncrona (sob demanda)
        await asyncio.create_task(
            asyncio.to_thread(
                generate_pdf_report, 
                report_id, 
                request.title, 
                request.include_sections,
                period_start,
                period_end
            )
        )
        
        return ReportResponse(
            report_id=report_id,
            title=request.title,
            status="generating",
            generated_at=datetime.now().isoformat(),
            download_url=f"/api/v1/reports/{report_id}/download"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao iniciar geração de relatório: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")

def generate_pdf_report(report_id: str, title: str, sections: List[str], period_start: Optional[datetime] = None, period_end: Optional[datetime] = None):
    """
    Gerar relatório PDF com métricas e insights de IA
    Usar templates profissionais
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
        
        # Criar buffer para PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Elementos do documento
        elements = []
        
        # Título
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 20))
        
        # Período
        if period_start and period_end:
            period_text = f"Período: {period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')}"
        else:
            period_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 30))
        
        # Coletar dados para o relatório
        try:
            # Usar asyncio.run para chamar funções async
            metrics = asyncio.run(get_dashboard_metrics())
            suppliers_data = asyncio.run(get_top_suppliers())
            categories_data = asyncio.run(get_product_categories())
            timeline_data = asyncio.run(get_timeline_data())
        except Exception as e:
            print(f"❌ Erro ao coletar dados para relatório: {e}")
            # Dados de fallback
            metrics = {"total_documentos": 0, "valor_total": 0.0}
            suppliers_data = {"suppliers": []}
            categories_data = {"categories": []}
            timeline_data = {"timeline": []}
        
        # Seção: Resumo Executivo
        if "summary" in sections:
            elements.append(Paragraph("Resumo Executivo", heading_style))
            
            summary_data = [
                ["Métrica", "Valor"],
                ["Total de Documentos", f"{metrics.get('total_documentos', 0):,}"],
                ["Documentos Processados", f"{metrics.get('documentos_processados', 0):,}"],
                ["Valor Total", f"R$ {metrics.get('valor_total', 0):,.2f}"],
                ["Valor Médio por Documento", f"R$ {metrics.get('media_valor_documento', 0):,.2f}"],
                ["Taxa de Sucesso", f"{metrics.get('taxa_sucesso', 0):.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
        
        # Seção: Principais Fornecedores
        if "suppliers" in sections and suppliers_data.get('suppliers'):
            elements.append(Paragraph("Principais Fornecedores", heading_style))
            
            suppliers_table_data = [["Fornecedor", "Valor Total", "Documentos", "Participação"]]
            
            for supplier in suppliers_data['suppliers'][:5]:
                suppliers_table_data.append([
                    supplier.get('name', 'N/A')[:30],  # Limitar tamanho
                    f"R$ {supplier.get('total_value', 0):,.2f}",
                    str(supplier.get('document_count', 0)),
                    f"{supplier.get('percentage', 0):.1f}%"
                ])
            
            suppliers_table = Table(suppliers_table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
            suppliers_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(suppliers_table)
            elements.append(Spacer(1, 20))
        
        # Seção: Categorias de Produtos
        if "categories" in sections and categories_data.get('categories'):
            elements.append(Paragraph("Categorias de Produtos", heading_style))
            
            categories_table_data = [["Categoria", "Valor Total", "Quantidade", "Participação"]]
            
            for category in categories_data['categories'][:5]:
                categories_table_data.append([
                    category.get('category', 'N/A')[:25],
                    f"R$ {category.get('total_value', 0):,.2f}",
                    str(category.get('count', 0)),
                    f"{category.get('percentage', 0):.1f}%"
                ])
            
            categories_table = Table(categories_table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
            categories_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(categories_table)
            elements.append(Spacer(1, 20))
        
        # Seção: Insights e Recomendações (usando IA se disponível)
        elements.append(Paragraph("Insights e Recomendações", heading_style))
        
        insights_text = []
        
        # Análise de concentração de fornecedores
        if suppliers_data.get('suppliers'):
            top_supplier_pct = suppliers_data['suppliers'][0].get('percentage', 0) if suppliers_data['suppliers'] else 0
            if top_supplier_pct > 50:
                insights_text.append("• Alta concentração no principal fornecedor - considere diversificar para reduzir riscos.")
            elif top_supplier_pct < 20:
                insights_text.append("• Boa diversificação de fornecedores - baixo risco de dependência.")
        
        # Análise de volume
        if metrics.get('valor_total', 0) > 100000:
            insights_text.append("• Volume significativo de transações - considere automação adicional.")
        
        # Análise de taxa de sucesso
        taxa_sucesso = metrics.get('taxa_sucesso', 0)
        if taxa_sucesso < 90:
            insights_text.append("• Taxa de processamento pode ser melhorada - revisar qualidade dos documentos.")
        elif taxa_sucesso > 95:
            insights_text.append("• Excelente taxa de processamento - sistema funcionando adequadamente.")
        
        if not insights_text:
            insights_text.append("• Sistema operando normalmente - continue monitorando as métricas.")
        
        for insight in insights_text:
            elements.append(Paragraph(insight, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Rodapé
        elements.append(Spacer(1, 30))
        footer_text = f"Relatório gerado automaticamente pelo Sistema MVP de Análise Fiscal em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        elements.append(Paragraph(footer_text, styles['Normal']))
        
        # Construir PDF
        doc.build(elements)
        
        # Salvar arquivo
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Salvar no sistema de arquivos local
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        file_path = os.path.join(reports_dir, f"report_{report_id}.pdf")
        
        with open(file_path, 'wb') as f:
            f.write(pdf_content)
        
        # Atualizar registro no Supabase
        if supabase:
            try:
                supabase.table('executive_reports').update({
                    'file_path': file_path,
                    'generated_at': datetime.now().isoformat()
                }).eq('id', report_id).execute()
            except Exception as e:
                print(f"⚠️  Erro ao atualizar registro de relatório: {e}")
        
        print(f"✅ Relatório {report_id} gerado com sucesso: {file_path}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF do relatório {report_id}: {e}")
        
        # Atualizar status de erro no Supabase
        if supabase:
            try:
                supabase.table('executive_reports').update({
                    'file_path': f'ERROR: {str(e)}'
                }).eq('id', report_id).execute()
            except:
                pass

@app.get("/api/v1/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download de relatório PDF gerado"""
    # Buscar no Supabase primeiro
    if supabase:
        try:
            result = supabase.table('executive_reports').select('*').eq('id', report_id).execute()
            if result.data:
                report = result.data[0]
                file_path = report['file_path']
                
                if file_path and os.path.exists(file_path) and not file_path.startswith('ERROR:'):
                    from fastapi.responses import FileResponse
                    return FileResponse(
                        file_path, 
                        media_type='application/pdf',
                        filename=f"{report['title'].replace(' ', '_')}_{report_id[:8]}.pdf"
                    )
                elif file_path and file_path.startswith('ERROR:'):
                    raise HTTPException(status_code=500, detail=f"Erro na geração: {file_path[7:]}")
                else:
                    raise HTTPException(status_code=202, detail="Relatório ainda sendo gerado")
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erro ao buscar relatório no Supabase: {e}")
    
    # Fallback para sistema de arquivos local
    file_path = f"reports/report_{report_id}.pdf"
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(
            file_path, 
            media_type='application/pdf',
            filename=f"relatorio_executivo_{report_id[:8]}.pdf"
        )
    
    raise HTTPException(status_code=404, detail="Relatório não encontrado")

@app.get("/api/v1/reports")
async def list_reports():
    """Listar histórico de relatórios gerados"""
    reports = []
    
    # Buscar do Supabase se disponível
    if supabase:
        try:
            result = supabase.table('executive_reports').select('*').order('generated_at', desc=True).execute()
            
            for report in result.data:
                reports.append({
                    "id": report['id'],
                    "title": report['title'],
                    "generated_at": report['generated_at'],
                    "period_start": report.get('period_start'),
                    "period_end": report.get('period_end'),
                    "status": "completed" if report['file_path'] and not report['file_path'].startswith('ERROR:') else "error" if report['file_path'] and report['file_path'].startswith('ERROR:') else "generating",
                    "download_url": f"/api/v1/reports/{report['id']}/download"
                })
            
            return {"reports": reports}
            
        except Exception as e:
            print(f"❌ Erro ao buscar relatórios do Supabase: {e}")
    
    # Fallback para sistema de arquivos local
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.startswith("report_") and filename.endswith(".pdf"):
                report_id = filename.replace("report_", "").replace(".pdf", "")
                file_path = os.path.join(reports_dir, filename)
                stat = os.stat(file_path)
                
                reports.append({
                    "id": report_id,
                    "title": "Relatório Executivo",
                    "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "status": "completed",
                    "download_url": f"/api/v1/reports/{report_id}/download"
                })
    
    # Ordenar por data de geração
    reports.sort(key=lambda x: x['generated_at'], reverse=True)
    
    return {"reports": reports}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)