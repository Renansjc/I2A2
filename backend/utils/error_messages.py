"""
Portuguese error message generation and business rule validation
Geração de mensagens de erro em português e validação de regras de negócio
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import structlog

logger = structlog.get_logger()

class TipoErro(str, Enum):
    """Tipos de erro do sistema"""
    VALIDACAO = "validacao"
    AUTENTICACAO = "autenticacao"
    AUTORIZACAO = "autorizacao"
    NEGOCIO = "negocio"
    SISTEMA = "sistema"
    INTEGRACAO = "integracao"
    DADOS = "dados"
    LLM = "llm"

class SeveridadeErro(str, Enum):
    """Severidade do erro"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class GeradorMensagensPortugues:
    """Gerador de mensagens de erro em português brasileiro"""
    
    # Mensagens de erro por categoria
    MENSAGENS_VALIDACAO = {
        "campo_obrigatorio": "O campo '{campo}' é obrigatório",
        "formato_invalido": "O formato do campo '{campo}' está inválido",
        "valor_minimo": "O valor do campo '{campo}' deve ser maior que {minimo}",
        "valor_maximo": "O valor do campo '{campo}' deve ser menor que {maximo}",
        "tamanho_minimo": "O campo '{campo}' deve ter pelo menos {minimo} caracteres",
        "tamanho_maximo": "O campo '{campo}' deve ter no máximo {maximo} caracteres",
        "opcao_invalida": "O valor '{valor}' não é uma opção válida para o campo '{campo}'",
        "data_invalida": "A data informada no campo '{campo}' está inválida",
        "periodo_invalido": "O período informado é inválido: data de fim deve ser posterior à data de início",
        "documento_invalido": "O documento '{documento}' informado é inválido",
        "email_invalido": "O endereço de email informado é inválido",
        "telefone_invalido": "O número de telefone informado é inválido",
        "cep_invalido": "O CEP informado é inválido",
        "cnpj_invalido": "O CNPJ informado é inválido",
        "cpf_invalido": "O CPF informado é inválido",
        "chave_nfe_invalida": "A chave de acesso da NF-e é inválida",
        "ncm_invalido": "O código NCM informado é inválido",
        "cfop_invalido": "O código CFOP informado é inválido"
    }
    
    MENSAGENS_NEGOCIO = {
        "fornecedor_nao_encontrado": "Fornecedor não encontrado no sistema",
        "produto_nao_encontrado": "Produto não encontrado no sistema",
        "documento_ja_processado": "Este documento já foi processado anteriormente",
        "periodo_muito_longo": "O período selecionado é muito longo e pode impactar a performance",
        "dados_insuficientes": "Dados insuficientes para gerar o relatório solicitado",
        "categoria_inexistente": "A categoria especificada não existe",
        "permissao_negada": "Você não tem permissão para acessar estes dados",
        "limite_consultas_excedido": "Limite de consultas por minuto excedido",
        "arquivo_muito_grande": "O arquivo enviado é muito grande",
        "formato_arquivo_invalido": "Formato de arquivo não suportado",
        "xml_malformado": "O arquivo XML está malformado ou corrompido",
        "documento_fiscal_invalido": "O documento fiscal não atende aos padrões brasileiros"
    }
    
    MENSAGENS_SISTEMA = {
        "erro_interno": "Erro interno do sistema. Tente novamente em alguns minutos",
        "servico_indisponivel": "Serviço temporariamente indisponível",
        "timeout": "A operação demorou mais que o esperado e foi cancelada",
        "conexao_banco": "Erro de conexão com o banco de dados",
        "conexao_llm": "Erro de conexão com o serviço de IA",
        "memoria_insuficiente": "Memória insuficiente para processar a solicitação",
        "disco_cheio": "Espaço em disco insuficiente",
        "configuracao_invalida": "Configuração do sistema inválida"
    }
    
    MENSAGENS_LLM = {
        "api_key_invalida": "Chave de API do OpenAI inválida ou expirada",
        "quota_excedida": "Cota de uso da API OpenAI excedida",
        "modelo_indisponivel": "Modelo de IA temporariamente indisponível",
        "resposta_invalida": "Resposta inválida do serviço de IA",
        "contexto_muito_longo": "Contexto da conversa muito longo para processamento",
        "prompt_invalido": "Prompt inválido para o modelo de IA",
        "tokens_insuficientes": "Tokens insuficientes para completar a operação"
    }
    
    SUGESTOES_SOLUCAO = {
        "campo_obrigatorio": "Preencha o campo obrigatório",
        "formato_invalido": "Verifique o formato esperado e corrija",
        "documento_invalido": "Verifique se o documento foi digitado corretamente",
        "periodo_invalido": "Ajuste as datas para que a data de fim seja posterior à de início",
        "arquivo_muito_grande": "Reduza o tamanho do arquivo ou divida em partes menores",
        "xml_malformado": "Verifique se o arquivo XML não está corrompido",
        "erro_interno": "Tente novamente em alguns minutos. Se persistir, contate o suporte",
        "servico_indisponivel": "Aguarde alguns minutos e tente novamente",
        "conexao_llm": "Verifique sua conexão com a internet e tente novamente",
        "quota_excedida": "Aguarde a renovação da cota ou contate o administrador",
        "permissao_negada": "Contate o administrador para obter as permissões necessárias"
    }
    
    @classmethod
    def gerar_mensagem_erro(
        cls,
        tipo_erro: TipoErro,
        codigo_erro: str,
        detalhes: Optional[Dict[str, Any]] = None,
        contexto: Optional[str] = None
    ) -> Dict[str, str]:
        """Gerar mensagem de erro formatada em português"""
        
        detalhes = detalhes or {}
        
        # Selecionar dicionário de mensagens baseado no tipo
        if tipo_erro == TipoErro.VALIDACAO:
            mensagens = cls.MENSAGENS_VALIDACAO
        elif tipo_erro == TipoErro.NEGOCIO:
            mensagens = cls.MENSAGENS_NEGOCIO
        elif tipo_erro == TipoErro.SISTEMA:
            mensagens = cls.MENSAGENS_SISTEMA
        elif tipo_erro == TipoErro.LLM:
            mensagens = cls.MENSAGENS_LLM
        else:
            mensagens = cls.MENSAGENS_SISTEMA
        
        # Obter mensagem base
        mensagem_base = mensagens.get(codigo_erro, "Erro não identificado")
        
        # Formatar mensagem com detalhes
        try:
            mensagem_formatada = mensagem_base.format(**detalhes)
        except KeyError as e:
            logger.warning("Erro ao formatar mensagem", codigo_erro=codigo_erro, erro=str(e))
            mensagem_formatada = mensagem_base
        
        # Obter sugestão de solução
        sugestao = cls.SUGESTOES_SOLUCAO.get(codigo_erro, "Contate o suporte técnico")
        
        # Adicionar contexto se fornecido
        if contexto:
            mensagem_formatada = f"{mensagem_formatada} (Contexto: {contexto})"
        
        return {
            "codigo_erro": f"{tipo_erro.upper()}_{codigo_erro.upper()}",
            "mensagem": mensagem_formatada,
            "sugestao_solucao": sugestao,
            "tipo": tipo_erro,
            "severidade": cls._determinar_severidade(tipo_erro, codigo_erro)
        }
    
    @classmethod
    def _determinar_severidade(cls, tipo_erro: TipoErro, codigo_erro: str) -> SeveridadeErro:
        """Determinar severidade do erro"""
        
        # Erros críticos
        erros_criticos = [
            "erro_interno", "conexao_banco", "disco_cheio", "memoria_insuficiente"
        ]
        
        # Erros de alta severidade
        erros_alta = [
            "servico_indisponivel", "timeout", "xml_malformado", "api_key_invalida"
        ]
        
        # Erros de média severidade
        erros_media = [
            "documento_ja_processado", "arquivo_muito_grande", "quota_excedida"
        ]
        
        if codigo_erro in erros_criticos:
            return SeveridadeErro.CRITICA
        elif codigo_erro in erros_alta:
            return SeveridadeErro.ALTA
        elif codigo_erro in erros_media:
            return SeveridadeErro.MEDIA
        else:
            return SeveridadeErro.BAIXA
    
    @classmethod
    def gerar_mensagem_validacao_multipla(cls, erros_validacao: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gerar mensagem para múltiplos erros de validação"""
        
        if not erros_validacao:
            return {
                "codigo_erro": "VALIDACAO_OK",
                "mensagem": "Validação concluída com sucesso",
                "erros": [],
                "total_erros": 0
            }
        
        mensagens_formatadas = []
        
        for erro in erros_validacao:
            campo = erro.get("campo", "desconhecido")
            tipo_erro = erro.get("tipo", "formato_invalido")
            detalhes = erro.get("detalhes", {})
            
            mensagem = cls.gerar_mensagem_erro(
                TipoErro.VALIDACAO,
                tipo_erro,
                {**detalhes, "campo": campo}
            )
            
            mensagens_formatadas.append({
                "campo": campo,
                "mensagem": mensagem["mensagem"],
                "sugestao": mensagem["sugestao_solucao"]
            })
        
        return {
            "codigo_erro": "VALIDACAO_MULTIPLOS_ERROS",
            "mensagem": f"Encontrados {len(erros_validacao)} erros de validação",
            "erros": mensagens_formatadas,
            "total_erros": len(erros_validacao),
            "sugestao_solucao": "Corrija os erros listados e tente novamente"
        }

class ValidadorRegrasNegocioBrasileiro:
    """Validador específico para regras de negócio brasileiras"""
    
    @staticmethod
    def validar_documento_fiscal_brasileiro(dados: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validar regras específicas de documentos fiscais brasileiros"""
        erros = []
        
        # Validar CFOP vs tipo de operação
        cfop = dados.get("cfop", "")
        tipo_operacao = dados.get("tipo_operacao", "")
        
        if cfop and tipo_operacao:
            primeiro_digito_cfop = cfop[0] if cfop else ""
            
            # CFOP 1xxx, 2xxx, 3xxx = Entrada (tipo_operacao = 0)
            # CFOP 5xxx, 6xxx, 7xxx = Saída (tipo_operacao = 1)
            if primeiro_digito_cfop in ["1", "2", "3"] and tipo_operacao != "0":
                erros.append({
                    "campo": "cfop_tipo_operacao",
                    "tipo": "regra_negocio_cfop",
                    "detalhes": {"cfop": cfop, "tipo_operacao": tipo_operacao}
                })
            elif primeiro_digito_cfop in ["5", "6", "7"] and tipo_operacao != "1":
                erros.append({
                    "campo": "cfop_tipo_operacao",
                    "tipo": "regra_negocio_cfop",
                    "detalhes": {"cfop": cfop, "tipo_operacao": tipo_operacao}
                })
        
        # Validar consistência de valores
        valor_total = dados.get("valor_total_nf", 0)
        valor_produtos = dados.get("valor_total_produtos", 0)
        valor_servicos = dados.get("valor_total_servicos", 0)
        
        if valor_total and valor_produtos:
            diferenca = abs(float(valor_total) - float(valor_produtos) - float(valor_servicos or 0))
            if diferenca > 0.01:  # Tolerância de 1 centavo
                erros.append({
                    "campo": "valores_inconsistentes",
                    "tipo": "inconsistencia_valores",
                    "detalhes": {
                        "valor_total": valor_total,
                        "valor_produtos": valor_produtos,
                        "valor_servicos": valor_servicos,
                        "diferenca": diferenca
                    }
                })
        
        # Validar data de emissão vs data atual
        from datetime import datetime, timedelta
        data_emissao = dados.get("data_emissao")
        if data_emissao:
            if isinstance(data_emissao, str):
                try:
                    data_emissao = datetime.fromisoformat(data_emissao.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            if isinstance(data_emissao, datetime):
                agora = datetime.now()
                # Não pode ser mais de 30 dias no futuro
                if data_emissao > agora + timedelta(days=30):
                    erros.append({
                        "campo": "data_emissao",
                        "tipo": "data_futura_invalida",
                        "detalhes": {"data_emissao": data_emissao.isoformat()}
                    })
                
                # Não pode ser mais de 5 anos no passado (para NFe)
                if data_emissao < agora - timedelta(days=5*365):
                    erros.append({
                        "campo": "data_emissao",
                        "tipo": "data_muito_antiga",
                        "detalhes": {"data_emissao": data_emissao.isoformat()}
                    })
        
        return erros
    
    @staticmethod
    def validar_regras_tributarias(dados: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validar regras tributárias brasileiras"""
        erros = []
        
        # Validar alíquotas de impostos
        impostos = dados.get("impostos", [])
        for imposto in impostos:
            tipo_imposto = imposto.get("tipo_imposto", "")
            aliquota = imposto.get("aliquota", 0)
            
            # Validar alíquotas máximas conhecidas
            aliquotas_maximas = {
                "ICMS": 25.0,
                "IPI": 50.0,
                "PIS": 10.0,
                "COFINS": 10.0,
                "ISSQN": 5.0
            }
            
            aliquota_maxima = aliquotas_maximas.get(tipo_imposto)
            if aliquota_maxima and float(aliquota) > aliquota_maxima:
                erros.append({
                    "campo": f"aliquota_{tipo_imposto.lower()}",
                    "tipo": "aliquota_acima_maximo",
                    "detalhes": {
                        "tipo_imposto": tipo_imposto,
                        "aliquota": aliquota,
                        "maximo_permitido": aliquota_maxima
                    }
                })
        
        return erros

# Instância global do gerador de mensagens
gerador_mensagens = GeradorMensagensPortugues()
validador_regras_br = ValidadorRegrasNegocioBrasileiro()