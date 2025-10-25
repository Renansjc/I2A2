<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
          </svg>
          Métricas de Performance
        </h3>
        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-ghost btn-sm">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
            </svg>
          </label>
          <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
            <li><a @click="exportMetrics">Exportar Métricas</a></li>
            <li><a @click="resetMetrics">Resetar Métricas</a></li>
            <li><a @click="configureAlerts">Configurar Alertas</a></li>
          </ul>
        </div>
      </div>

      <!-- Time Range Selector -->
      <div class="mb-4">
        <div class="tabs tabs-boxed tabs-xs">
          <button 
            v-for="range in timeRanges"
            :key="range.value"
            @click="selectedTimeRange = range.value"
            class="tab"
            :class="{ 'tab-active': selectedTimeRange === range.value }"
          >
            {{ range.label }}
          </button>
        </div>
      </div>

      <!-- Performance Overview -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-primary">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Taxa de Sucesso</div>
          <div class="stat-value text-lg">{{ overallMetrics.successRate }}%</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(overallMetrics.successRateTrend)">
              {{ overallMetrics.successRateTrend > 0 ? '+' : '' }}{{ overallMetrics.successRateTrend }}%
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
          <div class="stat-value text-lg">{{ overallMetrics.avgResponseTime }}s</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(-overallMetrics.responseTimeTrend)">
              {{ overallMetrics.responseTimeTrend > 0 ? '+' : '' }}{{ overallMetrics.responseTimeTrend }}s
            </span>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-accent">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Total de Tarefas</div>
          <div class="stat-value text-lg">{{ overallMetrics.totalTasks }}</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(overallMetrics.tasksTrend)">
              {{ overallMetrics.tasksTrend > 0 ? '+' : '' }}{{ overallMetrics.tasksTrend }}
            </span>
          </div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-3">
          <div class="stat-figure text-warning">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title text-xs">Taxa de Erro</div>
          <div class="stat-value text-lg">{{ overallMetrics.errorRate }}%</div>
          <div class="stat-desc text-xs">
            <span :class="getTrendClass(-overallMetrics.errorRateTrend)">
              {{ overallMetrics.errorRateTrend > 0 ? '+' : '' }}{{ overallMetrics.errorRateTrend }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Agent Performance Breakdown -->
      <div class="space-y-3">
        <h4 class="font-semibold">Performance por Agente</h4>
        <div class="space-y-2">
          <div
            v-for="agent in agentMetrics"
            :key="agent.id"
            class="bg-base-100 rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getPerformanceColor(agent.performance)"
                ></div>
                <h5 class="font-medium">{{ agent.name }}</h5>
                <div class="badge badge-outline badge-sm">{{ agent.type }}</div>
              </div>
              <div class="text-right">
                <div class="text-sm font-bold">{{ agent.performance }}%</div>
                <div class="text-xs text-base-content/50">Performance</div>
              </div>
            </div>

            <!-- Agent Metrics Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <div class="text-base-content/50">Tarefas</div>
                <div class="font-medium">{{ agent.tasksCompleted }}/{{ agent.totalTasks }}</div>
              </div>
              <div>
                <div class="text-base-content/50">Tempo Médio</div>
                <div class="font-medium">{{ agent.avgTime }}s</div>
              </div>
              <div>
                <div class="text-base-content/50">Sucesso</div>
                <div class="font-medium">{{ agent.successRate }}%</div>
              </div>
              <div>
                <div class="text-base-content/50">Uptime</div>
                <div class="font-medium">{{ agent.uptime }}</div>
              </div>
            </div>

            <!-- Performance Trend -->
            <div class="mt-3">
              <div class="flex justify-between text-xs mb-1">
                <span>Tendência de Performance</span>
                <span>{{ agent.performance }}%</span>
              </div>
              <progress 
                class="progress progress-xs w-full"
                :class="getPerformanceProgressClass(agent.performance)"
                :value="agent.performance" 
                max="100"
              ></progress>
            </div>

            <!-- Recent Activity -->
            <div class="mt-3 pt-3 border-t border-base-200">
              <div class="text-xs text-base-content/50">
                Última atividade: {{ formatTime(agent.lastActivity) }}
              </div>
              <div class="text-xs text-base-content/70 mt-1">
                {{ agent.lastTask }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Alerts -->
      <div v-if="performanceAlerts.length > 0" class="mt-6">
        <h4 class="font-semibold mb-3">Alertas de Performance</h4>
        <div class="space-y-2">
          <div
            v-for="alert in performanceAlerts"
            :key="alert.id"
            class="alert shadow-lg"
            :class="getAlertClass(alert.severity)"
          >
            <div>
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path :d="getAlertIcon(alert.severity)"></path>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AgentPerformanceMetrics, PerformanceAlert } from '~/types/dashboard'

// Reactive state
const selectedTimeRange = ref('24h')
const performanceAlerts = ref<PerformanceAlert[]>([])

// Time range options
const timeRanges = [
  { value: '1h', label: '1h' },
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' }
]

// Mock data
const overallMetrics = ref({
  successRate: 94.2,
  successRateTrend: 2.1,
  avgResponseTime: 8.7,
  responseTimeTrend: -1.2,
  totalTasks: 1247,
  tasksTrend: 156,
  errorRate: 2.3,
  errorRateTrend: -0.8
})

const agentMetrics = ref<AgentPerformanceMetrics[]>([
  {
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
  {
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
  {
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
  {
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
  {
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
  }
])

// Mock performance alerts
const mockAlerts: PerformanceAlert[] = [
  {
    id: '1',
    severity: 'warning',
    title: 'Performance do Report Agent abaixo do esperado',
    description: 'Tempo médio de resposta 23% acima da média nas últimas 2 horas',
    timestamp: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: '2',
    severity: 'info',
    title: 'Pico de atividade detectado',
    description: 'XML Processing Agent processou 45% mais documentos que o usual',
    timestamp: new Date(Date.now() - 30 * 60 * 1000)
  }
]

performanceAlerts.value = [...mockAlerts]

// Methods
const exportMetrics = () => {
  console.log('Exporting performance metrics')
}

const resetMetrics = () => {
  console.log('Resetting performance metrics')
}

const configureAlerts = () => {
  console.log('Configuring performance alerts')
}

const dismissAlert = (alertId: string) => {
  performanceAlerts.value = performanceAlerts.value.filter(alert => alert.id !== alertId)
}

// Helper functions
const getTrendClass = (trend: number) => {
  if (trend > 0) return 'text-success'
  if (trend < 0) return 'text-error'
  return 'text-base-content/50'
}

const getPerformanceColor = (performance: number) => {
  if (performance >= 95) return 'bg-success'
  if (performance >= 85) return 'bg-warning'
  return 'bg-error'
}

const getPerformanceProgressClass = (performance: number) => {
  if (performance >= 95) return 'progress-success'
  if (performance >= 85) return 'progress-warning'
  return 'progress-error'
}

const getAlertClass = (severity: string) => {
  switch (severity) {
    case 'error': return 'alert-error'
    case 'warning': return 'alert-warning'
    case 'info': return 'alert-info'
    default: return 'alert-info'
  }
}

const getAlertIcon = (severity: string) => {
  switch (severity) {
    case 'error': return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'warning': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z'
    case 'info': return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
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
</script>