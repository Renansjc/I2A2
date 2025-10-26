<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="hero bg-gradient-to-r from-primary to-secondary text-primary-content rounded-lg">
      <div class="hero-content py-8">
        <div class="max-w-4xl w-full">
          <div class="flex items-center justify-between">
            <div class="text-center lg:text-left">
              <h1 class="text-4xl font-bold">Painel Executivo</h1>
              <p class="py-4 text-lg">Insights fiscais com IA para tomada de decisões estratégicas</p>
            </div>
            <div class="hidden lg:flex items-center gap-4">
              <button 
                @click="loadDashboardData" 
                class="btn btn-outline btn-primary-content"
                :disabled="isLoading"
              >
                <svg 
                  class="w-5 h-5" 
                  :class="{ 'animate-spin': isLoading }"
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                </svg>
                Atualizar
              </button>
              <div class="text-sm opacity-75">
                Última atualização: {{ new Date().toLocaleTimeString('pt-BR') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="alert alert-error shadow-lg">
      <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
      </svg>
      <div>
        <h3 class="font-bold">Erro no Dashboard</h3>
        <div class="text-xs">{{ error }}</div>
      </div>
      <button @click="error = null" class="btn btn-sm btn-ghost">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
      </button>
    </div>

    <!-- Quick Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-primary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"></path>
          </svg>
        </div>
        <div class="stat-title">Total de Notas</div>
        <div class="stat-value text-primary">
          <span v-if="isLoading" class="loading loading-dots loading-sm"></span>
          <span v-else>{{ formattedTotalInvoices }}</span>
        </div>
        <div class="stat-desc">
          <span v-if="isLoading">Carregando...</span>
          <span v-else>Processadas este mês</span>
        </div>
      </div>

      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-secondary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Valor Total</div>
        <div class="stat-value text-secondary">
          <span v-if="isLoading" class="loading loading-dots loading-sm"></span>
          <span v-else>{{ formattedTotalValue }}</span>
        </div>
        <div class="stat-desc">
          <span v-if="isLoading">Carregando...</span>
          <span v-else>Faturamento mensal</span>
        </div>
      </div>

      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-accent">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <div class="stat-title">Fornecedores Ativos</div>
        <div class="stat-value text-accent">
          <span v-if="isLoading" class="loading loading-dots loading-sm"></span>
          <span v-else>{{ formattedActiveSuppliers }}</span>
        </div>
        <div class="stat-desc">
          <span v-if="isLoading">Carregando...</span>
          <span v-else>Com transações ativas</span>
        </div>
      </div>

      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-warning">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Eficiência Fiscal</div>
        <div class="stat-value text-warning">
          <span v-if="isLoading" class="loading loading-dots loading-sm"></span>
          <span v-else>{{ formattedFiscalEfficiency }}</span>
        </div>
        <div class="stat-desc">
          <span v-if="isLoading">Carregando...</span>
          <span v-else>Taxa de conformidade</span>
        </div>
      </div>
    </div>

    <!-- Natural Language Query Section -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h2 class="card-title text-2xl mb-4">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
          </svg>
          Consulte Seus Dados Fiscais
        </h2>
        <QueryInput />
      </div>
    </div>

    <!-- Workflow Monitoring and Agent Status -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <WorkflowMonitor />
      <AgentStatus />
    </div>

    <!-- Real Data Dashboard Components -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <FinancialSummary />
      <TrendsAnalysis />
    </div>

    <!-- Suppliers and Products Analysis -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <SuppliersChart />
      <ProductsAnalysis />
    </div>

    <!-- Recent Activity and System Status -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <RecentActivity :activities="recentActivities" />
      <SystemStatusCard />
    </div>

    <!-- Quick Actions -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Ações Rápidas</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <NuxtLink to="/upload" class="btn btn-primary btn-lg">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
            </svg>
            Enviar Arquivos XML
          </NuxtLink>
          <NuxtLink to="/reports" class="btn btn-secondary btn-lg">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>
            </svg>
            Gerar Relatório
          </NuxtLink>
          <NuxtLink to="/analytics" class="btn btn-accent btn-lg">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
            </svg>
            Ver Análises
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Dashboard page setup
definePageMeta({
  layout: 'default'
})

// Use dashboard composable
const {
  stats,
  recentActivities,
  isLoading,
  error,
  formattedTotalValue,
  formattedTotalInvoices,
  formattedActiveSuppliers,
  formattedFiscalEfficiency,
  loadDashboardData,
  refreshStats,
  formatActivityTime,
  getActivityColorClass
} = useDashboard()

// Load dashboard data on mount
onMounted(async () => {
  await loadDashboardData()
  
  // Set up periodic refresh
  const refreshInterval = setInterval(() => {
    refreshStats()
  }, 30000) // Refresh every 30 seconds
  
  // Cleanup on unmount
  onUnmounted(() => {
    clearInterval(refreshInterval)
  })
})

// Error handling
watch(error, (newError) => {
  if (newError) {
    console.error('Dashboard error:', newError)
    // In a real app, you might want to show a toast notification
  }
})
</script>