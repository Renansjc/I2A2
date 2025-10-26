<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Top Fornecedores
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
          </select>
          <select 
            v-model="suppliersLimit"
            class="select select-sm select-bordered"
          >
            <option :value="5">Top 5</option>
            <option :value="10">Top 10</option>
            <option :value="20">Top 20</option>
            <option :value="50">Top 50</option>
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
            @click="loadSuppliersData" 
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

      <!-- Suppliers List -->
      <div v-else-if="suppliersData?.top_suppliers?.length" class="space-y-3">
        <div 
          v-for="(supplier, index) in suppliersData.top_suppliers" 
          :key="supplier.cnpj"
          class="flex items-center justify-between p-3 bg-base-100 rounded-lg hover:bg-base-300 transition-colors cursor-pointer"
          @click="navigateToSupplierDetails(supplier.cnpj)"
        >
          <div class="flex items-center gap-3">
            <div class="avatar placeholder">
              <div class="bg-primary text-primary-content rounded-full w-10">
                <span class="text-sm font-bold">{{ index + 1 }}</span>
              </div>
            </div>
            <div>
              <div class="font-semibold text-sm">{{ supplier.razao_social }}</div>
              <div class="text-xs opacity-70">
                {{ supplier.nome_fantasia || 'Sem nome fantasia' }} • {{ supplier.uf }}
              </div>
              <div class="text-xs opacity-60">
                CNPJ: {{ formatCNPJ(supplier.cnpj) }}
              </div>
            </div>
          </div>
          <div class="text-right">
            <div class="font-bold text-sm">{{ formatCurrency(supplier.valor_total) }}</div>
            <div class="text-xs opacity-70">{{ supplier.total_documentos }} docs</div>
            <div class="text-xs opacity-60">{{ supplier.produtos_distintos }} produtos</div>
          </div>
        </div>

        <!-- Monthly Trends -->
        <div v-if="suppliersData.monthly_trend?.length > 0" class="mt-4">
          <h4 class="font-semibold mb-3">Tendência Mensal</h4>
          <div class="overflow-x-auto">
            <table class="table table-sm bg-base-100">
              <thead>
                <tr>
                  <th>Mês</th>
                  <th>Fornecedores Ativos</th>
                  <th>Valor Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="trend in suppliersData.monthly_trend" :key="trend.mes">
                  <td>{{ formatMonth(trend.mes) }}</td>
                  <td>{{ trend.fornecedores_ativos }}</td>
                  <td>{{ formatCurrency(trend.valor_total_mes) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="stats stats-horizontal bg-base-100 shadow mt-4">
          <div class="stat">
            <div class="stat-title text-xs">Total Fornecedores</div>
            <div class="stat-value text-lg">{{ suppliersData.total_suppliers }}</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Período</div>
            <div class="stat-desc text-xs">{{ suppliersData.periodo_analise }}</div>
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
          <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-base-content opacity-70">Nenhum fornecedor encontrado</p>
        <p class="text-sm text-base-content opacity-50">Processe alguns documentos fiscais para ver os dados</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface SupplierSummary {
  cnpj: string
  razao_social: string
  nome_fantasia?: string
  uf: string
  total_documentos: number
  valor_total: number
  valor_medio_item: number
  primeira_compra?: string
  ultima_compra?: string
  produtos_distintos: number
}

interface SuppliersResponse {
  total_suppliers: number
  top_suppliers: SupplierSummary[]
  monthly_trend: any[]
  periodo_analise: string
}

// Reactive state
const isLoading = ref(false)
const error = ref<string | null>(null)
const suppliersData = ref<SuppliersResponse | null>(null)
const selectedPeriod = ref('last_90_days')
const suppliersLimit = ref(10)
const lastUpdated = ref<Date | null>(null)
const autoRefreshEnabled = ref(true)
const autoRefreshInterval = ref<NodeJS.Timeout | null>(null)

// Load suppliers data from API
const loadSuppliersData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const { apiCall } = useApi()
    const data = await apiCall<SuppliersResponse>('/api/v1/api/dashboard/suppliers', {
      query: {
        period: selectedPeriod.value,
        limit: suppliersLimit.value
      },
      cache: true,
      cacheTTL: 300000, // 5 minutes cache
      retry: 3
    })

    suppliersData.value = data
    lastUpdated.value = new Date()
  } catch (err: any) {
    console.error('Error loading suppliers data:', err)
    error.value = err.message || err.data?.mensagem || 'Erro ao carregar dados de fornecedores'
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

const formatCNPJ = (cnpj: string): string => {
  return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
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

// Navigation function
const navigateToSupplierDetails = (cnpj: string) => {
  // TODO: Implement navigation to supplier details page
  console.log('Navigate to supplier details:', cnpj)
  // navigateTo(`/suppliers/${cnpj}`)
}

// Auto-refresh functionality
const startAutoRefresh = () => {
  if (autoRefreshEnabled.value && !autoRefreshInterval.value) {
    autoRefreshInterval.value = setInterval(() => {
      loadSuppliersData()
    }, 300000) // Refresh every 5 minutes
  }
}

const stopAutoRefresh = () => {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value)
    autoRefreshInterval.value = null
  }
}

// Watch for changes to reload data
watch([selectedPeriod, suppliersLimit], () => {
  loadSuppliersData()
})

// Load data on mount and start auto-refresh
onMounted(() => {
  loadSuppliersData()
  startAutoRefresh()
})

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>