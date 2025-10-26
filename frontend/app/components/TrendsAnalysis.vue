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
        <div class="flex items-center gap-2">
          <select 
            v-model="selectedTrendType" 
            @change="loadTrendsData"
            class="select select-sm select-bordered"
          >
            <option value="volume">Volume de Documentos</option>
            <option value="valor">Valor Total</option>
            <option value="fornecedores">Fornecedores Ativos</option>
          </select>
          <select 
            v-model="selectedPeriod" 
            @change="loadTrendsData"
            class="select select-sm select-bordered"
          >
            <option value="last_6_months">Últimos 6 meses</option>
            <option value="last_12_months">Últimos 12 meses</option>
            <option value="current_year">Ano atual</option>
          </select>
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
                      v-if="index > 0" 
                      :class="getVariationClass(calculateVariation(trendsData.trend_data[index - 1].valor, point.valor))"
                      class="badge badge-sm"
                    >
                      {{ formatVariation(calculateVariation(trendsData.trend_data[index - 1].valor, point.valor)) }}
                    </span>
                    <span v-else class="text-xs opacity-50">-</span>
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
            <div class="stat-title text-xs">Período</div>
            <div class="stat-desc text-xs">{{ trendsData.periodo_analise }}</div>
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

// Load trends data from API
const loadTrendsData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const data = await $fetch<TrendsResponse>('/api/v1/api/dashboard/trends', {
      query: {
        period: selectedPeriod.value,
        trend_type: selectedTrendType.value
      }
    })

    trendsData.value = data as TrendsResponse
  } catch (err: any) {
    console.error('Error loading trends data:', err)
    error.value = err.data?.mensagem || 'Erro ao carregar dados de tendências'
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

// Load data on mount
onMounted(() => {
  loadTrendsData()
})
</script>