# 🤖 Agente Autônomo de Análise Exploratória de Dados (EDA)

Um agente inteligente que utiliza OpenAI GPT-4 para realizar análises exploratórias de dados de forma autônoma e interativa.

## 🚀 Configuração Rápida

### 1. Instalar Python
- Baixe Python 3.8+ em: https://www.python.org/downloads/
- Durante a instalação, marque "Add Python to PATH"

### 2. Configurar Ambiente

#### Opção A: Automática (Recomendada)
```bash
python setup.py
```

#### Opção B: Manual
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
venv\Scripts\activate

# Ativar ambiente virtual (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Chave da OpenAI

1. Abra o arquivo `config.env`
2. Substitua `your_openai_api_key_here` pela sua chave real da OpenAI:
```
OPENAI_API_KEY=sk-1234567890abcdef...
```

### 4. Executar o App

```bash
# Certifique-se que o ambiente virtual está ativo
streamlit run app.py
```

## 📊 Funcionalidades

- **Análise Interativa**: Faça perguntas em linguagem natural sobre seus dados
- **Visualizações Automáticas**: Gráficos gerados automaticamente baseados na análise
- **Memória Persistente**: O agente lembra análises anteriores
- **Detecção de Anomalias**: Identifica outliers automaticamente
- **Análise de Correlação**: Encontra relações entre variáveis
- **Conclusões Inteligentes**: Gera insights e conclusões baseadas em IA

## 🔧 Estrutura do Projeto

```
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências Python
├── config.env          # Configurações (chave API)
├── setup.py           # Script de configuração
├── README.md          # Este arquivo
└── .eda_sessions/     # Memória das análises (criado automaticamente)
```

## 🎯 Como Usar

1. **Upload de Dados**: Carregue um arquivo CSV
2. **Visão Geral**: Explore estatísticas básicas do dataset
3. **Análise Interativa**: Faça perguntas como:
   - "Existe correlação entre as variáveis?"
   - "Quais são os outliers na coluna Amount?"
   - "Como está distribuída a variável Price?"
4. **Insights**: Veja análises anteriores e insights acumulados
5. **Conclusões**: Gere um relatório final baseado em todas as análises

## 🛠️ Dependências

- `streamlit`: Interface web
- `openai`: Integração com GPT-4
- `pandas`: Manipulação de dados
- `numpy`: Computação numérica
- `matplotlib/seaborn`: Visualizações estáticas
- `plotly`: Visualizações interativas
- `python-dotenv`: Gerenciamento de variáveis de ambiente

## 📝 Exemplo de Uso

```python
# O app carrega automaticamente a chave da API do config.env
# Você pode fazer perguntas como:

"Mostre a correlação entre todas as variáveis numéricas"
"Identifique anomalias na coluna 'valor'"
"Como está distribuída a variável 'idade'?"
"Gere conclusões gerais sobre este dataset"
```

## 🔒 Segurança

- A chave da API é carregada do arquivo `config.env`
- Nunca commite o arquivo `config.env` com sua chave real
- Use `.gitignore` para proteger informações sensíveis

## 🆘 Solução de Problemas

### Erro: "ModuleNotFoundError"
```bash
# Certifique-se que o ambiente virtual está ativo
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstale as dependências
pip install -r requirements.txt
```

### Erro: "OpenAI API Key not found"
1. Verifique se o arquivo `config.env` existe
2. Confirme que a chave está correta no formato: `OPENAI_API_KEY=sk-...`
3. Reinicie o Streamlit após alterar o arquivo

### Erro: "Port already in use"
```bash
# Use uma porta diferente
streamlit run app.py --server.port 8502
```

## 📞 Suporte

Para dúvidas ou problemas, verifique:
1. Se todas as dependências estão instaladas
2. Se a chave da OpenAI está configurada corretamente
3. Se o arquivo CSV está no formato correto

