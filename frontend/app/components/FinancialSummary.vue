<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
          </svg>
          Resumo Financeiro
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
            @click="loadFinancialData" 
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

      <!-- Financial Data -->
      <div v-else-if="financialData" class="space-y-6">
        <!-- Main Financial Stats -->
        <div class="stats stats-vertical lg:stats-horizontal bg-base-100 shadow">
          <div class="stat">
            <div class="stat-figure text-primary">
              <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"></path>
              </svg>
            </div>
            <div class="stat-title">Total de Notas</div>
            <div class="stat-value text-primary">{{ formatNumber(financialData.total_invoices) }}</div>
            <div class="stat-desc">Documentos processados</div>
          </div>

          <div class="stat">
            <div class="stat-figure text-secondary">
              <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
              </svg>
            </div>
            <div class="stat-title">Valor Total</div>
            <div class="stat-value text-secondary">{{ formatCurrency(financialData.total_value) }}</div>
            <div class="stat-desc">Faturamento no período</div>
          </div>

          <div class="stat">
            <div class="stat-figure text-accent">
              <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
              </svg>
            </div>
            <div class="stat-title">Ticket Médio</div>
            <div class="stat-value text-accent">{{ formatCurrency(financialData.average_invoice_value) }}</div>
            <div class="stat-desc">Valor médio por nota</div>
          </div>
        </div>

        <!-- Tax Summary -->
        <div v-if="financialData.tax_summary">
          <h4 class="font-semibold mb-3">Resumo de Impostos</h4>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">ICMS</div>
              <div class="stat-value text-sm text-info">{{ formatCurrency(financialData.tax_summary.total_icms) }}</div>
            </div>
            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">IPI</div>
              <div class="stat-value text-sm text-warning">{{ formatCurrency(financialData.tax_summary.total_ipi) }}</div>
            </div>
            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">PIS</div>
              <div class="stat-value text-sm text-success">{{ formatCurrency(financialData.tax_summary.total_pis) }}</div>
            </div>
            <div class="stat bg-base-100 rounded-lg shadow-sm">
              <div class="stat-title text-xs">COFINS</div>
              <div class="stat-value text-sm text-error">{{ formatCurrency(financialData.tax_summary.total_cofins) }}</div>
            </div>
          </div>
        </div>

        <!-- Monthly Trend -->
        <div v-if="financialData.monthly_totals?.length > 0">
          <h4 class="font-semibold mb-3">Evolução Mensal</h4>
          <div class="overflow-x-auto">
            <table class="table table-sm bg-base-100">
              <thead>
                <tr>
                  <th>Mês</th>
                  <th>Notas</th>
                  <th>Valor Total</th>
                  <th>Impostos</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="month in financialData.monthly_totals" :key="month.mes">
                  <td>{{ formatMonth(month.mes) }}</td>
                  <td>{{ formatNumber(month.total_invoices) }}</td>
                  <td>{{ formatCurrency(month.total_value) }}</td>
                  <td>{{ formatCurrency(month.total_taxes) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Period Info -->
        <div class="alert alert-info">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          <div>
            <div>Período analisado: {{ financialData.periodo_analise }}</div>
            <div v-if="lastUpdated" class="text-xs opacity-70 mt-1">
              Última atualização: {{ formatLastUpdated(lastUpdated) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-base-content opacity-50 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-base-content opacity-70">Nenhum dado financeiro encontrado</p>
        <p class="text-sm text-base-content opacity-50">Processe alguns documentos fiscais para ver os dados</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface TaxSummary {
  total_icms: number
  total_ipi: number
  total_pis: number
  total_cofins: number
}

interface MonthlyTotal {
  mes: string
  total_invoices: number
  total_value: number
  total_taxes: number
}

interface FinancialSummaryResponse {
  total_invoices: number
  total_value: number
  average_invoice_value: number
  monthly_totals: MonthlyTotal[]
  tax_summary: TaxSummary
  periodo_analise: string
}

// Reactive state
const isLoading = ref(false)
const error = ref<string | null>(null)
const financialData = ref<FinancialSummaryResponse | null>(null)
const selectedPeriod = ref('last_90_days')
const lastUpdated = ref<Date | null>(null)

// Load financial data from API using enhanced composable
const loadFinancialData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const { apiCall } = useApi()
    const data = await apiCall<FinancialSummaryResponse>('/api/v1/api/dashboard/financial-summary', {
      query: {
        period: selectedPeriod.value
      },
      cache: true,
      cacheTTL: 300000, // 5 minutes cache
      retry: 3
    })

    financialData.value = data
    lastUpdated.value = new Date()
  } catch (err: any) {
    console.error('Error loading financial data:', err)
    error.value = err.message || err.data?.mensagem || 'Erro ao carregar dados financeiros'
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

const formatLastUpdated = (date: Date): string => {
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Auto-refresh functionality
const autoRefreshInterval = ref<NodeJS.Timeout | null>(null)
const autoRefreshEnabled = ref(true)

const startAutoRefresh = () => {
  if (autoRefreshEnabled.value && !autoRefreshInterval.value) {
    autoRefreshInterval.value = setInterval(() => {
      loadFinancialData()
    }, 300000) // Refresh every 5 minutes
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
  loadFinancialData()
})

// Load data on mount and start auto-refresh
onMounted(() => {
  loadFinancialData()
  startAutoRefresh()
})

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>