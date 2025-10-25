# Instruções de Setup - Serviço LLM

## ✅ Status Atual

O **Serviço de Integração OpenAI** foi implementado com sucesso! Todos os componentes principais estão funcionando:

- ✅ Configurações LLM brasileiras
- ✅ Gerenciador de templates de prompts (5 templates carregados)
- ✅ Integração OpenAI com rate limiting e cache
- ✅ Gerenciamento de contexto e conversas
- ✅ Serviço LLM integrado unificado

## 🔧 Próximos Passos para Produção

### 1. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

**Variáveis críticas para configurar:**

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_DEFAULT_MODEL=gpt-5-mini
OPENAI_FALLBACK_MODEL=gpt-4o-mini

# Redis Configuration (para cache e rate limiting)
REDIS_URL=redis://localhost:6379

# Application
DEBUG=false
```

### 2. Instalar Redis

O sistema precisa do Redis para cache e rate limiting:

**Windows (usando Docker):**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Ou usando WSL/Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

### 3. Instalar Dependências Completas (Opcional)

Para funcionalidades avançadas, instale dependências adicionais:

```bash
# Instalar dependências mínimas (já funcionando)
pip install -r requirements-minimal.txt

# Para funcionalidades completas (requer compiladores C++)
pip install -r requirements.txt
```

### 4. Testar o Sistema

Execute o teste para verificar se tudo está funcionando:

```bash
python test_llm_setup.py
```

### 5. Executar Exemplos

Teste as funcionalidades com os exemplos:

```bash
python examples/llm_integration_example.py
```

## 🚀 Como Usar o Serviço LLM

### Importação Básica

```python
from utils.llm_service import obter_servico_llm

# Inicializar serviço
servico = await obter_servico_llm()
```

### Criar Sessão de Usuário

```python
sessao_id = await servico.criar_sessao_usuario(
    usuario_id="usuario_exemplo",
    contexto_empresarial={
        "empresa_id": "empresa_123",
        "setor_atuacao": "Indústria",
        "porte_empresa": "media"
    }
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

## 📋 Funcionalidades Implementadas

### 🧠 Processamento de Linguagem Natural
- Interpretação de consultas executivas em português
- Extração de intenção e entidades
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

## 🔧 Configurações Avançadas

### Rate Limiting
```python
# Configurar limites personalizados
configuracoes_llm_padrao.rate_limiting.requests_per_minute = 5000
configuracoes_llm_padrao.rate_limiting.tokens_per_minute = 120000
```

### Cache
```python
# Configurar TTL do cache
configuracoes_llm_padrao.cache.ttl_segundos = 7200  # 2 horas
```

### Modelos
```python
# Usar modelo diferente
configuracoes_llm_padrao.modelo_padrao = ModeloLLM.GPT_4_TURBO
```

## 📊 Monitoramento

### Obter Métricas
```python
metricas = servico.obter_metricas_servico()
print(f"Total de requests: {metricas['metricas_openai']['total_requests']}")
print(f"Cache hit rate: {metricas['metricas_openai']['cache_hit_rate']:.2%}")
```

### Estatísticas de Sessão
```python
stats = servico.obter_estatisticas_sessao(sessao_id)
print(f"Interações: {stats['total_interacoes']}")
print(f"Tokens usados: {stats['total_tokens']}")
```

## 🛠️ Troubleshooting

### Problema: "OpenAI API Key não configurado"
**Solução:** Configure a variável `OPENAI_API_KEY` no arquivo `.env`

### Problema: "Redis connection failed"
**Solução:** Verifique se o Redis está rodando na porta 6379

### Problema: "Template não encontrado"
**Solução:** Verifique se o `gerenciador_prompts` foi inicializado corretamente

### Problema: "Rate limit atingido"
**Solução:** Aguarde ou ajuste as configurações de rate limiting

## 📚 Documentação Completa

Consulte o arquivo `utils/README_LLM_Integration.md` para documentação detalhada de todas as funcionalidades.

## 🎯 Integração com Agentes

O serviço está pronto para ser usado pelos agentes do sistema:

1. **Master Agent**: Use `processar_consulta_natural()`
2. **XML Processing Agent**: Use `analisar_documento_fiscal()`
3. **AI Categorization Agent**: Use `categorizar_produtos_inteligente()`
4. **SQL Agent**: Use `traduzir_consulta_sql()`
5. **Report Agent**: Use `gerar_relatorio_executivo()`

## ✅ Checklist de Produção

- [ ] Configurar `OPENAI_API_KEY`
- [ ] Instalar e configurar Redis
- [ ] Configurar variáveis de ambiente de produção
- [ ] Testar com `python test_llm_setup.py`
- [ ] Executar exemplos para validar funcionalidades
- [ ] Configurar monitoramento e logs
- [ ] Implementar backup das configurações
- [ ] Configurar alertas de custo e rate limiting

---

**🎉 Parabéns! O Serviço de Integração OpenAI está pronto para uso!**