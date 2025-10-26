<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
          Histórico de Workflows
        </h3>
        <div class="flex items-center gap-2">
          <select v-model="statusFilter" class="select select-bordered select-sm">
            <option value="">Todos</option>
            <option value="completed">Concluídos</option>
            <option value="error">Com erro</option>
            <option value="paused">Pausados</option>
          </select>
          <select v-model="timeFilter" class="select select-bordered select-sm">
            <option value="24h">Últimas 24h</option>
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
          </select>
        </div>
      </div>

      <!-- History Table -->
      <div class="overflow-x-auto">
        <table class="table table-zebra w-full">
          <thead>
            <tr>
              <th>Workflow</th>
              <th>Status</th>
              <th>Duração</th>
              <th>Agente Principal</th>
              <th>Concluído em</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="workflow in filteredHistory" :key="workflow.id">
              <td>
                <div class="flex items-center gap-3">
                  <div 
                    class="w-3 h-3 rounded-full"
                    :class="getStatusColor(workflow.status)"
                  ></div>
                  <div>
                    <div class="font-bold">{{ workflow.name }}</div>
                    <div class="text-sm opacity-50">ID: {{ workflow.id }}</div>
                  </div>
                </div>
              </td>
              <td>
                <div 
                  class="badge badge-sm"
                  :class="getStatusBadgeClass(workflow.status)"
                >
                  {{ getStatusText(workflow.status) }}
                </div>
              </td>
              <td>
                <div class="text-sm">
                  {{ workflow.duration || calculateDuration(workflow) }}
                </div>
              </td>
              <td>
                <div class="badge badge-outline badge-sm">
                  {{ workflow.currentAgent }}
                </div>
              </td>
              <td>
                <div class="text-sm">
                  {{ formatDateTime(workflow.completedAt || workflow.startTime) }}
                </div>
              </td>
              <td>
                <div class="flex gap-1">
                  <button 
                    @click="viewDetails(workflow)"
                    class="btn btn-ghost btn-xs"
                    title="Ver detalhes"
                  >
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                      <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                    </svg>
                  </button>
                  <button 
                    v-if="workflow.status === 'error'"
                    @click="retryWorkflow(workflow)"
                    class="btn btn-ghost btn-xs text-primary"
                    title="Tentar novamente"
                  >
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                    </svg>
                  </button>
                  <button 
                    @click="exportWorkflow(workflow)"
                    class="btn btn-ghost btn-xs"
                    title="Exportar"
                  >
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-if="filteredHistory.length === 0" class="text-center py-8">
        <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-base-content/50">Nenhum workflow encontrado no histórico</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex justify-center mt-6">
        <div class="btn-group">
          <button 
            v-for="page in totalPages" 
            :key="page"
            @click="currentPage = page"
            class="btn btn-sm"
            :class="{ 'btn-active': currentPage === page }"
          >
            {{ page }}
          </button>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-4 border-t border-base-300">
        <div class="text-center">
          <div class="text-2xl font-bold text-success">{{ summaryStats.completed }}</div>
          <div class="text-xs text-base-content/50">Concluídos</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-error">{{ summaryStats.failed }}</div>
          <div class="text-xs text-base-content/50">Com Erro</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-primary">{{ summaryStats.avgDuration }}</div>
          <div class="text-xs text-base-content/50">Duração Média</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-info">{{ summaryStats.successRate }}%</div>
          <div class="text-xs text-base-content/50">Taxa de Sucesso</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { WorkflowExecution } from '~/types/dashboard'

// Props and emits
const emit = defineEmits<{
  viewWorkflow: [workflow: WorkflowExecution]
}>()

// Reactive state
const statusFilter = ref('')
const timeFilter = ref('24h')
const currentPage = ref(1)
const itemsPerPage = 10
const workflowHistory = ref<WorkflowExecution[]>([])

// Mock history data
const mockHistory: WorkflowExecution[] = [
  {
    id: 'wf-001',
    name: 'Processamento XML - Lote Dezembro',
    status: 'completed',
    progress: 100,
    currentStep: 'Concluído',
    currentAgent: 'XML Processing Agent',
    startTime: new Date(Date.now() - 2 * 60 * 60 * 1000),
    completedAt: new Date(Date.now() - 1.5 * 60 * 60 * 1000),
    duration: '30m',
    steps: []
  },
  {
    id: 'wf-002',
    name: 'Análise de Fornecedores Q3',
    status: 'completed',
    progress: 100,
    currentStep: 'Concluído',
    currentAgent: 'Report Agent',
    startTime: new Date(Date.now() - 4 * 60 * 60 * 1000),
    completedAt: new Date(Date.now() - 3.2 * 60 * 60 * 1000),
    duration: '48m',
    steps: []
  },
  {
    id: 'wf-003',
    name: 'Categorização de Produtos Novos',
    status: 'error',
    progress: 45,
    currentStep: 'Erro na validação',
    currentAgent: 'AI Categorization Agent',
    startTime: new Date(Date.now() - 6 * 60 * 60 * 1000),
    completedAt: new Date(Date.now() - 5.5 * 60 * 60 * 1000),
    duration: '30m',
    steps: []
  },
  {
    id: 'wf-004',
    name: 'Relatório Executivo Mensal',
    status: 'completed',
    progress: 100,
    currentStep: 'Concluído',
    currentAgent: 'Report Agent',
    startTime: new Date(Date.now() - 8 * 60 * 60 * 1000),
    completedAt: new Date(Date.now() - 7.1 * 60 * 60 * 1000),
    duration: '54m',
    steps: []
  },
  {
    id: 'wf-005',
    name: 'Sincronização Data Lake',
    status: 'completed',
    progress: 100,
    currentStep: 'Concluído',
    currentAgent: 'Data Lake Agent',
    startTime: new Date(Date.now() - 12 * 60 * 60 * 1000),
    completedAt: new Date(Date.now() - 11.5 * 60 * 60 * 1000),
    duration: '30m',
    steps: []
  }
]

// Computed properties
const filteredHistory = computed(() => {
  let filtered = workflowHistory.value

  // Filter by status
  if (statusFilter.value) {
    filtered = filtered.filter(w => w.status === statusFilter.value)
  }

  // Filter by time
  const now = new Date()
  let timeLimit: Date
  switch (timeFilter.value) {
    case '24h':
      timeLimit = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      break
    case '7d':
      timeLimit = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case '30d':
      timeLimit = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    default:
      timeLimit = new Date(0)
  }
  
  filtered = filtered.filter(w => w.startTime >= timeLimit)

  // Sort by completion time (most recent first)
  filtered.sort((a, b) => {
    const aTime = a.completedAt || a.startTime
    const bTime = b.completedAt || b.startTime
    return bTime.getTime() - aTime.getTime()
  })

  // Paginate
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filtered.slice(start, end)
})

const totalPages = computed(() => {
  const totalItems = workflowHistory.value.length
  return Math.ceil(totalItems / itemsPerPage)
})

const summaryStats = computed(() => {
  const completed = workflowHistory.value.filter(w => w.status === 'completed').length
  const failed = workflowHistory.value.filter(w => w.status === 'error').length
  const total = workflowHistory.value.length
  
  // Calculate average duration (mock calculation)
  const avgDurationMinutes = Math.round(
    workflowHistory.value
      .filter(w => w.duration)
      .reduce((sum, w) => {
        const minutes = parseInt(w.duration!.replace('m', '')) || 0
        return sum + minutes
      }, 0) / Math.max(1, workflowHistory.value.filter(w => w.duration).length)
  )

  return {
    completed,
    failed,
    avgDuration: `${avgDurationMinutes}m`,
    successRate: total > 0 ? Math.round((completed / total) * 100) : 0
  }
})

// Methods
const viewDetails = (workflow: WorkflowExecution) => {
  emit('viewWorkflow', workflow)
}

const retryWorkflow = (workflow: WorkflowExecution) => {
  console.log('Retrying workflow:', workflow.id)
  // In real implementation, trigger workflow retry
}

const exportWorkflow = (workflow: WorkflowExecution) => {
  console.log('Exporting workflow:', workflow.id)
  // In real implementation, export workflow data
}

const calculateDuration = (workflow: WorkflowExecution) => {
  if (workflow.duration) return workflow.duration
  
  const start = workflow.startTime
  const end = workflow.completedAt || new Date()
  const diff = end.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

// Helper functions
const getStatusColor = (status: string) => {
  switch (status) {
    case 'running': return 'bg-primary animate-pulse'
    case 'completed': return 'bg-success'
    case 'error': return 'bg-error'
    case 'paused': return 'bg-warning'
    default: return 'bg-base-300'
  }
}

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'running': return 'badge-primary'
    case 'completed': return 'badge-success'
    case 'error': return 'badge-error'
    case 'paused': return 'badge-warning'
    default: return 'badge-ghost'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'running': return 'Executando'
    case 'completed': return 'Concluído'
    case 'error': return 'Erro'
    case 'paused': return 'Pausado'
    default: return 'Desconhecido'
  }
}

const formatDateTime = (timestamp: Date) => {
  return timestamp.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  workflowHistory.value = [...mockHistory]
})
</script>