<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
          </svg>
          Análise de Tendências
        </h3>
        <div class="flex items-center gap-2 flex-wrap">
          <select 
            v-model="selectedTrendType"
            class="select select-sm select-bordered"
          >
            <option value="volume">Volume de Documentos</option>
            <option value="valor">Valor Total</option>
            <option value="fornecedores">Fornecedores Ativos</option>
          </select>
          <select 
            v-model="selectedPeriod"
            class="select select-sm select-bordered"
          >
            <option value="last_6_months">Últimos 6 meses</option>
            <option value="last_12_months">Últimos 12 meses</option>
            <option value="current_year">Ano atual</option>
            <option value="last_24_months">Últimos 24 meses</option>
          </select>
          <div class="tooltip" data-tip="Mostrar projeções">
            <input 
              type="checkbox" 
              v-model="showProjections"
              class="toggle toggle-sm toggle-secondary"
            />
          </div>
          <div class="tooltip" data-tip="Atualização automática">
            <input 
              type="checkbox" 
              v-model="autoRefreshEnabled"
              @change="autoRefreshEnabled ? startAutoRefresh() : stopAutoRefresh()"
              class="toggle toggle-sm toggle-primary"
            />
          </div>
          <button 
            @click="loadTrendsData" 
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

      <!-- Trends Data -->
      <div v-else-if="trendsData" class="space-y-6">
        <!-- Growth Rate Card -->
        <div class="alert" :class="getGrowthAlertClass(trendsData.growth_rate)">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd"></path>
          </svg>
          <div>
            <h3 class="font-bold">Taxa de Crescimento</h3>
            <div class="text-xs">
              {{ trendsData.growth_rate >= 0 ? 'Crescimento' : 'Declínio' }} de 
              <strong>{{ Math.abs(trendsData.growth_rate).toFixed(1) }}%</strong> 
              no período analisado
            </div>
          </div>
        </div>

        <!-- Trend Chart (Simple visualization) -->
        <div v-if="trendsData.trend_data?.length > 0">
          <h4 class="font-semibold mb-3">{{ trendsData.trend_type }} - Evolução Temporal</h4>
          <div class="overflow-x-auto">
            <table class="table table-sm bg-base-100">
              <thead>
                <tr>
                  <th>Período</th>
                  <th>{{ trendsData.trend_data[0]?.metrica || 'Valor' }}</th>
                  <th>Variação</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(point, index) in trendsData.trend_data" :key="point.periodo">
                  <td>{{ formatMonth(point.periodo) }}</td>
                  <td>
                    <span v-if="trendsData.trend_type === 'valor'">
                      {{ formatCurrency(point.valor) }}
                    </span>
                    <span v-else>
                      {{ formatNumber(point.valor) }}
                    </span>
                  </td>
                  <td>
                    <span 
                      v-if="index > 0 && trendsData?.trend_data" 
                      :class="getVariationClass(calculateVariation(trendsData.trend_data[index - 1]?.valor || 0, point.valor))"
                      class="badge badge-sm"
                    >
                      {{ formatVariation(calculateVariation(trendsData.trend_data[index - 1]?.valor || 0, point.valor)) }}
                    </span>
                    <span v-else class="text-xs opacity-50">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Seasonality Analysis -->
        <div v-if="seasonalityData.length > 0">
          <h4 class="font-semibold mb-3">Análise de Sazonalidade</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div 
              v-for="season in seasonalityData" 
              :key="season.period"
              class="stat bg-base-100 rounded-lg shadow-sm"
            >
              <div class="stat-title text-xs">{{ season.period }}</div>
              <div class="stat-value text-sm" :class="getSeasonalityClass(season.variation)">
                {{ season.variation >= 0 ? '+' : '' }}{{ season.variation.toFixed(1) }}%
              </div>
              <div class="stat-desc text-xs">{{ season.description }}</div>
            </div>
          </div>
        </div>

        <!-- Projections -->
        <div v-if="showProjections && projectionData.length > 0">
          <h4 class="font-semibold mb-3">Projeções Baseadas em Dados Históricos</h4>
          <div class="overflow-x-auto">
            <table class="table table-sm bg-base-100">
              <thead>
                <tr>
                  <th>Período Projetado</th>
                  <th>Valor Estimado</th>
                  <th>Confiança</th>
                  <th>Tendência</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="projection in projectionData" :key="projection.periodo">
                  <td>{{ formatMonth(projection.periodo) }}</td>
                  <td>
                    <span v-if="selectedTrendType === 'valor'">
                      {{ formatCurrency(projection.valor_estimado) }}
                    </span>
                    <span v-else>
                      {{ formatNumber(projection.valor_estimado) }}
                    </span>
                  </td>
                  <td>
                    <div class="badge badge-sm" :class="getConfidenceClass(projection.confianca)">
                      {{ (projection.confianca * 100).toFixed(0) }}%
                    </div>
                  </td>
                  <td>
                    <div class="badge badge-sm" :class="getTrendClass(projection.tendencia)">
                      {{ projection.tendencia }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Insights -->
        <div v-if="trendsData.insights?.length > 0">
          <h4 class="font-semibold mb-3">Insights da Análise</h4>
          <div class="space-y-2">
            <div 
              v-for="(insight, index) in trendsData.insights" 
              :key="index"
              class="flex items-start gap-3 p-3 bg-base-100 rounded-lg"
            >
              <svg class="w-5 h-5 text-info mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
              </svg>
              <span class="text-sm">{{ insight }}</span>
            </div>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="stats stats-horizontal bg-base-100 shadow">
          <div class="stat">
            <div class="stat-title text-xs">Tipo de Análise</div>
            <div class="stat-value text-sm">{{ getTrendTypeLabel(trendsData.trend_type) }}</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Pontos de Dados</div>
            <div class="stat-value text-sm">{{ trendsData.trend_data?.length || 0 }}</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Taxa de Crescimento</div>
            <div class="stat-value text-sm" :class="getGrowthClass(trendsData.growth_rate)">
              {{ trendsData.growth_rate >= 0 ? '+' : '' }}{{ trendsData.growth_rate.toFixed(1) }}%
            </div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Período</div>
            <div class="stat-desc text-xs">{{ trendsData.periodo_analise }}</div>
          </div>
          <div v-if="lastUpdated" class="stat">
            <div class="stat-title text-xs">Última Atualização</div>
            <div class="stat-desc text-xs">{{ formatLastUpdated(lastUpdated) }}</div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-base-content opacity-50 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
        </svg>
        <p class="text-base-content opacity-70">Nenhuma tendência encontrada</p>
        <p class="text-sm text-base-content opacity-50">Processe alguns documentos fiscais para ver os dados</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface TrendData {
  periodo: string
  valor: number
  metrica: string
}

interface TrendsResponse {
  trend_data: TrendData[]
  growth_rate: number
  trend_type: string
  periodo_analise: string
  insights: string[]
}

// Reactive state
const isLoading = ref(false)
const error = ref<string | null>(null)
const trendsData = ref<TrendsResponse | null>(null)
const selectedPeriod = ref('last_12_months')
const selectedTrendType = ref('volume')
const lastUpdated = ref<Date | null>(null)
const autoRefreshEnabled = ref(true)
const autoRefreshInterval = ref<NodeJS.Timeout | null>(null)
const showProjections = ref(false)

// Load trends data from API
const loadTrendsData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const { apiCall } = useApi()
    const data = await apiCall<TrendsResponse>('/api/v1/api/dashboard/trends', {
      query: {
        period: selectedPeriod.value,
        trend_type: selectedTrendType.value
      },
      cache: true,
      cacheTTL: 600000, // 10 minutes cache for trends
      retry: 3
    })

    trendsData.value = data
    lastUpdated.value = new Date()
  } catch (err: any) {
    console.error('Error loading trends data:', err)
    error.value = err.message || err.data?.mensagem || 'Erro ao carregar dados de tendências'
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

const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('pt-BR').format(value)
}

const formatMonth = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', { 
    year: 'numeric', 
    month: 'short' 
  })
}

const calculateVariation = (previousValue: number, currentValue: number): number => {
  if (previousValue === 0) return 0
  return ((currentValue - previousValue) / previousValue) * 100
}

const formatVariation = (variation: number): string => {
  const sign = variation >= 0 ? '+' : ''
  return `${sign}${variation.toFixed(1)}%`
}

const getVariationClass = (variation: number): string => {
  if (variation > 0) return 'badge-success'
  if (variation < 0) return 'badge-error'
  return 'badge-neutral'
}

const getGrowthAlertClass = (growthRate: number): string => {
  if (growthRate > 10) return 'alert-success'
  if (growthRate > 0) return 'alert-info'
  if (growthRate > -10) return 'alert-warning'
  return 'alert-error'
}

const getTrendTypeLabel = (trendType: string): string => {
  const labels: Record<string, string> = {
    volume: 'Volume de Documentos',
    valor: 'Valor Total',
    fornecedores: 'Fornecedores Ativos'
  }
  return labels[trendType] || trendType
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

const getGrowthClass = (growthRate: number): string => {
  if (growthRate > 10) return 'text-success'
  if (growthRate > 0) return 'text-info'
  if (growthRate > -10) return 'text-warning'
  return 'text-error'
}

const getSeasonalityClass = (variation: number): string => {
  if (variation > 15) return 'text-success'
  if (variation > 0) return 'text-info'
  if (variation > -15) return 'text-warning'
  return 'text-error'
}

const getConfidenceClass = (confidence: number): string => {
  if (confidence > 0.8) return 'badge-success'
  if (confidence > 0.6) return 'badge-warning'
  return 'badge-error'
}

const getTrendClass = (trend: string): string => {
  if (trend === 'crescimento') return 'badge-success'
  if (trend === 'estável') return 'badge-info'
  return 'badge-warning'
}

// Computed properties for seasonality and projections
const seasonalityData = computed(() => {
  if (!trendsData.value?.trend_data || trendsData.value.trend_data.length < 4) return []
  
  // Simple seasonality analysis based on quarterly data
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4']
  const trendData = trendsData.value.trend_data
  const quarterlyData = quarters.map((quarter, index) => {
    const quarterPoints = trendData.filter((_, i) => i % 4 === index)
    const average = quarterPoints.reduce((sum, point) => sum + point.valor, 0) / quarterPoints.length
    const overallAverage = trendData.reduce((sum, point) => sum + point.valor, 0) / trendData.length
    const variation = ((average - overallAverage) / overallAverage) * 100
    
    return {
      period: quarter,
      variation,
      description: variation > 0 ? 'Acima da média' : 'Abaixo da média'
    }
  })
  
  return quarterlyData
})

const projectionData = computed(() => {
  if (!showProjections.value || !trendsData.value?.trend_data || trendsData.value.trend_data.length < 3) return []
  
  // Simple linear projection for next 3 months
  const data = trendsData.value.trend_data
  const lastThreePoints = data.slice(-3)
  
  if (lastThreePoints.length < 3) return []
  
  const trend = ((lastThreePoints[2]?.valor || 0) - (lastThreePoints[0]?.valor || 0)) / 2
  const lastPoint = data[data.length - 1]
  
  if (!lastPoint) return []
  
  const projections = []
  for (let i = 1; i <= 3; i++) {
    const lastDate = new Date(lastPoint.periodo)
    const projectionDate = new Date(lastDate.getFullYear(), lastDate.getMonth() + i, 1)
    const projectedValue = lastPoint.valor + (trend * i)
    
    projections.push({
      periodo: projectionDate.toISOString(),
      valor_estimado: Math.max(0, projectedValue),
      confianca: Math.max(0.3, 0.9 - (i * 0.2)), // Decreasing confidence
      tendencia: trend > 0 ? 'crescimento' : trend < 0 ? 'declínio' : 'estável'
    })
  }
  
  return projections
})

// Auto-refresh functionality
const startAutoRefresh = () => {
  if (autoRefreshEnabled.value && !autoRefreshInterval.value) {
    autoRefreshInterval.value = setInterval(() => {
      loadTrendsData()
    }, 600000) // Refresh every 10 minutes
  }
}

const stopAutoRefresh = () => {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value)
    autoRefreshInterval.value = null
  }
}

// Watch for changes to reload data
watch([selectedPeriod, selectedTrendType], () => {
  loadTrendsData()
})

// Load data on mount and start auto-refresh
onMounted(() => {
  loadTrendsData()
  startAutoRefresh()
})

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>