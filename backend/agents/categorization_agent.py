"""
Agente de Categorização
Adaptado dos agentes CrewAI do projeto alternativo
Mantém CrewAI para orquestração mas simplifica número de agentes
"""

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re


class CategorizationAgent:
    """
    Agente especializado em categorização inteligente de produtos, serviços e fornecedores.
    Usa CrewAI para orquestração e aplica contexto de negócios brasileiros.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.name = "Categorization Agent"
        self.version = "1.0.0"
        self.openai_api_key = openai_api_key
        self.model = model
        
        # Inicializar LLM se API key disponível
        if self.openai_api_key:
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model=self.model,
                temperature=0.1
            )
        else:
            self.llm = None
        
        # Categorias padrão brasileiras
        self.categorias_produtos = {
            "Alimentação": ["alimento", "bebida", "comida", "lanche", "refeição", "café", "água", "suco"],
            "Tecnologia": ["computador", "software", "hardware", "sistema", "aplicativo", "licença", "equipamento"],
            "Serviços": ["consultoria", "manutenção", "suporte", "treinamento", "desenvolvimento", "análise"],
            "Material de Escritório": ["papel", "caneta", "impressora", "toner", "material", "escritório"],
            "Transporte": ["combustível", "frete", "entrega", "transporte", "logística", "correio"],
            "Telecomunicações": ["telefone", "internet", "comunicação", "dados", "linha", "plano"],
            "Energia": ["energia", "elétrica", "luz", "conta", "consumo", "kwh"],
            "Limpeza": ["limpeza", "higiene", "produto", "detergente", "sabão", "papel higiênico"],
            "Móveis": ["mesa", "cadeira", "armário", "móvel", "mobiliário", "decoração"],
            "Outros": []  # Categoria padrão para itens não classificados
        }
        
        # Tipos de fornecedores brasileiros
        self.tipos_fornecedores = {
            "Distribuidora": ["distribuidora", "distribuição", "atacado", "comercial"],
            "Prestadora de Serviços": ["serviços", "consultoria", "manutenção", "suporte"],
            "Indústria": ["indústria", "industrial", "fabricante", "manufatura"],
            "Varejo": ["loja", "varejo", "comércio", "mercado"],
            "Tecnologia": ["tecnologia", "software", "sistemas", "informática"],
            "Governo": ["prefeitura", "governo", "municipal", "estadual", "federal"],
            "Outros": []
        }
    
    def categorize_document(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categoriza documento completo incluindo itens, fornecedor e contexto de negócio
        
        Args:
            extracted_data: Dados extraídos pelo XMLProcessingAgent
            
        Returns:
            Dict com dados categorizados e insights de confiança
        """
        try:
            # Categorizar itens
            categorized_items = self._categorize_items(extracted_data.get('itens', []))
            
            # Categorizar fornecedor
            supplier_category = self._categorize_supplier(extracted_data.get('emitente', {}))
            
            # Análise de padrões e tendências
            patterns = self._analyze_patterns(categorized_items, supplier_category)
            
            # Gerar insights com IA se disponível
            ai_insights = None
            if self.llm:
                ai_insights = self._generate_ai_insights(extracted_data, categorized_items, supplier_category)
            
            return {
                "categorized_items": categorized_items,
                "supplier_category": supplier_category,
                "patterns": patterns,
                "ai_insights": ai_insights,
                "categorization_metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "processed_at": datetime.now().isoformat(),
                    "method": "ai_enhanced" if self.llm else "rule_based",
                    "confidence": self._calculate_overall_confidence(categorized_items, supplier_category)
                }
            }
            
        except Exception as e:
            return {
                "categorized_items": [],
                "supplier_category": {"type": "Outros", "confidence": 0.0},
                "patterns": {},
                "ai_insights": None,
                "categorization_metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "processed_at": datetime.now().isoformat(),
                    "method": "error",
                    "error": str(e),
                    "confidence": 0.0
                }
            }
    
    def _categorize_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categoriza lista de itens usando regras e IA"""
        categorized = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            descricao = item.get('descricao', '').lower() if item.get('descricao') else ''
            
            # Categorização baseada em regras
            categoria_regra, confianca_regra = self._categorize_by_rules(descricao)
            
            # Categorização com IA se disponível
            categoria_ia, confianca_ia = None, 0.0
            if self.llm and descricao:
                categoria_ia, confianca_ia = self._categorize_with_ai(descricao)
            
            # Escolher melhor categorização
            if confianca_ia > confianca_regra:
                categoria_final = categoria_ia
                confianca_final = confianca_ia
                metodo = "ai"
            else:
                categoria_final = categoria_regra
                confianca_final = confianca_regra
                metodo = "rules"
            
            categorized_item = item.copy()
            categorized_item.update({
                'categoria': categoria_final,
                'categoria_confianca': confianca_final,
                'categoria_metodo': metodo,
                'categoria_alternativas': {
                    'regra': {'categoria': categoria_regra, 'confianca': confianca_regra},
                    'ia': {'categoria': categoria_ia, 'confianca': confianca_ia} if categoria_ia else None
                }
            })
            
            categorized.append(categorized_item)
        
        return categorized
    
    def _categorize_by_rules(self, descricao: str) -> tuple[str, float]:
        """Categorização baseada em regras heurísticas"""
        if not descricao:
            return "Outros", 0.0
        
        descricao_lower = descricao.lower()
        
        # Buscar matches nas categorias
        for categoria, keywords in self.categorias_produtos.items():
            if categoria == "Outros":
                continue
            
            matches = sum(1 for keyword in keywords if keyword in descricao_lower)
            if matches > 0:
                # Confiança baseada no número de matches e especificidade
                confianca = min(0.9, 0.3 + (matches * 0.2))
                return categoria, confianca
        
        return "Outros", 0.1
    
    def _categorize_with_ai(self, descricao: str) -> tuple[str, float]:
        """Categorização usando IA (CrewAI)"""
        try:
            # Criar agente especializado
            categorization_agent = Agent(
                role="Especialista em Categorização de Produtos Brasileiros",
                goal="Categorizar produtos e serviços brasileiros com alta precisão baseado na descrição",
                backstory=(
                    "Você é um especialista em classificação de produtos e serviços no mercado brasileiro. "
                    "Conhece as principais categorias de negócios, NCM, e padrões de nomenclatura usados "
                    "em documentos fiscais brasileiros."
                ),
                llm=self.llm,
                verbose=False
            )
            
            # Criar task de categorização
            categorization_task = Task(
                description=f"""
                Categorize o seguinte produto/serviço brasileiro em uma das categorias:
                {list(self.categorias_produtos.keys())}
                
                Descrição: "{descricao}"
                
                Retorne APENAS um JSON com:
                {{
                    "categoria": "nome_da_categoria",
                    "confianca": 0.85,
                    "justificativa": "breve explicação"
                }}
                
                Considere:
                - Terminologia brasileira comum
                - Contexto fiscal e comercial
                - Sinônimos e abreviações
                - Se não tiver certeza, use "Outros" com baixa confiança
                """,
                agent=categorization_agent,
                expected_output="JSON com categoria, confiança e justificativa"
            )
            
            # Executar com CrewAI
            crew = Crew(
                agents=[categorization_agent],
                tasks=[categorization_task],
                verbose=False
            )
            
            result = crew.kickoff()
            
            # Parse do resultado
            try:
                # Limpar resultado se necessário
                result_str = str(result).strip()
                if result_str.startswith('```json'):
                    result_str = result_str.replace('```json', '').replace('```', '').strip()
                
                parsed = json.loads(result_str)
                categoria = parsed.get('categoria', 'Outros')
                confianca = float(parsed.get('confianca', 0.5))
                
                # Validar categoria
                if categoria not in self.categorias_produtos:
                    categoria = "Outros"
                    confianca = 0.1
                
                return categoria, min(1.0, max(0.0, confianca))
                
            except (json.JSONDecodeError, ValueError, KeyError):
                return "Outros", 0.1
                
        except Exception as e:
            print(f"Erro na categorização IA: {e}")
            return "Outros", 0.1
    
    def _categorize_supplier(self, emitente: Dict[str, Any]) -> Dict[str, Any]:
        """Categoriza fornecedor baseado nos dados do emitente"""
        if not emitente or not isinstance(emitente, dict):
            return {"type": "Outros", "confidence": 0.0, "details": {}}
        
        razao_social = emitente.get('razao_social', '').lower() if emitente.get('razao_social') else ''
        cnpj = emitente.get('cnpj', '')
        
        # Categorização por razão social
        categoria_tipo = "Outros"
        confianca = 0.1
        
        for tipo, keywords in self.tipos_fornecedores.items():
            if tipo == "Outros":
                continue
            
            matches = sum(1 for keyword in keywords if keyword in razao_social)
            if matches > 0:
                categoria_tipo = tipo
                confianca = min(0.9, 0.4 + (matches * 0.2))
                break
        
        # Análise adicional do CNPJ (porte da empresa)
        porte = self._analyze_company_size(cnpj)
        
        return {
            "type": categoria_tipo,
            "confidence": confianca,
            "details": {
                "razao_social": emitente.get('razao_social'),
                "cnpj": cnpj,
                "porte": porte,
                "endereco": emitente.get('endereco')
            }
        }
    
    def _analyze_company_size(self, cnpj: str) -> str:
        """Análise básica do porte da empresa baseado no CNPJ"""
        if not cnpj:
            return "Desconhecido"
        
        # Remove caracteres não numéricos
        cnpj_digits = re.sub(r'\D', '', cnpj)
        
        if len(cnpj_digits) == 14:
            # Análise heurística simples baseada nos primeiros dígitos
            # Esta é uma simplificação - na prática seria necessário consultar base da Receita
            primeiro_digito = cnpj_digits[0]
            if primeiro_digito in ['0', '1', '2']:
                return "Grande Porte"
            elif primeiro_digito in ['3', '4', '5']:
                return "Médio Porte"
            else:
                return "Pequeno Porte"
        
        return "Desconhecido"
    
    def _analyze_patterns(self, categorized_items: List[Dict[str, Any]], supplier_category: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa padrões nos dados categorizados"""
        if not categorized_items:
            return {}
        
        # Distribuição por categoria
        categoria_count = {}
        valor_por_categoria = {}
        
        for item in categorized_items:
            categoria = item.get('categoria', 'Outros')
            valor = item.get('valor_total', 0) or 0
            
            categoria_count[categoria] = categoria_count.get(categoria, 0) + 1
            valor_por_categoria[categoria] = valor_por_categoria.get(categoria, 0) + valor
        
        # Categoria principal (por quantidade)
        categoria_principal = max(categoria_count.items(), key=lambda x: x[1]) if categoria_count else ("Outros", 0)
        
        # Categoria de maior valor
        categoria_maior_valor = max(valor_por_categoria.items(), key=lambda x: x[1]) if valor_por_categoria else ("Outros", 0)
        
        return {
            "distribuicao_categorias": categoria_count,
            "valor_por_categoria": valor_por_categoria,
            "categoria_principal": {
                "nome": categoria_principal[0],
                "quantidade": categoria_principal[1],
                "percentual": (categoria_principal[1] / len(categorized_items)) * 100
            },
            "categoria_maior_valor": {
                "nome": categoria_maior_valor[0],
                "valor": categoria_maior_valor[1]
            },
            "diversidade": len(categoria_count),  # Número de categorias diferentes
            "fornecedor_especializado": len(categoria_count) <= 2  # Fornecedor especializado se poucas categorias
        }
    
    def _generate_ai_insights(self, extracted_data: Dict[str, Any], categorized_items: List[Dict[str, Any]], supplier_category: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Gera insights executivos usando IA"""
        if not self.llm:
            return None
        
        try:
            # Criar agente de insights
            insights_agent = Agent(
                role="Analista de Insights Executivos",
                goal="Gerar insights estratégicos sobre fornecedores e categorias de produtos",
                backstory=(
                    "Você é um analista sênior especializado em análise de fornecedores e categorização "
                    "de produtos no mercado brasileiro. Gera insights acionáveis para executivos."
                ),
                llm=self.llm,
                verbose=False
            )
            
            # Preparar contexto
            context = {
                "valor_total": extracted_data.get('valor_total'),
                "quantidade_itens": len(categorized_items),
                "fornecedor": supplier_category.get('details', {}).get('razao_social'),
                "tipo_fornecedor": supplier_category.get('type'),
                "categorias": [item.get('categoria') for item in categorized_items]
            }
            
            insights_task = Task(
                description=f"""
                Analise os dados categorizados e gere insights executivos:
                
                Contexto: {json.dumps(context, ensure_ascii=False)}
                
                Retorne JSON com:
                {{
                    "insights_principais": ["insight 1", "insight 2"],
                    "recomendacoes": ["recomendação 1", "recomendação 2"],
                    "alertas": ["alerta se houver"],
                    "oportunidades": ["oportunidade identificada"],
                    "score_fornecedor": 8.5
                }}
                
                Foque em:
                - Padrões de compra
                - Diversificação de fornecedores
                - Oportunidades de negociação
                - Riscos identificados
                """,
                agent=insights_agent,
                expected_output="JSON com insights executivos estruturados"
            )
            
            crew = Crew(
                agents=[insights_agent],
                tasks=[insights_task],
                verbose=False
            )
            
            result = crew.kickoff()
            
            # Parse resultado
            try:
                result_str = str(result).strip()
                if result_str.startswith('```json'):
                    result_str = result_str.replace('```json', '').replace('```', '').strip()
                
                return json.loads(result_str)
                
            except json.JSONDecodeError:
                return None
                
        except Exception as e:
            print(f"Erro na geração de insights IA: {e}")
            return None
    
    def _calculate_overall_confidence(self, categorized_items: List[Dict[str, Any]], supplier_category: Dict[str, Any]) -> float:
        """Calcula confiança geral da categorização"""
        if not categorized_items:
            return 0.0
        
        # Confiança média dos itens
        item_confidences = [item.get('categoria_confianca', 0.0) for item in categorized_items]
        avg_item_confidence = sum(item_confidences) / len(item_confidences) if item_confidences else 0.0
        
        # Confiança do fornecedor
        supplier_confidence = supplier_category.get('confidence', 0.0)
        
        # Média ponderada (70% itens, 30% fornecedor)
        overall_confidence = (avg_item_confidence * 0.7) + (supplier_confidence * 0.3)
        
        return round(overall_confidence, 2)