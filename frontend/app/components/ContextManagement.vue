<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          Gerenciamento de Contexto
        </h3>
        <div class="flex items-center gap-2">
          <div class="badge badge-primary">{{ activeContexts.length }} Ativos</div>
          <button 
            @click="refreshContexts"
            class="btn btn-ghost btn-sm"
            :disabled="isRefreshing"
          >
            <svg 
              class="w-4 h-4" 
              :class="{ 'animate-spin': isRefreshing }"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Context Overview -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg p-4">
          <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>
          </div>
          <div class="stat-title">Conversas Ativas</div>
          <div class="stat-value text-primary">{{ contextStats.activeConversations }}</div>
          <div class="stat-desc">{{ contextStats.newToday }} novas hoje</div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-4">
          <div class="stat-figure text-secondary">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
            </svg>
          </div>
          <div class="stat-title">Memória Utilizada</div>
          <div class="stat-value text-secondary">{{ contextStats.memoryUsage }}MB</div>
          <div class="stat-desc">{{ contextStats.memoryEfficiency }}% eficiência</div>
        </div>

        <div class="stat bg-base-100 rounded-lg p-4">
          <div class="stat-figure text-accent">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="stat-title">Tempo Médio</div>
          <div class="stat-value text-accent">{{ contextStats.avgRetention }}</div>
          <div class="stat-desc">retenção de contexto</div>
        </div>
      </div>

      <!-- Active Contexts -->
      <div class="space-y-3">
        <h4 class="font-semibold">Contextos Ativos</h4>
        <div class="space-y-2 max-h-64 overflow-y-auto">
          <div
            v-for="context in activeContexts"
            :key="context.conversationId"
            class="bg-base-100 rounded-lg p-4"
            :class="{ 'ring-2 ring-primary': selectedContextId === context.conversationId }"
            @click="selectContext(context)"
          >
            <!-- Context Header -->
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="avatar placeholder">
                  <div class="bg-primary text-primary-content rounded-full w-8">
                    <span class="text-xs">{{ context.userId.slice(-2).toUpperCase() }}</span>
                  </div>
                </div>
                <div>
                  <h5 class="font-medium">Usuário {{ context.userId }}</h5>
                  <p class="text-sm text-base-content/50">{{ context.history.length }} mensagens</p>
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm font-bold">{{ getContextSize(context) }}KB</div>
                <div class="text-xs text-base-content/50">Tamanho</div>
              </div>
            </div>

            <!-- Context Metadata -->
            <div class="grid grid-cols-2 gap-4 text-sm mb-3">
              <div>
                <span class="text-base-content/50">Sessão:</span>
                <span class="font-medium ml-1">{{ context.conversationId.slice(0, 8) }}...</span>
              </div>
              <div>
                <span class="text-base-content/50">Última atividade:</span>
                <span class="font-medium ml-1">{{ formatTime(getLastActivity(context)) }}</span>
              </div>
            </div>

            <!-- Context Preferences -->
            <div v-if="Object.keys(context.preferences).length > 0" class="mb-3">
              <div class="text-xs text-base-content/50 mb-1">Preferências:</div>
              <div class="flex gap-1 flex-wrap">
                <div 
                  v-for="(value, key) in context.preferences" 
                  :key="key"
                  class="badge badge-outline badge-xs"
                >
                  {{ key }}: {{ value }}
                </div>
              </div>
            </div>

            <!-- Session Data Summary -->
            <div v-if="Object.keys(context.sessionData).length > 0" class="mb-3">
              <div class="text-xs text-base-content/50 mb-1">Dados da Sessão:</div>
              <div class="text-xs bg-base-200 p-2 rounded">
                <div v-for="(value, key) in getSessionSummary(context.sessionData)" :key="key">
                  <strong>{{ key }}:</strong> {{ value }}
                </div>
              </div>
            </div>

            <!-- Context Actions -->
            <div class="flex gap-2 pt-3 border-t border-base-200">
              <button 
                @click.stop="viewContextDetails(context)"
                class="btn btn-ghost btn-xs"
              >
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                  <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                </svg>
                Ver Detalhes
              </button>
              <button 
                @click.stop="compressContext(context)"
                class="btn btn-ghost btn-xs"
              >
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 11-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15 13.586V12a1 1 0 011-1z" clip-rule="evenodd"></path>
                </svg>
                Comprimir
              </button>
              <button 
                @click.stop="clearContext(context)"
                class="btn btn-ghost btn-xs text-error"
              >
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
                  <path fill-rule="evenodd" d="M10 5a2 2 0 00-2 2v6a2 2 0 002 2h4a2 2 0 002-2V7a2 2 0 00-2-2H10zm3 6a1 1 0 10-2 0v2a1 1 0 102 0v-2z" clip-rule="evenodd"></path>
                </svg>
                Limpar
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="activeContexts.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          <p class="text-base-content/50">Nenhum contexto ativo no momento</p>
        </div>
      </div>

      <!-- Context Management Actions -->
      <div class="mt-6 pt-4 border-t border-base-300">
        <h4 class="font-semibold mb-3">Ações de Gerenciamento</h4>
        <div class="flex gap-2 flex-wrap">
          <button 
            @click="compressAllContexts"
            class="btn btn-outline btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 11-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12z" clip-rule="evenodd"></path>
            </svg>
            Comprimir Todos
          </button>
          <button 
            @click="clearInactiveContexts"
            class="btn btn-outline btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
              <path fill-rule="evenodd" d="M10 5a2 2 0 00-2 2v6a2 2 0 002 2h4a2 2 0 002-2V7a2 2 0 00-2-2H10z" clip-rule="evenodd"></path>
            </svg>
            Limpar Inativos
          </button>
          <button 
            @click="exportContexts"
            class="btn btn-outline btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Exportar Contextos
          </button>
          <button 
            @click="configureRetention"
            class="btn btn-outline btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"></path>
            </svg>
            Configurar Retenção
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ContextData } from '~/types/dashboard'

// Props and emits
const emit = defineEmits<{
  selectContext: [context: ContextData]
}>()

// Reactive state
const isRefreshing = ref(false)
const selectedContextId = ref<string | null>(null)
const contexts = ref<ContextData[]>([])

// Mock context data
const mockContexts: ContextData[] = [
  {
    conversationId: 'conv-001',
    userId: 'exec-001',
    sessionData: {
      lastQuery: 'Análise de fornecedores Q4',
      queryCount: 15,
      preferredFormat: 'executive',
      businessContext: 'quarterly_review'
    },
    preferences: {
      language: 'pt-BR',
      reportFormat: 'pdf',
      detailLevel: 'executive'
    },
    history: [
      {
        id: '1',
        conversationId: 'conv-001',
        sender: 'user',
        content: 'Quais são os principais fornecedores por volume?',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        metadata: null
      },
      {
        id: '2',
        conversationId: 'conv-001',
        sender: 'agent',
        content: 'Analisando dados fiscais...',
        timestamp: new Date(Date.now() - 8 * 60 * 1000),
        metadata: {
          agent: 'SQL Agent',
          executionTime: '3.2s',
          confidence: 95
        }
      }
    ],
    metadata: {
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
      lastActivity: new Date(Date.now() - 5 * 60 * 1000),
      compressionLevel: 0,
      retentionPolicy: 'standard'
    }
  },
  {
    conversationId: 'conv-002',
    userId: 'exec-002',
    sessionData: {
      lastQuery: 'Relatório mensal de compliance',
      queryCount: 8,
      preferredFormat: 'detailed',
      businessContext: 'compliance_review'
    },
    preferences: {
      language: 'pt-BR',
      reportFormat: 'xlsx',
      detailLevel: 'detailed'
    },
    history: [
      {
        id: '3',
        conversationId: 'conv-002',
        sender: 'user',
        content: 'Gere relatório de compliance fiscal',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        metadata: null
      }
    ],
    metadata: {
      createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000),
      lastActivity: new Date(Date.now() - 25 * 60 * 1000),
      compressionLevel: 1,
      retentionPolicy: 'extended'
    }
  },
  {
    conversationId: 'conv-003',
    userId: 'exec-001',
    sessionData: {
      lastQuery: 'Categorização de produtos novos',
      queryCount: 3,
      preferredFormat: 'summary',
      businessContext: 'product_management'
    },
    preferences: {
      language: 'pt-BR',
      reportFormat: 'pdf',
      detailLevel: 'summary'
    },
    history: [
      {
        id: '4',
        conversationId: 'conv-003',
        sender: 'user',
        content: 'Categorize os novos produtos do lote Janeiro',
        timestamp: new Date(Date.now() - 45 * 60 * 1000),
        metadata: null
      }
    ],
    metadata: {
      createdAt: new Date(Date.now() - 50 * 60 * 1000),
      lastActivity: new Date(Date.now() - 40 * 60 * 1000),
      compressionLevel: 0,
      retentionPolicy: 'standard'
    }
  }
]

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Computed properties
const activeContexts = computed(() => {
  return contexts.value.filter(context => {
    const lastActivity = new Date(context.metadata.lastActivity)
    const now = new Date()
    const hoursSinceActivity = (now.getTime() - lastActivity.getTime()) / (1000 * 60 * 60)
    
    // Consider active if activity within last 4 hours
    return hoursSinceActivity < 4
  })
})

const contextStats = computed(() => {
  const activeCount = activeContexts.value.length
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const newToday = contexts.value.filter(context => 
    new Date(context.metadata.createdAt) >= today
  ).length

  const totalMemory = contexts.value.reduce((sum, context) => sum + getContextSize(context), 0)
  const avgRetention = '2.5h' // Mock calculation

  return {
    activeConversations: activeCount,
    newToday,
    memoryUsage: Math.round(totalMemory / 1024), // Convert to MB
    memoryEfficiency: 87, // Mock efficiency percentage
    avgRetention
  }
})

// Methods
const selectContext = (context: ContextData) => {
  selectedContextId.value = context.conversationId
  emit('selectContext', context)
}

const refreshContexts = async () => {
  isRefreshing.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    // In real implementation, fetch from API
  } finally {
    isRefreshing.value = false
  }
}

const viewContextDetails = (context: ContextData) => {
  console.log('Viewing context details:', context.conversationId)
  // In real implementation, open context details modal
}

const compressContext = (context: ContextData) => {
  console.log('Compressing context:', context.conversationId)
  context.metadata.compressionLevel = Math.min(3, context.metadata.compressionLevel + 1)
  
  // Simulate compression by reducing history
  if (context.history.length > 5) {
    context.history = context.history.slice(-5)
  }
}

const clearContext = (context: ContextData) => {
  console.log('Clearing context:', context.conversationId)
  const index = contexts.value.findIndex(c => c.conversationId === context.conversationId)
  if (index > -1) {
    contexts.value.splice(index, 1)
  }
}

const compressAllContexts = () => {
  console.log('Compressing all contexts')
  contexts.value.forEach(context => {
    if (context.metadata.compressionLevel < 2) {
      compressContext(context)
    }
  })
}

const clearInactiveContexts = () => {
  console.log('Clearing inactive contexts')
  const now = new Date()
  contexts.value = contexts.value.filter(context => {
    const lastActivity = new Date(context.metadata.lastActivity)
    const hoursSinceActivity = (now.getTime() - lastActivity.getTime()) / (1000 * 60 * 60)
    return hoursSinceActivity < 24 // Keep contexts active within 24 hours
  })
}

const exportContexts = () => {
  console.log('Exporting contexts')
  // In real implementation, export context data
}

const configureRetention = () => {
  console.log('Configuring retention policies')
  // In real implementation, open retention configuration modal
}

// Helper functions
const getContextSize = (context: ContextData) => {
  // Estimate context size in KB
  const historySize = context.history.length * 0.5 // ~0.5KB per message
  const sessionSize = Object.keys(context.sessionData).length * 0.1 // ~0.1KB per session key
  const preferencesSize = Object.keys(context.preferences).length * 0.05 // ~0.05KB per preference
  
  return Math.round((historySize + sessionSize + preferencesSize) * 100) / 100
}

const getLastActivity = (context: ContextData) => {
  return new Date(context.metadata.lastActivity)
}

const getSessionSummary = (sessionData: Record<string, any>) => {
  // Return a simplified view of session data
  const summary: Record<string, string> = {}
  Object.entries(sessionData).forEach(([key, value]) => {
    if (typeof value === 'string' && value.length > 30) {
      summary[key] = value.substring(0, 30) + '...'
    } else {
      summary[key] = String(value)
    }
  })
  return summary
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

// Lifecycle
onMounted(() => {
  contexts.value = [...mockContexts]
  
  // Set up auto-refresh every 30 seconds
  refreshInterval = setInterval(() => {
    // Simulate context updates
    contexts.value.forEach(context => {
      if (Math.random() > 0.8) {
        context.metadata.lastActivity = new Date()
      }
    })
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>