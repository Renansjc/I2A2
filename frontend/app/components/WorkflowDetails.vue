<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div v-if="selectedWorkflow" class="space-y-4">
        <!-- Workflow Header -->
        <div class="flex items-center justify-between pb-4 border-b border-base-300">
          <div>
            <h3 class="card-title">{{ selectedWorkflow.name }}</h3>
            <div class="flex items-center gap-2 mt-1">
              <div 
                class="badge badge-sm"
                :class="getStatusBadgeClass(selectedWorkflow.status)"
              >
                {{ getStatusText(selectedWorkflow.status) }}
              </div>
              <span class="text-sm text-base-content/50">
                Iniciado {{ formatTime(selectedWorkflow.startTime) }}
              </span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold">{{ selectedWorkflow.progress }}%</div>
            <div class="text-sm text-base-content/50">Progresso</div>
          </div>
        </div>

        <!-- Progress Visualization -->
        <div class="space-y-3">
          <div class="flex justify-between text-sm">
            <span>Progresso Geral</span>
            <span>{{ selectedWorkflow.progress }}%</span>
          </div>
          <progress 
            class="progress w-full"
            :class="getProgressClass(selectedWorkflow.status)"
            :value="selectedWorkflow.progress" 
            max="100"
          ></progress>
        </div>

        <!-- Current Step -->
        <div class="bg-base-100 rounded-lg p-4">
          <h4 class="font-semibold mb-2 flex items-center gap-2">
            <div 
              class="w-3 h-3 rounded-full bg-primary animate-pulse"
            ></div>
            Etapa Atual
          </h4>
          <p class="text-sm mb-2">{{ selectedWorkflow.currentStep }}</p>
          <div class="flex items-center gap-2">
            <div class="badge badge-outline badge-sm">{{ selectedWorkflow.currentAgent }}</div>
            <span class="text-xs text-base-content/50">
              Executando há {{ getStepDuration() }}
            </span>
          </div>
        </div>

        <!-- Workflow Steps -->
        <div class="space-y-2">
          <h4 class="font-semibold">Etapas do Workflow</h4>
          <div class="space-y-2">
            <div
              v-for="(step, index) in workflowSteps"
              :key="step.id"
              class="flex items-center gap-3 p-3 bg-base-100 rounded-lg"
              :class="{ 'ring-2 ring-primary': step.status === 'current' }"
            >
              <!-- Step Status Icon -->
              <div class="flex-shrink-0">
                <div 
                  v-if="step.status === 'completed'"
                  class="w-6 h-6 bg-success rounded-full flex items-center justify-center"
                >
                  <svg class="w-4 h-4 text-success-content" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                  </svg>
                </div>
                <div 
                  v-else-if="step.status === 'current'"
                  class="w-6 h-6 bg-primary rounded-full flex items-center justify-center animate-pulse"
                >
                  <div class="w-2 h-2 bg-primary-content rounded-full"></div>
                </div>
                <div 
                  v-else-if="step.status === 'error'"
                  class="w-6 h-6 bg-error rounded-full flex items-center justify-center"
                >
                  <svg class="w-4 h-4 text-error-content" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                  </svg>
                </div>
                <div 
                  v-else
                  class="w-6 h-6 bg-base-300 rounded-full flex items-center justify-center"
                >
                  <span class="text-xs font-medium">{{ index + 1 }}</span>
                </div>
              </div>

              <!-- Step Content -->
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <h5 class="font-medium text-sm">{{ step.name }}</h5>
                  <div class="flex items-center gap-2">
                    <div class="badge badge-outline badge-xs">{{ step.agent }}</div>
                    <span v-if="step.duration" class="text-xs text-base-content/50">
                      {{ step.duration }}
                    </span>
                  </div>
                </div>
                <p class="text-xs text-base-content/70 mt-1">{{ step.description }}</p>
                
                <!-- Step Progress -->
                <div v-if="step.status === 'current' && step.progress !== undefined" class="mt-2">
                  <div class="flex justify-between text-xs mb-1">
                    <span>Progresso da etapa</span>
                    <span>{{ step.progress }}%</span>
                  </div>
                  <progress 
                    class="progress progress-primary progress-xs w-full" 
                    :value="step.progress" 
                    max="100"
                  ></progress>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Execution Metrics -->
        <div class="bg-base-100 rounded-lg p-4">
          <h4 class="font-semibold mb-3">Métricas de Execução</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div class="text-lg font-bold text-primary">{{ executionMetrics.totalSteps }}</div>
              <div class="text-xs text-base-content/50">Total de Etapas</div>
            </div>
            <div>
              <div class="text-lg font-bold text-success">{{ executionMetrics.completedSteps }}</div>
              <div class="text-xs text-base-content/50">Concluídas</div>
            </div>
            <div>
              <div class="text-lg font-bold text-warning">{{ executionMetrics.estimatedTime }}</div>
              <div class="text-xs text-base-content/50">Tempo Estimado</div>
            </div>
            <div>
              <div class="text-lg font-bold text-info">{{ executionMetrics.resourceUsage }}%</div>
              <div class="text-xs text-base-content/50">Uso de Recursos</div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2 pt-4 border-t border-base-300">
          <button 
            v-if="selectedWorkflow.status === 'running'"
            @click="pauseWorkflow"
            class="btn btn-warning btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            Pausar
          </button>
          <button 
            v-if="selectedWorkflow.status === 'error'"
            @click="retryWorkflow"
            class="btn btn-primary btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
            Tentar Novamente
          </button>
          <button 
            @click="exportWorkflowLog"
            class="btn btn-ghost btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Exportar Log
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-base-content/50">Selecione um workflow para ver os detalhes</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { WorkflowExecution, WorkflowStep } from '~/types/dashboard'

// Props
const props = defineProps<{
  selectedWorkflow: WorkflowExecution | null
}>()

// Reactive state
const workflowSteps = ref<WorkflowStep[]>([])

// Mock workflow steps data
const mockWorkflowSteps: WorkflowStep[] = [
  {
    id: '1',
    name: 'Validação de entrada',
    description: 'Validando arquivos XML e estrutura de dados',
    agent: 'XML Processing Agent',
    status: 'completed',
    duration: '2.3s',
    progress: 100
  },
  {
    id: '2',
    name: 'Análise semântica',
    description: 'Extraindo contexto e significado dos documentos',
    agent: 'XML Processing Agent',
    status: 'completed',
    duration: '8.7s',
    progress: 100
  },
  {
    id: '3',
    name: 'Categorização inteligente',
    description: 'Categorizando produtos e fornecedores com IA',
    agent: 'AI Categorization Agent',
    status: 'current',
    duration: '5.2s',
    progress: 75
  },
  {
    id: '4',
    name: 'Armazenamento de dados',
    description: 'Salvando dados processados no Data Lake',
    agent: 'Data Lake Agent',
    status: 'pending',
    progress: 0
  },
  {
    id: '5',
    name: 'Geração de insights',
    description: 'Gerando insights e recomendações executivas',
    agent: 'Report Agent',
    status: 'pending',
    progress: 0
  }
]

// Computed properties
const executionMetrics = computed(() => {
  if (!props.selectedWorkflow) {
    return {
      totalSteps: 0,
      completedSteps: 0,
      estimatedTime: '0m',
      resourceUsage: 0
    }
  }

  const completed = workflowSteps.value.filter(step => step.status === 'completed').length
  const total = workflowSteps.value.length
  const remaining = total - completed
  const avgStepTime = 6 // seconds
  const estimatedMinutes = Math.ceil((remaining * avgStepTime) / 60)

  return {
    totalSteps: total,
    completedSteps: completed,
    estimatedTime: estimatedMinutes > 0 ? `${estimatedMinutes}m` : 'Concluído',
    resourceUsage: Math.round(props.selectedWorkflow.progress * 0.8) // Simulate resource usage
  }
})

// Watch for workflow changes
watch(() => props.selectedWorkflow, (newWorkflow) => {
  if (newWorkflow) {
    loadWorkflowSteps(newWorkflow.id)
  }
}, { immediate: true })

// Methods
const loadWorkflowSteps = async (workflowId: string) => {
  // In a real implementation, this would fetch steps from API
  // For now, use mock data
  workflowSteps.value = [...mockWorkflowSteps]
}

const getStepDuration = () => {
  if (!props.selectedWorkflow) return '0s'
  
  const now = new Date()
  const start = props.selectedWorkflow.startTime
  const diff = now.getTime() - start.getTime()
  const seconds = Math.floor(diff / 1000)
  
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

const pauseWorkflow = () => {
  console.log('Pausing workflow:', props.selectedWorkflow?.id)
}

const retryWorkflow = () => {
  console.log('Retrying workflow:', props.selectedWorkflow?.id)
}

const exportWorkflowLog = () => {
  console.log('Exporting workflow log:', props.selectedWorkflow?.id)
}

// Helper functions
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

const getProgressClass = (status: string) => {
  switch (status) {
    case 'running': return 'progress-primary'
    case 'completed': return 'progress-success'
    case 'error': return 'progress-error'
    case 'paused': return 'progress-warning'
    default: return 'progress-ghost'
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