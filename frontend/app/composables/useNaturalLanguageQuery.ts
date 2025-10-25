import { ref, computed } from 'vue'
import type { 
  IntelligentSuggestion, 
  QuickAction, 
  QueryPreview, 
  QueryResult, 
  QueryHistoryItem 
} from '~/types/dashboard'

export const useNaturalLanguageQuery = () => {
  // Reactive state
  const query = ref('')
  const isLoading = ref(false)
  const showSuggestions = ref(false)
  const showPreview = ref(false)
  const queryPreview = ref<QueryPreview | null>(null)
  const queryResult = ref<QueryResult | null>(null)
  const queryHistory = ref<QueryHistoryItem[]>([])

  // Intelligent suggestions based on business context
  const intelligentSuggestions = ref<IntelligentSuggestion[]>([
    {
      text: "Quais fornecedores tiveram maior crescimento neste trimestre?",
      description: "Análise comparativa de crescimento de fornecedores com insights de performance",
      category: "Fornecedores",
      estimatedTime: "2-3 min"
    },
    {
      text: "Mostre o resumo fiscal de outubro com principais métricas",
      description: "Dashboard executivo com KPIs fiscais, eficiência e conformidade",
      category: "Resumo Fiscal",
      estimatedTime: "1-2 min"
    },
    {
      text: "Identifique anomalias nos últimos 30 dias de processamento",
      description: "Detecção inteligente de padrões incomuns e possíveis problemas",
      category: "Análise de Anomalias",
      estimatedTime: "3-4 min"
    },
    {
      text: "Compare eficiência fiscal por região geográfica",
      description: "Análise regional com benchmarks e oportunidades de melhoria",
      category: "Análise Regional",
      estimatedTime: "2-3 min"
    },
    {
      text: "Analise padrões de sazonalidade nas vendas",
      description: "Identificação de tendências sazonais e oportunidades de otimização",
      category: "Análise Temporal",
      estimatedTime: "2-3 min"
    },
    {
      text: "Verifique conformidade fiscal dos últimos 90 dias",
      description: "Auditoria automática de conformidade com alertas e recomendações",
      category: "Conformidade",
      estimatedTime: "3-4 min"
    }
  ])

  // Quick action buttons for common executive queries
  const quickActions: QuickAction[] = [
    {
      text: "Relatório Mensal",
      icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
      query: "Gere o relatório executivo mensal com principais KPIs e insights"
    },
    {
      text: "Top Fornecedores",
      icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
      query: "Liste os top 10 fornecedores por volume de transações este mês"
    },
    {
      text: "Análise de Tendências",
      icon: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
      query: "Analise tendências de crescimento nos últimos 6 meses com projeções"
    },
    {
      text: "Conformidade Fiscal",
      icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
      query: "Verifique status de conformidade fiscal e identifique riscos"
    },
    {
      text: "Categorização IA",
      icon: "M7 7h.01M7 3h5c.512 0 .853.61.5 1.11l-2 2.79a1.001 1.001 0 000 1.2l2 2.79c.353.5.012 1.11-.5 1.11H7a1 1 0 01-1-1V4a1 1 0 011-1z",
      query: "Mostre resultados da categorização automática de produtos e serviços"
    },
    {
      text: "Eficiência Operacional",
      icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
      query: "Analise eficiência operacional dos agentes e tempo de processamento"
    }
  ]

  // Computed properties
  const filteredSuggestions = computed(() => {
    if (!query.value || query.value.length < 2) {
      return intelligentSuggestions.value.slice(0, 4)
    }
    
    return intelligentSuggestions.value.filter(suggestion =>
      suggestion.text.toLowerCase().includes(query.value.toLowerCase()) ||
      suggestion.category.toLowerCase().includes(query.value.toLowerCase()) ||
      suggestion.description.toLowerCase().includes(query.value.toLowerCase())
    ).slice(0, 6)
  })

  // Load query history from localStorage
  const loadQueryHistory = () => {
    try {
      const saved = localStorage.getItem('nlq_history')
      if (saved) {
        queryHistory.value = JSON.parse(saved).map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }))
      }
    } catch (error) {
      console.error('Error loading query history:', error)
      queryHistory.value = []
    }
  }

  // Save query history to localStorage
  const saveQueryHistory = () => {
    try {
      localStorage.setItem('nlq_history', JSON.stringify(queryHistory.value))
    } catch (error) {
      console.error('Error saving query history:', error)
    }
  }

  // Add query to history
  const addToHistory = (queryText: string, status: QueryHistoryItem['status'] = 'processando') => {
    const historyItem: QueryHistoryItem = {
      query: queryText,
      timestamp: new Date(),
      status
    }
    
    queryHistory.value.unshift(historyItem)
    
    // Keep only last 50 queries
    if (queryHistory.value.length > 50) {
      queryHistory.value = queryHistory.value.slice(0, 50)
    }
    
    saveQueryHistory()
  }

  // Update history item status
  const updateHistoryStatus = (queryText: string, status: QueryHistoryItem['status']) => {
    const item = queryHistory.value.find(h => h.query === queryText)
    if (item) {
      item.status = status
      saveQueryHistory()
    }
  }

  // Remove history item
  const removeHistoryItem = (index: number) => {
    queryHistory.value.splice(index, 1)
    saveQueryHistory()
  }

  // Clear all history
  const clearHistory = () => {
    queryHistory.value = []
    saveQueryHistory()
  }

  // Generate query preview
  const generateQueryPreview = (queryText: string): QueryPreview => {
    return {
      interpretedQuery: `Análise: "${queryText}" - Sistema interpretou como consulta sobre ${getQueryCategory(queryText)}`,
      involvedAgents: getInvolvedAgents(queryText),
      estimatedTime: getEstimatedTime(queryText)
    }
  }

  // Execute natural language query
  const executeQuery = async (queryText: string): Promise<QueryResult> => {
    // Add to history
    addToHistory(queryText, 'processando')
    
    try {
      // In production, this would call the actual API
      // const response = await $fetch('/api/agents/consulta-natural', {
      //   method: 'POST',
      //   body: { query: queryText }
      // })
      
      // Simulate API call for development
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 2000))
      
      // Generate mock result
      const result = generateMockResult(queryText)
      
      // Update history status
      updateHistoryStatus(queryText, 'concluída')
      
      return result
      
    } catch (error) {
      console.error('Query execution failed:', error)
      updateHistoryStatus(queryText, 'erro')
      throw error
    }
  }

  // Generate mock result for development
  const generateMockResult = (queryText: string): QueryResult => {
    const category = getQueryCategory(queryText)
    
    return {
      originalQuery: queryText,
      executionTime: `${(2 + Math.random() * 3).toFixed(1)}s`,
      confidence: Math.floor(85 + Math.random() * 15),
      executiveSummary: `Análise executiva baseada na consulta "${queryText}". Os dados foram processados pelos agentes de IA especializados em ${category} e revelam insights estratégicos importantes para tomada de decisões. A análise considerou padrões históricos, tendências de mercado e benchmarks do setor.`,
      keyInsights: generateMockInsights(category) || [],
      chartData: generateMockChartData(category),
      recommendations: generateMockRecommendations(category) || []
    }
  }

  // Helper functions
  const getQueryCategory = (queryText: string): string => {
    const categories = {
      'fornecedor': 'análise de fornecedores',
      'fiscal': 'conformidade fiscal',
      'relatório': 'geração de relatórios',
      'tendência': 'análise de tendências',
      'categoria': 'categorização de produtos',
      'eficiência': 'eficiência operacional',
      'anomalia': 'detecção de anomalias',
      'região': 'análise regional',
      'sazon': 'análise sazonal',
      'conformidade': 'auditoria de conformidade'
    }
    
    for (const [key, value] of Object.entries(categories)) {
      if (queryText.toLowerCase().includes(key)) {
        return value
      }
    }
    
    return 'análise geral de dados fiscais'
  }

  const getInvolvedAgents = (queryText: string): string[] => {
    const agents = []
    const text = queryText.toLowerCase()
    
    if (text.includes('fornecedor') || text.includes('supplier')) {
      agents.push('Agente de Categorização IA', 'Agente SQL')
    }
    if (text.includes('relatório') || text.includes('report')) {
      agents.push('Agente de Relatórios', 'Agente Master')
    }
    if (text.includes('xml') || text.includes('nota') || text.includes('nf-e') || text.includes('nfs-e')) {
      agents.push('Agente de Processamento XML')
    }
    if (text.includes('tendência') || text.includes('análise') || text.includes('padrão')) {
      agents.push('Agente SQL', 'Agente de Relatórios')
    }
    if (text.includes('anomalia') || text.includes('erro') || text.includes('problema')) {
      agents.push('Agente de Monitoramento', 'Agente de Categorização IA')
    }
    if (text.includes('eficiência') || text.includes('performance') || text.includes('otimização')) {
      agents.push('Agente de Monitoramento', 'Agente SQL')
    }
    
    if (agents.length === 0) {
      agents.push('Agente Master', 'Agente SQL')
    }
    
    return [...new Set(agents)]
  }

  const getEstimatedTime = (queryText: string): string => {
    const text = queryText.toLowerCase()
    
    if (text.includes('relatório') || text.includes('análise completa')) return '3-5 minutos'
    if (text.includes('anomalia') || text.includes('auditoria')) return '4-6 minutos'
    if (text.includes('tendência') || text.includes('padrão')) return '2-4 minutos'
    if (text.includes('resumo') || text.includes('kpi')) return '1-2 minutos'
    
    return '2-3 minutos'
  }

  const generateMockInsights = (category: string) => {
    const insights: Record<string, Array<{title: string, description: string, impact: string}>> = {
      'análise de fornecedores': [
        {
          title: 'Crescimento de Fornecedores Estratégicos',
          description: 'Identificados 5 fornecedores com crescimento superior a 25% no trimestre',
          impact: 'Alto impacto positivo na diversificação de fornecimento'
        },
        {
          title: 'Concentração de Risco',
          description: '3 fornecedores representam 60% do volume total, indicando necessidade de diversificação',
          impact: 'Risco médio de dependência excessiva'
        }
      ],
      'conformidade fiscal': [
        {
          title: 'Taxa de Conformidade Elevada',
          description: '97.3% das notas fiscais estão em conformidade com as regulamentações',
          impact: 'Baixo risco de autuações fiscais'
        },
        {
          title: 'Oportunidades de Otimização Tributária',
          description: 'Identificadas oportunidades de economia fiscal em 4 categorias de produtos',
          impact: 'Potencial economia de R$ 45.000 mensais'
        }
      ],
      'default': [
        {
          title: 'Performance Geral Positiva',
          description: 'Indicadores gerais mostram tendência de crescimento sustentável',
          impact: 'Impacto positivo na estratégia empresarial'
        },
        {
          title: 'Oportunidades Identificadas',
          description: 'Sistema detectou 3 áreas com potencial de melhoria significativa',
          impact: 'Oportunidade de otimização operacional'
        }
      ]
    }
    
    return insights[category] || insights['default']
  }

  const generateMockChartData = (category: string) => {
    const baseData = [
      { label: 'Jan', value: 120000 + Math.random() * 50000 },
      { label: 'Fev', value: 135000 + Math.random() * 50000 },
      { label: 'Mar', value: 148000 + Math.random() * 50000 },
      { label: 'Abr', value: 162000 + Math.random() * 50000 },
      { label: 'Mai', value: 155000 + Math.random() * 50000 },
      { label: 'Jun', value: 178000 + Math.random() * 50000 }
    ]
    
    return baseData.map(item => ({
      ...item,
      value: Math.floor(item.value)
    }))
  }

  const generateMockRecommendations = (category: string) => {
    const recommendations: Record<string, Array<{title: string, description: string, priority: 'alta' | 'média' | 'baixa', timeline?: string, impact?: string}>> = {
      'análise de fornecedores': [
        {
          title: 'Diversificar Base de Fornecedores',
          description: 'Reduzir dependência dos 3 principais fornecedores através de parcerias estratégicas',
          priority: 'alta' as const,
          timeline: '60 dias',
          impact: 'Redução de 30% no risco de fornecimento'
        },
        {
          title: 'Implementar Avaliação Contínua',
          description: 'Estabelecer sistema de monitoramento contínuo de performance de fornecedores',
          priority: 'média' as const,
          timeline: '90 dias',
          impact: 'Melhoria de 15% na qualidade do fornecimento'
        }
      ],
      'conformidade fiscal': [
        {
          title: 'Automatizar Validações Fiscais',
          description: 'Implementar validações automáticas para os 2.7% de não conformidades identificadas',
          priority: 'alta' as const,
          timeline: '45 dias',
          impact: 'Redução de 90% nos erros fiscais'
        }
      ],
      'default': [
        {
          title: 'Otimizar Processos Identificados',
          description: 'Implementar melhorias nos processos com maior potencial de otimização',
          priority: 'média' as const,
          timeline: '60 dias',
          impact: 'Aumento de 20% na eficiência operacional'
        }
      ]
    }
    
    return recommendations[category] || recommendations['default']
  }

  // Format timestamp for display
  const formatTime = (timestamp: Date) => {
    const now = new Date()
    const diff = now.getTime() - timestamp.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Agora mesmo'
    if (minutes < 60) return `há ${minutes}m`
    if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`
    return timestamp.toLocaleDateString('pt-BR')
  }

  const getStatusBadgeClass = (status: QueryHistoryItem['status']) => {
    switch (status) {
      case 'concluída': return 'badge-success'
      case 'processando': return 'badge-warning'
      case 'erro': return 'badge-error'
      default: return 'badge-ghost'
    }
  }

  return {
    // State
    query,
    isLoading,
    showSuggestions,
    showPreview,
    queryPreview,
    queryResult,
    queryHistory,

    // Computed
    filteredSuggestions,

    // Data
    intelligentSuggestions,
    quickActions,

    // Methods
    loadQueryHistory,
    saveQueryHistory,
    addToHistory,
    updateHistoryStatus,
    removeHistoryItem,
    clearHistory,
    generateQueryPreview,
    executeQuery,
    generateMockResult,
    formatTime,
    getStatusBadgeClass,

    // Helper functions
    getQueryCategory,
    getInvolvedAgents,
    getEstimatedTime
  }
}