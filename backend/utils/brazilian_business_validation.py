"""
Localized validation for Brazilian business data
Validação localizada para dados empresariais brasileiros
"""

import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
import structlog

logger = structlog.get_logger()

class ValidadorNegociosBrasil:
    """Validador específico para regras de negócio brasileiras"""
    
    # Códigos CFOP válidos por categoria
    CFOP_ENTRADA = ['1', '2', '3']  # Primeiro dígito para operações de entrada
    CFOP_SAIDA = ['5', '6', '7']    # Primeiro dígito para operações de saída
    
    # NCM - Nomenclatura Comum do Mercosul (8 dígitos)
    NCM_PATTERN = r'^\d{8}$'
    
    # CEST - Código Especificador da Substituição Tributária (7 dígitos)
    CEST_PATTERN = r'^\d{2}\.\d{3}\.\d{2}$'
    
    # Códigos de situação tributária ICMS
    CST_ICMS_VALIDOS = [
        '00', '10', '20', '30', '40', '41', '50', '51', '60', '70', '90',
        '101', '102', '103', '201', '202', '203', '300', '400', '500', '900'
    ]
    
    # Códigos de situação tributária IPI
    CST_IPI_VALIDOS = [
        '00', '01', '02', '03', '04', '05', '49', '50', '51', '52', '53', '54', '55', '99'
    ]
    
    # Códigos de situação tributária PIS/COFINS
    CST_PIS_COFINS_VALIDOS = [
        '01', '02', '03', '04', '05', '06', '07', '08', '09', '49', '50', '51', '52', '53', '54', '55', '56', '60', '61', '62', '63', '64', '65', '66', '67', '70', '71', '72', '73', '74', '75', '98', '99'
    ]
    
    # UFs brasileiras
    UFS_VALIDAS = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
        'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
        'SP', 'SE', 'TO'
    ]
    
    # Códigos de país (BACEN)
    CODIGO_BRASIL = '1058'
    
    @classmethod
    def validar_cfop(cls, cfop: str, tipo_operacao: str) -> Dict[str, Any]:
        """Validar CFOP considerando tipo de operação"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        try:
            if not cfop or len(cfop) != 4 or not cfop.isdigit():
                resultado['valido'] = False
                resultado['erros'].append('CFOP deve ter exatamente 4 dígitos numéricos')
                return resultado
            
            primeiro_digito = cfop[0]
            
            # Validar consistência com tipo de operação
            if tipo_operacao == '0':  # Entrada
                if primeiro_digito not in cls.CFOP_ENTRADA:
                    resultado['valido'] = False
                    resultado['erros'].append(f'CFOP {cfop} não é válido para operação de entrada')
            elif tipo_operacao == '1':  # Saída
                if primeiro_digito not in cls.CFOP_SAIDA:
                    resultado['valido'] = False
                    resultado['erros'].append(f'CFOP {cfop} não é válido para operação de saída')
            
            # Validações específicas por categoria
            if primeiro_digito == '1':
                resultado['avisos'].append('CFOP de entrada - operação dentro do estado')
            elif primeiro_digito == '2':
                resultado['avisos'].append('CFOP de entrada - operação interestadual')
            elif primeiro_digito == '3':
                resultado['avisos'].append('CFOP de entrada - operação exterior')
            elif primeiro_digito == '5':
                resultado['avisos'].append('CFOP de saída - operação dentro do estado')
            elif primeiro_digito == '6':
                resultado['avisos'].append('CFOP de saída - operação interestadual')
            elif primeiro_digito == '7':
                resultado['avisos'].append('CFOP de saída - operação exterior')
            
        except Exception as e:
            logger.error("Erro ao validar CFOP", cfop=cfop, tipo_operacao=tipo_operacao, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação do CFOP: {str(e)}')
        
        return resultado
    
    @classmethod
    def validar_ncm(cls, ncm: str) -> Dict[str, Any]:
        """Validar código NCM"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        try:
            if not ncm:
                resultado['valido'] = False
                resultado['erros'].append('NCM é obrigatório')
                return resultado
            
            # Remover formatação
            ncm_limpo = re.sub(r'[^0-9]', '', ncm)
            
            if not re.match(cls.NCM_PATTERN, ncm_limpo):
                resultado['valido'] = False
                resultado['erros'].append('NCM deve ter exatamente 8 dígitos')
                return resultado
            
            # Validações específicas por capítulo (primeiros 2 dígitos)
            capitulo = ncm_limpo[:2]
            
            # Capítulos conhecidos (exemplos)
            capitulos_conhecidos = {
                '01': 'Animais vivos',
                '02': 'Carnes e miudezas',
                '84': 'Máquinas e equipamentos',
                '85': 'Máquinas e aparelhos elétricos',
                '87': 'Veículos automóveis'
            }
            
            if capitulo in capitulos_conhecidos:
                resultado['avisos'].append(f'NCM do capítulo: {capitulos_conhecidos[capitulo]}')
            
        except Exception as e:
            logger.error("Erro ao validar NCM", ncm=ncm, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação do NCM: {str(e)}')
        
        return resultado
    
    @classmethod
    def validar_situacao_tributaria(cls, cst: str, tipo_imposto: str) -> Dict[str, Any]:
        """Validar código de situação tributária"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        try:
            if not cst:
                resultado['valido'] = False
                resultado['erros'].append('Código de situação tributária é obrigatório')
                return resultado
            
            # Validar baseado no tipo de imposto
            if tipo_imposto.upper() == 'ICMS':
                if cst not in cls.CST_ICMS_VALIDOS:
                    resultado['valido'] = False
                    resultado['erros'].append(f'CST ICMS {cst} não é válido')
                else:
                    # Adicionar descrição do CST
                    descricoes_icms = {
                        '00': 'Tributada integralmente',
                        '10': 'Tributada e com cobrança do ICMS por substituição tributária',
                        '20': 'Com redução de base de cálculo',
                        '30': 'Isenta ou não tributada e com cobrança do ICMS por substituição tributária',
                        '40': 'Isenta',
                        '41': 'Não tributada',
                        '50': 'Suspensão',
                        '51': 'Diferimento',
                        '60': 'ICMS cobrado anteriormente por substituição tributária',
                        '70': 'Com redução de base de cálculo e cobrança do ICMS por substituição tributária',
                        '90': 'Outras'
                    }
                    if cst in descricoes_icms:
                        resultado['avisos'].append(f'ICMS: {descricoes_icms[cst]}')
            
            elif tipo_imposto.upper() == 'IPI':
                if cst not in cls.CST_IPI_VALIDOS:
                    resultado['valido'] = False
                    resultado['erros'].append(f'CST IPI {cst} não é válido')
            
            elif tipo_imposto.upper() in ['PIS', 'COFINS']:
                if cst not in cls.CST_PIS_COFINS_VALIDOS:
                    resultado['valido'] = False
                    resultado['erros'].append(f'CST {tipo_imposto} {cst} não é válido')
            
        except Exception as e:
            logger.error("Erro ao validar situação tributária", cst=cst, tipo_imposto=tipo_imposto, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação da situação tributária: {str(e)}')
        
        return resultado
    
    @classmethod
    def validar_aliquotas_impostos(cls, impostos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validar alíquotas de impostos brasileiros"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        # Alíquotas máximas conhecidas
        aliquotas_maximas = {
            'ICMS': 25.0,
            'IPI': 50.0,
            'PIS': 10.0,
            'COFINS': 10.0,
            'ISSQN': 5.0,
            'II': 35.0,  # Imposto de Importação
            'IOF': 25.0   # Imposto sobre Operações Financeiras
        }
        
        try:
            for imposto in impostos:
                tipo_imposto = imposto.get('tipo_imposto', '').upper()
                aliquota = float(imposto.get('aliquota', 0))
                
                if tipo_imposto in aliquotas_maximas:
                    aliquota_maxima = aliquotas_maximas[tipo_imposto]
                    
                    if aliquota > aliquota_maxima:
                        resultado['erros'].append(
                            f'Alíquota {tipo_imposto} ({aliquota}%) acima do máximo permitido ({aliquota_maxima}%)'
                        )
                        resultado['valido'] = False
                    elif aliquota > aliquota_maxima * 0.8:  # 80% do máximo
                        resultado['avisos'].append(
                            f'Alíquota {tipo_imposto} ({aliquota}%) próxima do máximo ({aliquota_maxima}%)'
                        )
                
                # Validar se alíquota não é negativa
                if aliquota < 0:
                    resultado['erros'].append(f'Alíquota {tipo_imposto} não pode ser negativa')
                    resultado['valido'] = False
        
        except Exception as e:
            logger.error("Erro ao validar alíquotas", impostos=impostos, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação das alíquotas: {str(e)}')
        
        return resultado
    
    @classmethod
    def validar_endereco_brasileiro(cls, endereco: Dict[str, Any]) -> Dict[str, Any]:
        """Validar endereço brasileiro"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        try:
            # Validar UF
            uf = endereco.get('uf', '').upper()
            if uf not in cls.UFS_VALIDAS:
                resultado['erros'].append(f'UF {uf} não é válida')
                resultado['valido'] = False
            
            # Validar CEP
            cep = endereco.get('cep', '')
            if cep:
                cep_limpo = re.sub(r'[^0-9]', '', cep)
                if len(cep_limpo) != 8:
                    resultado['erros'].append('CEP deve ter 8 dígitos')
                    resultado['valido'] = False
                else:
                    # Validar faixa de CEP por UF (exemplos)
                    faixas_cep = {
                        'SP': ('01000', '19999'),
                        'RJ': ('20000', '28999'),
                        'MG': ('30000', '39999'),
                        'RS': ('90000', '99999')
                    }
                    
                    if uf in faixas_cep:
                        inicio, fim = faixas_cep[uf]
                        if not (inicio <= cep_limpo[:5] <= fim):
                            resultado['avisos'].append(f'CEP pode não corresponder à UF {uf}')
            
            # Validar código do município
            codigo_municipio = endereco.get('codigo_municipio', '')
            if codigo_municipio and len(codigo_municipio) != 7:
                resultado['avisos'].append('Código do município deve ter 7 dígitos')
            
            # Validar campos obrigatórios
            campos_obrigatorios = ['logradouro', 'bairro', 'nome_municipio', 'uf']
            for campo in campos_obrigatorios:
                if not endereco.get(campo, '').strip():
                    resultado['erros'].append(f'Campo {campo} é obrigatório')
                    resultado['valido'] = False
        
        except Exception as e:
            logger.error("Erro ao validar endereço", endereco=endereco, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação do endereço: {str(e)}')
        
        return resultado
    
    @classmethod
    def validar_valores_nfe(cls, dados_nfe: Dict[str, Any]) -> Dict[str, Any]:
        """Validar consistência de valores em NF-e"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        try:
            valor_total_nf = Decimal(str(dados_nfe.get('valor_total_nf', 0)))
            valor_produtos = Decimal(str(dados_nfe.get('valor_total_produtos', 0)))
            valor_servicos = Decimal(str(dados_nfe.get('valor_total_servicos', 0)))
            valor_frete = Decimal(str(dados_nfe.get('valor_frete', 0)))
            valor_seguro = Decimal(str(dados_nfe.get('valor_seguro', 0)))
            valor_desconto = Decimal(str(dados_nfe.get('valor_desconto', 0)))
            valor_outras_despesas = Decimal(str(dados_nfe.get('valor_outras_despesas', 0)))
            
            # Calcular valor esperado
            valor_calculado = (valor_produtos + valor_servicos + valor_frete + 
                             valor_seguro + valor_outras_despesas - valor_desconto)
            
            # Verificar diferença (tolerância de R$ 0,01)
            diferenca = abs(valor_total_nf - valor_calculado)
            if diferenca > Decimal('0.01'):
                resultado['erros'].append(
                    f'Valor total da NF-e (R$ {valor_total_nf}) não confere com a soma dos componentes (R$ {valor_calculado})'
                )
                resultado['valido'] = False
            
            # Validar valores não negativos
            valores_para_validar = {
                'valor_total_nf': valor_total_nf,
                'valor_produtos': valor_produtos,
                'valor_servicos': valor_servicos,
                'valor_frete': valor_frete,
                'valor_seguro': valor_seguro,
                'valor_outras_despesas': valor_outras_despesas
            }
            
            for nome_valor, valor in valores_para_validar.items():
                if valor < 0:
                    resultado['erros'].append(f'{nome_valor} não pode ser negativo')
                    resultado['valido'] = False
            
            # Avisos para valores altos
            if valor_total_nf > Decimal('1000000'):  # R$ 1 milhão
                resultado['avisos'].append('Valor total da NF-e muito alto (acima de R$ 1 milhão)')
            
        except Exception as e:
            logger.error("Erro ao validar valores da NF-e", dados=dados_nfe, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação dos valores: {str(e)}')
        
        return resultado
    
    @classmethod
    def validar_regime_tributario(cls, regime: str, cnpj: str) -> Dict[str, Any]:
        """Validar regime tributário brasileiro"""
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        regimes_validos = {
            '1': 'Simples Nacional',
            '2': 'Simples Nacional - excesso de sublimite de receita bruta',
            '3': 'Regime Normal'
        }
        
        try:
            if regime not in regimes_validos:
                resultado['erros'].append(f'Regime tributário {regime} não é válido')
                resultado['valido'] = False
            else:
                resultado['avisos'].append(f'Regime: {regimes_validos[regime]}')
                
                # Validações específicas por regime
                if regime == '1' and cnpj:
                    # Simples Nacional tem limitações de faturamento
                    resultado['avisos'].append('Verificar se empresa está dentro dos limites do Simples Nacional')
        
        except Exception as e:
            logger.error("Erro ao validar regime tributário", regime=regime, cnpj=cnpj, erro=str(e))
            resultado['valido'] = False
            resultado['erros'].append(f'Erro na validação do regime tributário: {str(e)}')
        
        return resultado

class ValidadorCompleto:
    """Validador completo para dados empresariais brasileiros"""
    
    def __init__(self):
        self.validador_negocio = ValidadorNegociosBrasil()
    
    def validar_documento_fiscal_completo(self, documento: Dict[str, Any]) -> Dict[str, Any]:
        """Validação completa de documento fiscal brasileiro"""
        resultado_geral = {
            'valido': True,
            'erros': [],
            'avisos': [],
            'validacoes_detalhadas': {}
        }
        
        try:
            # Validar CFOP
            if 'cfop' in documento and 'tipo_operacao' in documento:
                resultado_cfop = self.validador_negocio.validar_cfop(
                    documento['cfop'], 
                    documento['tipo_operacao']
                )
                resultado_geral['validacoes_detalhadas']['cfop'] = resultado_cfop
                if not resultado_cfop['valido']:
                    resultado_geral['valido'] = False
                resultado_geral['erros'].extend(resultado_cfop['erros'])
                resultado_geral['avisos'].extend(resultado_cfop['avisos'])
            
            # Validar endereços
            for campo_endereco in ['endereco_emitente', 'endereco_destinatario']:
                if campo_endereco in documento:
                    resultado_endereco = self.validador_negocio.validar_endereco_brasileiro(
                        documento[campo_endereco]
                    )
                    resultado_geral['validacoes_detalhadas'][campo_endereco] = resultado_endereco
                    if not resultado_endereco['valido']:
                        resultado_geral['valido'] = False
                    resultado_geral['erros'].extend(resultado_endereco['erros'])
                    resultado_geral['avisos'].extend(resultado_endereco['avisos'])
            
            # Validar valores
            resultado_valores = self.validador_negocio.validar_valores_nfe(documento)
            resultado_geral['validacoes_detalhadas']['valores'] = resultado_valores
            if not resultado_valores['valido']:
                resultado_geral['valido'] = False
            resultado_geral['erros'].extend(resultado_valores['erros'])
            resultado_geral['avisos'].extend(resultado_valores['avisos'])
            
            # Validar impostos
            if 'impostos' in documento:
                resultado_impostos = self.validador_negocio.validar_aliquotas_impostos(
                    documento['impostos']
                )
                resultado_geral['validacoes_detalhadas']['impostos'] = resultado_impostos
                if not resultado_impostos['valido']:
                    resultado_geral['valido'] = False
                resultado_geral['erros'].extend(resultado_impostos['erros'])
                resultado_geral['avisos'].extend(resultado_impostos['avisos'])
            
            # Validar itens
            if 'itens' in documento:
                for i, item in enumerate(documento['itens']):
                    # Validar NCM
                    if 'ncm' in item:
                        resultado_ncm = self.validador_negocio.validar_ncm(item['ncm'])
                        resultado_geral['validacoes_detalhadas'][f'item_{i}_ncm'] = resultado_ncm
                        if not resultado_ncm['valido']:
                            resultado_geral['valido'] = False
                        resultado_geral['erros'].extend([f'Item {i+1}: {erro}' for erro in resultado_ncm['erros']])
                        resultado_geral['avisos'].extend([f'Item {i+1}: {aviso}' for aviso in resultado_ncm['avisos']])
        
        except Exception as e:
            logger.error("Erro na validação completa", documento=documento, erro=str(e))
            resultado_geral['valido'] = False
            resultado_geral['erros'].append(f'Erro interno na validação: {str(e)}')
        
        return resultado_geral

# Instância global
validador_completo_br = ValidadorCompleto()