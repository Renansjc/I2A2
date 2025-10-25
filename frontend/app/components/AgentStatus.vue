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
          <div class="badge badge-success badge-sm">{{ onlineAgents.length }} Online</div>
          <div class="badge badge-error badge-sm">{{ offlineAgents.length }} Offline</div>
        </div>
      </div>

      <!-- Agent Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div
          v-for="agent in allAgents"
          :key="agent.id"
          class="bg-base-100 rounded-lg p-3 border-l-4"
          :class="getAgentBorderClass(agent.status)"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div 
                class="w-3 h-3 rounded-full"
                :class="getStatusIndicatorClass(agent.status)"
              ></div>
              <h4 class="font-semibold text-sm">{{ agent.name }}</h4>
            </div>
            <div class="badge badge-xs" :class="getStatusBadgeClass(agent.status)">
              {{ getStatusText(agent.status) }}
            </div>
          </div>

          <p class="text-xs text-base-content/70 mb-2">{{ agent.description }}</p>

          <!-- Performance Metrics -->
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span class="text-base-content/50">CPU:</span>
              <span class="font-medium ml-1">{{ agent.metrics.cpu.toFixed(1) }}%</span>
            </div>
            <div>
              <span class="text-base-content/50">Memória:</span>
              <span class="font-medium ml-1">{{ agent.metrics.memory.toFixed(1) }}%</span>
            </div>
            <div>
              <span class="text-base-content/50">Tarefas:</span>
              <span class="font-medium ml-1">{{ agent.metrics.activeTasks }}</span>
            </div>
            <div>
              <span class="text-base-content/50">Uptime:</span>
              <span class="font-medium ml-1">{{ agent.metrics.uptime }}</span>
            </div>
          </div>

          <!-- Last Activity -->
          <div class="mt-2 pt-2 border-t border-base-200">
            <div class="text-xs text-base-content/50">
              Última atividade: {{ formatTime(agent.lastActivity) }}
            </div>
          </div>
        </div>
      </div>

      <!-- System Health Summary -->
      <div class="mt-6 p-4 bg-base-100 rounded-lg">
        <h4 class="font-semibold mb-3 text-sm">Resumo do Sistema</h4>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div class="text-2xl font-bold text-success">{{ systemHealth.overallHealth }}%</div>
            <div class="text-xs text-base-content/50">Saúde Geral</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-primary">{{ systemHealth.totalRequests }}</div>
            <div class="text-xs text-base-content/50">Requisições/h</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-secondary">{{ parseInt(systemHealth.avgResponseTime) }}ms</div>
            <div class="text-xs text-base-content/50">Tempo Médio</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-accent">{{ systemHealth.successRate }}%</div>
            <div class="text-xs text-base-content/50">Taxa de Sucesso</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Agent, AgentMetrics, SystemHealth } from '~/types/dashboard'

// Reactive state
const agents = ref<Agent[]>([])
const systemHealth = ref<SystemHealth>({
  overallHealth: 95,
  totalRequests: 1247,
  avgResponseTime: 245,
  successRate: 98.5
})

let updateInterval: NodeJS.Timeout | null = null

// Mock agents data
const mockAgents: Agent[] = [
  {
    id: 'master',
    name: 'Master Agent',
    description: 'Orquestrador central com compreensão de linguagem natural',
    status: 'online',
    metrics: { cpu: 15, memory: 32, activeTasks: 3, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    id: 'xml',
    name: 'XML Processing Agent',
    description: 'Processamento de documentos NF-e/NFS-e com análise semântica',
    status: 'busy',
    metrics: { cpu: 45, memory: 68, activeTasks: 8, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 30 * 1000)
  },
  {
    id: 'categorization',
    name: 'AI Categorization Agent',
    description: 'Categorização inteligente com compreensão contextual',
    status: 'online',
    metrics: { cpu: 22, memory: 41, activeTasks: 2, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 5 * 60 * 1000)
  },
  {
    id: 'sql',
    name: 'SQL Agent',
    description: 'Tradução de linguagem natural para consultas SQL',
    status: 'online',
    metrics: { cpu: 8, memory: 25, activeTasks: 1, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 1 * 60 * 1000)
  },
  {
    id: 'report',
    name: 'Report Agent',
    description: 'Geração de relatórios inteligentes com insights executivos',
    status: 'busy',
    metrics: { cpu: 35, memory: 55, activeTasks: 4, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 45 * 1000)
  },
  {
    id: 'scheduler',
    name: 'Scheduler Agent',
    description: 'Gerenciamento automatizado de tarefas e agendamentos',
    status: 'online',
    metrics: { cpu: 5, memory: 18, activeTasks: 0, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 10 * 60 * 1000)
  },
  {
    id: 'datalake',
    name: 'Data Lake Agent',
    description: 'Armazenamento e otimização de dados com detecção de padrões',
    status: 'online',
    metrics: { cpu: 12, memory: 38, activeTasks: 2, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 3 * 60 * 1000)
  },
  {
    id: 'monitoring',
    name: 'Monitoring Agent',
    description: 'Monitoramento de saúde do sistema com análise preditiva',
    status: 'online',
    metrics: { cpu: 18, memory: 29, activeTasks: 1, uptime: '2d 14h' },
    lastActivity: new Date(Date.now() - 1 * 60 * 1000)
  }
]

// Computed properties
const allAgents = computed(() => agents.value)
const onlineAgents = computed(() => agents.value.filter(agent => agent.status === 'online' || agent.status === 'busy'))
const offlineAgents = computed(() => agents.value.filter(agent => agent.status === 'offline' || agent.status === 'error'))

// Initialize data
onMounted(() => {
  agents.value = [...mockAgents]
  
  // Simulate real-time updates
  updateInterval = setInterval(() => {
    agents.value.forEach(agent => {
      // Simulate metric changes
      agent.metrics.cpu = Math.max(0, Math.min(100, agent.metrics.cpu + (Math.random() - 0.5) * 10))
      agent.metrics.memory = Math.max(0, Math.min(100, agent.metrics.memory + (Math.random() - 0.5) * 5))
      
      // Occasionally update last activity for busy agents
      if (agent.status === 'busy' && Math.random() < 0.3) {
        agent.lastActivity = new Date()
      }
    })
    
    // Update system health
    systemHealth.value.totalRequests += Math.floor(Math.random() * 50)
    systemHealth.value.avgResponseTime = Math.max(100, Math.min(500, systemHealth.value.avgResponseTime + (Math.random() - 0.5) * 50))
  }, 5000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})

// Helper functions
const getAgentBorderClass = (status: string) => {
  switch (status) {
    case 'online': return 'border-l-success'
    case 'busy': return 'border-l-warning'
    case 'offline': return 'border-l-base-300'
    case 'error': return 'border-l-error'
    default: return 'border-l-base-300'
  }
}

const getStatusIndicatorClass = (status: string) => {
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

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Agora mesmo'
  if (minutes < 60) return `há ${minutes}m`
  if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`
  return timestamp.toLocaleDateString()
}
</script>