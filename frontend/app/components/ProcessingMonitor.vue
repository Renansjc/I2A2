<template>
  <div class="space-y-6">
    <!-- Simplified Processing Monitor -->
    <div class="card bg-gradient-to-r from-primary/5 to-secondary/5 shadow-lg border border-primary/20">
      <div class="card-body">
        <div class="flex justify-between items-center mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z" />
              </svg>
            </div>
            <div>
              <h2 class="text-xl font-bold">Monitor de Processamento</h2>
              <p class="text-sm text-base-content/70">Acompanhe o progresso dos seus documentos em tempo real</p>
            </div>
          </div>
          
          <div class="flex items-center space-x-3">
            <div class="badge badge-primary badge-lg">
              {{ activeProcessing.length }} processando
            </div>
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

        <!-- Active Processing Items -->
        <div v-if="activeProcessing.length > 0" class="space-y-4">
          <div
            v-for="item in activeProcessing"
            :key="item.documentId"
            class="card bg-base-100 shadow-md border border-base-300"
          >
            <div class="card-body p-6">
              <!-- Header -->
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-4">
                  <div class="w-12 h-12 bg-primary/20 rounded-xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-primary animate-pulse" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                    </svg>
                  </div>
                  <div>
                    <h4 class="font-semibold text-lg">{{ item.filename }}</h4>
                    <p class="text-sm text-base-content/70">ID: {{ item.documentId.slice(0, 8) }}... • {{ formatElapsedTime(item.startTime) }}</p>
                  </div>
                </div>
                
                <div class="text-right">
                  <div class="badge badge-info badge-lg">{{ item.currentAgent }}</div>
                  <div class="text-xs text-base-content/60 mt-1">
                    {{ item.progress }}% concluído
                  </div>
                </div>
              </div>

              <!-- Progress Section -->
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-sm font-medium">{{ item.currentStep }}</span>
                  <span class="text-sm text-base-content/70">{{ item.progress }}%</span>
                </div>
                
                <div class="w-full bg-base-300 rounded-full h-3">
                  <div 
                    class="bg-gradient-to-r from-primary to-secondary h-3 rounded-full transition-all duration-500 ease-out"
                    :style="`width: ${item.progress}%`"
                  ></div>
                </div>
              </div>

              <!-- Agents Progress -->
              <div class="mt-4">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium text-base-content/80">Progresso dos Agentes IA:</span>
                  <span class="text-xs text-base-content/60">{{ getCompletedAgents(item.agents) }}/{{ item.agents.length }} concluídos</span>
                </div>
                
                <div class="flex space-x-2">
                  <div
                    v-for="agent in item.agents"
                    :key="agent.name"
                    class="flex-1 h-2 rounded-full transition-all duration-300"
                    :class="{
                      'bg-success': agent.status === 'completed',
                      'bg-primary animate-pulse': agent.status === 'running',
                      'bg-error': agent.status === 'failed',
                      'bg-base-300': agent.status === 'pending'
                    }"
                    :title="agent.displayName"
                  ></div>
                </div>
                
                <div class="flex justify-between text-xs text-base-content/60 mt-1">
                  <span v-for="agent in item.agents" :key="agent.name" class="flex-1 text-center">
                    {{ agent.displayName.split(' ')[0] }}
                  </span>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex justify-between items-center mt-4 pt-4 border-t border-base-300">
                <div class="text-sm text-base-content/70">
                  <span v-if="item.estimatedTimeRemaining">
                    ⏱️ Restam {{ formatDuration(item.estimatedTimeRemaining) }}
                  </span>
                  <span v-else>⏱️ Calculando tempo restante...</span>
                </div>
                
                <button 
                  class="btn btn-ghost btn-sm"
                  @click="viewDetails(item.documentId)"
                >
                  <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                    <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                  </svg>
                  Ver Detalhes
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <div class="w-20 h-20 mx-auto mb-4 text-success/60">
            <svg fill="currentColor" viewBox="0 0 24 24" class="w-full h-full">
              <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,16.5L6.5,12L7.91,10.59L11,13.67L16.59,8.09L18,9.5L11,16.5Z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-base-content/80 mb-2">Tudo processado! 🎉</h3>
          <p class="text-base-content/60">Nenhum documento está sendo processado no momento</p>
        </div>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="stats stats-vertical lg:stats-horizontal shadow-lg w-full">
      <div class="stat">
        <div class="stat-figure text-success">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,16.5L6.5,12L7.91,10.59L11,13.67L16.59,8.09L18,9.5L11,16.5Z" />
          </svg>
        </div>
        <div class="stat-title">Concluídos Hoje</div>
        <div class="stat-value text-success">{{ completedToday }}</div>
        <div class="stat-desc">{{ successRate.toFixed(1) }}% de sucesso</div>
      </div>
      
      <div class="stat">
        <div class="stat-figure text-primary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z" />
          </svg>
        </div>
        <div class="stat-title">Tempo Médio</div>
        <div class="stat-value text-primary">{{ averageProcessingTime }}</div>
        <div class="stat-desc">Por documento</div>
      </div>
      
      <div class="stat">
        <div class="stat-figure text-info">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,5V19H5V5H19Z" />
          </svg>
        </div>
        <div class="stat-title">Em Processamento</div>
        <div class="stat-value text-info">{{ activeProcessing.length }}</div>
        <div class="stat-desc">Documentos ativos</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useApi } from '~/composables/useApi'

interface ProcessingItem {
  documentId: string
  filename: string
  startTime: Date
  progress: number
  currentStep: string
  currentAgent: string
  estimatedTimeRemaining?: number
  agents: {
    name: string
    displayName: string
    status: 'pending' | 'running' | 'completed' | 'failed'
  }[]
}

// Reactive state
const activeProcessing = ref<ProcessingItem[]>([])
const isRefreshing = ref(false)

// Use API composable
const { apiBaseUrl } = useApi()

// Computed properties
const completedToday = computed(() => {
  // Mock value for MVP - in production, this would come from API
  return 8
})

const successRate = computed(() => {
  // Mock value for MVP - in production, this would be calculated from real data
  return 92.5
})

const averageProcessingTime = computed(() => {
  // Mock value for MVP - in production, this would come from API
  return '2.1min'
})

// Simplified methods
const refreshAll = async () => {
  if (isRefreshing.value) return
  
  isRefreshing.value = true
  
  try {
    await loadActiveProcessing()
  } catch (error) {
    console.error('Error refreshing data:', error)
  } finally {
    isRefreshing.value = false
  }
}

const loadActiveProcessing = async () => {
  try {
    // In production, this would fetch from /api/documents?status_filter=processing
    const response = await fetch(`${apiBaseUrl}/api/documents?status_filter=processing&limit=10`)
    
    if (response.ok) {
      const data = await response.json()
      
      // Transform API data to ProcessingItem format
      activeProcessing.value = data.documents.map((doc: any) => ({
        documentId: doc.id,
        filename: doc.filename,
        startTime: new Date(doc.upload_timestamp),
        progress: calculateProgress(doc.processing_status),
        currentStep: getCurrentStep(doc.processing_status),
        currentAgent: getCurrentAgent(doc.processing_status),
        estimatedTimeRemaining: getEstimatedTime(doc.processing_status),
        agents: [
          { name: 'xml_processing_agent', displayName: 'XML', status: getAgentStatus(doc, 'xml_processing_agent') },
          { name: 'ai_categorization_agent', displayName: 'IA', status: getAgentStatus(doc, 'ai_categorization_agent') },
          { name: 'sql_agent', displayName: 'SQL', status: getAgentStatus(doc, 'sql_agent') },
          { name: 'report_agent', displayName: 'Relatório', status: getAgentStatus(doc, 'report_agent') }
        ]
      }))
    }
  } catch (error) {
    console.error('Error loading active processing:', error)
    // Keep empty array on error
    activeProcessing.value = []
  }
}

const viewDetails = (documentId: string) => {
  navigateTo(`/documents/${documentId}`)
}

// Helper functions
const calculateProgress = (status: string): number => {
  const progressMap: Record<string, number> = {
    'pending': 0,
    'processing': 50,
    'completed': 100,
    'error': 0
  }
  return progressMap[status] || 25
}

const getCurrentStep = (status: string): string => {
  const stepMap: Record<string, string> = {
    'pending': 'Aguardando processamento...',
    'processing': 'Processando com agentes IA...',
    'completed': 'Processamento concluído',
    'error': 'Erro no processamento'
  }
  return stepMap[status] || 'Processando...'
}

const getCurrentAgent = (status: string): string => {
  if (status === 'processing') return 'Agentes IA'
  if (status === 'completed') return 'Concluído'
  if (status === 'error') return 'Erro'
  return 'Aguardando'
}

const getEstimatedTime = (status: string): number | undefined => {
  if (status === 'processing') return 90000 // 1.5 minutes
  if (status === 'pending') return 180000 // 3 minutes
  return undefined
}

const getAgentStatus = (doc: any, agentName: string): 'pending' | 'running' | 'completed' | 'failed' => {
  // Simplified status mapping for MVP
  if (doc.processing_status === 'completed') return 'completed'
  if (doc.processing_status === 'error') return 'failed'
  if (doc.processing_status === 'processing') {
    // Simulate different agents being at different stages
    const agentOrder = ['xml_processing_agent', 'ai_categorization_agent', 'sql_agent', 'report_agent']
    const currentIndex = Math.floor(Math.random() * agentOrder.length)
    const agentIndex = agentOrder.indexOf(agentName)
    
    if (agentIndex < currentIndex) return 'completed'
    if (agentIndex === currentIndex) return 'running'
    return 'pending'
  }
  return 'pending'
}

const getCompletedAgents = (agents: ProcessingItem['agents']): number => {
  return agents.filter(agent => agent.status === 'completed').length
}

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

// Auto-refresh with intelligent polling
let refreshInterval: NodeJS.Timeout

onMounted(() => {
  refreshAll()
  
  // Auto-refresh every 5 seconds when there are active processes
  refreshInterval = setInterval(() => {
    if (!isRefreshing.value && activeProcessing.value.length > 0) {
      refreshAll()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>