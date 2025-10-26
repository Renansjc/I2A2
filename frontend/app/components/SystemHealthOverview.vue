<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          Saúde Geral do Sistema
        </h3>
        <div class="flex items-center gap-2">
          <div 
            class="badge"
            :class="getHealthBadgeClass(systemHealth.overallHealth)"
          >
            {{ getHealthStatus(systemHealth.overallHealth) }}
          </div>
          <div class="text-sm text-base-content/50">
            {{ systemHealth.overallHealth }}%
          </div>
        </div>
      </div>

      <!-- Overall Health Score -->
      <div class="mb-6">
        <div class="flex justify-between text-sm mb-2">
          <span>Saúde Geral do Sistema</span>
          <span>{{ systemHealth.overallHealth }}%</span>
        </div>
        <div class="relative">
          <progress 
            class="progress progress-lg w-full"
            :class="getHealthProgressClass(systemHealth.overallHealth)"
            :value="systemHealth.overallHealth" 
            max="100"
          ></progress>
          <div class="absolute inset-0 flex items-center justify-center">
            <span class="text-sm font-bold text-base-content">
              {{ systemHealth.overallHealth }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Key Metrics Grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-primary">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Requisições</div>
          <div class="stat-value text-lg">{{ formatNumber(systemHealth.totalRequests) }}</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(requestsTrend)">
              {{ requestsTrend > 0 ? '+' : '' }}{{ requestsTrend }}%
            </span>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-secondary">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Tempo Médio</div>
          <div class="stat-value text-lg">{{ systemHealth.avgResponseTime }}ms</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(-responseTimeTrend)">
              {{ responseTimeTrend > 0 ? '+' : '' }}{{ responseTimeTrend }}ms
            </span>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-success">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Taxa de Sucesso</div>
          <div class="stat-value text-lg">{{ systemHealth.successRate }}%</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(successRateTrend)">
              {{ successRateTrend > 0 ? '+' : '' }}{{ successRateTrend }}%
            </span>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-info">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Uptime</div>
          <div class="stat-value text-lg">{{ systemUptime }}</div>
          <div class="stat-desc text-xs">
            <span class="text-success">99.8%</span> disponibilidade
          </div>
        </div>
      </div>

      <!-- Component Health Status -->
      <div class="space-y-3">
        <h4 class="font-semibold">Status dos Componentes</h4>
        <div class="space-y-2">
          <div
            v-for="component in systemComponents"
            :key="component.name"
            class="flex items-center justify-between p-3 bg-base-100 rounded-lg"
          >
            <div class="flex items-center gap-3">
              <div 
                class="w-3 h-3 rounded-full"
                :class="getComponentStatusColor(component.status)"
              ></div>
              <div>
                <h5 class="font-medium">{{ component.name }}</h5>
                <p class="text-sm text-base-content/50">{{ component.description }}</p>
              </div>
            </div>
            <div class="text-right">
              <div 
                class="badge badge-sm"
                :class="getComponentStatusBadgeClass(component.status)"
              >
                {{ getComponentStatusText(component.status) }}
              </div>
              <div class="text-xs text-base-content/50 mt-1">
                {{ component.responseTime }}ms
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Incidents -->
      <div v-if="recentIncidents.length > 0" class="mt-6 pt-4 border-t border-base-300">
        <h4 class="font-semibold mb-3">Incidentes Recentes</h4>
        <div class="space-y-2">
          <div
            v-for="incident in recentIncidents"
            :key="incident.id"
            class="alert shadow-lg"
            :class="getIncidentAlertClass(incident.severity)"
          >
            <div>
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path :d="getIncidentIcon(incident.severity)"></path>
              </svg>
              <div>
                <h3 class="font-bold">{{ incident.title }}</h3>
                <div class="text-xs">{{ incident.description }}</div>
                <div class="text-xs opacity-50 mt-1">
                  {{ formatTime(incident.timestamp) }}
                </div>
              </div>
            </div>
            <div class="flex-none">
              <button 
                v-if="!incident.resolved"
                @click="resolveIncident(incident)"
                class="btn btn-sm"
              >
                Resolver
              </button>
              <div v-else class="badge badge-success">Resolvido</div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Actions -->
      <div class="mt-6 pt-4 border-t border-base-300">
        <div class="flex gap-2 flex-wrap">
          <button 
            @click="runHealthCheck"
            class="btn btn-primary btn-sm"
            :disabled="isRunningHealthCheck"
          >
            <svg 
              class="w-4 h-4 mr-1" 
              :class="{ 'animate-spin': isRunningHealthCheck }"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
            Verificar Saúde
          </button>
          <button 
            @click="viewDetailedMetrics"
            class="btn btn-outline btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
            </svg>
            Métricas Detalhadas
          </button>
          <button 
            @click="exportHealthReport"
            class="btn btn-outline btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Exportar Relatório
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { SystemHealth } from '~/types/dashboard'

// Reactive state
const isRunningHealthCheck = ref(false)
const systemHealth = ref<SystemHealth>({
  overallHealth: 94,
  totalRequests: 15847,
  avgResponseTime: 234,
  successRate: 96.8
})

// Mock data
const requestsTrend = ref(12.5)
const responseTimeTrend = ref(-8.3)
const successRateTrend = ref(2.1)

const systemComponents = ref([
  {
    name: 'API Gateway',
    description: 'Ponto de entrada principal do sistema',
    status: 'healthy',
    responseTime: 45
  },
  {
    name: 'Database (PostgreSQL)',
    description: 'Banco de dados principal via Supabase',
    status: 'healthy',
    responseTime: 12
  },
  {
    name: 'Redis Cache',
    description: 'Sistema de cache e filas de tarefas',
    status: 'healthy',
    responseTime: 3
  },
  {
    name: 'OpenAI API',
    description: 'Integração com serviços de LLM',
    status: 'warning',
    responseTime: 1250
  },
  {
    name: 'Agent Orchestrator',
    description: 'Coordenador de agentes de IA',
    status: 'healthy',
    responseTime: 89
  },
  {
    name: 'File Storage',
    description: 'Armazenamento de arquivos XML',
    status: 'healthy',
    responseTime: 156
  }
])

const recentIncidents = ref([
  {
    id: '1',
    title: 'Latência elevada na API OpenAI',
    description: 'Tempo de resposta acima do normal detectado',
    severity: 'warning',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    resolved: false
  },
  {
    id: '2',
    title: 'Pico de tráfego resolvido',
    description: 'Sistema se recuperou automaticamente do pico de requisições',
    severity: 'info',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    resolved: true
  }
])

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Computed properties
const systemUptime = computed(() => {
  // Mock uptime calculation
  const days = 15
  const hours = 7
  const minutes = 23
  
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
})

// Methods
const runHealthCheck = async () => {
  isRunningHealthCheck.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Simulate health check results
    systemHealth.value.overallHealth = Math.min(100, systemHealth.value.overallHealth + Math.random() * 4 - 2)
    systemHealth.value.avgResponseTime = Math.max(50, systemHealth.value.avgResponseTime + Math.random() * 40 - 20)
    systemHealth.value.successRate = Math.min(100, Math.max(90, systemHealth.value.successRate + Math.random() * 2 - 1))
    
    // Update component statuses
    systemComponents.value.forEach(component => {
      if (Math.random() > 0.8) {
        component.responseTime = Math.max(1, component.responseTime + Math.random() * 100 - 50)
      }
    })
  } finally {
    isRunningHealthCheck.value = false
  }
}

const viewDetailedMetrics = () => {
  console.log('Opening detailed metrics view')
  // In real implementation, navigate to detailed metrics page
}

const exportHealthReport = () => {
  console.log('Exporting health report')
  // In real implementation, generate and download health report
}

const resolveIncident = (incident: any) => {
  incident.resolved = true
  console.log('Incident resolved:', incident.id)
}

const refreshSystemHealth = () => {
  // Simulate real-time updates
  systemHealth.value.totalRequests += Math.floor(Math.random() * 10)
  
  // Occasionally update other metrics
  if (Math.random() > 0.9) {
    systemHealth.value.avgResponseTime = Math.max(50, systemHealth.value.avgResponseTime + Math.random() * 20 - 10)
    systemHealth.value.successRate = Math.min(100, Math.max(90, systemHealth.value.successRate + Math.random() * 1 - 0.5))
  }
}

// Helper functions
const getHealthBadgeClass = (health: number) => {
  if (health >= 95) return 'badge-success'
  if (health >= 85) return 'badge-warning'
  return 'badge-error'
}

const getHealthStatus = (health: number) => {
  if (health >= 95) return 'Excelente'
  if (health >= 85) return 'Bom'
  if (health >= 70) return 'Regular'
  return 'Crítico'
}

const getHealthProgressClass = (health: number) => {
  if (health >= 95) return 'progress-success'
  if (health >= 85) return 'progress-warning'
  return 'progress-error'
}

const getTrendClass = (trend: number) => {
  if (trend > 0) return 'text-success'
  if (trend < 0) return 'text-error'
  return 'text-base-content/50'
}

const getComponentStatusColor = (status: string) => {
  switch (status) {
    case 'healthy': return 'bg-success'
    case 'warning': return 'bg-warning'
    case 'error': return 'bg-error'
    default: return 'bg-base-300'
  }
}

const getComponentStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'healthy': return 'badge-success'
    case 'warning': return 'badge-warning'
    case 'error': return 'badge-error'
    default: return 'badge-ghost'
  }
}

const getComponentStatusText = (status: string) => {
  switch (status) {
    case 'healthy': return 'Saudável'
    case 'warning': return 'Atenção'
    case 'error': return 'Erro'
    default: return 'Desconhecido'
  }
}

const getIncidentAlertClass = (severity: string) => {
  switch (severity) {
    case 'error': return 'alert-error'
    case 'warning': return 'alert-warning'
    case 'info': return 'alert-info'
    default: return 'alert-info'
  }
}

const getIncidentIcon = (severity: string) => {
  switch (severity) {
    case 'error': return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'warning': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z'
    case 'info': return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const formatNumber = (num: number) => {
  return num.toLocaleString('pt-BR')
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
  refreshInterval = setInterval(refreshSystemHealth, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>