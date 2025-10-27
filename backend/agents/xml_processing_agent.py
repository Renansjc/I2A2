"""
Agente de Processamento XML
Adaptado do projeto alternativo (main.py linhas 150-200)
Migrado de JSON file storage para Supabase
"""

import xml.etree.ElementTree as ET
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


class XMLProcessingAgent:
    """
    Agente especializado em processamento de documentos XML fiscais brasileiros.
    Extrai dados estruturados de NF-e, NFS-e e outros documentos fiscais.
    """
    
    def __init__(self):
        self.name = "XML Processing Agent"
        self.version = "1.0.0"
    
    def process_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Processa conteúdo XML e extrai dados estruturados
        
        Args:
            xml_content: Conteúdo XML como string
            
        Returns:
            Dict com dados extraídos seguindo schema fiscal brasileiro
        """
        try:
            # Primeiro tenta parsing XML estruturado
            structured_data = self._parse_xml_structured(xml_content)
            
            # Se não conseguir dados suficientes, usa parser heurístico
            if self._is_data_insufficient(structured_data):
                text_content = self._xml_to_text(xml_content)
                heuristic_data = self._simple_receipt_parser(text_content)
                structured_data = self._merge_data(structured_data, heuristic_data)
            
            # Normaliza e valida dados
            normalized_data = self._normalize_extracted(structured_data)
            
            # Valida usando regras fiscais brasileiras
            validation_result = self._validate_fiscal_data(normalized_data)
            
            return {
                "extracted_data": normalized_data,
                "validation": validation_result,
                "processing_metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "processed_at": datetime.now().isoformat(),
                    "method": "xml_structured" if not self._is_data_insufficient(structured_data) else "heuristic_fallback"
                }
            }
            
        except Exception as e:
            return {
                "extracted_data": self._get_empty_schema(),
                "validation": {"valid": False, "errors": [f"Processing error: {str(e)}"]},
                "processing_metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "processed_at": datetime.now().isoformat(),
                    "method": "error",
                    "error": str(e)
                }
            }
    
    def _parse_xml_structured(self, xml_content: str) -> Dict[str, Any]:
        """Parse XML usando estrutura conhecida de NF-e/NFS-e com campos detalhados"""
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace handling para NF-e
            namespaces = {
                'nfe': 'http://www.portalfiscal.inf.br/nfe',
                'nfse': 'http://www.abrasf.org.br/nfse.xsd'
            }
            
            data = self._get_empty_schema()
            
            # Extrair dados básicos da nota (ide)
            ide = root.find('.//ide') or root.find('.//nfe:ide', namespaces)
            if ide is not None:
                data['numero_nota'] = self._get_text(ide.find('nNF') or ide.find('nfe:nNF', namespaces))
                data['serie'] = self._get_text(ide.find('serie') or ide.find('nfe:serie', namespaces))
                
                # Extrair datas com timestamp completo para controle de versão
                dh_emi_raw = self._get_text(ide.find('dhEmi') or ide.find('nfe:dhEmi', namespaces))
                data['data_emissao'] = self._parse_date(dh_emi_raw)
                data['dh_emi'] = self._parse_datetime(dh_emi_raw)  # Timestamp completo para controle
                
                dh_saida_raw = self._get_text(ide.find('dhSaiEnt') or ide.find('nfe:dhSaiEnt', namespaces))
                data['data_saida'] = self._parse_date(dh_saida_raw)
                
                data['natureza_operacao'] = self._get_text(ide.find('natOp') or ide.find('nfe:natOp', namespaces))
                data['consumidor_final'] = self._get_text(ide.find('indFinal') or ide.find('nfe:indFinal', namespaces)) == '1'
                data['presenca_comprador'] = self._parse_number(self._get_text(ide.find('indPres') or ide.find('nfe:indPres', namespaces)))
                data['tipo_operacao'] = 'Entrada' if self._get_text(ide.find('tpNF') or ide.find('nfe:tpNF', namespaces)) == '0' else 'Saída'
            
            # Extrair dhEvento se existir (para eventos de NF-e como cancelamento, correção, etc.)
            eventos = root.findall('.//evento') or root.findall('.//nfe:evento', namespaces)
            if eventos:
                # Pegar o evento mais recente
                dh_eventos = []
                for evento in eventos:
                    dh_evento_raw = self._get_text(evento.find('dhEvento') or evento.find('nfe:dhEvento', namespaces))
                    if dh_evento_raw:
                        dh_eventos.append(self._parse_datetime(dh_evento_raw))
                
                if dh_eventos:
                    data['dh_evento'] = max(dh_eventos)  # Evento mais recente
            
            # Chave de acesso
            inf_nfe = root.find('.//infNFe') or root.find('.//nfe:infNFe', namespaces)
            if inf_nfe is not None:
                data['chave_acesso'] = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else None
            
            # Extrair dados detalhados do emitente
            emit = root.find('.//emit') or root.find('.//nfe:emit', namespaces)
            if emit is not None:
                endereco_emit = emit.find('enderEmit') or emit.find('nfe:enderEmit', namespaces)
                data['emitente'] = {
                    'razao_social': self._get_text(emit.find('xNome') or emit.find('nfe:xNome', namespaces)),
                    'nome_fantasia': self._get_text(emit.find('xFant') or emit.find('nfe:xFant', namespaces)),
                    'cnpj': self._get_text(emit.find('CNPJ') or emit.find('nfe:CNPJ', namespaces)),
                    'inscricao_estadual': self._get_text(emit.find('IE') or emit.find('nfe:IE', namespaces)),
                    'crt': self._parse_number(self._get_text(emit.find('CRT') or emit.find('nfe:CRT', namespaces))),
                    'logradouro': self._get_text(endereco_emit.find('xLgr') or endereco_emit.find('nfe:xLgr', namespaces)) if endereco_emit is not None else None,
                    'numero': self._get_text(endereco_emit.find('nro') or endereco_emit.find('nfe:nro', namespaces)) if endereco_emit is not None else None,
                    'complemento': self._get_text(endereco_emit.find('xCpl') or endereco_emit.find('nfe:xCpl', namespaces)) if endereco_emit is not None else None,
                    'bairro': self._get_text(endereco_emit.find('xBairro') or endereco_emit.find('nfe:xBairro', namespaces)) if endereco_emit is not None else None,
                    'municipio': self._get_text(endereco_emit.find('xMun') or endereco_emit.find('nfe:xMun', namespaces)) if endereco_emit is not None else None,
                    'uf': self._get_text(endereco_emit.find('UF') or endereco_emit.find('nfe:UF', namespaces)) if endereco_emit is not None else None,
                    'cep': self._get_text(endereco_emit.find('CEP') or endereco_emit.find('nfe:CEP', namespaces)) if endereco_emit is not None else None,
                    'telefone': self._get_text(endereco_emit.find('fone') or endereco_emit.find('nfe:fone', namespaces)) if endereco_emit is not None else None,
                }
            
            # Extrair dados detalhados do destinatário
            dest = root.find('.//dest') or root.find('.//nfe:dest', namespaces)
            if dest is not None:
                endereco_dest = dest.find('enderDest') or dest.find('nfe:enderDest', namespaces)
                # Para destinatário, usar xNome como nome principal, mas também verificar razão social
                nome_dest = self._get_text(dest.find('xNome') or dest.find('nfe:xNome', namespaces))
                data['destinatario'] = {
                    'nome': nome_dest,
                    'razao_social': nome_dest,  # Para compatibilidade
                    'cnpj': self._get_text(dest.find('CNPJ') or dest.find('nfe:CNPJ', namespaces)),
                    'cpf': self._get_text(dest.find('CPF') or dest.find('nfe:CPF', namespaces)),
                    'inscricao_estadual': self._get_text(dest.find('IE') or dest.find('nfe:IE', namespaces)),
                    'logradouro': self._get_text(endereco_dest.find('xLgr') or endereco_dest.find('nfe:xLgr', namespaces)) if endereco_dest is not None else None,
                    'numero': self._get_text(endereco_dest.find('nro') or endereco_dest.find('nfe:nro', namespaces)) if endereco_dest is not None else None,
                    'complemento': self._get_text(endereco_dest.find('xCpl') or endereco_dest.find('nfe:xCpl', namespaces)) if endereco_dest is not None else None,
                    'bairro': self._get_text(endereco_dest.find('xBairro') or endereco_dest.find('nfe:xBairro', namespaces)) if endereco_dest is not None else None,
                    'municipio': self._get_text(endereco_dest.find('xMun') or endereco_dest.find('nfe:xMun', namespaces)) if endereco_dest is not None else None,
                    'uf': self._get_text(endereco_dest.find('UF') or endereco_dest.find('nfe:UF', namespaces)) if endereco_dest is not None else None,
                    'cep': self._get_text(endereco_dest.find('CEP') or endereco_dest.find('nfe:CEP', namespaces)) if endereco_dest is not None else None,
                    'telefone': self._get_text(endereco_dest.find('fone') or endereco_dest.find('nfe:fone', namespaces)) if endereco_dest is not None else None,
                    'email': self._get_text(dest.find('email') or dest.find('nfe:email', namespaces)),
                }
            
            # Extrair itens detalhados
            items = []
            det_elements = root.findall('.//det') or root.findall('.//nfe:det', namespaces)
            for det in det_elements:
                prod = det.find('prod') or det.find('nfe:prod', namespaces)
                imposto = det.find('imposto') or det.find('nfe:imposto', namespaces)
                
                if prod is not None:
                    item = {
                        # Identificação do produto
                        'codigo_produto': self._get_text(prod.find('cProd') or prod.find('nfe:cProd', namespaces)),
                        'codigo_ean': self._get_text(prod.find('cEAN') or prod.find('nfe:cEAN', namespaces)),
                        'descricao': self._get_text(prod.find('xProd') or prod.find('nfe:xProd', namespaces)),
                        'ncm': self._get_text(prod.find('NCM') or prod.find('nfe:NCM', namespaces)),
                        'cfop': self._get_text(prod.find('CFOP') or prod.find('nfe:CFOP', namespaces)),
                        
                        # Quantidades e unidades
                        'unidade_comercial': self._get_text(prod.find('uCom') or prod.find('nfe:uCom', namespaces)),
                        'quantidade_comercial': self._parse_number(self._get_text(prod.find('qCom') or prod.find('nfe:qCom', namespaces))),
                        'valor_unitario_comercial': self._parse_number(self._get_text(prod.find('vUnCom') or prod.find('nfe:vUnCom', namespaces))),
                        'unidade_tributavel': self._get_text(prod.find('uTrib') or prod.find('nfe:uTrib', namespaces)),
                        'quantidade_tributavel': self._parse_number(self._get_text(prod.find('qTrib') or prod.find('nfe:qTrib', namespaces))),
                        'valor_unitario_tributavel': self._parse_number(self._get_text(prod.find('vUnTrib') or prod.find('nfe:vUnTrib', namespaces))),
                        
                        # Valores do item
                        'valor_produto': self._parse_number(self._get_text(prod.find('vProd') or prod.find('nfe:vProd', namespaces))),
                        'valor_frete': self._parse_number(self._get_text(prod.find('vFrete') or prod.find('nfe:vFrete', namespaces))),
                        'valor_seguro': self._parse_number(self._get_text(prod.find('vSeg') or prod.find('nfe:vSeg', namespaces))),
                        'valor_desconto': self._parse_number(self._get_text(prod.find('vDesc') or prod.find('nfe:vDesc', namespaces))),
                        'valor_outros': self._parse_number(self._get_text(prod.find('vOutro') or prod.find('nfe:vOutro', namespaces))),
                    }
                    
                    # Extrair impostos do item
                    if imposto is not None:
                        # Total de tributos do item
                        item['total_tributos_item'] = self._parse_number(self._get_text(imposto.find('vTotTrib') or imposto.find('nfe:vTotTrib', namespaces)))
                        
                        # ICMS - verificar diferentes tipos
                        icms_elem = imposto.find('ICMS') or imposto.find('nfe:ICMS', namespaces)
                        if icms_elem is not None:
                            # Tentar diferentes tipos de ICMS (buscar diretamente nos filhos)
                            icms = None
                            for child in icms_elem:
                                if child.tag.endswith(('ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40', 'ICMS51', 
                                                      'ICMS60', 'ICMS70', 'ICMS90', 'ICMSSN101', 'ICMSSN102', 
                                                      'ICMSSN201', 'ICMSSN202', 'ICMSSN500', 'ICMSSN900')):
                                    icms = child
                                    break
                            
                            if icms is not None:
                                item['icms_origem'] = self._parse_number(self._get_text(icms.find('orig') or icms.find('nfe:orig', namespaces)))
                                item['icms_cst'] = self._get_text(icms.find('CST') or icms.find('CSOSN') or icms.find('nfe:CST') or icms.find('nfe:CSOSN', namespaces))
                                item['icms_base_calculo'] = self._parse_number(self._get_text(icms.find('vBC') or icms.find('nfe:vBC', namespaces)))
                                item['icms_aliquota'] = self._parse_number(self._get_text(icms.find('pICMS') or icms.find('nfe:pICMS', namespaces)))
                                item['icms_valor'] = self._parse_number(self._get_text(icms.find('vICMS') or icms.find('nfe:vICMS', namespaces)))
                        
                        # PIS - verificar diferentes tipos
                        pis_elem = imposto.find('PIS') or imposto.find('nfe:PIS', namespaces)
                        if pis_elem is not None:
                            pis = None
                            for child in pis_elem:
                                if child.tag.endswith(('PISAliq', 'PISQtde', 'PISNT', 'PISOutr')):
                                    pis = child
                                    break
                            
                            if pis is not None:
                                item['pis_cst'] = self._get_text(pis.find('CST') or pis.find('nfe:CST', namespaces))
                                item['pis_base_calculo'] = self._parse_number(self._get_text(pis.find('vBC') or pis.find('nfe:vBC', namespaces)))
                                item['pis_aliquota'] = self._parse_number(self._get_text(pis.find('pPIS') or pis.find('nfe:pPIS', namespaces)))
                                item['pis_valor'] = self._parse_number(self._get_text(pis.find('vPIS') or pis.find('nfe:vPIS', namespaces)))
                        
                        # COFINS - verificar diferentes tipos
                        cofins_elem = imposto.find('COFINS') or imposto.find('nfe:COFINS', namespaces)
                        if cofins_elem is not None:
                            cofins = None
                            for child in cofins_elem:
                                if child.tag.endswith(('COFINSAliq', 'COFINSQtde', 'COFINSNT', 'COFINSOutr')):
                                    cofins = child
                                    break
                            
                            if cofins is not None:
                                item['cofins_cst'] = self._get_text(cofins.find('CST') or cofins.find('nfe:CST', namespaces))
                                item['cofins_base_calculo'] = self._parse_number(self._get_text(cofins.find('vBC') or cofins.find('nfe:vBC', namespaces)))
                                item['cofins_aliquota'] = self._parse_number(self._get_text(cofins.find('pCOFINS') or cofins.find('nfe:pCOFINS', namespaces)))
                                item['cofins_valor'] = self._parse_number(self._get_text(cofins.find('vCOFINS') or cofins.find('nfe:vCOFINS', namespaces)))
                        
                        # IPI
                        ipi_elem = imposto.find('IPI') or imposto.find('nfe:IPI', namespaces)
                        if ipi_elem is not None:
                            ipi = None
                            for child in ipi_elem:
                                if child.tag.endswith(('IPITrib', 'IPINT')):
                                    ipi = child
                                    break
                            if ipi is not None:
                                item['ipi_cst'] = self._get_text(ipi.find('CST') or ipi.find('nfe:CST', namespaces))
                                item['ipi_valor'] = self._parse_number(self._get_text(ipi.find('vIPI') or ipi.find('nfe:vIPI', namespaces)))
                    
                    items.append(item)
            data['itens'] = items
            
            # Extrair totais
            total = root.find('.//total') or root.find('.//nfe:total', namespaces)
            if total is not None:
                icms_tot = total.find('.//ICMSTot') or total.find('.//nfe:ICMSTot', namespaces)
                if icms_tot is not None:
                    data['valor_total'] = self._parse_number(self._get_text(icms_tot.find('vNF') or icms_tot.find('nfe:vNF', namespaces)))
                    data['valor_produtos'] = self._parse_number(self._get_text(icms_tot.find('vProd') or icms_tot.find('nfe:vProd', namespaces)))
                    data['valor_frete'] = self._parse_number(self._get_text(icms_tot.find('vFrete') or icms_tot.find('nfe:vFrete', namespaces)))
                    data['valor_seguro'] = self._parse_number(self._get_text(icms_tot.find('vSeg') or icms_tot.find('nfe:vSeg', namespaces)))
                    data['valor_desconto'] = self._parse_number(self._get_text(icms_tot.find('vDesc') or icms_tot.find('nfe:vDesc', namespaces)))
                    data['valor_outros'] = self._parse_number(self._get_text(icms_tot.find('vOutro') or icms_tot.find('nfe:vOutro', namespaces)))
                    
                    # Impostos
                    data['impostos'] = {
                        'icms': {
                            'valor': self._parse_number(self._get_text(icms_tot.find('vICMS') or icms_tot.find('nfe:vICMS', namespaces))),
                            'base_calculo': self._parse_number(self._get_text(icms_tot.find('vBC') or icms_tot.find('nfe:vBC', namespaces))),
                            'aliquota': None
                        },
                        'icms_st': {
                            'valor': self._parse_number(self._get_text(icms_tot.find('vST') or icms_tot.find('nfe:vST', namespaces))),
                            'base_calculo': self._parse_number(self._get_text(icms_tot.find('vBCST') or icms_tot.find('nfe:vBCST', namespaces)))
                        },
                        'ipi': {'valor': self._parse_number(self._get_text(icms_tot.find('vIPI') or icms_tot.find('nfe:vIPI', namespaces)))},
                        'pis': {'valor': self._parse_number(self._get_text(icms_tot.find('vPIS') or icms_tot.find('nfe:vPIS', namespaces)))},
                        'cofins': {'valor': self._parse_number(self._get_text(icms_tot.find('vCOFINS') or icms_tot.find('nfe:vCOFINS', namespaces)))}
                    }
            
            # Extrair dados de transporte
            transp = root.find('.//transp') or root.find('.//nfe:transp', namespaces)
            if transp is not None:
                data['modalidade_frete'] = self._parse_number(self._get_text(transp.find('modFrete') or transp.find('nfe:modFrete', namespaces)))
                
                # Transportadora
                transporta = transp.find('transporta') or transp.find('nfe:transporta', namespaces)
                if transporta is not None:
                    data['transportadora'] = self._get_text(transporta.find('xNome') or transporta.find('nfe:xNome', namespaces))
                
                # Volumes
                vol = transp.find('vol') or transp.find('nfe:vol', namespaces)
                if vol is not None:
                    data['quantidade_volumes'] = self._parse_number(self._get_text(vol.find('qVol') or vol.find('nfe:qVol', namespaces)))
                    data['peso_liquido'] = self._parse_number(self._get_text(vol.find('pesoL') or vol.find('nfe:pesoL', namespaces)))
                    data['peso_bruto'] = self._parse_number(self._get_text(vol.find('pesoB') or vol.find('nfe:pesoB', namespaces)))
            
            # Extrair dados de pagamento
            pag = root.find('.//pag') or root.find('.//nfe:pag', namespaces)
            if pag is not None:
                det_pag = pag.find('detPag') or pag.find('nfe:detPag', namespaces)
                if det_pag is not None:
                    data['forma_pagamento'] = self._parse_number(self._get_text(det_pag.find('tPag') or det_pag.find('nfe:tPag', namespaces)))
                    data['valor_pagamento'] = self._parse_number(self._get_text(det_pag.find('vPag') or det_pag.find('nfe:vPag', namespaces)))
                    data['data_vencimento'] = self._parse_date(self._get_text(det_pag.find('dVenc') or det_pag.find('nfe:dVenc', namespaces)))
            
            # Dados da nota
            ide = root.find('.//ide') or root.find('.//nfe:ide', namespaces)
            if ide is not None:
                data['numero_nota'] = self._get_text(ide.find('nNF') or ide.find('nfe:nNF', namespaces))
                data['data_emissao'] = self._parse_date(self._get_text(ide.find('dhEmi') or ide.find('nfe:dhEmi', namespaces)))
                data['natureza_operacao'] = self._get_text(ide.find('natOp') or ide.find('nfe:natOp', namespaces))
            
            # Chave de acesso
            inf_nfe = root.find('.//infNFe') or root.find('.//nfe:infNFe', namespaces)
            if inf_nfe is not None:
                data['chave_acesso'] = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else None
            
            return data
            
        except ET.ParseError as e:
            # Se não conseguir fazer parse do XML, retorna schema vazio
            return self._get_empty_schema()
    
    def _simple_receipt_parser(self, text: Optional[str]) -> Dict[str, Any]:
        """
        Parser heurístico adaptado do projeto alternativo
        Para documentos que não seguem estrutura XML padrão
        """
        data = self._get_empty_schema()
        
        if not text:
            return data
        
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        # Heurística: primeira linha não vazia provavelmente é o nome da empresa
        if lines:
            data['emitente']['razao_social'] = lines[0]

        # Buscar valores monetários - melhorado para XML
        xml_value_patterns = [
            r'<vNF>([0-9]+\.?[0-9]*)</vNF>',  # Valor total da NF
            r'<vProd>([0-9]+\.?[0-9]*)</vProd>',  # Valor dos produtos
            r'([0-9]+\.[0-9]{2})',  # Qualquer valor decimal
        ]
        
        full_text = '\n'.join(lines)
        
        for pattern in xml_value_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                data['valor_total'] = self._parse_number(matches[-1])  # Último valor encontrado
                break
        
        # Fallback: buscar padrões gerais
        if data['valor_total'] is None:
            total_re = re.compile(r'(?:total|valor total|valor|vNF|vProd)\s*[:\->]?\s*([0-9]+[\.,][0-9]{2})', re.IGNORECASE)
            
            for ln in reversed(lines[-20:]):
                m = total_re.search(ln)
                if m:
                    data['valor_total'] = self._parse_number(m.group(1))
                    break
        
        # Buscar itens simples
        item_line_re = re.compile(r'^(.{3,60})\s+(\d+)\s+([0-9]+[\.,][0-9]{2})', re.MULTILINE)
        matches = item_line_re.findall(full_text)
        
        for match in matches:
            desc, qty, val = match
            data['itens'].append({
                "descricao": desc.strip(),
                "quantidade": self._parse_number(qty),
                "unidade": None,
                "valor_unitario": self._parse_number(val),
                "valor_total": self._parse_number(val),
                "codigo": None,
                "ncm": None,
                "cfop": None
            })

        return data
    
    def _validate_fiscal_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados usando regras fiscais brasileiras"""
        errors = []
        warnings = []
        
        # Validar CNPJ
        emitente_cnpj = data.get('emitente', {}).get('cnpj')
        if emitente_cnpj and not self._validate_cnpj(emitente_cnpj):
            errors.append("CNPJ do emitente inválido")
        
        destinatario_cnpj = data.get('destinatario', {}).get('cnpj')
        if destinatario_cnpj and not self._validate_cnpj(destinatario_cnpj):
            warnings.append("CNPJ do destinatário inválido")
        
        # Validar valores
        valor_total = data.get('valor_total')
        if valor_total is not None and valor_total <= 0:
            errors.append("Valor total deve ser positivo")
        
        # Validar itens
        itens = data.get('itens', [])
        if not itens:
            warnings.append("Nenhum item encontrado no documento")
        
        for i, item in enumerate(itens):
            if not item.get('descricao'):
                warnings.append(f"Item {i+1} sem descrição")
            
            if item.get('valor_total') is not None and item.get('valor_total') <= 0:
                warnings.append(f"Item {i+1} com valor inválido")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "confidence": max(0.0, 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1))
        }
    
    def _validate_cnpj(self, cnpj: str) -> bool:
        """Validação básica de CNPJ"""
        if not cnpj:
            return False
        
        # Remove caracteres não numéricos
        cnpj = re.sub(r'\D', '', cnpj)
        
        # CNPJ deve ter 14 dígitos
        if len(cnpj) != 14:
            return False
        
        # Verifica se não são todos iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        return True
    
    def _get_empty_schema(self) -> Dict[str, Any]:
        """Retorna schema vazio padronizado"""
        return {
            "emitente": {"razao_social": None, "cnpj": None, "inscricao_estadual": None, "endereco": None},
            "destinatario": {"razao_social": None, "cnpj": None, "inscricao_estadual": None, "endereco": None},
            "itens": [],
            "impostos": {
                "icms": {"aliquota": None, "base_calculo": None, "valor": None},
                "ipi": {"valor": None},
                "pis": {"valor": None},
                "cofins": {"valor": None}
            },
            "codigos_fiscais": {"cfop": None, "cst": None, "ncm": None, "csosn": None},
            "numero_nota": None,
            "chave_acesso": None,
            "data_emissao": None,
            "natureza_operacao": None,
            "forma_pagamento": None,
            "valor_total": None
        }
    
    def _get_text(self, element) -> Optional[str]:
        """Extrai texto de elemento XML de forma segura"""
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse seguro de números"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # Remove separadores de milhares e normaliza decimal
            str_val = str(value).strip().replace(',', '.')
            return float(str_val)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse de data para formato ISO"""
        if not date_str:
            return None
        
        # Remove timezone info se presente
        date_str = date_str.split('T')[0] if 'T' in date_str else date_str
        
        # Tenta diferentes formatos
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%Y%m%d']
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[str]:
        """Parse de datetime completo para controle de versão (formato ISO 8601)"""
        if not datetime_str:
            return None
        
        # Formatos possíveis de datetime em NF-e
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',      # 2025-03-16T15:34:24-03:00
            '%Y-%m-%dT%H:%M:%S',        # 2025-03-16T15:34:24
            '%Y-%m-%d %H:%M:%S',        # 2025-03-16 15:34:24
            '%d/%m/%Y %H:%M:%S',        # 16/03/2025 15:34:24
            '%Y%m%d%H%M%S',             # 20250316153424
        ]
        
        # Normalizar timezone info
        datetime_str = datetime_str.replace('Z', '+00:00')
        
        for fmt in formats:
            try:
                if '%z' in fmt:
                    # Parse com timezone
                    dt = datetime.strptime(datetime_str, fmt)
                else:
                    # Parse sem timezone, assumir UTC
                    dt = datetime.strptime(datetime_str, fmt)
                    # Adicionar timezone UTC se não tiver
                    if dt.tzinfo is None:
                        from datetime import timezone
                        dt = dt.replace(tzinfo=timezone.utc)
                
                # Retornar em formato ISO 8601 com timezone
                return dt.isoformat()
            except ValueError:
                continue
        
        return None
    
    def _extract_address(self, element) -> Optional[str]:
        """Extrai endereço de elemento XML"""
        if element is None:
            return None
        
        endereco = element.find('enderEmit') or element.find('enderDest')
        if endereco is None:
            return None
        
        parts = []
        for field in ['xLgr', 'nro', 'xBairro', 'xMun', 'UF']:
            elem = endereco.find(field)
            if elem is not None and elem.text:
                parts.append(elem.text.strip())
        
        return ', '.join(parts) if parts else None
    
    def _xml_to_text(self, xml_content: str) -> str:
        """Converte XML para texto plano"""
        try:
            root = ET.fromstring(xml_content)
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
            return "\n".join(text_parts)
        except:
            return xml_content
    
    def _is_data_insufficient(self, data: Dict[str, Any]) -> bool:
        """Verifica se os dados extraídos são insuficientes"""
        if not data:
            return True
        
        # Considera insuficiente se não tem valor total nem itens
        has_value = data.get('valor_total') is not None
        has_items = len(data.get('itens', [])) > 0
        has_emitente = data.get('emitente', {}).get('razao_social') is not None
        
        return not (has_value or has_items or has_emitente)
    
    def _merge_data(self, primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Merge dados priorizando primary, usando fallback para campos vazios"""
        result = primary.copy()
        
        for key, value in fallback.items():
            if key not in result or result[key] is None or (isinstance(result[key], (list, dict)) and not result[key]):
                result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._merge_data(result[key], value)
        
        return result
    
    def _normalize_extracted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados extraídos para schema canônico
        Adaptado da função normalize_extracted do projeto alternativo
        """
        if not data or not isinstance(data, dict):
            return self._get_empty_schema()

        def only_digits(s):
            if not s: return None
            return re.sub(r'\D', '', str(s)) or None

        def normalize_party(p):
            if not p or not isinstance(p, dict): 
                return {"razao_social": None, "cnpj": None, "inscricao_estadual": None, "endereco": None}
            
            return {
                "razao_social": p.get('razao_social') or p.get('nome') or None,
                "cnpj": only_digits(p.get('cnpj') or p.get('cpf')),
                "inscricao_estadual": only_digits(p.get('inscricao_estadual') or p.get('ie')),
                "endereco": p.get('endereco') or p.get('logradouro') or None
            }

        # Normalizar estrutura mantendo dados detalhados
        normalized = data.copy()  # Manter dados originais
        
        # Normalizar apenas se não existirem dados detalhados
        if not isinstance(normalized.get('emitente'), dict) or not normalized['emitente']:
            normalized['emitente'] = normalize_party(data.get('emitente') or {})
        
        if not isinstance(normalized.get('destinatario'), dict) or not normalized['destinatario']:
            normalized['destinatario'] = normalize_party(data.get('destinatario') or {})
        
        # Itens - manter dados detalhados se existirem
        if 'itens' not in normalized or not normalized['itens']:
            items = []
            raw_items = data.get('itens') or []
            if isinstance(raw_items, list):
                for it in raw_items:
                    if not isinstance(it, dict): continue
                    items.append({
                        'descricao': it.get('descricao') or it.get('desc') or None,
                        'quantidade': self._parse_number(it.get('quantidade')),
                        'unidade': it.get('unidade') or it.get('un') or None,
                        'valor_unitario': self._parse_number(it.get('valor_unitario') or it.get('valor')),
                        'valor_total': self._parse_number(it.get('valor_total') or it.get('total')),
                        'codigo': it.get('codigo') or it.get('cod') or None,
                        'ncm': it.get('ncm') or None,
                        'cfop': it.get('cfop') or None,
                    })
            normalized['itens'] = items
        
        # Impostos
        impostos_data = data.get('impostos') or {}
        normalized['impostos'] = {
            'icms': {
                'aliquota': self._parse_number(impostos_data.get('icms', {}).get('aliquota') if isinstance(impostos_data.get('icms'), dict) else None),
                'base_calculo': self._parse_number(impostos_data.get('icms', {}).get('base_calculo') if isinstance(impostos_data.get('icms'), dict) else None),
                'valor': self._parse_number(impostos_data.get('icms', {}).get('valor') if isinstance(impostos_data.get('icms'), dict) else None),
            },
            'ipi': {'valor': self._parse_number((impostos_data.get('ipi') or {}).get('valor') if isinstance(impostos_data.get('ipi'), dict) else None)},
            'pis': {'valor': self._parse_number((impostos_data.get('pis') or {}).get('valor') if isinstance(impostos_data.get('pis'), dict) else None)},
            'cofins': {'valor': self._parse_number((impostos_data.get('cofins') or {}).get('valor') if isinstance(impostos_data.get('cofins'), dict) else None)},
        }
        
        # Códigos fiscais
        cf = data.get('codigos_fiscais') or {}
        normalized['codigos_fiscais'] = {
            'cfop': cf.get('cfop') or data.get('cfop') or None,
            'cst': cf.get('cst') or data.get('cst') or None,
            'ncm': cf.get('ncm') or data.get('ncm') or None,
            'csosn': cf.get('csosn') or data.get('csosn') or None,
        }
        
        # Campos principais
        normalized['numero_nota'] = data.get('numero_nota') or None
        normalized['chave_acesso'] = data.get('chave_acesso') or None
        normalized['data_emissao'] = self._parse_date(data.get('data_emissao'))
        normalized['natureza_operacao'] = data.get('natureza_operacao') or None
        normalized['forma_pagamento'] = data.get('forma_pagamento') or None
        normalized['valor_total'] = self._parse_number(data.get('valor_total'))
        
        return normalized