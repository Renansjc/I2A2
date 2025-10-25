<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
          </svg>
          Monitor de Workflows
        </h3>
        <div class="badge badge-primary">{{ activeWorkflows.length }} Ativos</div>
      </div>

      <!-- Active Workflows -->
      <div class="space-y-3">
        <div
          v-for="workflow in activeWorkflows"
          :key="workflow.id"
          class="bg-base-100 rounded-lg p-4 border-l-4"
          :class="getWorkflowBorderClass(workflow.status)"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-3">
              <div 
                class="w-3 h-3 rounded-full"
                :class="getStatusIndicatorClass(workflow.status)"
              ></div>
              <h4 class="font-semibold">{{ workflow.name }}</h4>
              <div class="badge badge-sm" :class="getStatusBadgeClass(workflow.status)">
                {{ getStatusText(workflow.status) }}
              </div>
            </div>
            <div class="text-sm text-base-content/70">
              {{ formatTime(workflow.startTime) }}
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mb-3">
            <div class="flex justify-between text-sm mb-1">
              <span>Progresso</span>
              <span>{{ workflow.progress }}%</span>
            </div>
            <progress 
              class="progress w-full"
              :class="getProgressClass(workflow.status)"
              :value="workflow.progress" 
              max="100"
            ></progress>
          </div>

          <!-- Current Step -->
          <div class="text-sm">
            <span class="text-base-content/70">Etapa atual:</span>
            <span class="font-medium ml-1">{{ workflow.currentStep }}</span>
          </div>

          <!-- Agent Information -->
          <div class="flex items-center gap-2 mt-2">
            <span class="text-xs text-base-content/50">Agente:</span>
            <div class="badge badge-outline badge-xs">{{ workflow.currentAgent }}</div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="activeWorkflows.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
          </svg>
          <p class="text-base-content/50">Nenhum workflow ativo no momento</p>
        </div>
      </div>

      <!-- Recent Completed Workflows -->
      <div v-if="recentCompleted.length > 0" class="mt-6">
        <h4 class="font-semibold mb-3 text-sm text-base-content/70">Concluídos Recentemente</h4>
        <div class="space-y-2">
          <div
            v-for="workflow in recentCompleted"
            :key="workflow.id"
            class="flex items-center justify-between p-2 bg-base-100 rounded text-sm"
          >
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 bg-success rounded-full"></div>
              <span>{{ workflow.name }}</span>
            </div>
            <div class="flex items-center gap-2 text-base-content/50">
              <span>{{ workflow.duration }}</span>
              <span>•</span>
              <span>{{ workflow.completedAt ? formatTime(workflow.completedAt) : 'N/A' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Workflow } from '~/types/dashboard'

// Reactive state
const activeWorkflows = ref<Workflow[]>([])
const recentCompleted = ref<Workflow[]>([])
let updateInterval: NodeJS.Timeout | null = null

// Mock data for development
const mockActiveWorkflows: Workflow[] = [
  {
    id: '1',
    name: 'Processamento XML - Lote 2025-001',
    status: 'running',
    progress: 75,
    currentStep: 'Categorizando produtos com IA',
    currentAgent: 'AI Categorization Agent',
    startTime: new Date(Date.now() - 5 * 60 * 1000) // 5 minutes ago
  },
  {
    id: '2',
    name: 'Geração de Relatório Mensal',
    status: 'running',
    progress: 45,
    currentStep: 'Analisando dados fiscais',
    currentAgent: 'Report Agent',
    startTime: new Date(Date.now() - 12 * 60 * 1000) // 12 minutes ago
  }
]

const mockRecentCompleted: Workflow[] = [
  {
    id: '3',
    name: 'Consulta: Top fornecedores Q4',
    status: 'completed',
    progress: 100,
    currentStep: 'Concluído',
    currentAgent: 'SQL Agent',
    startTime: new Date(Date.now() - 30 * 60 * 1000),
    completedAt: new Date(Date.now() - 25 * 60 * 1000),
    duration: '5m 23s'
  },
  {
    id: '4',
    name: 'Validação XML - Lote 2024-999',
    status: 'completed',
    progress: 100,
    currentStep: 'Concluído',
    currentAgent: 'XML Processing Agent',
    startTime: new Date(Date.now() - 45 * 60 * 1000),
    completedAt: new Date(Date.now() - 40 * 60 * 1000),
    duration: '5m 12s'
  }
]

// Initialize mock data
onMounted(() => {
  activeWorkflows.value = [...mockActiveWorkflows]
  recentCompleted.value = [...mockRecentCompleted]
  
  // Simulate progress updates
  updateInterval = setInterval(() => {
    activeWorkflows.value.forEach(workflow => {
      if (workflow.status === 'running' && workflow.progress < 100) {
        workflow.progress = Math.min(100, workflow.progress + Math.random() * 5)
        
        // Simulate step changes
        if (workflow.progress > 80 && workflow.currentStep !== 'Finalizando processamento') {
          workflow.currentStep = 'Finalizando processamento'
        }
      }
    })
  }, 3000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})

// Helper functions
const getWorkflowBorderClass = (status: string) => {
  switch (status) {
    case 'running': return 'border-l-primary'
    case 'completed': return 'border-l-success'
    case 'error': return 'border-l-error'
    case 'paused': return 'border-l-warning'
    default: return 'border-l-base-300'
  }
}

const getStatusIndicatorClass = (status: string) => {
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

const getProgressClass = (status: string) => {
  switch (status) {
    case 'running': return 'progress-primary'
    case 'completed': return 'progress-success'
    case 'error': return 'progress-error'
    case 'paused': return 'progress-warning'
    default: return 'progress-ghost'
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