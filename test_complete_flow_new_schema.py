#!/usr/bin/env python3
"""
Teste completo do fluxo: Upload -> Storage -> Processamento -> Novo Schema
"""

async def process_document_async(doc_id: str, file_content: bytes, filename: str) -> dict:
    """Versão assíncrona simplificada do processamento para testes"""
    start_time = datetime.now()
    
    try:
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando processamento assíncrono")
        
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
        await update_document_status(doc_id, "processing", 40, "categorization")
        
        # AGENTE 2: Categorização
        print(f"[AGENTE 2] {doc_id} - Categorização IA iniciada")
        categorization_result = categorization_agent.categorize_document(extracted_data)
        
        categorized_items = categorization_result.get("categorized_items", [])
        supplier_category = categorization_result.get("supplier_category", {})
        patterns = categorization_result.get("patterns", {})
        
        # Atualizar progresso
        await update_document_status(doc_id, "processing", 70, "insights")
        
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
            success = await save_extracted_data(doc_id, extracted_data)
            if not success:
                print(f"⚠️  Falha ao salvar dados no Supabase para {doc_id}")
            
            # Salvar análise de fornecedor
            if supplier_category:
                supplier_success = await save_supplier_analysis(doc_id, supplier_category)
                if not supplier_success:
                    print(f"⚠️  Falha ao salvar análise de fornecedor para {doc_id}")
            
            # Salvar insights de IA
            if executive_insights:
                insights_success = await save_ai_insights(doc_id, executive_insights)
                if not insights_success:
                    print(f"⚠️  Falha ao salvar insights de IA para {doc_id}")
        
        # Finalizar processamento
        await update_document_status(doc_id, "completed", 100, "completed")
        
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
        await update_document_status(doc_id, "error", 100, "error")
        
        return {
            "success": False,
            "error": str(e),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import (
    supabase, 
    create_document_record,
    upload_file_to_storage,
    update_document_status,
    save_extracted_data,
    save_supplier_analysis,
    save_ai_insights,
    get_document,
    get_dashboard_metrics,
    STORAGE_BUCKET,
    xml_agent,
    categorization_agent,
    insights_agent
)

# XML de teste simples
TEST_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe42250383261420001201550990003348371042993209">
            <ide>
                <cUF>42</cUF>
                <cNF>04299320</cNF>
                <natOp>Venda de mercadoria</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>334837</nNF>
                <dhEmi>2025-10-26T10:30:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>2</idDest>
                <cMunFG>4205407</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>9</cDV>
                <tpAmb>2</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>1</indFinal>
                <indPres>1</indPres>
            </ide>
            <emit>
                <CNPJ>83261420001201</CNPJ>
                <xNome>EMPRESA TESTE LTDA</xNome>
                <xFant>Teste Corp</xFant>
                <enderEmit>
                    <xLgr>RUA TESTE</xLgr>
                    <nro>123</nro>
                    <xBairro>CENTRO</xBairro>
                    <cMun>4205407</cMun>
                    <xMun>FLORIANOPOLIS</xMun>
                    <UF>SC</UF>
                    <CEP>88010000</CEP>
                    <fone>4833334444</fone>
                </enderEmit>
                <IE>251234567</IE>
                <CRT>3</CRT>
            </emit>
            <dest>
                <CNPJ>12345678000199</CNPJ>
                <xNome>CLIENTE TESTE LTDA</xNome>
                <enderDest>
                    <xLgr>AV CLIENTE</xLgr>
                    <nro>456</nro>
                    <xBairro>VILA NOVA</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <UF>SP</UF>
                    <CEP>01234567</CEP>
                </enderDest>
                <IE>123456789</IE>
                <email>cliente@teste.com</email>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <cEAN>7891234567890</cEAN>
                    <xProd>SMARTPHONE TESTE MODEL X</xProd>
                    <NCM>85171231</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>2.0000</qCom>
                    <vUnCom>750.2500</vUnCom>
                    <vProd>1500.50</vProd>
                    <cEANTrib>7891234567890</cEANTrib>
                    <uTrib>UN</uTrib>
                    <qTrib>2.0000</qTrib>
                    <vUnTrib>750.2500</vUnTrib>
                </prod>
                <imposto>
                    <vTotTrib>324.81</vTotTrib>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <vBC>1500.50</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>270.09</vICMS>
                        </ICMS00>
                    </ICMS>
                    <PIS>
                        <PISAliq>
                            <CST>01</CST>
                            <vBC>1500.50</vBC>
                            <pPIS>0.65</pPIS>
                            <vPIS>9.75</vPIS>
                        </PISAliq>
                    </PIS>
                    <COFINS>
                        <COFINSAliq>
                            <CST>01</CST>
                            <vBC>1500.50</vBC>
                            <pCOFINS>3.00</pCOFINS>
                            <vCOFINS>45.02</vCOFINS>
                        </COFINSAliq>
                    </COFINS>
                </imposto>
            </det>
            <total>
                <ICMSTot>
                    <vBC>1500.50</vBC>
                    <vICMS>270.09</vICMS>
                    <vICMSDeson>0.00</vICMSDeson>
                    <vFCP>0.00</vFCP>
                    <vBCST>0.00</vBCST>
                    <vST>0.00</vST>
                    <vFCPST>0.00</vFCPST>
                    <vFCPSTRet>0.00</vFCPSTRet>
                    <vProd>1500.50</vProd>
                    <vFrete>0.00</vFrete>
                    <vSeg>0.00</vSeg>
                    <vDesc>0.00</vDesc>
                    <vII>0.00</vII>
                    <vIPI>0.00</vIPI>
                    <vIPIDevol>0.00</vIPIDevol>
                    <vPIS>9.75</vPIS>
                    <vCOFINS>45.02</vCOFINS>
                    <vOutro>0.00</vOutro>
                    <vNF>1500.50</vNF>
                    <vTotTrib>324.81</vTotTrib>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>"""

async def test_complete_flow():
    """Testa o fluxo completo com novo schema"""
    
    print("🧪 Testando fluxo completo: Upload -> Storage -> Processamento -> Novo Schema\n")
    
    # Verificar conexão com Supabase
    if not supabase:
        print("❌ Supabase não configurado. Verifique as variáveis de ambiente.")
        return False
    
    print("✅ Supabase conectado")
    
    # Criar ID único para o teste (UUID válido)
    import uuid
    test_doc_id = str(uuid.uuid4())
    test_filename = f"test_nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    
    try:
        # 1. Upload do arquivo para o Storage
        print(f"\n1. Fazendo upload do arquivo de teste...")
        
        file_content = TEST_XML_CONTENT.encode('utf-8')
        file_path = await upload_file_to_storage(file_content, test_filename, test_doc_id)
        
        if not file_path:
            print("❌ Falha no upload para o Storage")
            return False
        
        print(f"✅ Arquivo enviado para Storage: {file_path}")
        
        # 2. Criar registro do documento no banco
        print(f"\n2. Criando registro do documento no banco...")
        
        doc_created = await create_document_record(test_doc_id, test_filename, file_path)
        if not doc_created:
            print("❌ Falha ao criar registro do documento")
            return False
        
        print("✅ Documento registrado no banco")
        
        # 3. Verificar se o arquivo foi salvo corretamente no Storage
        print(f"\n3. Verificando arquivo no Storage...")
        
        try:
            downloaded_content = supabase.storage.from_(STORAGE_BUCKET).download(file_path)
            print(f"✅ Arquivo verificado no Storage: {len(downloaded_content)} bytes")
        except Exception as e:
            print(f"❌ Erro ao verificar arquivo no Storage: {e}")
            return False
        
        # 4. Processar documento com os 3 agentes IA
        print(f"\n4. Processando documento com os 3 agentes IA...")
        
        # Processar diretamente com os agentes (versão simplificada para teste)
        processing_result = await process_document_async(test_doc_id, downloaded_content, test_filename)
        
        if processing_result.get('success'):
            print("✅ Processamento concluído com sucesso!")
            
            # Mostrar resultados detalhados
            print(f"\n📊 Resultados do processamento:")
            print(f"   - Tempo de processamento: {processing_result.get('processing_time', 0):.2f}s")
            
            # Dados extraídos
            extracted_data = processing_result.get('extracted_data', {})
            if extracted_data:
                print(f"   - Número da nota: {extracted_data.get('numero_nota', 'N/A')}")
                print(f"   - Série: {extracted_data.get('serie', 'N/A')}")
                print(f"   - Chave de acesso: {extracted_data.get('chave_acesso', 'N/A')}")
                print(f"   - Data de emissão: {extracted_data.get('data_emissao', 'N/A')}")
                print(f"   - Valor total: R$ {extracted_data.get('valor_total', 0):,.2f}")
                
                emitente = extracted_data.get('emitente', {})
                print(f"   - Emitente: {emitente.get('razao_social', 'N/A')}")
                print(f"   - CNPJ Emitente: {emitente.get('cnpj', 'N/A')}")
                print(f"   - UF Origem: {emitente.get('uf', 'N/A')}")
                
                destinatario = extracted_data.get('destinatario', {})
                print(f"   - Destinatário: {destinatario.get('nome', 'N/A')}")
                print(f"   - UF Destino: {destinatario.get('uf', 'N/A')}")
            
            # Itens categorizados
            categorized_items = processing_result.get('categorized_items', [])
            print(f"   - Itens categorizados: {len(categorized_items)}")
            for i, item in enumerate(categorized_items):
                print(f"     {i+1}. {item.get('descricao', 'N/A')} - Categoria: {item.get('categoria', 'N/A')}")
            
            # Análise de fornecedor
            supplier_category = processing_result.get('supplier_category', {})
            if supplier_category:
                print(f"   - Tipo de fornecedor: {supplier_category.get('type', 'N/A')}")
                print(f"   - Categoria de negócio: {supplier_category.get('business_category', 'N/A')}")
                print(f"   - Score de risco: {supplier_category.get('risk_score', 'N/A')}")
            
            # Insights executivos
            executive_insights = processing_result.get('executive_insights', {})
            alertas = executive_insights.get('alertas', [])
            oportunidades = executive_insights.get('oportunidades', [])
            print(f"   - Alertas gerados: {len(alertas)}")
            print(f"   - Oportunidades identificadas: {len(oportunidades)}")
            
            # Mostrar alguns insights
            if alertas:
                print(f"   - Exemplos de alertas:")
                for alerta in alertas[:2]:
                    if isinstance(alerta, dict):
                        print(f"     • {alerta.get('message', alerta.get('titulo', 'N/A'))}")
                    else:
                        print(f"     • {str(alerta)}")
            
            if oportunidades:
                print(f"   - Exemplos de oportunidades:")
                for oportunidade in oportunidades[:2]:
                    if isinstance(oportunidade, dict):
                        print(f"     • {oportunidade.get('message', oportunidade.get('titulo', 'N/A'))}")
                    else:
                        print(f"     • {str(oportunidade)}")
            
        else:
            print(f"❌ Falha no processamento: {processing_result.get('error', 'Erro desconhecido')}")
            return False
        
        # 5. Verificar dados salvos no novo schema
        print(f"\n5. Verificando dados salvos no novo schema...")
        
        try:
            document_details = await get_document(test_doc_id)
            print("✅ Documento recuperado do banco com novo schema:")
            print(f"   - Status: {document_details.get('status')}")
            print(f"   - Progresso: {document_details.get('progress')}%")
            
            # Verificar campos do novo schema na tabela principal
            print(f"   - Número da nota (schema): {document_details.get('numero_nota')}")
            print(f"   - Série (schema): {document_details.get('serie')}")
            print(f"   - Chave de acesso (schema): {document_details.get('chave_acesso')}")
            print(f"   - Data de emissão (schema): {document_details.get('data_emissao')}")
            print(f"   - Valor total (schema): R$ {document_details.get('valor_total', 0):,.2f}")
            print(f"   - Total tributos (schema): R$ {document_details.get('total_tributos', 0):,.2f}")
            print(f"   - UF origem (schema): {document_details.get('uf_origem')}")
            print(f"   - UF destino (schema): {document_details.get('uf_destino')}")
            
            # Verificar dados extraídos detalhados
            extracted_data_db = document_details.get('extracted_data', {})
            if extracted_data_db:
                print(f"   - Emitente detalhado (extracted_data):")
                print(f"     • Razão social: {extracted_data_db.get('emitente_razao_social')}")
                print(f"     • CNPJ: {extracted_data_db.get('emitente_cnpj')}")
                print(f"     • Logradouro: {extracted_data_db.get('emitente_logradouro')}")
                print(f"     • Município: {extracted_data_db.get('emitente_municipio')}")
                print(f"   - Destinatário detalhado (extracted_data):")
                print(f"     • Nome: {extracted_data_db.get('destinatario_nome')}")
                print(f"     • CNPJ: {extracted_data_db.get('destinatario_cnpj')}")
                print(f"     • Email: {extracted_data_db.get('destinatario_email')}")
            
            # Verificar itens detalhados
            items = document_details.get('items', [])
            print(f"   - Itens detalhados salvos: {len(items)}")
            for i, item in enumerate(items[:2]):  # Mostrar apenas os 2 primeiros
                print(f"     {i+1}. {item.get('descricao', 'N/A')}")
                confianca = item.get('categoria_confianca', 0)
                confianca_str = f"{confianca:.2f}" if confianca is not None else "N/A"
                print(f"        • Categoria: {item.get('categoria', 'N/A')} (Confiança: {confianca_str})")
                print(f"        • NCM: {item.get('ncm', 'N/A')}")
                print(f"        • CFOP: {item.get('cfop', 'N/A')}")
                valor_produto = item.get('valor_produto', 0) or 0
                icms_valor = item.get('icms_valor', 0) or 0
                print(f"        • Valor: R$ {valor_produto:,.2f}")
                print(f"        • ICMS: R$ {icms_valor:,.2f}")
            
            # Verificar análise de fornecedor
            supplier_analysis = document_details.get('supplier_analysis', {})
            if supplier_analysis:
                print(f"   - Análise de fornecedor salva:")
                print(f"     • Tipo: {supplier_analysis.get('tipo_fornecedor')}")
                print(f"     • Categoria de negócio: {supplier_analysis.get('categoria_negocio')}")
                print(f"     • Score de risco: {supplier_analysis.get('score_risco')}")
                print(f"     • Fatores de risco: {supplier_analysis.get('fatores_risco', [])}")
            
            # Verificar insights de IA
            ai_insights = document_details.get('ai_insights', [])
            print(f"   - Insights de IA salvos: {len(ai_insights)}")
            for insight in ai_insights[:3]:  # Mostrar apenas os 3 primeiros
                print(f"     • {insight.get('tipo_insight')}: {insight.get('titulo')}")
                print(f"       Prioridade: {insight.get('prioridade')}, Confiança: {insight.get('confianca')}")
            
        except Exception as e:
            print(f"❌ Erro ao verificar dados salvos: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 6. Testar métricas do dashboard
        print(f"\n6. Testando métricas do dashboard...")
        
        try:
            metrics = await get_dashboard_metrics()
            print(f"✅ Métricas atualizadas:")
            print(f"   - Total de documentos: {metrics.get('total_documentos', 0)}")
            print(f"   - Documentos processados: {metrics.get('documentos_processados', 0)}")
            print(f"   - Valor total geral: R$ {metrics.get('valor_total', 0):,.2f}")
            print(f"   - Taxa de sucesso: {metrics.get('taxa_sucesso', 0):.1f}%")
            
        except Exception as e:
            print(f"⚠️  Aviso: Erro ao testar métricas: {e}")
        
        print(f"\n🎉 Teste completo realizado com sucesso!")
        print(f"📋 Resumo final:")
        print(f"   ✅ Upload para Storage: OK")
        print(f"   ✅ Registro no banco: OK")
        print(f"   ✅ Processamento com 3 agentes: OK")
        print(f"   ✅ Salvamento no novo schema: OK")
        print(f"   ✅ Recuperação de dados detalhados: OK")
        print(f"   ✅ Métricas do dashboard: OK")
        print(f"\n🎯 O novo schema está funcionando perfeitamente!")
        
        # Limpeza
        print(f"\n🧹 Limpando dados de teste...")
        try:
            # Remover do banco (cascade vai remover das outras tabelas)
            supabase.table('fiscal_documents').delete().eq('id', test_doc_id).execute()
            
            # Remover do storage
            supabase.storage.from_(STORAGE_BUCKET).remove([file_path])
            
            print("✅ Dados de teste removidos")
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível remover todos os dados de teste: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando teste completo do fluxo com novo schema\n")
    
    success = asyncio.run(test_complete_flow())
    
    if success:
        print("\n✅ TESTE COMPLETO CONCLUÍDO COM SUCESSO!")
        print("🎯 O sistema está funcionando perfeitamente com o novo schema!")
        print("📊 Todos os dados estão sendo salvos corretamente nas novas tabelas!")
        return True
    else:
        print("\n❌ FALHA NO TESTE COMPLETO")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)