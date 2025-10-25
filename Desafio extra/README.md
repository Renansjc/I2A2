# 🤖 Agente Autônomo de Análise Exploratória de Dados (EDA)

## 📋 Descrição

Este é um aplicativo Streamlit avançado que utiliza inteligência artificial (Modelo OpenAI, configurado no front) para realizar análises exploratórias de dados de forma autônoma. O sistema é especialmente otimizado para análise de detecção de fraude em cartões de crédito, mas também funciona com qualquer dataset CSV.

## ✨ Funcionalidades Principais

### 🔍 Análises Gerais
- **Análise de Correlação**: Identifica relações entre variáveis numéricas
- **Detecção de Outliers**: Usa múltiplos métodos (IQR, Z-Score, Isolation Forest)
- **Análise de Distribuições**: Verifica normalidade e características das distribuições
- **Análise PCA**: Reduz dimensionalidade e identifica componentes principais
- **Análise Temporal**: Identifica tendências e sazonalidade
- **Padrões de Missing Data**: Analisa padrões nos dados faltantes
- **Clustering**: Identifica agrupamentos naturais nos dados

### 🎯 Análises Específicas para Fraude
- **Detecção Automática**: Identifica automaticamente datasets de fraude
- **Análise de Padrões**: Compara transações fraudulentas vs legítimas
- **Correlações com Fraude**: Identifica features mais correlacionadas com fraude
- **Análise Temporal de Fraudes**: Padrões de horário e sazonalidade
- **Detecção de Anomalias**: Métodos especializados para detecção de fraude
- **Métricas de Performance**: Precisão, Recall e F1-Score

### 🧠 Inteligência Artificial
- **Processamento de Linguagem Natural**: Entenda perguntas em português
- **Geração de Insights**: Insights automáticos baseados nos resultados
- **Memória Persistente**: Mantém histórico das análises realizadas
- **Sugestões Inteligentes**: Recomenda análises baseadas no dataset

## 🚀 Instalação

1. **Clone o repositório**:
```bash
git clone <seu-repositorio>
cd desafiopy
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure a API Key**:
   - Crie um arquivo `config.env` na raiz do projeto
   - Adicione sua chave da OpenAI:
```env
OPENAI_API_KEY=sua_chave_aqui
```

4. **Execute o aplicativo**:
```bash
streamlit run app_inacabado.py
```


## 📊 Como Usar

### 0. Selecione o modelo de LLM a ser utilizado
No menu esquerdo, selecione o modelo de LLM que deseja utilizar para as análises

### 1. Upload do Dataset
- Faça upload de um arquivo CSV
- O sistema detectará automaticamente se é um dataset de fraude
- Visualize informações básicas do dataset

### 2. Análise Interativa
- **Perguntas em Português**: Digite perguntas como:
  - "Existe correlação entre as variáveis?"
  - "Quais são os outliers na coluna Amount?"
  - "Como estão distribuídas as variáveis?"
  - "Há padrões temporais nos dados?"

### 3. Análises Especializadas (para datasets de fraude)
- **Distribuição de Fraude**: Visualize a proporção de fraudes
- **Padrões Monetários**: Compare valores entre fraudes e transações legítimas
- **Correlações com Fraude**: Identifique features mais importantes
- **Detecção de Anomalias**: Métodos especializados para fraude

### 4. Sugestões Automáticas
- O sistema sugere análises baseadas nas características do dataset
- Prioriza análises por importância (alta, média, baixa)

### 5. Memória e Conclusões
- Histórico de todas as análises realizadas
- Insights acumulados
- Geração de conclusões finais

## 🎯 Exemplos de Perguntas

### Para Datasets Gerais:
- "Existe correlação entre as variáveis numéricas?"
- "Quais são os outliers nas variáveis?"
- "Como está distribuída cada variável?"
- "Há padrões temporais nos dados?"
- "Existem agrupamentos (clusters) nos dados?"
- "Quais valores são mais/menos frequentes?"

### Para Datasets de Fraude:
- "Quais são os padrões de fraude neste dataset?"
- "Como as fraudes se relacionam com o valor da transação?"
- "Há correlações específicas com fraude?"
- "Quais são os horários de maior incidência de fraude?"
- "Como detectar anomalias relacionadas a fraude?"

## 🔧 Configurações

### Limites do Sistema:
- **Tamanho máximo**: 200MB
- **Colunas máximas**: 50 (para análise)
- **Preview máximo**: 1000 linhas

### Configurações de Análise:
- **Threshold de correlação**: 0.5
- **Z-Score para outliers**: 3
- **Multiplicador IQR**: 1.5
- **Variância PCA**: 95%

## 📁 Estrutura do Projeto

```
desafiopy/
├── app.py                    # Versão base
├── requirements.txt          # Dependências
├── README.md                 # Este arquivo
├── config.env               # Configurações (criar)
└── .eda_sessions/           # Sessões salvas (criado automaticamente)
```

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Interface web
- **OpenAI GPT-4o-mini**: Processamento de linguagem natural
- **Pandas**: Manipulação de dados
- **NumPy**: Computação numérica
- **Matplotlib/Seaborn**: Visualizações estáticas
- **Plotly**: Visualizações interativas
- **Scikit-learn**: Machine learning
- **SciPy**: Estatísticas

## 🎯 Casos de Uso

### 1. Análise de Fraude em Cartões de Crédito
- Detecção automática de padrões fraudulentos
- Análise de correlações específicas
- Métricas de performance para modelos de detecção

### 2. Análise Exploratória Geral
- Qualquer dataset CSV
- Análises estatísticas completas
- Visualizações interativas

### 3. Pesquisa e Desenvolvimento
- Prototipagem rápida de análises
- Geração de insights automáticos
- Documentação automática de descobertas

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Renan Mello Nogueira**
- Desenvolvido como parte do desafio de análise de fraude em cartões de crédito
- Framework: OpenAI + Streamlit

## 🆘 Suporte

Se encontrar problemas ou tiver dúvidas:
1. Verifique se todas as dependências estão instaladas
2. Confirme se a API Key da OpenAI está configurada
3. Verifique se o arquivo CSV está no formato correto
4. Consulte os logs de erro no terminal

---


**🎉 Divirta-se explorando seus dados com IA!**


