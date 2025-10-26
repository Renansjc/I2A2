<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path>
            <path fill-rule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"></path>
          </svg>
          Logs de Interação dos Agentes
        </h3>
        <div class="flex items-center gap-2">
          <button 
            @click="refreshLogs"
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
          <div class="badge badge-primary">{{ logs.length }}</div>
        </div>
      </div>

      <!-- Filters -->
      <div class="mb-4 flex gap-2 flex-wrap">
        <select v-model="levelFilter" class="select select-bordered select-sm">
          <option value="">Todos os níveis</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>
        <select v-model="sourceFilter" class="select select-bordered select-sm">
          <option value="">Todos os agentes</option>
          <option value="master">Master Agent</option>
          <option value="xml">XML Agent</option>
          <option value="categorization">AI Categorization</option>
          <option value="sql">SQL Agent</option>
          <option value="report">Report Agent</option>
        </select>
        <input 
          v-model="searchQuery"
          type="text" 
          placeholder="Buscar logs..." 
          class="input input-bordered input-sm flex-1 min-w-48"
        >
        <button 
          @click="clearLogs"
          class="btn btn-ghost btn-sm"
        >
          Limpar
        </button>
      </div>

      <!-- Logs List -->
      <div class="space-y-2 max-h-96 overflow-y-auto">
        <div
          v-for="log in filteredLogs"
          :key="log.id"
          class="p-3 rounded-lg border-l-4"
          :class="getLogClass(log.level)"
        >
          <!-- Log Header -->
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div 
                class="w-2 h-2 rounded-full"
                :class="getLevelColor(log.level)"
              ></div>
              <span class="font-medium text-sm">{{ log.source }}</span>
              <div 
                class="badge badge-xs"
                :class="getLevelBadgeClass(log.level)"
              >
                {{ log.level.toUpperCase() }}
              </div>
            </div>
            <div class="text-xs text-base-content/50">
              {{ formatTime(log.timestamp) }}
            </div>
          </div>

          <!-- Log Message -->
          <p class="text-sm mb-2">{{ log.message }}</p>

          <!-- Log Context -->
          <div v-if="log.context && Object.keys(log.context).length > 0" class="mb-2">
            <details class="collapse collapse-arrow bg-base-200 rounded">
              <summary class="collapse-title text-xs font-medium">
                Contexto Adicional
              </summary>
              <div class="collapse-content">
                <pre class="text-xs bg-base-300 p-2 rounded overflow-x-auto">{{ JSON.stringify(log.context, null, 2) }}</pre>
              </div>
            </details>
          </div>

          <!-- Stack Trace -->
          <div v-if="log.stack" class="mb-2">
            <details class="collapse collapse-arrow bg-base-200 rounded">
              <summary class="collapse-title text-xs font-medium text-error">
                Stack Trace
              </summary>
              <div class="collapse-content">
                <pre class="text-xs bg-base-300 p-2 rounded overflow-x-auto">{{ log.stack }}</pre>
              </div>
            </details>
          </div>

          <!-- Resolution Status -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div v-if="log.resolved" class="badge badge-success badge-xs">
                Resolvido
              </div>
              <div v-else-if="log.level === 'error'" class="badge badge-error badge-xs">
                Pendente
              </div>
            </div>
            <div class="flex gap-1">
              <button 
                v-if="!log.resolved && log.level === 'error'"
                @click="markAsResolved(log)"
                class="btn btn-ghost btn-xs text-success"
                title="Marcar como resolvido"
              >
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
              </button>
              <button 
                @click="copyLog(log)"
                class="btn btn-ghost btn-xs"
                title="Copiar log"
              >
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"></path>
                  <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="filteredLogs.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path>
            <path fill-rule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"></path>
          </svg>
          <p class="text-base-content/50">
            {{ searchQuery || levelFilter || sourceFilter ? 'Nenhum log encontrado' : 'Nenhum log disponível' }}
          </p>
        </div>
      </div>

      <!-- Log Statistics -->
      <div class="mt-4 pt-4 border-t border-base-300">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div class="text-2xl font-bold text-info">{{ logStats.total }}</div>
            <div class="text-xs text-base-content/50">Total</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-error">{{ logStats.errors }}</div>
            <div class="text-xs text-base-content/50">Erros</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-warning">{{ logStats.warnings }}</div>
            <div class="text-xs text-base-content/50">Avisos</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-success">{{ logStats.resolved }}</div>
            <div class="text-xs text-base-content/50">Resolvidos</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ErrorLog } from '~/types/dashboard'

// Reactive state
const isRefreshing = ref(false)
const levelFilter = ref('')
const sourceFilter = ref('')
const searchQuery = ref('')
const logs = ref<ErrorLog[]>([])

// Mock logs data
const mockLogs: ErrorLog[] = [
  {
    id: '1',
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
    level: 'info',
    source: 'Master Agent',
    message: 'Consulta executiva interpretada com sucesso: "Análise de fornecedores Q4"',
    resolved: true,
    context: {
      userId: 'exec-001',
      queryType: 'supplier_analysis',
      confidence: 0.95
    }
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    level: 'warning',
    source: 'XML Processing Agent',
    message: 'Documento XML com estrutura não padrão detectado, aplicando correções automáticas',
    resolved: true,
    context: {
      fileName: 'nfe_123456.xml',
      corrections: ['missing_namespace', 'invalid_date_format']
    }
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 8 * 60 * 1000),
    level: 'error',
    source: 'AI Categorization Agent',
    message: 'Falha na categorização automática de produtos: timeout na API OpenAI',
    resolved: false,
    context: {
      productCount: 45,
      retryAttempts: 3,
      lastError: 'Request timeout after 30s'
    },
    stack: 'OpenAIError: Request timeout\n  at OpenAIClient.request (openai.js:234)\n  at CategorizationAgent.categorize (categorization.js:89)'
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 12 * 60 * 1000),
    level: 'info',
    source: 'SQL Agent',
    message: 'Consulta SQL executada com sucesso em 2.3s',
    resolved: true,
    context: {
      query: 'SELECT * FROM suppliers WHERE volume > 10000',
      executionTime: '2.3s',
      rowsReturned: 156
    }
  },
  {
    id: '5',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    level: 'warning',
    source: 'Report Agent',
    message: 'Geração de gráfico demorou mais que o esperado (18.5s)',
    resolved: true,
    context: {
      chartType: 'supplier_volume_trend',
      dataPoints: 1250,
      expectedTime: '8s',
      actualTime: '18.5s'
    }
  },
  {
    id: '6',
    timestamp: new Date(Date.now() - 20 * 60 * 1000),
    level: 'error',
    source: 'Data Lake Agent',
    message: 'Falha na sincronização com o banco de dados: conexão perdida',
    resolved: false,
    context: {
      operation: 'bulk_insert',
      recordsProcessed: 234,
      totalRecords: 567,
      connectionError: 'Connection lost to PostgreSQL server'
    },
    stack: 'DatabaseError: Connection lost\n  at PostgreSQLClient.query (pg.js:456)\n  at DataLakeAgent.syncData (datalake.js:123)'
  }
]

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Computed properties
const filteredLogs = computed(() => {
  let filtered = logs.value

  // Filter by level
  if (levelFilter.value) {
    filtered = filtered.filter(log => log.level === levelFilter.value)
  }

  // Filter by source
  if (sourceFilter.value) {
    filtered = filtered.filter(log => log.source.toLowerCase().includes(sourceFilter.value))
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(log => 
      log.message.toLowerCase().includes(query) ||
      log.source.toLowerCase().includes(query)
    )
  }

  // Sort by timestamp (most recent first)
  return filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
})

const logStats = computed(() => {
  const total = logs.value.length
  const errors = logs.value.filter(log => log.level === 'error').length
  const warnings = logs.value.filter(log => log.level === 'warning').length
  const resolved = logs.value.filter(log => log.resolved).length

  return {
    total,
    errors,
    warnings,
    resolved
  }
})

// Methods
const refreshLogs = async () => {
  isRefreshing.value = true
  try {
    // In real implementation, fetch from API
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Simulate new logs
    const newLog: ErrorLog = {
      id: Date.now().toString(),
      timestamp: new Date(),
      level: 'info',
      source: 'System',
      message: 'Logs atualizados com sucesso',
      resolved: true
    }
    logs.value.unshift(newLog)
  } finally {
    isRefreshing.value = false
  }
}

const clearLogs = () => {
  logs.value = []
}

const markAsResolved = (log: ErrorLog) => {
  log.resolved = true
}

const copyLog = async (log: ErrorLog) => {
  const logText = `[${log.timestamp.toISOString()}] ${log.level.toUpperCase()} - ${log.source}: ${log.message}`
  
  try {
    await navigator.clipboard.writeText(logText)
    // In real implementation, show toast notification
    console.log('Log copiado para a área de transferência')
  } catch (err) {
    console.error('Erro ao copiar log:', err)
  }
}

const addRealtimeLog = () => {
  // Simulate real-time logs
  const sources = ['Master Agent', 'XML Processing Agent', 'AI Categorization Agent', 'SQL Agent', 'Report Agent']
  const levels: ('info' | 'warning' | 'error')[] = ['info', 'warning', 'error']
  const messages = [
    'Tarefa executada com sucesso',
    'Processamento concluído',
    'Timeout detectado na operação',
    'Conexão com API restabelecida',
    'Cache invalidado automaticamente'
  ]

  const newLog: ErrorLog = {
    id: Date.now().toString(),
    timestamp: new Date(),
    level: levels[Math.floor(Math.random() * levels.length)],
    source: sources[Math.floor(Math.random() * sources.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    resolved: Math.random() > 0.3
  }

  logs.value.unshift(newLog)
  
  // Keep only last 100 logs
  if (logs.value.length > 100) {
    logs.value = logs.value.slice(0, 100)
  }
}

// Helper functions
const getLogClass = (level: string) => {
  switch (level) {
    case 'error': return 'bg-error/10 border-error'
    case 'warning': return 'bg-warning/10 border-warning'
    case 'info': return 'bg-info/10 border-info'
    default: return 'bg-base-100 border-base-300'
  }
}

const getLevelColor = (level: string) => {
  switch (level) {
    case 'error': return 'bg-error'
    case 'warning': return 'bg-warning'
    case 'info': return 'bg-info'
    default: return 'bg-base-300'
  }
}

const getLevelBadgeClass = (level: string) => {
  switch (level) {
    case 'error': return 'badge-error'
    case 'warning': return 'badge-warning'
    case 'info': return 'badge-info'
    default: return 'badge-ghost'
  }
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  logs.value = [...mockLogs]
  
  // Set up auto-refresh every 15 seconds
  refreshInterval = setInterval(addRealtimeLog, 15000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>