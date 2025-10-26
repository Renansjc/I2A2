<template>
  <div class="space-y-6">
    <!-- Processing Queue Overview -->
    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">Monitor de Processamento</h2>
          <div class="flex items-center space-x-2">
            <div class="badge badge-info">{{ activeProcessing.length }} ativo(s)</div>
            <button 
              class="btn btn-ghost btn-sm"
              :disabled="isRefreshing"
              @click="refreshAll"
            >
              <svg class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
              </svg>
              Atualizar
            </button>
          </div>
        </div>

        <!-- Queue Statistics -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">Em Processamento</div>
            <div class="stat-value text-info">{{ activeProcessing.length }}</div>
            <div class="stat-desc">Documentos ativos</div>
          </div>
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">Concluídos Hoje</div>
            <div class="stat-value text-success">{{ completedToday }}</div>
            <div class="stat-desc">{{ successRate.toFixed(1) }}% sucesso</div>
          </div>
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">Tempo Médio</div>
            <div class="stat-value text-primary">{{ averageProcessingTime }}</div>
            <div class="stat-desc">Por documento</div>
          </div>
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">Fila de Espera</div>
            <div class="stat-value text-warning">{{ queueLength }}</div>
            <div class="stat-desc">Aguardando</div>
          </div>
        </div>

        <!-- Active Processing Items -->
        <div v-if="activeProcessing.length > 0" class="space-y-4">
          <h3 class="font-semibold">Processamento Ativo</h3>
          
          <div class="space-y-3">
            <div
              v-for="item in activeProcessing"
              :key="item.documentId"
              class="card bg-base-200 shadow-sm"
            >
              <div class="card-body p-4">
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
                      <svg class="w-5 h-5 text-primary animate-spin" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"></path>
                      </svg>
                    </div>
                    <div>
                      <h4 class="font-medium">{{ item.filename }}</h4>
                      <p class="text-sm text-base-content/70">ID: {{ item.documentId.slice(0, 8) }}...</p>
                    </div>
                  </div>
                  
                  <div class="text-right">
                    <div class="badge badge-info">{{ item.currentAgent }}</div>
                    <div class="text-xs text-base-content/50 mt-1">
                      {{ formatElapsedTime(item.startTime) }}
                    </div>
                  </div>
                </div>

                <!-- Progress Bar -->
                <div class="space-y-2">
                  <div class="flex justify-between items-center">
                    <span class="text-sm font-medium">{{ item.currentStep }}</span>
                    <span class="text-sm text-base-content/70">{{ item.progress }}%</span>
                  </div>
                  <progress 
                    class="progress progress-primary w-full" 
                    :value="item.progress" 
                    max="100"
                  ></progress>
                </div>

                <!-- Agent Progress -->
                <div class="mt-3">
                  <div class="flex items-center space-x-2 text-sm">
                    <span class="text-base-content/70">Agentes:</span>
                    <div class="flex space-x-1">
                      <div
                        v-for="agent in item.agents"
                        :key="agent.name"
                        class="w-3 h-3 rounded-full"
                        :class="{
                          'bg-success': agent.status === 'completed',
                          'bg-primary animate-pulse': agent.status === 'running',
                          'bg-error': agent.status === 'failed',
                          'bg-base-300': agent.status === 'pending'
                        }"
                        :title="`${agent.displayName}: ${agent.status}`"
                      ></div>
                    </div>
                  </div>
                </div>

                <!-- Time Estimation -->
                <div class="mt-3 flex justify-between items-center text-sm">
                  <div class="text-base-content/70">
                    <span v-if="item.estimatedTimeRemaining">
                      Tempo estimado: {{ formatDuration(item.estimatedTimeRemaining) }}
                    </span>
                    <span v-else>Calculando estimativa...</span>
                  </div>
                  
                  <div class="flex space-x-2">
                    <button 
                      class="btn btn-ghost btn-xs"
                      @click="viewDetails(item.documentId)"
                    >
                      Detalhes
                    </button>
                    <button 
                      v-if="item.canRetry"
                      class="btn btn-ghost btn-xs text-warning"
                      @click="retryProcessing(item.documentId)"
                    >
                      Tentar Novamente
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-8">
          <div class="w-16 h-16 mx-auto mb-4 text-base-content/30">
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-base-content/70">Nenhum processamento ativo</h3>
          <p class="text-base-content/50">Todos os documentos foram processados com sucesso</p>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h3 class="card-title">Atividade Recente</h3>
          <button 
            class="btn btn-ghost btn-sm"
            @click="clearHistory"
          >
            Limpar Histórico
          </button>
        </div>

        <div class="space-y-2">
          <div
            v-for="activity in recentActivity.slice(0, 10)"
            :key="activity.id"
            class="flex items-center space-x-3 p-3 bg-base-200 rounded"
          >
            <div 
              class="w-3 h-3 rounded-full flex-shrink-0"
              :class="{
                'bg-success': activity.type === 'completed',
                'bg-error': activity.type === 'failed',
                'bg-info': activity.type === 'started',
                'bg-warning': activity.type === 'retry'
              }"
            ></div>
            
            <div class="flex-1 min-w-0">
              <p class="text-sm">{{ activity.message }}</p>
              <p class="text-xs text-base-content/50">{{ formatDate(activity.timestamp) }}</p>
            </div>
            
            <div v-if="activity.documentId" class="flex-shrink-0">
              <button 
                class="btn btn-ghost btn-xs"
                @click="viewDetails(activity.documentId)"
              >
                Ver
              </button>
            </div>
          </div>
        </div>

        <div v-if="recentActivity.length === 0" class="text-center py-4 text-base-content/50">
          Nenhuma atividade recente
        </div>
      </div>
    </div>

    <!-- System Health -->
    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h3 class="card-title mb-4">Saúde do Sistema</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">API Backend</div>
            <div class="stat-value" :class="{
              'text-success': systemHealth.api === 'healthy',
              'text-warning': systemHealth.api === 'degraded',
              'text-error': systemHealth.api === 'down'
            }">
              {{ getHealthStatus(systemHealth.api) }}
            </div>
            <div class="stat-desc">{{ systemHealth.apiResponseTime }}ms</div>
          </div>
          
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">Agentes IA</div>
            <div class="stat-value" :class="{
              'text-success': systemHealth.agents === 'healthy',
              'text-warning': systemHealth.agents === 'degraded',
              'text-error': systemHealth.agents === 'down'
            }">
              {{ systemHealth.activeAgents }}/{{ systemHealth.totalAgents }}
            </div>
            <div class="stat-desc">Agentes ativos</div>
          </div>
          
          <div class="stat bg-base-200 rounded">
            <div class="stat-title">Banco de Dados</div>
            <div class="stat-value" :class="{
              'text-success': systemHealth.database === 'healthy',
              'text-warning': systemHealth.database === 'degraded',
              'text-error': systemHealth.database === 'down'
            }">
              {{ getHealthStatus(systemHealth.database) }}
            </div>
            <div class="stat-desc">{{ systemHealth.dbResponseTime }}ms</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface ProcessingItem {
  documentId: string
  filename: string
  startTime: Date
  progress: number
  currentStep: string
  currentAgent: string
  estimatedTimeRemaining?: number
  canRetry: boolean
  agents: {
    name: string
    displayName: string
    status: 'pending' | 'running' | 'completed' | 'failed'
  }[]
}

interface ActivityItem {
  id: string
  type: 'started' | 'completed' | 'failed' | 'retry'
  message: string
  timestamp: Date
  documentId?: string
}

interface SystemHealth {
  api: 'healthy' | 'degraded' | 'down'
  agents: 'healthy' | 'degraded' | 'down'
  database: 'healthy' | 'degraded' | 'down'
  apiResponseTime: number
  dbResponseTime: number
  activeAgents: number
  totalAgents: number
}

// Reactive state
const activeProcessing = ref<ProcessingItem[]>([])
const recentActivity = ref<ActivityItem[]>([])
const isRefreshing = ref(false)
const systemHealth = ref<SystemHealth>({
  api: 'healthy',
  agents: 'healthy',
  database: 'healthy',
  apiResponseTime: 120,
  dbResponseTime: 45,
  activeAgents: 8,
  totalAgents: 8
})

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Computed properties
const completedToday = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  return recentActivity.value.filter(activity => 
    activity.type === 'completed' && activity.timestamp >= today
  ).length
})

const successRate = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const todayActivities = recentActivity.value.filter(activity => 
    (activity.type === 'completed' || activity.type === 'failed') && 
    activity.timestamp >= today
  )
  
  if (todayActivities.length === 0) return 100
  
  const successful = todayActivities.filter(activity => activity.type === 'completed').length
  return (successful / todayActivities.length) * 100
})

const averageProcessingTime = computed(() => {
  // Mock calculation - in real implementation, this would come from API
  return '2.3min'
})

const queueLength = computed(() => {
  // Mock value - in real implementation, this would come from API
  return 0
})

// Methods
const refreshAll = async () => {
  isRefreshing.value = true
  
  try {
    await Promise.all([
      loadActiveProcessing(),
      loadRecentActivity(),
      checkSystemHealth()
    ])
  } catch (error) {
    console.error('Error refreshing data:', error)
  } finally {
    isRefreshing.value = false
  }
}

const loadActiveProcessing = async () => {
  try {
    // Mock data - in real implementation, this would fetch from API
    activeProcessing.value = [
      {
        documentId: 'doc-123-456',
        filename: 'nfe_exemplo_001.xml',
        startTime: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        progress: 67,
        currentStep: 'Processamento de categorização IA',
        currentAgent: 'AI Categorization Agent',
        estimatedTimeRemaining: 45000, // 45 seconds
        canRetry: false,
        agents: [
          { name: 'xml_processing_agent', displayName: 'XML Processing', status: 'completed' },
          { name: 'ai_categorization_agent', displayName: 'AI Categorization', status: 'running' },
          { name: 'sql_agent', displayName: 'SQL Agent', status: 'pending' },
          { name: 'report_agent', displayName: 'Report Agent', status: 'pending' }
        ]
      }
    ]
  } catch (error) {
    console.error('Error loading active processing:', error)
  }
}

const loadRecentActivity = async () => {
  try {
    // Mock data - in real implementation, this would fetch from API
    const mockActivities: ActivityItem[] = [
      {
        id: '1',
        type: 'completed',
        message: 'Documento nfe_exemplo_002.xml processado com sucesso',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        documentId: 'doc-789-012'
      },
      {
        id: '2',
        type: 'started',
        message: 'Iniciado processamento de nfe_exemplo_001.xml',
        timestamp: new Date(Date.now() - 2 * 60 * 1000),
        documentId: 'doc-123-456'
      },
      {
        id: '3',
        type: 'failed',
        message: 'Falha no processamento de nfse_erro.xml - XML inválido',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        documentId: 'doc-345-678'
      }
    ]
    
    recentActivity.value = mockActivities
  } catch (error) {
    console.error('Error loading recent activity:', error)
  }
}

const checkSystemHealth = async () => {
  try {
    // Mock health check - in real implementation, this would call health endpoints
    const startTime = Date.now()
    
    // Simulate API health check
    const apiHealthy = Math.random() > 0.1 // 90% chance of being healthy
    const apiResponseTime = Math.floor(Math.random() * 200) + 50
    
    systemHealth.value = {
      api: apiHealthy ? 'healthy' : 'degraded',
      agents: 'healthy',
      database: 'healthy',
      apiResponseTime,
      dbResponseTime: Math.floor(Math.random() * 100) + 20,
      activeAgents: 8,
      totalAgents: 8
    }
  } catch (error) {
    console.error('Error checking system health:', error)
    systemHealth.value.api = 'down'
  }
}

const viewDetails = (documentId: string) => {
  navigateTo(`/documents/${documentId}`)
}

const retryProcessing = async (documentId: string) => {
  try {
    // Mock retry - in real implementation, this would call retry API
    addActivity({
      type: 'retry',
      message: `Tentativa de reprocessamento iniciada para documento ${documentId.slice(0, 8)}...`,
      documentId
    })
  } catch (error) {
    console.error('Error retrying processing:', error)
  }
}

const clearHistory = () => {
  recentActivity.value = []
}

const addActivity = (activity: Omit<ActivityItem, 'id' | 'timestamp'>) => {
  recentActivity.value.unshift({
    ...activity,
    id: Date.now().toString(),
    timestamp: new Date()
  })
  
  // Keep only last 50 activities
  if (recentActivity.value.length > 50) {
    recentActivity.value = recentActivity.value.slice(0, 50)
  }
}

// Utility functions
const formatElapsedTime = (startTime: Date): string => {
  const elapsed = Date.now() - startTime.getTime()
  const minutes = Math.floor(elapsed / 60000)
  const seconds = Math.floor((elapsed % 60000) / 1000)
  
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}

const formatDuration = (milliseconds: number): string => {
  const minutes = Math.floor(milliseconds / 60000)
  const seconds = Math.floor((milliseconds % 60000) / 1000)
  
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}

const formatDate = (date: Date): string => {
  return date.toLocaleString('pt-BR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getHealthStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'healthy': 'Saudável',
    'degraded': 'Degradado',
    'down': 'Inativo'
  }
  return statusMap[status] || status
}

// Auto-refresh
let refreshInterval: NodeJS.Timeout

onMounted(() => {
  refreshAll()
  
  // Auto-refresh every 3 seconds
  refreshInterval = setInterval(() => {
    if (!isRefreshing.value) {
      refreshAll()
    }
  }, 3000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>