<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
          </svg>
          Workflows Ativos
        </h3>
        <div class="badge badge-primary">{{ activeWorkflows.length }}</div>
      </div>

      <!-- Active Workflows -->
      <div class="space-y-3 max-h-80 overflow-y-auto">
        <div
          v-for="workflow in activeWorkflows"
          :key="workflow.id"
          @click="selectWorkflow(workflow)"
          class="bg-base-100 rounded-lg p-4 cursor-pointer hover:bg-base-300 transition-colors"
          :class="{ 'ring-2 ring-primary': selectedWorkflowId === workflow.id }"
        >
          <!-- Workflow Header -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <div 
                class="w-3 h-3 rounded-full"
                :class="getStatusColor(workflow.status)"
              ></div>
              <h4 class="font-semibold">{{ workflow.name }}</h4>
              <div 
                class="badge badge-sm"
                :class="getStatusBadgeClass(workflow.status)"
              >
                {{ getStatusText(workflow.status) }}
              </div>
            </div>
            <div class="text-sm text-base-content/50">
              {{ formatDuration(workflow.startTime) }}
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mb-3">
            <div class="flex justify-between text-sm mb-1">
              <span>Progresso</span>
              <span>{{ workflow.progress }}%</span>
            </div>
            <progress 
              class="progress progress-primary w-full"
              :value="workflow.progress" 
              max="100"
            ></progress>
          </div>

          <!-- Current Step -->
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              <span class="text-base-content/70">{{ workflow.currentStep }}</span>
            </div>
            <div class="badge badge-outline badge-xs">{{ workflow.currentAgent }}</div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="activeWorkflows.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
          </svg>
          <p class="text-base-content/50">Nenhum workflow ativo no momento</p>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-base-300">
        <div class="text-center">
          <div class="text-2xl font-bold text-primary">{{ totalWorkflows }}</div>
          <div class="text-xs text-base-content/50">Total</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-success">{{ completedToday }}</div>
          <div class="text-xs text-base-content/50">Concluídos Hoje</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-warning">{{ avgExecutionTime }}</div>
          <div class="text-xs text-base-content/50">Tempo Médio</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { WorkflowExecution } from '~/types/dashboard'

// Props and emits
const emit = defineEmits<{
  selectWorkflow: [workflow: WorkflowExecution]
}>()

// Reactive state
const selectedWorkflowId = ref<string | null>(null)
const workflows = ref<WorkflowExecution[]>([])

// Mock data
const mockWorkflows: WorkflowExecution[] = [
  {
    id: '1',
    name: 'Processamento XML - Lote Janeiro',
    status: 'running',
    progress: 67,
    currentStep: 'Validação de documentos NF-e',
    currentAgent: 'XML Processing Agent',
    startTime: new Date(Date.now() - 15 * 60 * 1000),
    steps: [
      {
        id: '1-1',
        name: 'Carregamento de arquivos',
        agent: 'XML Processing Agent',
        status: 'completed',
        startTime: new Date(Date.now() - 15 * 60 * 1000),
        completedAt: new Date(Date.now() - 12 * 60 * 1000),
        duration: '3m'
      },
      {
        id: '1-2',
        name: 'Validação de documentos NF-e',
        agent: 'XML Processing Agent',
        status: 'running',
        startTime: new Date(Date.now() - 12 * 60 * 1000)
      },
      {
        id: '1-3',
        name: 'Categorização automática',
        agent: 'AI Categorization Agent',
        status: 'pending'
      }
    ]
  },
  {
    id: '2',
    name: 'Análise de Fornecedores Q4',
    status: 'running',
    progress: 34,
    currentStep: 'Extração de dados fiscais',
    currentAgent: 'SQL Agent',
    startTime: new Date(Date.now() - 8 * 60 * 1000),
    steps: [
      {
        id: '2-1',
        name: 'Interpretação da consulta',
        agent: 'Master Agent',
        status: 'completed',
        startTime: new Date(Date.now() - 8 * 60 * 1000),
        completedAt: new Date(Date.now() - 6 * 60 * 1000),
        duration: '2m'
      },
      {
        id: '2-2',
        name: 'Extração de dados fiscais',
        agent: 'SQL Agent',
        status: 'running',
        startTime: new Date(Date.now() - 6 * 60 * 1000)
      }
    ]
  },
  {
    id: '3',
    name: 'Geração de Relatório Executivo',
    status: 'running',
    progress: 89,
    currentStep: 'Formatação final do relatório',
    currentAgent: 'Report Agent',
    startTime: new Date(Date.now() - 25 * 60 * 1000),
    steps: [
      {
        id: '3-1',
        name: 'Coleta de dados',
        agent: 'SQL Agent',
        status: 'completed',
        startTime: new Date(Date.now() - 25 * 60 * 1000),
        completedAt: new Date(Date.now() - 20 * 60 * 1000),
        duration: '5m'
      },
      {
        id: '3-2',
        name: 'Análise e insights',
        agent: 'Report Agent',
        status: 'completed',
        startTime: new Date(Date.now() - 20 * 60 * 1000),
        completedAt: new Date(Date.now() - 5 * 60 * 1000),
        duration: '15m'
      },
      {
        id: '3-3',
        name: 'Formatação final do relatório',
        agent: 'Report Agent',
        status: 'running',
        startTime: new Date(Date.now() - 5 * 60 * 1000)
      }
    ]
  }
]

// Computed properties
const activeWorkflows = computed(() => {
  return workflows.value.filter(w => w.status === 'running' || w.status === 'paused')
})

const totalWorkflows = computed(() => workflows.value.length)

const completedToday = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return workflows.value.filter(w => 
    w.status === 'completed' && 
    w.completedAt && 
    w.completedAt >= today
  ).length
})

const avgExecutionTime = computed(() => {
  const completed = workflows.value.filter(w => w.status === 'completed' && w.duration)
  if (completed.length === 0) return '0m'
  
  // Mock calculation - in real implementation, calculate from actual durations
  return '12m'
})

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Methods
const selectWorkflow = (workflow: WorkflowExecution) => {
  selectedWorkflowId.value = workflow.id
  emit('selectWorkflow', workflow)
}

const refreshWorkflows = async () => {
  // In real implementation, fetch from API
  // For now, simulate progress updates
  workflows.value.forEach(workflow => {
    if (workflow.status === 'running' && workflow.progress < 100) {
      workflow.progress = Math.min(100, workflow.progress + Math.random() * 5)
    }
  })
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

const formatDuration = (startTime: Date) => {
  const now = new Date()
  const diff = now.getTime() - startTime.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

// Lifecycle
onMounted(() => {
  workflows.value = [...mockWorkflows]
  
  // Set up auto-refresh every 5 seconds
  refreshInterval = setInterval(refreshWorkflows, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>