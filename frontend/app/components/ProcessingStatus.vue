<template>
  <div class="card bg-base-100 shadow">
    <div class="card-body">
      <div class="flex justify-between items-center mb-4">
        <h2 class="card-title">Status de Processamento</h2>
        <button 
          class="btn btn-ghost btn-sm"
          :disabled="isLoading"
          @click="refreshStatus"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': isLoading }" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
          </svg>
          Atualizar
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && !status" class="flex justify-center py-8">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="alert alert-error">
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
        </svg>
        <div>
          <h3 class="font-bold">Erro ao carregar status</h3>
          <div class="text-sm">{{ error }}</div>
        </div>
      </div>

      <!-- Status Content -->
      <div v-else-if="status" class="space-y-6">
        <!-- Overall Status -->
        <div class="flex items-center justify-between p-4 bg-base-200 rounded-lg">
          <div>
            <h3 class="font-semibold">Status Geral</h3>
            <p class="text-sm text-base-content/70">{{ status.document_id.slice(0, 8) }}...</p>
          </div>
          <div class="text-right">
            <div 
              class="badge badge-lg"
              :class="{
                'badge-warning': status.overall_status === 'pending',
                'badge-info': status.overall_status === 'processing',
                'badge-success': status.overall_status === 'completed',
                'badge-error': status.overall_status === 'error'
              }"
            >
              {{ getStatusText(status.overall_status) }}
            </div>
            <div v-if="status.total_processing_time_ms" class="text-xs text-base-content/50 mt-1">
              Tempo total: {{ formatProcessingTime(status.total_processing_time_ms) }}
            </div>
          </div>
        </div>

        <!-- Processing Timeline -->
        <div class="space-y-4">
          <h3 class="font-semibold">Progresso dos Agentes</h3>
          
          <div class="space-y-3">
            <div
              v-for="agentStatus in status.agent_statuses"
              :key="agentStatus.agent_name"
              class="flex items-center space-x-4 p-3 bg-base-200 rounded-lg"
            >
              <!-- Agent Icon -->
              <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                   :class="{
                     'bg-gray-200 text-gray-500': agentStatus.status === 'pending',
                     'bg-blue-200 text-blue-600': agentStatus.status === 'in_progress',
                     'bg-green-200 text-green-600': agentStatus.status === 'completed',
                     'bg-red-200 text-red-600': agentStatus.status === 'failed'
                   }">
                <svg v-if="agentStatus.status === 'completed'" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                <svg v-else-if="agentStatus.status === 'failed'" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                </svg>
                <svg v-else-if="agentStatus.status === 'in_progress'" class="w-5 h-5 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"></path>
                </svg>
                <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
                </svg>
              </div>
              
              <!-- Agent Details -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                  <h4 class="font-medium">{{ getAgentDisplayName(agentStatus.agent_name) }}</h4>
                  <div 
                    class="badge badge-sm"
                    :class="{
                      'badge-ghost': agentStatus.status === 'pending',
                      'badge-info': agentStatus.status === 'in_progress',
                      'badge-success': agentStatus.status === 'completed',
                      'badge-error': agentStatus.status === 'failed'
                    }"
                  >
                    {{ getStatusText(agentStatus.status) }}
                  </div>
                </div>
                
                <div class="text-sm text-base-content/70 mt-1">
                  <div v-if="agentStatus.started_at" class="flex items-center space-x-4">
                    <span>Iniciado: {{ formatDate(agentStatus.started_at) }}</span>
                    <span v-if="agentStatus.completed_at">
                      Concluído: {{ formatDate(agentStatus.completed_at) }}
                    </span>
                  </div>
                  
                  <div v-if="agentStatus.error_message" class="text-error mt-1">
                    Erro: {{ agentStatus.error_message }}
                  </div>
                  
                  <div v-if="agentStatus.retry_count > 0" class="text-warning mt-1">
                    Tentativas: {{ agentStatus.retry_count }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Processing Results -->
        <div v-if="status.processing_results && status.processing_results.length > 0" class="space-y-4">
          <h3 class="font-semibold">Resultados do Processamento</h3>
          
          <div class="space-y-3">
            <div
              v-for="result in status.processing_results"
              :key="`${result.agent_name}-${result.result_type}`"
              class="collapse collapse-arrow bg-base-200"
            >
              <input type="checkbox" />
              <div class="collapse-title">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="font-medium">{{ getAgentDisplayName(result.agent_name) }}</span>
                    <span class="text-sm text-base-content/70 ml-2">{{ result.result_type }}</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <div v-if="result.confidence_score" class="text-sm text-base-content/70">
                      Confiança: {{ Math.round(result.confidence_score * 100) }}%
                    </div>
                    <div v-if="result.processing_time_ms" class="text-sm text-base-content/70">
                      {{ formatProcessingTime(result.processing_time_ms) }}
                    </div>
                  </div>
                </div>
              </div>
              <div class="collapse-content">
                <div class="pt-2">
                  <pre class="text-sm bg-base-300 p-3 rounded overflow-x-auto">{{ JSON.stringify(result.result_data, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Error Summary -->
        <div v-if="status.error_summary" class="alert alert-error">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
          <div>
            <h3 class="font-bold">Resumo de Erros</h3>
            <div class="text-sm">{{ status.error_summary }}</div>
          </div>
        </div>

        <!-- Processing Timeline -->
        <div v-if="status.processing_started_at" class="space-y-2">
          <h3 class="font-semibold">Cronologia</h3>
          <div class="text-sm text-base-content/70 space-y-1">
            <div>Processamento iniciado: {{ formatDate(status.processing_started_at) }}</div>
            <div v-if="status.processing_completed_at">
              Processamento concluído: {{ formatDate(status.processing_completed_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface AgentStatus {
  agent_name: string
  status: string
  started_at?: string
  completed_at?: string
  error_message?: string
  retry_count: number
}

interface ProcessingResult {
  agent_name: string
  result_type: string
  result_data: any
  confidence_score?: number
  processing_time_ms?: number
  created_at: string
}

interface ProcessingStatusResponse {
  document_id: string
  overall_status: string
  agent_statuses: AgentStatus[]
  processing_results: ProcessingResult[]
  processing_started_at?: string
  processing_completed_at?: string
  total_processing_time_ms?: number
  error_summary?: string
}

// Props
const props = defineProps<{
  documentId: string
}>()

// Reactive state
const status = ref<ProcessingStatusResponse | null>(null)
const isLoading = ref(false)
const error = ref<string>('')

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Load processing status
const loadStatus = async () => {
  try {
    isLoading.value = true
    error.value = ''
    
    const response = await fetch(`${apiBaseUrl}/api/documents/${props.documentId}/status`)
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Status de processamento não encontrado')
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    status.value = await response.json()
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Erro desconhecido'
    console.error('Error loading processing status:', err)
  } finally {
    isLoading.value = false
  }
}

// Refresh status
const refreshStatus = () => {
  loadStatus()
}

// Utility functions
const getStatusText = (statusValue: string): string => {
  const statusMap: Record<string, string> = {
    'pending': 'Pendente',
    'in_progress': 'Em Progresso',
    'processing': 'Processando',
    'completed': 'Concluído',
    'failed': 'Falhou',
    'error': 'Erro',
    'skipped': 'Ignorado'
  }
  return statusMap[statusValue] || statusValue
}

const getAgentDisplayName = (agentName: string): string => {
  const agentMap: Record<string, string> = {
    'xml_processing_agent': 'Processamento XML',
    'ai_categorization_agent': 'Categorização IA',
    'sql_agent': 'Agente SQL',
    'report_agent': 'Geração de Relatórios',
    'scheduler_agent': 'Agendador',
    'data_lake_agent': 'Data Lake',
    'monitoring_agent': 'Monitoramento'
  }
  return agentMap[agentName] || agentName
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatProcessingTime = (milliseconds: number): string => {
  if (milliseconds < 1000) {
    return `${milliseconds}ms`
  } else if (milliseconds < 60000) {
    return `${(milliseconds / 1000).toFixed(1)}s`
  } else {
    const minutes = Math.floor(milliseconds / 60000)
    const seconds = Math.floor((milliseconds % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }
}

// Watchers
watch(() => props.documentId, () => {
  if (props.documentId) {
    loadStatus()
  }
}, { immediate: true })

// Auto-refresh for active processing
let refreshInterval: NodeJS.Timeout
onMounted(() => {
  refreshInterval = setInterval(() => {
    if (status.value && 
        (status.value.overall_status === 'processing' || status.value.overall_status === 'pending') &&
        !isLoading.value) {
      loadStatus()
    }
  }, 5000) // Refresh every 5 seconds for active processing
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>