#!/usr/bin/env python3
"""
Teste com XML real do projeto
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.xml_processing_agent import XMLProcessingAgent

def test_real_xml():
    """Testa com XML real"""
    print("🔍 Testando com XML real...")
    
    # Ler XML real
    xml_path = "../xml_nf/exemplo.xml"
    if not os.path.exists(xml_path):
        print("❌ Arquivo XML não encontrado")
        return False
    
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    agent = XMLProcessingAgent()
    result = agent.process_xml(xml_content)
    
    extracted = result['extracted_data']
    validation = result['validation']
    
    print(f"✅ XML processado com sucesso!")
    print(f"   - Valor total: R$ {extracted.get('valor_total', 0)}")
    print(f"   - Emitente: {extracted.get('emitente', {}).get('razao_social')}")
    print(f"   - CNPJ Emitente: {extracted.get('emitente', {}).get('cnpj')}")
    print(f"   - Destinatário: {extracted.get('destinatario', {}).get('razao_social')}")
    print(f"   - Número da nota: {extracted.get('numero_nota')}")
    print(f"   - Data emissão: {extracted.get('data_emissao')}")
    print(f"   - Chave de acesso: {extracted.get('chave_acesso')}")
    print(f"   - Itens encontrados: {len(extracted.get('itens', []))}")
    
    if extracted.get('itens'):
        item = extracted['itens'][0]
        print(f"   - Primeiro item: {item.get('descricao')}")
        print(f"   - Valor do item: R$ {item.get('valor_total', 0)}")
        print(f"   - NCM: {item.get('ncm')}")
        print(f"   - CFOP: {item.get('cfop')}")
    
    print(f"   - Validação: {'✅ Válido' if validation.get('valid') else '❌ Inválido'}")
    if validation.get('errors'):
        print(f"   - Erros: {validation['errors']}")
    if validation.get('warnings'):
        print(f"   - Avisos: {validation['warnings']}")
    
    print(f"   - Confiança: {validation.get('confidence', 0.0):.2f}")
    
    return True

if __name__ == "__main__":
    test_real_xml()