# Serviço de Integração OpenAI - Sistema de Análise de Notas Fiscais

## Visão Geral

O Serviço de Integração OpenAI é o núcleo das capacidades de Large Language Model (LLM) do sistema de análise de notas fiscais. Ele fornece uma interface unificada e inteligente para todos os agentes do sistema, permitindo processamento de linguagem natural, análise semântica de documentos, categorização inteligente e geração de insights empresariais.

## Arquitetura

### Componentes Principais

1. **OpenAI Integration Service** (`openai_integration.py`)
   - Cliente central para API OpenAI
   - Gerenciamento de rate limiting e cache
   - Processamento de respostas e métricas

2. **Prompt Manager** (`prompt_manager.py`)
   - Templates de prompts especializados em português
   - Otimização e versionamento de prompts
   - Validação e renderização de templates

3. **Context Manager** (`context_manager.py`)
   - Gerenciamento de sessões e conversas
   - Histórico e memória de interações
   - Contexto empresarial e preferências

4. **LLM Service** (`llm_service.py`)
   - Interface unificada para todos os componentes
   - Métodos de alto nível para agentes
   - Integração completa dos serviços

5. **LLM Config** (`llm_config.py`)
   - Configurações específicas para o mercado brasileiro
   - Parâmetros de modelos e rate limiting
   - Configurações de cache e monitoramento

## Funcionalidades

### 🧠 Processamento de Linguagem Natural
- Interpretação de consultas executivas em português
- Reconhecimento de intenção e extração de entidades
- Geração de respostas contextualizadas

### 📄 Análise Semântica de Documentos
- Processamento inteligente de NF-e e NFS-e
- Extração de contexto empresarial
- Detecção de anomalias e padrões

### 🏷️ Categorização Inteligente
- Classificação contextual de produtos e serviços
- Criação dinâmica de categorias
- Análise de relacionamentos com fornecedores

### 🔍 Tradução SQL
- Conversão de perguntas empresariais para SQL
- Otimização de consultas
- Validação de lógica de negócio

### 📊 Geração de Relatórios
- Relatórios executivos com insights
- Recomendações acionáveis
- Análise de tendências e padrões

## Configuração

### Variáveis de Ambiente

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_FALLBACK_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=60
OPENAI_RATE_LIMIT_RPM=3500
OPENAI_RATE_LIMIT_TPM=90000
OPENAI_ENABLE_CACHING=true
OPENAI_CACHE_TTL=3600

# Redis Configuration (for caching and rate limiting)
REDIS_URL=redis://localhost:6379
```

### Instalação de Dependências

```bash
pip install openai==1.54.4
pip install redis
pip install pydantic
pip install pydantic-settings
```

## Uso Básico

### Inicialização

```python
from backend.utils.llm_service import obter_servico_llm

# Inicializar serviço
servico = await obter_servico_llm()
```

### Criar Sessão de Usuário

```python
# Contexto empresarial
contexto_empresarial = {
    "empresa_id": "empresa_123",
    "setor_atuacao": "Indústria Alimentícia",
    "porte_empresa": "media",
    "regioes_operacao": ["São Paulo", "Rio de Janeiro"]
}

# Criar sessão
sessao_id = await servico.criar_sessao_usuario(
    usuario_id="ceo_exemplo",
    contexto_empresarial=contexto_empresarial
)
```

### Processar Consulta Natural

```python
resultado = await servico.processar_consulta_natural(
    sessao_id=sessao_id,
    consulta="Quais foram os maiores fornecedores no último trimestre?",
    cargo_usuario="CEO"
)
```

### Analisar Documento Fiscal

```python
resultado = await servico.analisar_documento_fiscal(
    sessao_id=sessao_id,
    conteudo_xml=xml_content,
    tipo_documento="NF-e",
    info_fornecedor=fornecedor_info,
    itens=lista_itens,
    valor_total=1500.00
)
```

## Templates de Prompts

### Templates Disponíveis

1. **master_agent_interpretacao_consulta**
   - Interpretação de consultas executivas
   - Extração de intenção e entidades
   - Geração de esclarecimentos

2. **xml_analise_semantica**
   - Análise semântica de documentos XML
   - Extração de contexto empresarial
   - Detecção de anomalias

3. **categorizacao_produtos**
   - Categorização inteligente de produtos
   - Criação de novas categorias
   - Justificativas empresariais

4. **traducao_sql**
   - Tradução de linguagem natural para SQL
   - Otimização de consultas
   - Validação de lógica

5. **relatorio_executivo**
   - Geração de relatórios executivos
   - Insights e recomendações
   - Análise de impacto

### Personalização de Templates

```python
from backend.utils.prompt_manager import gerenciador_prompts

# Obter template
template = gerenciador_prompts.obter_template("nome_template")

# Renderizar com variáveis
prompt_renderizado, erros = gerenciador_prompts.renderizar_template(
    "nome_template", 
    {"variavel1": "valor1", "variavel2": "valor2"}
)
```

## Gerenciamento de Contexto

### Tipos de Memória

- **Curto Prazo**: Informações da sessão atual (1 hora)
- **Médio Prazo**: Padrões recentes do usuário (1 semana)
- **Longo Prazo**: Preferências e comportamentos (1 mês)

### Compressão de Contexto

O sistema automaticamente comprime o histórico de conversas para otimizar o uso de tokens, mantendo:
- 5 interações mais recentes
- Interações com alta relevância
- Entidades e decisões importantes

## Monitoramento e Métricas

### Métricas Coletadas

- **Uso de Tokens**: Total e por tipo de operação
- **Custos**: Estimativa de custos por modelo
- **Performance**: Tempo de resposta e cache hits
- **Qualidade**: Scores de confiança e feedback

### Obter Métricas

```python
# Métricas do serviço
metricas = servico.obter_metricas_servico()

# Estatísticas de sessão
stats = servico.obter_estatisticas_sessao(sessao_id)
```

## Rate Limiting e Cache

### Rate Limiting
- **Requests por minuto**: 3.500 (configurável)
- **Tokens por minuto**: 90.000 (configurável)
- **Backoff automático**: Em caso de limite atingido

### Cache Inteligente
- **TTL por tipo**: Diferentes tempos para cada tipo de prompt
- **Compressão**: Otimização automática de contexto
- **Invalidação**: Limpeza automática de cache expirado

## Tratamento de Erros

### Estratégias de Fallback
1. **Modelo Fallback**: GPT-3.5-turbo se GPT-4 falhar
2. **Retry Logic**: Até 3 tentativas com backoff
3. **Cache**: Uso de respostas em cache quando disponível
4. **Degradação Graceful**: Respostas simplificadas em caso de erro

### Logs e Debugging
```python
import logging
logging.getLogger("backend.utils.openai_integration").setLevel(logging.DEBUG)
```

## Segurança e Compliance

### Proteção de Dados
- **Não armazenamento**: Dados sensíveis não são persistidos
- **Criptografia**: Comunicação segura com APIs
- **Sanitização**: Limpeza automática de dados pessoais

### Auditoria
- **Logs estruturados**: Todas as interações são logadas
- **Rastreabilidade**: IDs únicos para cada operação
- **Métricas de uso**: Monitoramento de custos e performance

## Exemplos Avançados

Veja o arquivo `backend/examples/llm_integration_example.py` para exemplos completos de uso de todas as funcionalidades.

## Troubleshooting

### Problemas Comuns

1. **Erro de API Key**
   ```
   Solução: Verificar OPENAI_API_KEY no .env
   ```

2. **Rate Limit Atingido**
   ```
   Solução: Aguardar ou ajustar configurações de rate limiting
   ```

3. **Cache não funcionando**
   ```
   Solução: Verificar conexão Redis e configurações de cache
   ```

4. **Templates não encontrados**
   ```
   Solução: Verificar inicialização do gerenciador_prompts
   ```

### Debug Mode

```python
from backend.utils.llm_config import configuracoes_llm_padrao

# Ativar modo debug
configuracoes_llm_padrao.modo_debug = True
configuracoes_llm_padrao.log_prompts = True
configuracoes_llm_padrao.log_respostas = True
```

## Roadmap

### Próximas Funcionalidades
- [ ] Suporte a modelos locais (Ollama)
- [ ] Templates A/B testing
- [ ] Análise de sentimento em feedback
- [ ] Integração com ferramentas de BI
- [ ] Suporte a múltiplos idiomas
- [ ] Fine-tuning de modelos específicos

### Melhorias Planejadas
- [ ] Otimização de prompts com ML
- [ ] Cache distribuído
- [ ] Métricas avançadas de qualidade
- [ ] Dashboard de monitoramento
- [ ] Integração com Langchain Agents

## Contribuição

Para contribuir com melhorias:

1. Adicione novos templates em `prompt_manager.py`
2. Implemente novos tipos de análise em `openai_integration.py`
3. Estenda funcionalidades de contexto em `context_manager.py`
4. Adicione testes em `tests/test_llm_integration.py`

## Suporte

Para dúvidas ou problemas:
- Verifique os logs do sistema
- Consulte as métricas de performance
- Valide a configuração com `validar_configuracao()`
- Execute os exemplos para testar funcionalidades