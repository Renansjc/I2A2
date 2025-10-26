<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
          </svg>
          Métricas do Sistema
        </h3>
        <div class="flex items-center gap-2">
          <select v-model="timeRange" class="select select-bordered select-sm">
            <option value="1h">Última hora</option>
            <option value="24h">Últimas 24h</option>
            <option value="7d">Últimos 7 dias</option>
          </select>
          <button 
            @click="refreshMetrics"
            class="btn btn-ghost btn-sm"
            :disabled="isRefreshing"
          >
            <svg 
              class="w-4 h-4" 
              :class="{ 'animate-spin': isRefreshing }"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Current System Metrics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-primary">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">CPU</div>
          <div class="stat-value text-lg">{{ currentMetrics.cpu }}%</div>
          <div class="stat-desc">
            <progress 
              class="progress progress-xs w-full"
              :class="getUsageProgressClass(currentMetrics.cpu)"
              :value="currentMetrics.cpu" 
              max="100"
            ></progress>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-secondary">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Memória</div>
          <div class="stat-value text-lg">{{ currentMetrics.memory }}%</div>
          <div class="stat-desc">
            <progress 
              class="progress progress-xs w-full"
              :class="getUsageProgressClass(currentMetrics.memory)"
              :value="currentMetrics.memory" 
              max="100"
            ></progress>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-accent">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Disco</div>
          <div class="stat-value text-lg">{{ currentMetrics.disk }}%</div>
          <div class="stat-desc">
            <progress 
              class="progress progress-xs w-full"
              :class="getUsageProgressClass(currentMetrics.disk)"
              :value="currentMetrics.disk" 
              max="100"
            ></progress>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-info">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Rede</div>
          <div class="stat-value text-lg">{{ formatBytes(currentMetrics.network.inbound + currentMetrics.network.outbound) }}/s</div>
          <div class="stat-desc text-xs">
            ↓{{ formatBytes(currentMetrics.network.inbound) }} ↑{{ formatBytes(currentMetrics.network.outbound) }}
          </div>
        </div>
      </div>

      <!-- Database Metrics -->
      <div class="mb-6">
        <h4 class="font-semibold mb-3">Métricas do Banco de Dados</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-base-100 rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium">Conexões Ativas</span>
              <span class="text-lg font-bold">{{ currentMetrics.database.connections }}</span>
            </div>
            <progress 
              class="progress progress-primary progress-xs w-full" 
              :value="currentMetrics.database.connections" 
              max="100"
            ></progress>
            <div class="text-xs text-base-content/50 mt-1">
              Máximo: 100 conexões
            </div>
          </div>

          <div class="bg-base-100 rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium">Tempo de Query</span>
              <span class="text-lg font-bold">{{ currentMetrics.database.queryTime }}ms</span>
            </div>
            <progress 
              class="progress progress-xs w-full"
              :class="getQueryTimeProgressClass(currentMetrics.database.queryTime)"
              :value="Math.min(100, currentMetrics.database.queryTime / 10)" 
              max="100"
            ></progress>
            <div class="text-xs text-base-content/50 mt-1">
              Média das últimas consultas
            </div>
          </div>
        </div>
      </div>

      <!-- Redis Metrics -->
      <div class="mb-6">
        <h4 class="font-semibold mb-3">Métricas do Redis</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-base-100 rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium">Conexões</span>
              <span class="text-lg font-bold">{{ currentMetrics.redis.connections }}</span>
            </div>
            <progress 
              class="progress progress-secondary progress-xs w-full" 
              :value="currentMetrics.redis.connections" 
              max="50"
            ></progress>
            <div class="text-xs text-base-content/50 mt-1">
              Máximo: 50 conexões
            </div>
          </div>

          <div class="bg-base-100 rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium">Uso de Memória</span>
              <span class="text-lg font-bold">{{ currentMetrics.redis.memoryUsage }}%</span>
            </div>
            <progress 
              class="progress progress-xs w-full"
              :class="getUsageProgressClass(currentMetrics.redis.memoryUsage)"
              :value="currentMetrics.redis.memoryUsage" 
              max="100"
            ></progress>
            <div class="text-xs text-base-content/50 mt-1">
              {{ formatBytes(currentMetrics.redis.memoryUsage * 1024 * 1024 * 10) }} / 1GB
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Trends -->
      <div class="mb-6">
        <h4 class="font-semibold mb-3">Tendências de Performance</h4>
        <div class="bg-base-100 rounded-lg p-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <div class="text-2xl font-bold text-primary">{{ performanceTrends.avgCpu }}%</div>
              <div class="text-xs text-base-content/50">CPU Média</div>
              <div class="text-xs">
                <span :class="getTrendClass(performanceTrends.cpuTrend)">
                  {{ performanceTrends.cpuTrend > 0 ? '+' : '' }}{{ performanceTrends.cpuTrend }}%
                </span>
              </div>
            </div>
            <div>
              <div class="text-2xl font-bold text-secondary">{{ performanceTrends.avgMemory }}%</div>
              <div class="text-xs text-base-content/50">Memória Média</div>
              <div class="text-xs">
                <span :class="getTrendClass(performanceTrends.memoryTrend)">
                  {{ performanceTrends.memoryTrend > 0 ? '+' : '' }}{{ performanceTrends.memoryTrend }}%
                </span>
              </div>
            </div>
            <div>
              <div class="text-2xl font-bold text-accent">{{ performanceTrends.avgResponseTime }}ms</div>
              <div class="text-xs text-base-content/50">Tempo Resposta</div>
              <div class="text-xs">
                <span :class="getTrendClass(-performanceTrends.responseTimeTrend)">
                  {{ performanceTrends.responseTimeTrend > 0 ? '+' : '' }}{{ performanceTrends.responseTimeTrend }}ms
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Resource Alerts -->
      <div v-if="resourceAlerts.length > 0" class="mb-6">
        <h4 class="font-semibold mb-3">Alertas de Recursos</h4>
        <div class="space-y-2">
          <div
            v-for="alert in resourceAlerts"
            :key="alert.id"
            class="alert shadow-lg"
            :class="getAlertClass(alert.level)"
          >
            <div>
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path :d="getAlertIcon(alert.level)"></path>
              </svg>
              <div>
                <h3 class="font-bold">{{ alert.title }}</h3>
                <div class="text-xs">{{ alert.description }}</div>
              </div>
            </div>
            <div class="flex-none">
              <button @click="dismissAlert(alert.id)" class="btn btn-sm btn-ghost">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 flex-wrap">
        <button 
          @click="optimizeResources"
          class="btn btn-primary btn-sm"
        >
          <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"></path>
          </svg>
          Otimizar Recursos
        </button>
        <button 
          @click="clearCache"
          class="btn btn-outline btn-sm"
        >
          <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
            <path fill-rule="evenodd" d="M10 5a2 2 0 00-2 2v6a2 2 0 002 2h4a2 2 0 002-2V7a2 2 0 00-2-2H10zm3 6a1 1 0 10-2 0v2a1 1 0 102 0v-2z" clip-rule="evenodd"></path>
          </svg>
          Limpar Cache
        </button>
        <button 
          @click="exportMetrics"
          class="btn btn-outline btn-sm"
        >
          <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
          Exportar Métricas
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { SystemMetrics } from '~/types/dashboard'

// Reactive state
const isRefreshing = ref(false)
const timeRange = ref('24h')
const resourceAlerts = ref<any[]>([])

const currentMetrics = ref<SystemMetrics>({
  timestamp: new Date(),
  cpu: 34,
  memory: 67,
  disk: 23,
  network: {
    inbound: 1024 * 1024 * 2.5, // 2.5 MB/s
    outbound: 1024 * 1024 * 1.8  // 1.8 MB/s
  },
  database: {
    connections: 23,
    queryTime: 45
  },
  redis: {
    connections: 12,
    memoryUsage: 34
  }
})

const performanceTrends = ref({
  avgCpu: 32,
  cpuTrend: -2.3,
  avgMemory: 65,
  memoryTrend: 1.8,
  avgResponseTime: 234,
  responseTimeTrend: -12
})

// Mock alerts
const mockAlerts = [
  {
    id: '1',
    level: 'warning',
    title: 'Uso de memória elevado',
    description: 'Uso de memória acima de 65% detectado'
  }
]

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Methods
const refreshMetrics = async () => {
  isRefreshing.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Simulate metric updates
    currentMetrics.value.cpu = Math.max(0, Math.min(100, currentMetrics.value.cpu + Math.random() * 10 - 5))
    currentMetrics.value.memory = Math.max(0, Math.min(100, currentMetrics.value.memory + Math.random() * 6 - 3))
    currentMetrics.value.disk = Math.max(0, Math.min(100, currentMetrics.value.disk + Math.random() * 2 - 1))
    currentMetrics.value.database.queryTime = Math.max(10, currentMetrics.value.database.queryTime + Math.random() * 20 - 10)
    currentMetrics.value.timestamp = new Date()
    
    // Check for alerts
    checkResourceAlerts()
  } finally {
    isRefreshing.value = false
  }
}

const checkResourceAlerts = () => {
  resourceAlerts.value = []
  
  if (currentMetrics.value.cpu > 80) {
    resourceAlerts.value.push({
      id: 'cpu-high',
      level: 'error',
      title: 'CPU crítico',
      description: `Uso de CPU em ${currentMetrics.value.cpu}%`
    })
  } else if (currentMetrics.value.cpu > 65) {
    resourceAlerts.value.push({
      id: 'cpu-warning',
      level: 'warning',
      title: 'CPU elevado',
      description: `Uso de CPU em ${currentMetrics.value.cpu}%`
    })
  }
  
  if (currentMetrics.value.memory > 85) {
    resourceAlerts.value.push({
      id: 'memory-high',
      level: 'error',
      title: 'Memória crítica',
      description: `Uso de memória em ${currentMetrics.value.memory}%`
    })
  } else if (currentMetrics.value.memory > 70) {
    resourceAlerts.value.push({
      id: 'memory-warning',
      level: 'warning',
      title: 'Memória elevada',
      description: `Uso de memória em ${currentMetrics.value.memory}%`
    })
  }
  
  if (currentMetrics.value.database.queryTime > 500) {
    resourceAlerts.value.push({
      id: 'db-slow',
      level: 'warning',
      title: 'Consultas lentas',
      description: `Tempo médio de query: ${currentMetrics.value.database.queryTime}ms`
    })
  }
}

const optimizeResources = () => {
  console.log('Optimizing system resources')
  // In real implementation, trigger resource optimization
}

const clearCache = () => {
  console.log('Clearing system cache')
  // In real implementation, clear Redis cache
}

const exportMetrics = () => {
  console.log('Exporting system metrics')
  // In real implementation, export metrics data
}

const dismissAlert = (alertId: string) => {
  resourceAlerts.value = resourceAlerts.value.filter(alert => alert.id !== alertId)
}

const updateMetrics = () => {
  // Simulate real-time metric updates
  currentMetrics.value.cpu = Math.max(0, Math.min(100, currentMetrics.value.cpu + Math.random() * 4 - 2))
  currentMetrics.value.memory = Math.max(0, Math.min(100, currentMetrics.value.memory + Math.random() * 2 - 1))
  currentMetrics.value.network.inbound = Math.max(0, currentMetrics.value.network.inbound + Math.random() * 1024 * 1024 - 512 * 1024)
  currentMetrics.value.network.outbound = Math.max(0, currentMetrics.value.network.outbound + Math.random() * 1024 * 1024 - 512 * 1024)
  currentMetrics.value.database.connections = Math.max(0, Math.min(100, currentMetrics.value.database.connections + Math.random() * 4 - 2))
  currentMetrics.value.timestamp = new Date()
  
  // Occasionally check for alerts
  if (Math.random() > 0.8) {
    checkResourceAlerts()
  }
}

// Helper functions
const getUsageProgressClass = (usage: number) => {
  if (usage > 85) return 'progress-error'
  if (usage > 70) return 'progress-warning'
  return 'progress-success'
}

const getQueryTimeProgressClass = (time: number) => {
  if (time > 500) return 'progress-error'
  if (time > 200) return 'progress-warning'
  return 'progress-success'
}

const getTrendClass = (trend: number) => {
  if (trend > 0) return 'text-success'
  if (trend < 0) return 'text-error'
  return 'text-base-content/50'
}

const getAlertClass = (level: string) => {
  switch (level) {
    case 'error': return 'alert-error'
    case 'warning': return 'alert-warning'
    case 'info': return 'alert-info'
    default: return 'alert-info'
  }
}

const getAlertIcon = (level: string) => {
  switch (level) {
    case 'error': return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'warning': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z'
    case 'info': return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Lifecycle
onMounted(() => {
  resourceAlerts.value = [...mockAlerts]
  
  // Set up auto-refresh every 5 seconds
  refreshInterval = setInterval(updateMetrics, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>