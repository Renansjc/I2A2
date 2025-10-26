<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Status dos Agentes
        </h3>
        <div class="flex items-center gap-2">
          <div class="badge badge-success">{{ onlineAgents }} Online</div>
          <div class="badge badge-error">{{ offlineAgents }} Offline</div>
        </div>
      </div>

      <!-- Agent Grid -->
      <div class="space-y-3">
        <div
          v-for="agent in agents"
          :key="agent.id"
          class="bg-base-100 rounded-lg p-4"
          :class="{ 'ring-2 ring-primary': selectedAgentId === agent.id }"
          @click="selectAgent(agent)"
        >
          <!-- Agent Header -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <div 
                class="w-4 h-4 rounded-full"
                :class="getStatusColor(agent.status)"
              ></div>
              <div>
                <h4 class="font-semibold">{{ agent.name }}</h4>
                <p class="text-sm text-base-content/50">{{ agent.type }}</p>
              </div>
            </div>
            <div class="text-right">
              <div 
                class="badge badge-sm"
                :class="getStatusBadgeClass(agent.status)"
              >
                {{ getStatusText(agent.status) }}
              </div>
              <div class="text-xs text-base-content/50 mt-1">
                Uptime: {{ agent.performance.uptime }}
              </div>
            </div>
          </div>

          <!-- Current Task -->
          <div v-if="agent.currentTask" class="mb-3 p-2 bg-base-200 rounded">
            <div class="text-xs text-base-content/50 mb-1">Tarefa Atual:</div>
            <div class="text-sm font-medium">{{ agent.currentTask }}</div>
          </div>

          <!-- Agent Metrics -->
          <div class="grid grid-cols-3 gap-3 text-center text-sm">
            <div>
              <div class="text-base-content/50">Fila</div>
              <div class="font-bold">{{ agent.queueSize }}</div>
            </div>
            <div>
              <div class="text-base-content/50">CPU</div>
              <div class="font-bold">{{ agent.healthCheck.cpuUsage }}%</div>
            </div>
            <div>
              <div class="text-base-content/50">Memória</div>
              <div class="font-bold">{{ agent.healthCheck.memoryUsage }}%</div>
            </div>
          </div>

          <!-- Performance Indicators -->
          <div class="mt-3 space-y-2">
            <div class="flex justify-between text-xs">
              <span>Performance</span>
              <span>{{ agent.performance.performance }}%</span>
            </div>
            <progress 
              class="progress progress-xs w-full"
              :class="getPerformanceClass(agent.performance.performance)"
              :value="agent.performance.performance" 
              max="100"
            ></progress>
          </div>

          <!-- Health Check -->
          <div class="mt-3 pt-3 border-t border-base-200">
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-2">
                <div 
                  class="w-2 h-2 rounded-full"
                  :class="getHealthColor(agent.healthCheck.responseTime)"
                ></div>
                <span>Última verificação: {{ formatTime(agent.healthCheck.lastCheck) }}</span>
              </div>
              <span>{{ agent.healthCheck.responseTime }}ms</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent Actions -->
      <div v-if="selectedAgent" class="mt-4 pt-4 border-t border-base-300">
        <h4 class="font-semibold mb-2">Ações do Agente</h4>
        <div class="flex gap-2">
          <button 
            v-if="selectedAgent.status === 'offline'"
            @click="startAgent"
            class="btn btn-success btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path>
            </svg>
            Iniciar
          </button>
          <button 
            v-if="selectedAgent.status === 'online' || selectedAgent.status === 'busy'"
            @click="stopAgent"
            class="btn btn-error btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"></path>
            </svg>
            Parar
          </button>
          <button 
            @click="restartAgent"
            class="btn btn-warning btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
            Reiniciar
          </button>
          <button 
            @click="clearQueue"
            class="btn btn-ghost btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
              <path fill-rule="evenodd" d="M10 5a2 2 0 00-2 2v6a2 2 0 002 2h4a2 2 0 002-2V7a2 2 0 00-2-2H10zm3 6a1 1 0 10-2 0v2a1 1 0 102 0v-2z" clip-rule="evenodd"></path>
            </svg>
            Limpar Fila
          </button>
        </div>
      </div>

      <!-- System Overview -->
      <div class="mt-6 pt-4 border-t border-base-300">
        <h4 class="font-semibold mb-3">Visão Geral do Sistema</h4>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div class="text-2xl font-bold text-success">{{ systemOverview.totalTasks }}</div>
            <div class="text-xs text-base-content/50">Tarefas Ativas</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-primary">{{ systemOverview.avgResponseTime }}ms</div>
            <div class="text-xs text-base-content/50">Tempo Médio</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-warning">{{ systemOverview.queueSize }}</div>
            <div class="text-xs text-base-content/50">Fila Total</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-info">{{ systemOverview.systemLoad }}%</div>
            <div class="text-xs text-base-content/50">Carga do Sistema</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { AgentStatus } from '~/types/dashboard'

// Props and emits
const emit = defineEmits<{
  selectAgent: [agent: AgentStatus]
}>()

// Reactive state
const selectedAgentId = ref<string | null>(null)
const agents = ref<AgentStatus[]>([])

// Mock agents data
const mockAgents: AgentStatus[] = [
  {
    id: 'master',
    name: 'Master Agent',
    type: 'Orquestrador Central',
    status: 'online',
    currentTask: 'Interpretando consulta executiva sobre fornecedores',
    queueSize: 3,
    performance: {
      id: 'master',
      name: 'Master Agent',
      type: 'Orquestrador',
      performance: 96,
      tasksCompleted: 234,
      totalTasks: 245,
      avgTime: 3.2,
      successRate: 98.5,
      uptime: '99.8%',
      lastActivity: new Date(Date.now() - 2 * 60 * 1000),
      lastTask: 'Interpretação de consulta executiva'
    },
    healthCheck: {
      lastCheck: new Date(Date.now() - 30 * 1000),
      responseTime: 45,
      memoryUsage: 23,
      cpuUsage: 12
    }
  },
  {
    id: 'xml',
    name: 'XML Processing Agent',
    type: 'Processamento de Documentos',
    status: 'busy',
    currentTask: 'Processando lote de 45 documentos NF-e',
    queueSize: 12,
    performance: {
      id: 'xml',
      name: 'XML Processing Agent',
      type: 'Processamento',
      performance: 89,
      tasksCompleted: 456,
      totalTasks: 478,
      avgTime: 12.8,
      successRate: 94.2,
      uptime: '98.9%',
      lastActivity: new Date(Date.now() - 30 * 1000),
      lastTask: 'Processamento de lote NF-e'
    },
    healthCheck: {
      lastCheck: new Date(Date.now() - 15 * 1000),
      responseTime: 120,
      memoryUsage: 67,
      cpuUsage: 45
    }
  },
  {
    id: 'categorization',
    name: 'AI Categorization Agent',
    type: 'Categorização Inteligente',
    status: 'online',
    currentTask: undefined,
    queueSize: 5,
    performance: {
      id: 'categorization',
      name: 'AI Categorization Agent',
      type: 'Categorização',
      performance: 92,
      tasksCompleted: 789,
      totalTasks: 823,
      avgTime: 6.4,
      successRate: 96.1,
      uptime: '99.2%',
      lastActivity: new Date(Date.now() - 5 * 60 * 1000),
      lastTask: 'Categorização de produtos novos'
    },
    healthCheck: {
      lastCheck: new Date(Date.now() - 45 * 1000),
      responseTime: 78,
      memoryUsage: 34,
      cpuUsage: 18
    }
  },
  {
    id: 'sql',
    name: 'SQL Agent',
    type: 'Consultas e Análises',
    status: 'online',
    currentTask: 'Executando análise de fornecedores Q4',
    queueSize: 2,
    performance: {
      id: 'sql',
      name: 'SQL Agent',
      type: 'Consultas',
      performance: 94,
      tasksCompleted: 167,
      totalTasks: 178,
      avgTime: 4.9,
      successRate: 97.8,
      uptime: '99.5%',
      lastActivity: new Date(Date.now() - 1 * 60 * 1000),
      lastTask: 'Análise de fornecedores Q4'
    },
    healthCheck: {
      lastCheck: new Date(Date.now() - 20 * 1000),
      responseTime: 56,
      memoryUsage: 28,
      cpuUsage: 15
    }
  },
  {
    id: 'report',
    name: 'Report Agent',
    type: 'Geração de Relatórios',
    status: 'busy',
    currentTask: 'Gerando relatório executivo mensal',
    queueSize: 1,
    performance: {
      id: 'report',
      name: 'Report Agent',
      type: 'Relatórios',
      performance: 87,
      tasksCompleted: 89,
      totalTasks: 95,
      avgTime: 18.3,
      successRate: 92.6,
      uptime: '98.1%',
      lastActivity: new Date(Date.now() - 45 * 1000),
      lastTask: 'Geração de relatório executivo'
    },
    healthCheck: {
      lastCheck: new Date(Date.now() - 10 * 1000),
      responseTime: 234,
      memoryUsage: 56,
      cpuUsage: 32
    }
  },
  {
    id: 'monitoring',
    name: 'Monitoring Agent',
    type: 'Monitoramento do Sistema',
    status: 'error',
    currentTask: undefined,
    queueSize: 0,
    performance: {
      id: 'monitoring',
      name: 'Monitoring Agent',
      type: 'Monitoramento',
      performance: 45,
      tasksCompleted: 23,
      totalTasks: 45,
      avgTime: 8.7,
      successRate: 78.2,
      uptime: '87.3%',
      lastActivity: new Date(Date.now() - 15 * 60 * 1000),
      lastTask: 'Verificação de saúde do sistema'
    },
    healthCheck: {
      lastCheck: new Date(Date.now() - 5 * 60 * 1000),
      responseTime: 0,
      memoryUsage: 0,
      cpuUsage: 0
    }
  }
]

// Computed properties
const selectedAgent = computed(() => {
  return agents.value.find(agent => agent.id === selectedAgentId.value) || null
})

const onlineAgents = computed(() => {
  return agents.value.filter(agent => agent.status === 'online' || agent.status === 'busy').length
})

const offlineAgents = computed(() => {
  return agents.value.filter(agent => agent.status === 'offline' || agent.status === 'error').length
})

const systemOverview = computed(() => {
  const totalTasks = agents.value.reduce((sum, agent) => sum + agent.queueSize, 0)
  const avgResponseTime = Math.round(
    agents.value
      .filter(agent => agent.healthCheck.responseTime > 0)
      .reduce((sum, agent) => sum + agent.healthCheck.responseTime, 0) / 
    Math.max(1, agents.value.filter(agent => agent.healthCheck.responseTime > 0).length)
  )
  const queueSize = totalTasks
  const systemLoad = Math.round(
    agents.value.reduce((sum, agent) => sum + agent.healthCheck.cpuUsage, 0) / agents.value.length
  )

  return {
    totalTasks,
    avgResponseTime,
    queueSize,
    systemLoad
  }
})

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Methods
const selectAgent = (agent: AgentStatus) => {
  selectedAgentId.value = agent.id
  emit('selectAgent', agent)
}

const startAgent = () => {
  if (selectedAgent.value) {
    console.log('Starting agent:', selectedAgent.value.id)
    selectedAgent.value.status = 'online'
  }
}

const stopAgent = () => {
  if (selectedAgent.value) {
    console.log('Stopping agent:', selectedAgent.value.id)
    selectedAgent.value.status = 'offline'
  }
}

const restartAgent = () => {
  if (selectedAgent.value) {
    console.log('Restarting agent:', selectedAgent.value.id)
    selectedAgent.value.status = 'online'
    selectedAgent.value.healthCheck.lastCheck = new Date()
  }
}

const clearQueue = () => {
  if (selectedAgent.value) {
    console.log('Clearing queue for agent:', selectedAgent.value.id)
    selectedAgent.value.queueSize = 0
  }
}

const refreshAgentStatus = () => {
  // In real implementation, fetch from API
  // For now, simulate status updates
  agents.value.forEach(agent => {
    if (agent.status === 'online' || agent.status === 'busy') {
      agent.healthCheck.lastCheck = new Date()
      agent.healthCheck.responseTime = Math.floor(Math.random() * 200) + 20
      agent.healthCheck.cpuUsage = Math.floor(Math.random() * 50) + 10
      agent.healthCheck.memoryUsage = Math.floor(Math.random() * 60) + 20
    }
  })
}

// Helper functions
const getStatusColor = (status: string) => {
  switch (status) {
    case 'online': return 'bg-success'
    case 'busy': return 'bg-warning animate-pulse'
    case 'offline': return 'bg-base-300'
    case 'error': return 'bg-error'
    default: return 'bg-base-300'
  }
}

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'online': return 'badge-success'
    case 'busy': return 'badge-warning'
    case 'offline': return 'badge-ghost'
    case 'error': return 'badge-error'
    default: return 'badge-ghost'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'online': return 'Online'
    case 'busy': return 'Ocupado'
    case 'offline': return 'Offline'
    case 'error': return 'Erro'
    default: return 'Desconhecido'
  }
}

const getPerformanceClass = (performance: number) => {
  if (performance >= 90) return 'progress-success'
  if (performance >= 70) return 'progress-warning'
  return 'progress-error'
}

const getHealthColor = (responseTime: number) => {
  if (responseTime === 0) return 'bg-error'
  if (responseTime < 100) return 'bg-success'
  if (responseTime < 200) return 'bg-warning'
  return 'bg-error'
}

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const seconds = Math.floor(diff / 1000)
  
  if (seconds < 60) return `${seconds}s atrás`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m atrás`
  const hours = Math.floor(minutes / 60)
  return `${hours}h atrás`
}

// Lifecycle
onMounted(() => {
  agents.value = [...mockAgents]
  
  // Set up auto-refresh every 10 seconds
  refreshInterval = setInterval(refreshAgentStatus, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>