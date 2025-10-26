<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          Status do Sistema
        </h3>
        <button 
          @click="loadSystemStatus" 
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

      <!-- System Status -->
      <div v-else-if="systemStatus" class="space-y-6">
        <!-- Overall Health -->
        <div class="flex items-center justify-between p-4 bg-base-100 rounded-lg">
          <div class="flex items-center gap-3">
            <div 
              class="w-4 h-4 rounded-full"
              :class="getHealthStatusColor(systemStatus.system_health.status)"
            ></div>
            <div>
              <div class="font-semibold">Saúde Geral do Sistema</div>
              <div class="text-sm opacity-70">{{ getHealthStatusText(systemStatus.system_health.status) }}</div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold" :class="getHealthScoreColor(systemStatus.system_health.overall_health)">
              {{ systemStatus.system_health.overall_health.toFixed(0) }}%
            </div>
            <div class="text-xs opacity-60">Score de Saúde</div>
          </div>
        </div>

        <!-- Processing Statistics -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="stat bg-base-100 rounded-lg shadow-sm">
            <div class="stat-title text-xs">Documentos Hoje</div>
            <div class="stat-value text-lg text-primary">{{ systemStatus.processing_stats.documents_today }}</div>
          </div>
          <div class="stat bg-base-100 rounded-lg shadow-sm">
            <div class="stat-title text-xs">Taxa de Sucesso</div>
            <div class="stat-value text-lg text-success">{{ systemStatus.processing_stats.success_rate.toFixed(1) }}%</div>
          </div>
          <div class="stat bg-base-100 rounded-lg shadow-sm">
            <div class="stat-title text-xs">Total Processados</div>
            <div class="stat-value text-lg text-info">{{ systemStatus.processing_stats.total_documents }}</div>
          </div>
          <div class="stat bg-base-100 rounded-lg shadow-sm">
            <div class="stat-title text-xs">Documentos com Erro</div>
            <div class="stat-value text-lg text-error">{{ systemStatus.processing_stats.error_documents }}</div>
          </div>
        </div>

        <!-- API Status -->
        <div>
          <h4 class="font-semibold mb-3">Status das APIs</h4>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div 
              v-for="(status, api) in systemStatus.api_status" 
              :key="api"
              class="flex items-center gap-2 p-3 bg-base-100 rounded-lg"
            >
              <div 
                class="w-3 h-3 rounded-full"
                :class="status === 'active' ? 'bg-success' : 'bg-error'"
              ></div>
              <div>
                <div class="text-sm font-medium">{{ formatApiName(api) }}</div>
                <div class="text-xs opacity-70">{{ status === 'active' ? 'Ativa' : 'Inativa' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- System Uptime -->
        <div class="flex items-center justify-between p-4 bg-base-100 rounded-lg">
          <div>
            <div class="font-semibold">Tempo de Atividade</div>
            <div class="text-sm opacity-70">Sistema operacional há {{ systemStatus.system_health.uptime_days }} dias</div>
          </div>
          <div class="text-right">
            <div class="text-sm font-medium">Último Reinício</div>
            <div class="text-xs opacity-60">{{ formatDate(systemStatus.system_health.last_restart) }}</div>
          </div>
        </div>

        <!-- Last Update -->
        <div class="text-center text-xs opacity-50">
          Última atualização: {{ formatDate(systemStatus.generated_at) }}
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-base-content opacity-50 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-base-content opacity-70">Status do sistema indisponível</p>
        <p class="text-sm text-base-content opacity-50">Clique em atualizar para tentar novamente</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Use system activities composable
const {
  systemStatus,
  isLoading,
  error,
  loadSystemStatus
} = useSystemActivities()

// Utility functions
const getHealthStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
      return 'bg-success'
    case 'warning':
      return 'bg-warning'
    case 'critical':
      return 'bg-error'
    default:
      return 'bg-base-300'
  }
}

const getHealthStatusText = (status: string): string => {
  switch (status) {
    case 'healthy':
      return 'Sistema funcionando normalmente'
    case 'warning':
      return 'Sistema com alertas'
    case 'critical':
      return 'Sistema com problemas críticos'
    default:
      return 'Status desconhecido'
  }
}

const getHealthScoreColor = (score: number): string => {
  if (score >= 90) return 'text-success'
  if (score >= 70) return 'text-warning'
  return 'text-error'
}

const formatApiName = (apiKey: string): string => {
  const names: Record<string, string> = {
    'dimensional_apis': 'APIs Dimensionais',
    'search_apis': 'APIs de Busca',
    'upload_api': 'API de Upload',
    'export_api': 'API de Exportação'
  }
  return names[apiKey] || apiKey
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('pt-BR')
}

// Load system status on mount
onMounted(() => {
  loadSystemStatus()
})
</script>