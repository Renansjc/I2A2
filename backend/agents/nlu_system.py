"""
Natural Language Understanding System for Master Agent
Implements intent recognition and entity extraction using spaCy and transformers
"""

import spacy
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import structlog

logger = structlog.get_logger(__name__)


class Intent(Enum):
    """Tipos de intenção do usuário"""
    CONSULTA_DADOS = "consulta_dados"
    GERAR_RELATORIO = "gerar_relatorio"
    AGENDAR_TAREFA = "agendar_tarefa"
    ANALISAR_TENDENCIAS = "analisar_tendencias"
    COMPARAR_PERIODOS = "comparar_periodos"
    LISTAR_FORNECEDORES = "listar_fornecedores"
    ANALISAR_PRODUTOS = "analisar_produtos"
    VERIFICAR_IMPOSTOS = "verificar_impostos"
    DESCONHECIDO = "desconhecido"


class EntityType(Enum):
    """Tipos de entidades reconhecidas"""
    PERIODO_TEMPO = "periodo_tempo"
    TIPO_DOCUMENTO = "tipo_documento"
    FORMATO_RELATORIO = "formato_relatorio"
    FORNECEDOR = "fornecedor"
    PRODUTO = "produto"
    SERVICO = "servico"
    VALOR_MONETARIO = "valor_monetario"
    IMPOSTO = "imposto"
    REGIAO = "regiao"
    CATEGORIA = "categoria"


@dataclass
class Entity:
    """Entidade extraída do texto"""
    type: EntityType
    value: str
    confidence: float
    start: int
    end: int


@dataclass
class IntentResult:
    """Resultado da análise de intenção"""
    intent: Intent
    confidence: float
    entities: List[Entity]
    normalized_query: str
    parameters: Dict[str, Any]


class NLUSystem:
    """Sistema de Compreensão de Linguagem Natural"""
    
    def __init__(self):
        self.nlp = None
        self.intent_classifier = None
        self.tokenizer = None
        self.intent_patterns = {}
        self.entity_patterns = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializa o sistema NLU"""
        try:
            logger.info("Inicializando sistema NLU...")
            
            # Carrega modelo spaCy para português
            await self._load_spacy_model()
            
            # Carrega classificador de intenções
            await self._load_intent_classifier()
            
            # Carrega padrões de reconhecimento
            await self._load_patterns()
            
            self.is_initialized = True
            logger.info("Sistema NLU inicializado com sucesso")
            
        except Exception as e:
            logger.error("Erro ao inicializar sistema NLU", error=str(e))
            raise
    
    async def _load_spacy_model(self):
        """Carrega modelo spaCy"""
        try:
            # Tenta carregar modelo em português
            try:
                self.nlp = spacy.load("pt_core_news_sm")
            except OSError:
                logger.warning("Modelo pt_core_news_sm não encontrado, usando modelo em inglês")
                self.nlp = spacy.load("en_core_web_sm")
            
            logger.info("Modelo spaCy carregado")
            
        except Exception as e:
            logger.error("Erro ao carregar modelo spaCy", error=str(e))
            # Fallback para modelo básico
            self.nlp = spacy.blank("pt")
            logger.info("Usando modelo spaCy básico")
    
    async def _load_intent_classifier(self):
        """Carrega classificador de intenções usando transformers"""
        try:
            # Para este exemplo, usaremos um classificador baseado em padrões
            # Em produção, seria treinado um modelo específico
            
            # Configuração do pipeline de classificação
            device = 0 if torch.cuda.is_available() else -1
            
            # Usando modelo multilingual para classificação de texto
            model_name = "microsoft/DialoGPT-medium"
            
            # Por enquanto, implementaremos classificação baseada em regras
            # que é mais confiável para este domínio específico
            
            logger.info("Classificador de intenções configurado")
            
        except Exception as e:
            logger.error("Erro ao carregar classificador", error=str(e))
            # Continua com classificação baseada em regras
    
    async def _load_patterns(self):
        """Carrega padrões de reconhecimento de intenções e entidades"""
        
        # Padrões de intenção em português
        self.intent_patterns = {
            Intent.CONSULTA_DADOS: [
                r'\b(quanto|qual|quais|como|quando|onde)\b',
                r'\b(mostrar|listar|buscar|encontrar|consultar|ver)\b',
                r'\b(dados|informações|detalhes)\b',
                r'\b(fornecedor|produto|serviço|valor|total|quantidade)\b'
            ],
            Intent.GERAR_RELATORIO: [
                r'\b(relatório|report|gerar|criar|exportar)\b',
                r'\b(pdf|excel|xlsx|word|docx)\b',
                r'\b(relatório de|relatório sobre)\b',
                r'\b(imprimir|salvar|baixar)\b'
            ],
            Intent.AGENDAR_TAREFA: [
                r'\b(agendar|programar|automatizar|recorrente)\b',
                r'\b(diário|semanal|mensal|anual)\b',
                r'\b(toda|todo|a cada)\b',
                r'\b(schedule|cron|automático)\b'
            ],
            Intent.ANALISAR_TENDENCIAS: [
                r'\b(tendência|padrão|análise|comparar)\b',
                r'\b(crescimento|redução|evolução|histórico)\b',
                r'\b(trend|pattern|analysis)\b',
                r'\b(ao longo do tempo|no período)\b'
            ],
            Intent.COMPARAR_PERIODOS: [
                r'\b(comparar|comparação|versus|vs)\b',
                r'\b(período|mês|ano|trimestre)\b',
                r'\b(anterior|passado|último)\b',
                r'\b(diferença|variação)\b'
            ],
            Intent.LISTAR_FORNECEDORES: [
                r'\b(fornecedor|supplier|empresa)\b',
                r'\b(listar|mostrar|quais)\b',
                r'\b(cnpj|razão social)\b'
            ],
            Intent.ANALISAR_PRODUTOS: [
                r'\b(produto|item|mercadoria)\b',
                r'\b(mais vendido|mais comprado|top)\b',
                r'\b(categoria|ncm|cfop)\b'
            ],
            Intent.VERIFICAR_IMPOSTOS: [
                r'\b(imposto|taxa|tributo)\b',
                r'\b(icms|ipi|pis|cofins|issqn)\b',
                r'\b(alíquota|base de cálculo)\b'
            ]
        }
        
        # Padrões de entidades
        self.entity_patterns = {
            EntityType.PERIODO_TEMPO: [
                r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b',
                r'\b(2024|2023|2022|2021|2020)\b',
                r'\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b',
                r'\b(hoje|ontem|semana passada|mês passado|ano passado)\b',
                r'\b(último|última|últimos|últimas)\s+(dia|semana|mês|ano|trimestre)\b'
            ],
            EntityType.TIPO_DOCUMENTO: [
                r'\b(nfe|nf-e|nota fiscal eletrônica)\b',
                r'\b(nfse|nfs-e|nota fiscal de serviço)\b'
            ],
            EntityType.FORMATO_RELATORIO: [
                r'\b(pdf|excel|xlsx|word|docx|csv)\b'
            ],
            EntityType.VALOR_MONETARIO: [
                r'R\$\s*\d+(?:\.\d{3})*(?:,\d{2})?',
                r'\d+(?:\.\d{3})*(?:,\d{2})?\s*reais?',
                r'\b(mil|milhão|milhões|bilhão|bilhões)\b'
            ],
            EntityType.IMPOSTO: [
                r'\b(icms|ipi|pis|cofins|issqn|iss)\b'
            ],
            EntityType.REGIAO: [
                r'\b(sp|rj|mg|rs|pr|sc|ba|go|pe|ce|pa|ma|pb|rn|al|se|pi|ac|ro|rr|ap|am|to|df)\b',
                r'\b(são paulo|rio de janeiro|minas gerais|rio grande do sul)\b'
            ]
        }
        
        logger.info("Padrões de reconhecimento carregados")
    
    async def analyze_query(self, query: str) -> IntentResult:
        """Analisa consulta em linguagem natural"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info("Analisando consulta", query=query)
            
            # Normaliza o texto
            normalized_query = await self._normalize_text(query)
            
            # Processa com spaCy
            doc = self.nlp(normalized_query)
            
            # Detecta intenção
            intent, intent_confidence = await self._detect_intent(normalized_query, doc)
            
            # Extrai entidades
            entities = await self._extract_entities(normalized_query, doc)
            
            # Extrai parâmetros adicionais
            parameters = await self._extract_parameters(normalized_query, doc, entities)
            
            result = IntentResult(
                intent=intent,
                confidence=intent_confidence,
                entities=entities,
                normalized_query=normalized_query,
                parameters=parameters
            )
            
            logger.info("Análise concluída", 
                       intent=intent.value, 
                       confidence=intent_confidence,
                       entities_count=len(entities))
            
            return result
            
        except Exception as e:
            logger.error("Erro na análise da consulta", error=str(e))
            return IntentResult(
                intent=Intent.DESCONHECIDO,
                confidence=0.0,
                entities=[],
                normalized_query=query,
                parameters={}
            )
    
    async def _normalize_text(self, text: str) -> str:
        """Normaliza texto para processamento"""
        # Remove caracteres especiais desnecessários
        text = re.sub(r'[^\w\s\-.,!?]', '', text)
        
        # Converte para minúsculas
        text = text.lower()
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _detect_intent(self, query: str, doc) -> Tuple[Intent, float]:
        """Detecta intenção da consulta"""
        intent_scores = {}
        
        # Calcula pontuação para cada intenção baseada em padrões
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matches += 1
                    # Pontuação baseada na especificidade do padrão
                    score += len(pattern) / 10
            
            if matches > 0:
                # Normaliza pontuação pelo número de padrões
                intent_scores[intent] = score / len(patterns)
        
        # Aplica regras específicas para melhorar precisão
        intent_scores = await self._apply_intent_rules(query, doc, intent_scores)
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent], 1.0)
            
            # Threshold mínimo de confiança
            if confidence < 0.3:
                return Intent.DESCONHECIDO, confidence
            
            return best_intent, confidence
        
        return Intent.DESCONHECIDO, 0.0
    
    async def _apply_intent_rules(self, query: str, doc, scores: Dict[Intent, float]) -> Dict[Intent, float]:
        """Aplica regras específicas para refinar detecção de intenção"""
        
        # Regra: Se menciona formato de arquivo, provavelmente quer gerar relatório
        if re.search(r'\b(pdf|excel|xlsx|word|docx)\b', query, re.IGNORECASE):
            scores[Intent.GERAR_RELATORIO] = scores.get(Intent.GERAR_RELATORIO, 0) + 0.5
        
        # Regra: Se menciona agendamento, é tarefa recorrente
        if re.search(r'\b(todo|toda|diário|semanal|mensal)\b', query, re.IGNORECASE):
            scores[Intent.AGENDAR_TAREFA] = scores.get(Intent.AGENDAR_TAREFA, 0) + 0.4
        
        # Regra: Se menciona comparação temporal, é análise de tendências
        if re.search(r'\b(comparar|versus|anterior|passado|evolução)\b', query, re.IGNORECASE):
            scores[Intent.ANALISAR_TENDENCIAS] = scores.get(Intent.ANALISAR_TENDENCIAS, 0) + 0.3
        
        # Regra: Perguntas diretas são consultas de dados
        if re.search(r'^\s*(quanto|qual|quais|como|quando|onde)', query, re.IGNORECASE):
            scores[Intent.CONSULTA_DADOS] = scores.get(Intent.CONSULTA_DADOS, 0) + 0.6
        
        return scores
    
    async def _extract_entities(self, query: str, doc) -> List[Entity]:
        """Extrai entidades do texto"""
        entities = []
        
        # Extração baseada em padrões regex
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        type=entity_type,
                        value=match.group(),
                        confidence=0.8,  # Confiança baseada em regex
                        start=match.start(),
                        end=match.end()
                    )
                    entities.append(entity)
        
        # Extração usando spaCy NER
        for ent in doc.ents:
            entity_type = await self._map_spacy_entity(ent.label_)
            if entity_type:
                entity = Entity(
                    type=entity_type,
                    value=ent.text,
                    confidence=0.7,  # Confiança do spaCy
                    start=ent.start_char,
                    end=ent.end_char
                )
                entities.append(entity)
        
        # Remove duplicatas e ordena por posição
        entities = await self._deduplicate_entities(entities)
        entities.sort(key=lambda x: x.start)
        
        return entities
    
    async def _map_spacy_entity(self, spacy_label: str) -> Optional[EntityType]:
        """Mapeia labels do spaCy para tipos de entidade do sistema"""
        mapping = {
            'PERSON': None,  # Não relevante para nosso domínio
            'ORG': EntityType.FORNECEDOR,
            'MONEY': EntityType.VALOR_MONETARIO,
            'DATE': EntityType.PERIODO_TEMPO,
            'TIME': EntityType.PERIODO_TEMPO,
            'GPE': EntityType.REGIAO,  # Geopolitical entity
            'LOC': EntityType.REGIAO,
        }
        return mapping.get(spacy_label)
    
    async def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove entidades duplicadas ou sobrepostas"""
        if not entities:
            return entities
        
        # Ordena por posição
        entities.sort(key=lambda x: (x.start, x.end))
        
        deduplicated = []
        for entity in entities:
            # Verifica sobreposição com entidades já adicionadas
            overlaps = False
            for existing in deduplicated:
                if (entity.start < existing.end and entity.end > existing.start):
                    # Mantém a entidade com maior confiança
                    if entity.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                deduplicated.append(entity)
        
        return deduplicated
    
    async def _extract_parameters(self, query: str, doc, entities: List[Entity]) -> Dict[str, Any]:
        """Extrai parâmetros adicionais da consulta"""
        parameters = {}
        
        # Extrai período de tempo específico
        time_entities = [e for e in entities if e.type == EntityType.PERIODO_TEMPO]
        if time_entities:
            parameters['periodo'] = time_entities[0].value
        
        # Extrai tipo de documento
        doc_entities = [e for e in entities if e.type == EntityType.TIPO_DOCUMENTO]
        if doc_entities:
            parameters['tipo_documento'] = doc_entities[0].value.upper()
        
        # Extrai formato de relatório
        format_entities = [e for e in entities if e.type == EntityType.FORMATO_RELATORIO]
        if format_entities:
            parameters['formato'] = format_entities[0].value.lower()
        
        # Extrai valores monetários
        money_entities = [e for e in entities if e.type == EntityType.VALOR_MONETARIO]
        if money_entities:
            parameters['valor'] = money_entities[0].value
        
        # Detecta agregações (soma, média, etc.)
        if re.search(r'\b(total|soma|somar)\b', query, re.IGNORECASE):
            parameters['agregacao'] = 'sum'
        elif re.search(r'\b(média|media|médio)\b', query, re.IGNORECASE):
            parameters['agregacao'] = 'avg'
        elif re.search(r'\b(máximo|maior|max)\b', query, re.IGNORECASE):
            parameters['agregacao'] = 'max'
        elif re.search(r'\b(mínimo|menor|min)\b', query, re.IGNORECASE):
            parameters['agregacao'] = 'min'
        
        # Detecta ordenação
        if re.search(r'\b(maior|crescente|asc)\b', query, re.IGNORECASE):
            parameters['ordenacao'] = 'desc'
        elif re.search(r'\b(menor|decrescente|desc)\b', query, re.IGNORECASE):
            parameters['ordenacao'] = 'asc'
        
        # Detecta limite de resultados
        limit_match = re.search(r'\b(top|primeiro|primeiros)\s*(\d+)\b', query, re.IGNORECASE)
        if limit_match:
            parameters['limite'] = int(limit_match.group(2))
        
        return parameters
    
    async def get_intent_suggestions(self, partial_query: str) -> List[str]:
        """Retorna sugestões de consultas baseadas no texto parcial"""
        suggestions = []
        
        # Sugestões baseadas em padrões comuns
        common_queries = [
            "Gerar relatório mensal de fornecedores em PDF",
            "Mostrar produtos mais comprados no último mês",
            "Agendar relatório semanal de impostos",
            "Comparar vendas do mês atual com o anterior",
            "Listar fornecedores por região",
            "Analisar tendência de preços dos produtos",
            "Verificar total de ICMS do trimestre",
            "Exportar dados de NF-e em Excel"
        ]
        
        # Filtra sugestões baseadas no texto parcial
        partial_lower = partial_query.lower()
        for query in common_queries:
            if any(word in query.lower() for word in partial_lower.split()):
                suggestions.append(query)
        
        return suggestions[:5]  # Retorna até 5 sugestões