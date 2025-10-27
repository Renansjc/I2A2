# Melhorias no Schema do Banco de Dados

## 📊 Análise do XML de Exemplo

Baseado na análise detalhada do arquivo `xml_nf/exemplo.xml`, identifiquei campos cruciais que estavam sendo perdidos no schema anterior e que são fundamentais para análises fiscais e de IA.

## 🎯 Principais Melhorias Implementadas

### 1. **Tabela `fiscal_documents` - Campos Detalhados da Nota**

#### Valores Financeiros Granulares:
- `valor_produtos` (vProd) - Valor dos produtos sem impostos
- `valor_frete` (vFrete) - Valor do frete separadamente  
- `valor_seguro` (vSeg) - Valor do seguro
- `valor_desconto` (vDesc) - Descontos aplicados
- `valor_outros` (vOutro) - Outros valores
- `valor_total` (vNF) - Valor final da nota

#### Impostos Detalhados por Tipo:
- `icms_base_calculo`, `icms_valor` - ICMS completo
- `icms_st_base_calculo`, `icms_st_valor` - ICMS ST
- `ipi_valor` - IPI
- `pis_valor` - PIS  
- `cofins_valor` - COFINS
- `total_tributos` - Total de tributos

#### Informações Logísticas:
- `modalidade_frete` - Quem paga o frete
- `transportadora` - Nome da transportadora
- `peso_liquido`, `peso_bruto` - Pesos para análise logística
- `quantidade_volumes` - Volumes transportados

#### Metadados para IA:
- `uf_origem`, `uf_destino` - Para análise geográfica
- `tipo_operacao` - Venda, compra, transferência
- `consumidor_final` - B2B vs B2C
- `presenca_comprador` - Presencial, online, etc.

### 2. **Tabela `extracted_data` - Emitente/Destinatário Completos**

#### Emitente Detalhado:
- Razão social, nome fantasia, CNPJ, IE
- Endereço completo (logradouro, número, complemento, bairro, município, UF, CEP)
- Telefone para contato
- `crt` - Código de Regime Tributário

#### Destinatário Detalhado:
- Nome, CNPJ/CPF, IE
- Endereço completo
- Telefone e email
- Diferenciação entre pessoa física e jurídica

### 3. **Tabela `document_items` - Produtos/Serviços Granulares**

#### Identificação Completa:
- `codigo_produto`, `codigo_ean` - Códigos únicos
- `ncm`, `cfop` - Classificações fiscais
- `descricao` - Descrição completa

#### Quantidades e Valores Detalhados:
- Unidades comerciais vs tributáveis
- Quantidades e valores unitários separados
- Valores de frete, seguro, desconto por item

#### Impostos por Item:
- ICMS: origem, CST, base de cálculo, alíquota, valor
- IPI: CST, valor
- PIS: CST, base de cálculo, alíquota, valor  
- COFINS: CST, base de cálculo, alíquota, valor

#### Campos para IA:
- `categoria`, `subcategoria` - Classificação inteligente
- `marca`, `modelo` - Extraídos da descrição pela IA
- `categoria_confianca` - Nível de confiança da IA

### 4. **Novas Tabelas para IA Avançada**

#### `supplier_analysis` - Análise de Fornecedores:
- Classificação automática (tipo, categoria, porte)
- Métricas de relacionamento
- Score de risco calculado pela IA
- Fatores de risco identificados

#### `ai_insights` - Insights Inteligentes:
- Alertas, oportunidades, recomendações
- Categorização por tipo (fiscal, financeiro, operacional)
- Sistema de prioridade e confiança
- Tracking de visualização e ações tomadas

## 🚀 Benefícios para a IA

### 1. **Análises Financeiras Precisas**
```sql
-- Margem de lucro por produto
SELECT categoria, 
       AVG((valor_produto - valor_desconto) / valor_produto * 100) as margem_media
FROM document_items 
GROUP BY categoria;

-- Impacto de impostos por categoria
SELECT categoria,
       AVG(total_tributos_item / valor_produto * 100) as carga_tributaria_media
FROM document_items
GROUP BY categoria;
```

### 2. **Análises Geográficas**
```sql
-- Fluxo comercial por UF
SELECT uf_origem, uf_destino, 
       COUNT(*) as transacoes,
       SUM(valor_total) as volume_financeiro
FROM fiscal_documents fd
JOIN extracted_data ed ON fd.id = ed.document_id
GROUP BY uf_origem, uf_destino;
```

### 3. **Análises de Fornecedores Inteligentes**
```sql
-- Fornecedores de risco
SELECT emitente_razao_social, score_risco, fatores_risco
FROM supplier_analysis sa
JOIN extracted_data ed ON sa.document_id = ed.document_id
WHERE score_risco > 0.7
ORDER BY score_risco DESC;
```

### 4. **Insights Acionáveis**
```sql
-- Oportunidades de economia fiscal
SELECT titulo, descricao, acao_sugerida
FROM ai_insights
WHERE tipo_insight = 'oportunidade' 
  AND categoria = 'fiscal'
  AND visualizado = FALSE
ORDER BY prioridade DESC;
```

## 📈 Views Pré-Construídas

### `vw_dashboard_metrics`
Métricas principais para dashboard executivo

### `vw_top_fornecedores`  
Ranking de fornecedores com análise de risco

### `vw_categorias_produtos`
Análise de categorias de produtos

### `vw_insights_pendentes`
Insights não visualizados ordenados por prioridade

## 🔄 Migração do Schema Atual

Para implementar essas melhorias:

1. **Backup dos dados atuais**
2. **Executar o novo schema** (`enhanced_mvp_schema.sql`)
3. **Migrar dados existentes** para as novas estruturas
4. **Atualizar os agentes IA** para popular os novos campos
5. **Atualizar APIs** para retornar dados granulares

## 💡 Impacto na IA

Com esses campos detalhados, os agentes IA poderão:

- **Detectar padrões fiscais** mais complexos
- **Identificar oportunidades de economia** tributária
- **Analisar riscos de fornecedores** automaticamente
- **Gerar insights financeiros** mais precisos
- **Classificar produtos** com maior granularidade
- **Prever tendências** baseadas em dados históricos
- **Otimizar operações logísticas** baseado em pesos e volumes
- **Identificar fraudes** através de padrões anômalos

Este schema melhorado transforma o sistema de um simples extrator de dados em uma **plataforma inteligente de análise fiscal** com capacidades avançadas de IA.