<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
          Análise de Erros
        </h3>
        <div class="flex items-center gap-2">
          <div class="badge badge-error">{{ errorStats.totalErrors }}</div>
          <div class="badge badge-warning">{{ errorStats.unresolved }}</div>
        </div>
      </div>

      <!-- Error Statistics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-error">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Total de Erros</div>
          <div class="stat-value text-lg">{{ errorStats.totalErrors }}</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(-errorStats.errorTrend)">
              {{ errorStats.errorTrend > 0 ? '+' : '' }}{{ errorStats.errorTrend }}%
            </span>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-warning">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Não Resolvidos</div>
          <div class="stat-value text-lg">{{ errorStats.unresolved }}</div>
          <div class="stat-desc text-xs">
            {{ Math.round((errorStats.unresolved / errorStats.totalErrors) * 100) }}% do total
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-info">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Tempo Médio</div>
          <div class="stat-value text-lg">{{ errorStats.avgResolutionTime }}</div>
          <div class="stat-desc text-xs">para resolução</div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-success">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Taxa de Resolução</div>
          <div class="stat-value text-lg">{{ errorStats.resolutionRate }}%</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(errorStats.resolutionTrend)">
              {{ errorStats.resolutionTrend > 0 ? '+' : '' }}{{ errorStats.resolutionTrend }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Error Categories -->
      <div class="mb-6">
        <h4 class="font-semibold mb-3">Categorias de Erro</h4>
        <div class="space-y-2">
          <div
            v-for="category in errorCategories"
            :key="category.name"
            class="flex items-center justify-between p-3 bg-base-100 rounded-lg"
          >
            <div class="flex items-center gap-3">
              <div 
                class="w-4 h-4 rounded"
                :style="{ backgroundColor: category.color }"
              ></div>
              <div>
                <h5 class="font-medium">{{ category.name }}</h5>
                <p class="text-sm text-base-content/50">{{ category.description }}</p>
              </div>
            </div>
            <div class="text-right">
              <div class="text-lg font-bold">{{ category.count }}</div>
              <div class="text-xs text-base-content/50">
                {{ Math.round((category.count / errorStats.totalErrors) * 100) }}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Critical Errors -->
      <div class="mb-6">
        <h4 class="font-semibold mb-3">Erros Críticos Recentes</h4>
        <div class="space-y-2 max-h-64 overflow-y-auto">
          <div
            v-for="error in criticalErrors"
            :key="error.id"
            class="p-3 bg-base-100 rounded-lg border-l-4 border-error"
          >
            <!-- Error Header -->
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-error"></div>
                <span class="font-medium text-sm">{{ error.source }}</span>
                <div class="badge badge-error badge-xs">{{ error.level.toUpperCase() }}</div>
              </div>
              <div class="text-xs text-base-content/50">
                {{ formatTime(error.timestamp) }}
              </div>
            </div>

            <!-- Error Message -->
            <p class="text-sm mb-2">{{ error.message }}</p>

            <!-- Error Details -->
            <div class="grid grid-cols-2 gap-4 text-xs mb-2">
              <div>
                <span class="text-base-content/50">Frequência:</span>
                <span class="font-medium ml-1">{{ error.frequency }}x</span>
              </div>
              <div>
                <span class="text-base-content/50">Última ocorrência:</span>
                <span class="font-medium ml-1">{{ formatTime(error.lastOccurrence) }}</span>
              </div>
            </div>

            <!-- Error Actions -->
            <div class="flex gap-2 pt-2 border-t border-base-200">
              <button 
                @click="viewErrorDetails(error)"
                class="btn btn-ghost btn-xs"
              >
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                  <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                </svg>
                Detalhes
              </button>
              <button 
                v-if="!error.resolved"
                @click="markErrorAsResolved(error)"
                class="btn btn-ghost btn-xs text-success"
              >
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                Resolver
              </button>
              <button 
                @click="suppressError(error)"
                class="btn btn-ghost btn-xs text-warning"
              >
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"></path>
                  <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"></path>
                </svg>
                Suprimir
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="criticalErrors.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
          </svg>
          <p class="text-base-content/50">Nenhum erro crítico recente</p>
        </div>
      </div>

      <!-- Error Pattern Analysis -->
      <div class="mb-6">
        <h4 class="font-semibold mb-3">Análise de Padrões</h4>
        <div class="bg-base-100 rounded-lg p-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h5 class="font-medium mb-2">Horários de Pico</h5>
              <div class="space-y-1 text-sm">
                <div class="flex justify-between">
                  <span>14:00 - 16:00</span>
                  <span class="font-bold">23%</span>
                </div>
                <div class="flex justify-between">
                  <span>09:00 - 11:00</span>
                  <span class="font-bold">18%</span>
                </div>
                <div class="flex justify-between">
                  <span>20:00 - 22:00</span>
                  <span class="font-bold">15%</span>
                </div>
              </div>
            </div>
            <div>
              <h5 class="font-medium mb-2">Agentes Mais Afetados</h5>
              <div class="space-y-1 text-sm">
                <div class="flex justify-between">
                  <span>XML Processing Agent</span>
                  <span class="font-bold">34%</span>
                </div>
                <div class="flex justify-between">
                  <span>AI Categorization Agent</span>
                  <span class="font-bold">28%</span>
                </div>
                <div class="flex justify-between">
                  <span>Report Agent</span>
                  <span class="font-bold">21%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 flex-wrap">
        <button 
          @click="runErrorAnalysis"
          class="btn btn-primary btn-sm"
          :disabled="isRunningAnalysis"
        >
          <svg 
            class="w-4 h-4 mr-1" 
            :class="{ 'animate-spin': isRunningAnalysis }"
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
          </svg>
          Analisar Padrões
        </button>
        <button 
          @click="exportErrorReport"
          class="btn btn-outline btn-sm"
        >
          <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
          Exportar Relatório
        </button>
        <button 
          @click="configureAlerts"
          class="btn btn-outline btn-sm"
        >
          <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"></path>
          </svg>
          Configurar Alertas
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ErrorLog } from '~/types/dashboard'

// Reactive state
const isRunningAnalysis = ref(false)

const errorStats = ref({
  totalErrors: 47,
  unresolved: 12,
  avgResolutionTime: '2.3h',
  resolutionRate: 74,
  errorTrend: -8.5,
  resolutionTrend: 12.3
})

const errorCategories = ref([
  {
    name: 'API Timeout',
    description: 'Timeouts em chamadas para APIs externas',
    count: 18,
    color: '#ef4444'
  },
  {
    name: 'Database Connection',
    description: 'Problemas de conexão com banco de dados',
    count: 12,
    color: '#f97316'
  },
  {
    name: 'LLM Processing',
    description: 'Erros no processamento de LLM',
    count: 9,
    color: '#eab308'
  },
  {
    name: 'File Processing',
    description: 'Erros no processamento de arquivos XML',
    count: 5,
    color: '#22c55e'
  },
  {
    name: 'Authentication',
    description: 'Problemas de autenticação e autorização',
    count: 3,
    color: '#3b82f6'
  }
])

const criticalErrors = ref<(ErrorLog & { frequency: number; lastOccurrence: Date })[]>([
  {
    id: '1',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    level: 'error',
    source: 'OpenAI Integration Service',
    message: 'Rate limit exceeded: 429 Too Many Requests',
    resolved: false,
    frequency: 15,
    lastOccurrence: new Date(Date.now() - 2 * 60 * 1000),
    context: {
      endpoint: '/v1/chat/completions',
      model: 'gpt-4o-mini',
      retryAfter: 60
    }
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    level: 'error',
    source: 'Database Connection Pool',
    message: 'Connection pool exhausted: max 100 connections reached',
    resolved: false,
    frequency: 8,
    lastOccurrence: new Date(Date.now() - 8 * 60 * 1000),
    context: {
      activeConnections: 100,
      queuedRequests: 23,
      maxConnections: 100
    }
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    level: 'error',
    source: 'XML Processing Agent',
    message: 'Invalid XML structure: missing required namespace declaration',
    resolved: true,
    frequency: 3,
    lastOccurrence: new Date(Date.now() - 25 * 60 * 1000),
    context: {
      fileName: 'nfe_invalid_123.xml',
      lineNumber: 15,
      expectedNamespace: 'http://www.portalfiscal.inf.br/nfe'
    }
  }
])

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Methods
const runErrorAnalysis = async () => {
  isRunningAnalysis.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    // Simulate analysis results
    console.log('Error pattern analysis completed')
  } finally {
    isRunningAnalysis.value = false
  }
}

const exportErrorReport = () => {
  console.log('Exporting error analysis report')
  // In real implementation, generate and download error report
}

const configureAlerts = () => {
  console.log('Opening error alert configuration')
  // In real implementation, open alert configuration modal
}

const viewErrorDetails = (error: any) => {
  console.log('Viewing error details:', error.id)
  // In real implementation, open error details modal
}

const markErrorAsResolved = (error: any) => {
  error.resolved = true
  errorStats.value.unresolved = Math.max(0, errorStats.value.unresolved - 1)
  console.log('Error marked as resolved:', error.id)
}

const suppressError = (error: any) => {
  console.log('Suppressing error:', error.id)
  // In real implementation, add error to suppression list
}

const updateErrorStats = () => {
  // Simulate real-time error updates
  if (Math.random() > 0.95) {
    errorStats.value.totalErrors += 1
    if (Math.random() > 0.7) {
      errorStats.value.unresolved += 1
    }
  }
  
  // Occasionally resolve errors
  if (Math.random() > 0.98 && errorStats.value.unresolved > 0) {
    errorStats.value.unresolved -= 1
  }
}

// Helper functions
const getTrendClass = (trend: number) => {
  if (trend > 0) return 'text-success'
  if (trend < 0) return 'text-error'
  return 'text-base-content/50'
}

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'agora mesmo'
  if (minutes < 60) return `há ${minutes}m`
  if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`
  return timestamp.toLocaleDateString('pt-BR')
}

// Lifecycle
onMounted(() => {
  // Set up auto-refresh every 30 seconds
  refreshInterval = setInterval(updateErrorStats, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>