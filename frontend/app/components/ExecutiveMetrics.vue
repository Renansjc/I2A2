<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
          </svg>
          Métricas Executivas
        </h3>
        <div class="flex items-center gap-2">
          <select 
            v-model="selectedPeriod"
            class="select select-sm select-bordered"
          >
            <option value="last_30_days">Últimos 30 dias</option>
            <option value="last_90_days">Últimos 90 dias</option>
            <option value="last_6_months">Últimos 6 meses</option>
            <option value="last_12_months">Últimos 12 meses</option>
            <option value="current_year">Ano atual</option>
          </select>
          <div class="tooltip" data-tip="Atualização automática">
            <input 
              type="checkbox" 
              v-model="autoRefreshEnabled"
              @change="autoRefreshEnabled ? startAutoRefresh() : stopAutoRefresh()"
              class="toggle toggle-sm toggle-primary"
            />
          </div>
          <button 
            @click="loadMetricsData" 
            class="btn btn-sm btn-ghost"
            :disabled="isLoading"
          >
            <svg 
              class="w-4 h-4" 
              :class="{ 'animate-spin': isLoading }"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Error Alert -->
      <div v-if="error" class="alert alert-error mb-4">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center py-8">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <!-- Executive Metrics -->
      <div v-else-if="metricsData" class="space-y-6">
        <!-- Key Performance Indicators -->
        <div>
          <h4 class="font-semibold mb-3">Indicadores-Chave de Performance (KPIs)</h4>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-figure text-primary">
                <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div class="stat-title text-xs">Concentração de Fornecedores</div>
              <div class="stat-value text-lg" :class="getConcentrationClass(metricsData.kpis.concentracao_fornecedores)">
                {{ formatPercentage(metricsData.kpis.concentracao_fornecedores) }}
              </div>
              <div class="stat-desc text-xs">{{ getConcentrationDescription(metricsData.kpis.concentracao_fornecedores) }}</div>
            </div>

            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-figure text-secondary">
                <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path>
                </svg>
              </div>
              <div class="stat-title text-xs">Diversificação de Produtos</div>
              <div class="stat-value text-lg text-secondary">
                {{ formatPercentage(metricsData.kpis.diversificacao_produtos) }}
              </div>
              <div class="stat-desc text-xs">{{ getDiversificationDescription(metricsData.kpis.diversificacao_produtos) }}</div>
            </div>

            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-figure text-accent">
                <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                </svg>
              </div>
              <div class="stat-title text-xs">Crescimento Mensal</div>
              <div class="stat-value text-lg" :class="getGrowthClass(metricsData.kpis.crescimento_mensal)">
                {{ metricsData.kpis.crescimento_mensal >= 0 ? '+' : '' }}{{ metricsData.kpis.crescimento_mensal.toFixed(1) }}%
              </div>
              <div class="stat-desc text-xs">{{ getGrowthDescription(metricsData.kpis.crescimento_mensal) }}</div>
            </div>

            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-figure text-info">
                <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div class="stat-title text-xs">Ticket Médio</div>
              <div class="stat-value text-lg text-info">
                {{ formatCurrency(metricsData.kpis.ticket_medio) }}
              </div>
              <div class="stat-desc text-xs">Valor médio por transação</div>
            </div>
          </div>
        </div>

        <!-- Operational Metrics -->
        <div>
          <h4 class="font-semibold mb-3">Métricas Operacionais</h4>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">Fornecedores Ativos</div>
              <div class="stat-value text-sm">{{ metricsData.kpis.fornecedores_ativos }}</div>
              <div class="stat-desc text-xs">No período selecionado</div>
            </div>

            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">Produtos Ativos</div>
              <div class="stat-value text-sm">{{ metricsData.kpis.produtos_ativos }}</div>
              <div class="stat-desc text-xs">Produtos comercializados</div>
            </div>

            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">Score de Sazonalidade</div>
              <div class="stat-value text-sm" :class="getSeasonalityClass(metricsData.kpis.sazonalidade_score)">
                {{ formatPercentage(metricsData.kpis.sazonalidade_score) }}
              </div>
              <div class="stat-desc text-xs">{{ getSeasonalityDescription(metricsData.kpis.sazonalidade_score) }}</div>
            </div>

            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">Confiabilidade dos Dados</div>
              <div class="stat-value text-sm text-success">
                {{ formatPercentage(metricsData.kpis.confiabilidade_dados) }}
              </div>
              <div class="stat-desc text-xs">Qualidade dos dados processados</div>
            </div>
          </div>
        </div>

        <!-- Executive Insights -->
        <div v-if="executiveInsights.length > 0">
          <h4 class="font-semibold mb-3">Insights Executivos</h4>
          <div class="space-y-3">
            <div 
              v-for="(insight, index) in executiveInsights" 
              :key="index"
              class="alert" 
              :class="insight.type === 'warning' ? 'alert-warning' : insight.type === 'success' ? 'alert-success' : 'alert-info'"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
              </svg>
              <div>
                <h3 class="font-bold">{{ insight.title }}</h3>
                <div class="text-xs">{{ insight.description }}</div>
                <div v-if="insight.recommendation" class="text-xs mt-1 opacity-80">
                  <strong>Recomendação:</strong> {{ insight.recommendation }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Efficiency Indicators -->
        <div>
          <h4 class="font-semibold mb-3">Indicadores de Eficiência Fiscal</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="card bg-base-100 shadow-sm">
              <div class="card-body p-4">
                <h5 class="card-title text-sm">Concentração de Fornecedores</h5>
                <div class="flex items-center justify-between">
                  <div class="text-2xl font-bold" :class="getConcentrationClass(metricsData.kpis.concentracao_fornecedores)">
                    {{ formatPercentage(metricsData.kpis.concentracao_fornecedores) }}
                  </div>
                  <div class="radial-progress text-primary" :style="`--value:${metricsData.kpis.concentracao_fornecedores * 100}`">
                    {{ (metricsData.kpis.concentracao_fornecedores * 100).toFixed(0) }}%
                  </div>
                </div>
                <p class="text-xs opacity-70 mt-2">
                  {{ getConcentrationAnalysis(metricsData.kpis.concentracao_fornecedores) }}
                </p>
              </div>
            </div>

            <div class="card bg-base-100 shadow-sm">
              <div class="card-body p-4">
                <h5 class="card-title text-sm">Diversificação de Produtos</h5>
                <div class="flex items-center justify-between">
                  <div class="text-2xl font-bold text-secondary">
                    {{ formatPercentage(metricsData.kpis.diversificacao_produtos) }}
                  </div>
                  <div class="radial-progress text-secondary" :style="`--value:${metricsData.kpis.diversificacao_produtos * 100}`">
                    {{ (metricsData.kpis.diversificacao_produtos * 100).toFixed(0) }}%
                  </div>
                </div>
                <p class="text-xs opacity-70 mt-2">
                  {{ getDiversificationAnalysis(metricsData.kpis.diversificacao_produtos) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Period Info -->
        <div class="alert alert-info">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          <div>
            <div>Período analisado: {{ metricsData.periodo_analise }}</div>
            <div v-if="lastUpdated" class="text-xs opacity-70 mt-1">
              Última atualização: {{ formatLastUpdated(lastUpdated) }}
            </div>
            <div class="text-xs opacity-70 mt-1">
              Confiabilidade dos dados: {{ formatPercentage(metricsData.confiabilidade_dados) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-base-content opacity-50 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
        </svg>
        <p class="text-base-content opacity-70">Nenhuma métrica executiva encontrada</p>
        <p class="text-sm text-base-content opacity-50">Processe alguns documentos fiscais para ver os dados</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface DashboardMetricsResponse {
  kpis: {
    concentracao_fornecedores: number
    diversificacao_produtos: number
    crescimento_mensal: number
    ticket_medio: number
    fornecedores_ativos: number
    produtos_ativos: number
    sazonalidade_score: number
    confiabilidade_dados: number
  }
  periodo_analise: string
  ultima_atualizacao: string
  confiabilidade_dados: number
}

interface ExecutiveInsight {
  type: 'info' | 'warning' | 'success'
  title: string
  description: string
  recommendation?: string
}

// Reactive state
const isLoading = ref(false)
const error = ref<string | null>(null)
const metricsData = ref<DashboardMetricsResponse | null>(null)
const selectedPeriod = ref('last_90_days')
const lastUpdated = ref<Date | null>(null)
const autoRefreshEnabled = ref(true)
const autoRefreshInterval = ref<NodeJS.Timeout | null>(null)

// Load metrics data from API
const loadMetricsData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const { apiCall } = useApi()
    const data = await apiCall<DashboardMetricsResponse>('/api/v1/api/dashboard/metrics', {
      query: {
        period: selectedPeriod.value
      },
      cache: true,
      cacheTTL: 180000, // 3 minutes cache for metrics
      retry: 3
    })

    metricsData.value = data
    lastUpdated.value = new Date()
  } catch (err: any) {
    console.error('Error loading metrics data:', err)
    error.value = err.message || err.data?.mensagem || 'Erro ao carregar métricas executivas'
  } finally {
    isLoading.value = false
  }
}

// Utility functions
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

const formatPercentage = (value: number): string => {
  return (value * 100).toFixed(1) + '%'
}

const formatLastUpdated = (date: Date): string => {
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Classification functions
const getConcentrationClass = (value: number): string => {
  if (value > 0.7) return 'text-error'
  if (value > 0.5) return 'text-warning'
  return 'text-success'
}

const getConcentrationDescription = (value: number): string => {
  if (value > 0.7) return 'Alta concentração - Risco elevado'
  if (value > 0.5) return 'Concentração moderada'
  return 'Boa diversificação'
}

const getConcentrationAnalysis = (value: number): string => {
  if (value > 0.7) return 'Concentração alta pode representar risco de dependência. Considere diversificar fornecedores.'
  if (value > 0.5) return 'Concentração moderada. Monitore para evitar dependência excessiva.'
  return 'Boa diversificação de fornecedores reduz riscos operacionais.'
}

const getDiversificationDescription = (value: number): string => {
  if (value > 0.8) return 'Excelente diversificação'
  if (value > 0.6) return 'Boa diversificação'
  return 'Diversificação limitada'
}

const getDiversificationAnalysis = (value: number): string => {
  if (value > 0.8) return 'Portfólio bem diversificado oferece múltiplas oportunidades de mercado.'
  if (value > 0.6) return 'Diversificação adequada com oportunidades de expansão.'
  return 'Considere expandir o portfólio para reduzir riscos e aumentar oportunidades.'
}

const getGrowthClass = (value: number): string => {
  if (value > 10) return 'text-success'
  if (value > 0) return 'text-info'
  if (value > -10) return 'text-warning'
  return 'text-error'
}

const getGrowthDescription = (value: number): string => {
  if (value > 10) return 'Crescimento acelerado'
  if (value > 0) return 'Crescimento positivo'
  if (value > -10) return 'Crescimento lento'
  return 'Declínio'
}

const getSeasonalityClass = (value: number): string => {
  if (value > 0.7) return 'text-warning'
  if (value > 0.4) return 'text-info'
  return 'text-success'
}

const getSeasonalityDescription = (value: number): string => {
  if (value > 0.7) return 'Alta sazonalidade'
  if (value > 0.4) return 'Sazonalidade moderada'
  return 'Baixa sazonalidade'
}

// Computed executive insights
const executiveInsights = computed((): ExecutiveInsight[] => {
  if (!metricsData.value) return []
  
  const insights: ExecutiveInsight[] = []
  const kpis = metricsData.value.kpis
  
  // Concentration analysis
  if (kpis.concentracao_fornecedores > 0.7) {
    insights.push({
      type: 'warning',
      title: 'Alta Concentração de Fornecedores',
      description: `${formatPercentage(kpis.concentracao_fornecedores)} do volume está concentrado em poucos fornecedores.`,
      recommendation: 'Considere diversificar a base de fornecedores para reduzir riscos operacionais.'
    })
  }
  
  // Growth analysis
  if (kpis.crescimento_mensal > 15) {
    insights.push({
      type: 'success',
      title: 'Crescimento Acelerado',
      description: `Crescimento mensal de ${kpis.crescimento_mensal.toFixed(1)}% indica expansão robusta.`,
      recommendation: 'Monitore a capacidade operacional para sustentar este crescimento.'
    })
  } else if (kpis.crescimento_mensal < -5) {
    insights.push({
      type: 'warning',
      title: 'Declínio no Crescimento',
      description: `Crescimento mensal negativo de ${kpis.crescimento_mensal.toFixed(1)}% requer atenção.`,
      recommendation: 'Analise as causas do declínio e implemente ações corretivas.'
    })
  }
  
  // Diversification analysis
  if (kpis.diversificacao_produtos < 0.5) {
    insights.push({
      type: 'info',
      title: 'Oportunidade de Diversificação',
      description: `Diversificação de produtos em ${formatPercentage(kpis.diversificacao_produtos)} oferece espaço para crescimento.`,
      recommendation: 'Explore novos produtos ou categorias para ampliar o portfólio.'
    })
  }
  
  // Seasonality analysis
  if (kpis.sazonalidade_score > 0.7) {
    insights.push({
      type: 'info',
      title: 'Padrão Sazonal Identificado',
      description: `Score de sazonalidade de ${formatPercentage(kpis.sazonalidade_score)} indica variações previsíveis.`,
      recommendation: 'Use padrões sazonais para otimizar planejamento e estoque.'
    })
  }
  
  return insights
})

// Auto-refresh functionality
const startAutoRefresh = () => {
  if (autoRefreshEnabled.value && !autoRefreshInterval.value) {
    autoRefreshInterval.value = setInterval(() => {
      loadMetricsData()
    }, 180000) // Refresh every 3 minutes
  }
}

const stopAutoRefresh = () => {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value)
    autoRefreshInterval.value = null
  }
}

// Watch for period changes to reload data
watch(selectedPeriod, () => {
  loadMetricsData()
})

// Load data on mount and start auto-refresh
onMounted(() => {
  loadMetricsData()
  startAutoRefresh()
})

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>