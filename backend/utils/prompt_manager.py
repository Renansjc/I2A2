"""
Sistema de gerenciamento de templates de prompts para LLM
Especializado para análise de documentos fiscais brasileiros
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import logging

from .llm_config import TipoPrompt, ModeloLLM

logger = logging.getLogger(__name__)


class NivelComplexidade(str, Enum):
    """Nível de complexidade do prompt"""
    SIMPLES = "simples"
    MEDIO = "medio"
    COMPLEXO = "complexo"
    ESPECIALIZADO = "especializado"


@dataclass
class MetadadosPrompt:
    """Metadados do template de prompt"""
    nome: str
    descricao: str
    tipo: TipoPrompt
    nivel_complexidade: NivelComplexidade
    modelo_recomendado: ModeloLLM
    versao: str
    autor: str
    data_criacao: datetime
    data_atualizacao: datetime
    tags: List[str]
    exemplos_uso: List[str]
    metricas_performance: Dict[str, float]


@dataclass
class TemplatePrompt:
    """Template de prompt com metadados"""
    metadados: MetadadosPrompt
    template: str
    variaveis_obrigatorias: List[str]
    variaveis_opcionais: List[str]
    validacoes: Dict[str, str]
    pos_processamento: Optional[str] = None


class GerenciadorTemplatesPrompts:
    """Gerenciador central de templates de prompts"""
    
    def __init__(self):
        self.templates: Dict[str, TemplatePrompt] = {}
        self.metricas_uso: Dict[str, Dict[str, Any]] = {}
        self._carregar_templates_padrao()
    
    def _carregar_templates_padrao(self):
        """Carrega templates padrão do sistema"""
        templates_padrao = {
            # Template para interpretação de consultas do Master Agent
            "master_agent_interpretacao_consulta": TemplatePrompt(
                metadados=MetadadosPrompt(
                    nome="Interpretação de Consulta - Master Agent",
                    descricao="Interpreta consultas em linguagem natural para executivos brasileiros",
                    tipo=TipoPrompt.INTERPRETACAO_CONSULTA,
                    nivel_complexidade=NivelComplexidade.COMPLEXO,
                    modelo_recomendado=ModeloLLM.GPT_4,
                    versao="1.0",
                    autor="Sistema",
                    data_criacao=datetime.now(),
                    data_atualizacao=datetime.now(),
                    tags=["master_agent", "consulta", "executivo", "brasileiro"],
                    exemplos_uso=[
                        "Quais foram os maiores fornecedores no último trimestre?",
                        "Mostre-me as categorias de produtos com maior crescimento",
                        "Analise os padrões de compra por região"
                    ],
                    metricas_performance={"precisao": 0.92, "tempo_medio": 2.3}
                ),
                template="""Você é um assistente de IA especializado em análise de documentos fiscais brasileiros para executivos C-level.

CONTEXTO DA CONSULTA:
Consulta do Usuário: {consulta}
Cargo do Usuário: {cargo_usuario}
Contexto Empresarial: {contexto_empresarial}
Dados Disponíveis: {dados_disponiveis}
Histórico da Conversa: {historico_conversa}

INSTRUÇÕES:
1. Analise a consulta considerando o contexto empresarial brasileiro
2. Identifique a intenção principal e objetivos de negócio
3. Determine que tipo de dados e análise são necessários
4. Extraia entidades relevantes (períodos, fornecedores, produtos, regiões)
5. Avalie o nível de confiança na interpretação
6. Identifique esclarecimentos necessários

FORMATO DE RESPOSTA (JSON):
{{
    "intencao": "descrição clara da intenção",
    "objetivo_empresarial": "objetivo de negócio identificado",
    "tipo_analise_necessaria": "tipo de análise requerida",
    "entidades_extraidas": {{
        "periodo": "período mencionado ou inferido",
        "fornecedores": ["lista de fornecedores mencionados"],
        "produtos": ["lista de produtos/categorias"],
        "regioes": ["regiões geográficas"],
        "valores": ["valores monetários mencionados"]
    }},
    "requisitos_dados": ["lista de dados necessários"],
    "nivel_confianca": 0.0-1.0,
    "esclarecimentos_necessarios": ["perguntas para esclarecer ambiguidades"],
    "sugestoes_consultas_relacionadas": ["consultas relacionadas que podem interessar"],
    "complexidade_estimada": "simples|media|alta",
    "tempo_estimado_processamento": "estimativa em minutos"
}}

DIRETRIZES ESPECÍFICAS:
- Use terminologia empresarial apropriada para executivos brasileiros
- Considere o contexto fiscal e tributário brasileiro
- Priorize insights estratégicos sobre detalhes técnicos
- Mantenha foco em impacto nos negócios e tomada de decisão
- Considere sazonalidades e padrões do mercado brasileiro""",
                variaveis_obrigatorias=["consulta", "cargo_usuario"],
                variaveis_opcionais=["contexto_empresarial", "dados_disponiveis", "historico_conversa"],
                validacoes={
                    "consulta": "deve ser string não vazia",
                    "cargo_usuario": "deve ser um cargo executivo válido"
                }
            ),
            
            # Template para análise semântica de XML
            "xml_analise_semantica": TemplatePrompt(
                metadados=MetadadosPrompt(
                    nome="Análise Semântica XML - NF-e/NFS-e",
                    descricao="Analisa semanticamente documentos fiscais brasileiros XML",
                    tipo=TipoPrompt.ANALISE_SEMANTICA_XML,
                    nivel_complexidade=NivelComplexidade.ESPECIALIZADO,
                    modelo_recomendado=ModeloLLM.GPT_4,
                    versao="1.0",
                    autor="Sistema",
                    data_criacao=datetime.now(),
                    data_atualizacao=datetime.now(),
                    tags=["xml", "nfe", "nfse", "fiscal", "semantica"],
                    exemplos_uso=[
                        "Análise de NF-e de fornecedor de matéria-prima",
                        "Análise de NFS-e de serviços de consultoria",
                        "Identificação de padrões em documentos fiscais"
                    ],
                    metricas_performance={"precisao": 0.89, "tempo_medio": 3.1}
                ),
                template="""Você é um especialista em documentos fiscais brasileiros (NF-e/NFS-e) e análise empresarial.

DOCUMENTO PARA ANÁLISE:
Tipo de Documento: {tipo_documento}
Fornecedor: {info_fornecedor}
Itens/Serviços: {itens}
Valor Total: {valor_total}
Informações Tributárias: {info_tributaria}
Contexto Histórico: {contexto_empresarial}

INSTRUÇÕES DE ANÁLISE:
1. Analise o contexto empresarial e propósito da transação
2. Identifique insights para categorização de produtos/serviços
3. Avalie o relacionamento com o fornecedor
4. Detecte padrões incomuns ou anomalias
5. Determine implicações estratégicas empresariais

FORMATO DE RESPOSTA (JSON):
{{
    "tipo_documento": "NF-e|NFS-e|CT-e|outro",
    "contexto_empresarial": {{
        "proposito_transacao": "finalidade da transação",
        "categoria_operacao": "tipo de operação comercial",
        "impacto_cadeia_suprimentos": "impacto na cadeia",
        "sazonalidade_detectada": "padrões sazonais identificados"
    }},
    "insights_principais": [
        "insight 1 sobre o documento",
        "insight 2 sobre padrões identificados"
    ],
    "categorizacao_inteligente": {{
        "produtos_servicos": [
            {{
                "item": "nome do item",
                "categoria_sugerida": "categoria empresarial",
                "justificativa": "razão da categorização",
                "impacto_empresarial": "impacto nos negócios"
            }}
        ]
    }},
    "analise_fornecedor": {{
        "tipo_relacionamento": "estratégico|operacional|eventual",
        "importancia_relativa": "alta|media|baixa",
        "riscos_identificados": ["lista de riscos"],
        "oportunidades": ["lista de oportunidades"]
    }},
    "anomalias_detectadas": [
        {{
            "tipo_anomalia": "tipo da anomalia",
            "descricao": "descrição detalhada",
            "severidade": "alta|media|baixa",
            "recomendacao": "ação recomendada"
        }}
    ],
    "metricas_qualidade": {{
        "completude_dados": 0.0-1.0,
        "consistencia_interna": 0.0-1.0,
        "conformidade_fiscal": 0.0-1.0
    }},
    "implicacoes_estrategicas": [
        "implicação estratégica 1",
        "implicação estratégica 2"
    ],
    "score_confianca": 0.0-1.0,
    "recomendacoes_acao": [
        "recomendação 1",
        "recomendação 2"
    ]
}}

DIRETRIZES ESPECÍFICAS:
- Foque em insights de nível executivo, não detalhes técnicos
- Considere regulamentações fiscais brasileiras
- Identifique oportunidades de otimização de custos
- Avalie impactos na gestão de caixa e planejamento tributário
- Considere aspectos de compliance e auditoria""",
                variaveis_obrigatorias=["tipo_documento", "info_fornecedor", "itens", "valor_total"],
                variaveis_opcionais=["info_tributaria", "contexto_empresarial"],
                validacoes={
                    "tipo_documento": "deve ser NF-e, NFS-e, CT-e ou outro tipo válido",
                    "valor_total": "deve ser valor monetário válido"
                }
            ),
            
            # Template para categorização de produtos
            "categorizacao_produtos": TemplatePrompt(
                metadados=MetadadosPrompt(
                    nome="Categorização Inteligente de Produtos",
                    descricao="Categoriza produtos com compreensão de contexto empresarial",
                    tipo=TipoPrompt.CATEGORIZACAO_PRODUTOS,
                    nivel_complexidade=NivelComplexidade.MEDIO,
                    modelo_recomendado=ModeloLLM.GPT_4,
                    versao="1.0",
                    autor="Sistema",
                    data_criacao=datetime.now(),
                    data_atualizacao=datetime.now(),
                    tags=["categorizacao", "produtos", "ml", "classificacao"],
                    exemplos_uso=[
                        "Categorização de matérias-primas industriais",
                        "Classificação de produtos acabados",
                        "Organização de itens de consumo"
                    ],
                    metricas_performance={"precisao": 0.94, "tempo_medio": 1.8}
                ),
                template="""Você é um especialista em categorização de produtos para empresas brasileiras.

DADOS PARA CATEGORIZAÇÃO:
Produtos: {itens}
Tipo de Categoria: {tipo_categoria}
Contexto Empresarial: {contexto_empresarial}
Categorias Padrão Disponíveis: {categorias_padrao}

INSTRUÇÕES:
1. Analise cada produto considerando seu uso empresarial
2. Considere o contexto da empresa e setor de atuação
3. Use categorias existentes quando apropriado
4. Crie novas categorias quando necessário
5. Justifique cada categorização com lógica empresarial

FORMATO DE RESPOSTA (JSON):
{{
    "itens_categorizados": [
        {{
            "item": "nome do produto",
            "descricao_original": "descrição original",
            "categoria_atribuida": "categoria final",
            "subcategoria": "subcategoria se aplicável",
            "contexto_uso": "como é usado na empresa",
            "impacto_operacional": "impacto nas operações",
            "classificacao_fiscal": "classificação NCM se relevante",
            "score_confianca": 0.0-1.0
        }}
    ],
    "categorias_criadas": [
        {{
            "nome_categoria": "nova categoria",
            "descricao": "descrição da categoria",
            "criterios": "critérios de classificação",
            "produtos_exemplo": ["exemplos de produtos"]
        }}
    ],
    "estatisticas_categorizacao": {{
        "total_itens": 0,
        "categorias_usadas": 0,
        "categorias_novas": 0,
        "score_confianca_medio": 0.0-1.0
    }},
    "justificativas": {{
        "item_nome": "justificativa da categorização"
    }},
    "sugestoes_melhoria": [
        "sugestão 1 para melhorar categorização",
        "sugestão 2 para otimizar processo"
    ],
    "padroes_identificados": [
        "padrão 1 nos produtos",
        "padrão 2 na categorização"
    ]
}}

DIRETRIZES ESPECÍFICAS:
- Priorize utilidade empresarial sobre classificações técnicas
- Considere impacto em gestão de estoque e compras
- Mantenha consistência com padrões contábeis brasileiros
- Facilite relatórios gerenciais e análises de custo
- Considere aspectos tributários quando relevante""",
                variaveis_obrigatorias=["itens", "tipo_categoria"],
                variaveis_opcionais=["contexto_empresarial", "categorias_padrao"],
                validacoes={
                    "itens": "deve ser lista não vazia de produtos",
                    "tipo_categoria": "deve ser tipo válido de categorização"
                }
            ),
            
            # Template para tradução de consultas para SQL
            "traducao_sql": TemplatePrompt(
                metadados=MetadadosPrompt(
                    nome="Tradução Consulta Natural para SQL",
                    descricao="Converte perguntas empresariais em consultas SQL otimizadas",
                    tipo=TipoPrompt.TRADUCAO_SQL,
                    nivel_complexidade=NivelComplexidade.COMPLEXO,
                    modelo_recomendado=ModeloLLM.GPT_4,
                    versao="1.0",
                    autor="Sistema",
                    data_criacao=datetime.now(),
                    data_atualizacao=datetime.now(),
                    tags=["sql", "traducao", "consulta", "database"],
                    exemplos_uso=[
                        "Quais os maiores fornecedores por valor?",
                        "Produtos com maior crescimento no trimestre",
                        "Análise de sazonalidade por categoria"
                    ],
                    metricas_performance={"precisao": 0.91, "tempo_medio": 2.7}
                ),
                template="""Você é um desenvolvedor SQL especialista com profundo conhecimento das estruturas de dados fiscais brasileiros.

CONSULTA PARA TRADUÇÃO:
Pergunta Empresarial: {consulta_natural}
Schema do Banco: {schema_banco}
Regras de Negócio: {regras_negocio}
Relacionamentos de Dados: {relacionamentos_dados}
Exemplos Similares: {exemplos_consultas}
Cargo do Usuário: {cargo_usuario}

INSTRUÇÕES:
1. Entenda a intenção empresarial da pergunta
2. Identifique tabelas e campos necessários
3. Construa consulta SQL otimizada
4. Inclua lógica de negócio apropriada
5. Considere performance e índices
6. Valide contra regras de negócio

FORMATO DE RESPOSTA (JSON):
{{
    "consulta_sql": "SELECT ... FROM ... WHERE ...",
    "explicacao_logica": "explicação da lógica empresarial implementada",
    "tabelas_utilizadas": [
        {{
            "tabela": "nome_tabela",
            "proposito": "por que foi usada",
            "campos_principais": ["campo1", "campo2"]
        }}
    ],
    "joins_realizados": [
        {{
            "tipo_join": "INNER|LEFT|RIGHT",
            "tabelas": "tabela1 JOIN tabela2",
            "condicao": "condição do join",
            "justificativa": "por que este join"
        }}
    ],
    "filtros_aplicados": [
        {{
            "campo": "nome_campo",
            "condicao": "condição aplicada",
            "valor": "valor do filtro",
            "justificativa_empresarial": "razão empresarial"
        }}
    ],
    "otimizacoes_aplicadas": [
        "otimização 1",
        "otimização 2"
    ],
    "metricas_estimadas": {{
        "linhas_estimadas": 0,
        "tempo_execucao_estimado": "segundos",
        "complexidade": "baixa|media|alta",
        "uso_indices": ["índices utilizados"]
    }},
    "validacoes_negocio": [
        "validação 1 aplicada",
        "validação 2 considerada"
    ],
    "sugestoes_otimizacao": [
        "sugestão 1 para melhorar performance",
        "sugestão 2 para otimizar resultado"
    ],
    "problemas_potenciais": [
        "problema 1 identificado",
        "problema 2 possível"
    ],
    "score_confianca": 0.0-1.0,
    "consultas_relacionadas": [
        "consulta relacionada 1",
        "consulta relacionada 2"
    ]
}}

DIRETRIZES ESPECÍFICAS:
- Priorize clareza e performance da consulta
- Use padrões SQL apropriados para PostgreSQL
- Considere impacto em relatórios executivos
- Implemente filtros de segurança quando necessário
- Otimize para grandes volumes de dados fiscais
- Mantenha compatibilidade com ferramentas de BI""",
                variaveis_obrigatorias=["consulta_natural", "schema_banco"],
                variaveis_opcionais=["regras_negocio", "relacionamentos_dados", "exemplos_consultas", "cargo_usuario"],
                validacoes={
                    "consulta_natural": "deve ser pergunta empresarial válida",
                    "schema_banco": "deve conter informações válidas do schema"
                }
            ),
            
            # Template para geração de relatórios executivos
            "relatorio_executivo": TemplatePrompt(
                metadados=MetadadosPrompt(
                    nome="Geração de Relatório Executivo",
                    descricao="Gera relatórios executivos com insights e recomendações",
                    tipo=TipoPrompt.GERACAO_RELATORIO,
                    nivel_complexidade=NivelComplexidade.COMPLEXO,
                    modelo_recomendado=ModeloLLM.GPT_4,
                    versao="1.0",
                    autor="Sistema",
                    data_criacao=datetime.now(),
                    data_atualizacao=datetime.now(),
                    tags=["relatorio", "executivo", "insights", "recomendacoes"],
                    exemplos_uso=[
                        "Relatório mensal de fornecedores",
                        "Análise trimestral de categorias",
                        "Dashboard executivo de compras"
                    ],
                    metricas_performance={"precisao": 0.88, "tempo_medio": 4.2}
                ),
                template="""Você é um especialista em relatórios executivos para o mercado brasileiro.

DADOS PARA RELATÓRIO:
Dados Analisados: {dados_analisados}
Insights Gerados: {insights_gerados}
Contexto Empresarial: {contexto_empresarial}
Público Executivo: {publico_executivo}
Período Analisado: {periodo_analisado}

INSTRUÇÕES:
1. Crie resumo executivo focado em decisões
2. Destaque descobertas principais e tendências
3. Identifique implicações estratégicas
4. Gere recomendações acionáveis
5. Use linguagem apropriada para executivos

FORMATO DE RESPOSTA (JSON):
{{
    "resumo_executivo": {{
        "principais_descobertas": [
            "descoberta 1 com impacto quantificado",
            "descoberta 2 com relevância estratégica"
        ],
        "metricas_chave": {{
            "metrica_1": {{
                "valor": "valor atual",
                "variacao": "% de mudança",
                "benchmark": "comparação com período anterior",
                "status": "positivo|negativo|neutro"
            }}
        }},
        "alertas_criticos": [
            "alerta 1 que requer ação imediata",
            "alerta 2 com impacto significativo"
        ]
    }},
    "analise_detalhada": {{
        "tendencias_identificadas": [
            {{
                "tendencia": "nome da tendência",
                "descricao": "descrição detalhada",
                "impacto_estimado": "impacto nos negócios",
                "confiabilidade": 0.0-1.0,
                "prazo_manifestacao": "curto|medio|longo prazo"
            }}
        ],
        "comparacoes_historicas": [
            {{
                "periodo": "período de comparação",
                "variacao": "% de mudança",
                "fatores_influencia": ["fator 1", "fator 2"],
                "significancia": "alta|media|baixa"
            }}
        ]
    }},
    "recomendacoes_estrategicas": [
        {{
            "recomendacao": "ação recomendada",
            "justificativa": "por que é importante",
            "impacto_esperado": "resultado esperado",
            "prazo_implementacao": "tempo necessário",
            "recursos_necessarios": "recursos requeridos",
            "prioridade": "alta|media|baixa",
            "riscos_nao_implementacao": "riscos de não agir"
        }}
    ],
    "proximos_passos": [
        {{
            "acao": "próxima ação",
            "responsavel_sugerido": "quem deve executar",
            "prazo": "quando executar",
            "dependencias": ["dependência 1", "dependência 2"]
        }}
    ],
    "metricas_acompanhamento": [
        {{
            "metrica": "nome da métrica",
            "frequencia_monitoramento": "diária|semanal|mensal",
            "meta_sugerida": "meta recomendada",
            "fonte_dados": "de onde vem o dado"
        }}
    ],
    "anexos_sugeridos": [
        "gráfico 1 recomendado",
        "tabela 2 detalhada"
    ]
}}

DIRETRIZES ESPECÍFICAS:
- Use linguagem executiva clara e objetiva
- Quantifique impactos sempre que possível
- Priorize ações com maior ROI
- Considere restrições orçamentárias típicas
- Mantenha foco em resultados de negócio
- Inclua perspectiva de risco e oportunidade""",
                variaveis_obrigatorias=["dados_analisados", "publico_executivo"],
                variaveis_opcionais=["insights_gerados", "contexto_empresarial", "periodo_analisado"],
                validacoes={
                    "dados_analisados": "deve conter dados válidos para análise",
                    "publico_executivo": "deve especificar nível executivo"
                }
            )
        }
        
        # Carregar templates no gerenciador
        for nome, template in templates_padrao.items():
            self.templates[nome] = template
    
    def obter_template(self, nome_template: str) -> Optional[TemplatePrompt]:
        """Obtém template por nome"""
        return self.templates.get(nome_template)
    
    def obter_template_por_tipo(self, tipo: TipoPrompt) -> List[TemplatePrompt]:
        """Obtém templates por tipo"""
        return [
            template for template in self.templates.values()
            if template.metadados.tipo == tipo
        ]
    
    def renderizar_template(
        self, 
        nome_template: str, 
        variaveis: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Renderiza template com variáveis fornecidas
        Retorna (template_renderizado, lista_de_erros)
        """
        template = self.obter_template(nome_template)
        if not template:
            return "", [f"Template '{nome_template}' não encontrado"]
        
        # Validar variáveis obrigatórias
        erros = []
        for var_obrigatoria in template.variaveis_obrigatorias:
            if var_obrigatoria not in variaveis:
                erros.append(f"Variável obrigatória '{var_obrigatoria}' não fornecida")
        
        if erros:
            return "", erros
        
        # Aplicar validações específicas
        for var, regra in template.validacoes.items():
            if var in variaveis:
                if not self._validar_variavel(variaveis[var], regra):
                    erros.append(f"Variável '{var}' não atende à validação: {regra}")
        
        if erros:
            return "", erros
        
        # Preparar variáveis com valores padrão para opcionais
        variaveis_completas = variaveis.copy()
        for var_opcional in template.variaveis_opcionais:
            if var_opcional not in variaveis_completas:
                variaveis_completas[var_opcional] = self._obter_valor_padrao(var_opcional)
        
        # Renderizar template
        try:
            template_renderizado = template.template.format(**variaveis_completas)
            
            # Registrar uso para métricas
            self._registrar_uso_template(nome_template)
            
            return template_renderizado, []
            
        except KeyError as e:
            return "", [f"Variável não encontrada no template: {e}"]
        except Exception as e:
            return "", [f"Erro ao renderizar template: {e}"]
    
    def adicionar_template(self, nome: str, template: TemplatePrompt) -> bool:
        """Adiciona novo template ao gerenciador"""
        try:
            # Validar template
            erros_validacao = self._validar_template(template)
            if erros_validacao:
                logger.error(f"Erro ao validar template '{nome}': {erros_validacao}")
                return False
            
            self.templates[nome] = template
            logger.info(f"Template '{nome}' adicionado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar template '{nome}': {e}")
            return False
    
    def atualizar_template(self, nome: str, template: TemplatePrompt) -> bool:
        """Atualiza template existente"""
        if nome not in self.templates:
            logger.error(f"Template '{nome}' não existe para atualização")
            return False
        
        return self.adicionar_template(nome, template)
    
    def remover_template(self, nome: str) -> bool:
        """Remove template do gerenciador"""
        if nome in self.templates:
            del self.templates[nome]
            logger.info(f"Template '{nome}' removido")
            return True
        return False
    
    def listar_templates(self) -> List[str]:
        """Lista nomes de todos os templates"""
        return list(self.templates.keys())
    
    def obter_metricas_template(self, nome_template: str) -> Dict[str, Any]:
        """Obtém métricas de uso de um template"""
        return self.metricas_uso.get(nome_template, {
            "total_usos": 0,
            "ultima_utilizacao": None,
            "tempo_medio_renderizacao": 0.0,
            "taxa_erro": 0.0
        })
    
    def obter_templates_recomendados(
        self, 
        tipo: Optional[TipoPrompt] = None,
        modelo: Optional[ModeloLLM] = None,
        complexidade: Optional[NivelComplexidade] = None
    ) -> List[str]:
        """Obtém templates recomendados baseado em critérios"""
        templates_filtrados = []
        
        for nome, template in self.templates.items():
            if tipo and template.metadados.tipo != tipo:
                continue
            if modelo and template.metadados.modelo_recomendado != modelo:
                continue
            if complexidade and template.metadados.nivel_complexidade != complexidade:
                continue
            
            templates_filtrados.append(nome)
        
        # Ordenar por métricas de performance
        templates_filtrados.sort(
            key=lambda nome: self.templates[nome].metadados.metricas_performance.get("precisao", 0),
            reverse=True
        )
        
        return templates_filtrados
    
    def otimizar_template(self, nome_template: str) -> Dict[str, Any]:
        """Analisa e sugere otimizações para template"""
        template = self.obter_template(nome_template)
        if not template:
            return {"erro": "Template não encontrado"}
        
        sugestoes = []
        
        # Analisar comprimento do template
        if len(template.template) > 3000:
            sugestoes.append("Template muito longo - considere dividir em seções")
        
        # Analisar número de variáveis
        total_vars = len(template.variaveis_obrigatorias) + len(template.variaveis_opcionais)
        if total_vars > 10:
            sugestoes.append("Muitas variáveis - considere agrupar em objetos")
        
        # Analisar métricas de performance
        metricas = template.metadados.metricas_performance
        if metricas.get("precisao", 0) < 0.8:
            sugestoes.append("Baixa precisão - revisar instruções e exemplos")
        
        if metricas.get("tempo_medio", 0) > 5.0:
            sugestoes.append("Tempo de processamento alto - simplificar template")
        
        return {
            "template": nome_template,
            "sugestoes_otimizacao": sugestoes,
            "metricas_atuais": metricas,
            "score_qualidade": self._calcular_score_qualidade(template)
        }
    
    # Métodos privados de apoio
    
    def _validar_variavel(self, valor: Any, regra: str) -> bool:
        """Valida variável contra regra específica"""
        try:
            if "não vazia" in regra and not valor:
                return False
            if "lista não vazia" in regra and (not isinstance(valor, list) or len(valor) == 0):
                return False
            if "valor monetário" in regra and not isinstance(valor, (int, float)):
                return False
            return True
        except:
            return False
    
    def _obter_valor_padrao(self, variavel: str) -> str:
        """Obtém valor padrão para variável opcional"""
        valores_padrao = {
            "contexto_empresarial": "{}",
            "dados_disponiveis": "Dados fiscais padrão disponíveis",
            "historico_conversa": "Primeira interação",
            "info_tributaria": "Informações tributárias padrão",
            "categorias_padrao": "[]",
            "regras_negocio": "Regras de negócio padrão",
            "exemplos_consultas": "[]",
            "cargo_usuario": "Executivo",
            "insights_gerados": "{}",
            "periodo_analisado": "Período atual"
        }
        return valores_padrao.get(variavel, "")
    
    def _validar_template(self, template: TemplatePrompt) -> List[str]:
        """Valida estrutura do template"""
        erros = []
        
        if not template.template:
            erros.append("Template não pode estar vazio")
        
        if not template.variaveis_obrigatorias:
            erros.append("Template deve ter pelo menos uma variável obrigatória")
        
        # Verificar se todas as variáveis no template estão declaradas
        variaveis_no_template = re.findall(r'\{(\w+)\}', template.template)
        variaveis_declaradas = set(template.variaveis_obrigatorias + template.variaveis_opcionais)
        
        for var in variaveis_no_template:
            if var not in variaveis_declaradas:
                erros.append(f"Variável '{var}' usada no template mas não declarada")
        
        return erros
    
    def _registrar_uso_template(self, nome_template: str):
        """Registra uso do template para métricas"""
        if nome_template not in self.metricas_uso:
            self.metricas_uso[nome_template] = {
                "total_usos": 0,
                "ultima_utilizacao": None,
                "tempo_medio_renderizacao": 0.0,
                "taxa_erro": 0.0
            }
        
        self.metricas_uso[nome_template]["total_usos"] += 1
        self.metricas_uso[nome_template]["ultima_utilizacao"] = datetime.now()
    
    def _calcular_score_qualidade(self, template: TemplatePrompt) -> float:
        """Calcula score de qualidade do template"""
        score = 0.0
        
        # Métricas de performance (40%)
        metricas = template.metadados.metricas_performance
        score += metricas.get("precisao", 0) * 0.4
        
        # Completude da documentação (30%)
        if template.metadados.descricao:
            score += 0.1
        if template.metadados.exemplos_uso:
            score += 0.1
        if template.validacoes:
            score += 0.1
        
        # Estrutura do template (30%)
        if len(template.variaveis_obrigatorias) <= 5:  # Não muito complexo
            score += 0.1
        if len(template.template) < 2000:  # Tamanho razoável
            score += 0.1
        if template.variaveis_opcionais:  # Flexibilidade
            score += 0.1
        
        return min(score, 1.0)


# Instância global do gerenciador
gerenciador_prompts = GerenciadorTemplatesPrompts()