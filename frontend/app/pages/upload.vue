<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold">Enviar Arquivos XML</h1>
        <p class="text-base-content/70">Envie arquivos XML NF-e e NFS-e para processamento automático com IA</p>
        <div class="flex items-center space-x-4 mt-2 text-sm text-base-content/60">
          <span>Total processados hoje: {{ dailyStats.processed }}</span>
          <span>•</span>
          <span>Na fila: {{ processingQueue.length }}</span>
          <span>•</span>
          <span>Tempo médio: {{ dailyStats.averageTime }}</span>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <!-- View Toggle -->
        <div class="join">
          <button 
            class="join-item btn btn-sm"
            :class="{ 'btn-active': currentView === 'upload' }"
            @click="currentView = 'upload'"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
            </svg>
            Upload
          </button>
          <button 
            class="join-item btn btn-sm"
            :class="{ 'btn-active': currentView === 'documents' }"
            @click="currentView = 'documents'"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
            </svg>
            Documentos
          </button>
        </div>
        
        <!-- Help Dropdown -->
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-outline btn-sm">
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
            </svg>
            Ajuda
          </div>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-64">
            <li><a @click="showHelp('formats')">Formatos Suportados</a></li>
            <li><a @click="showHelp('guidelines')">Diretrizes de Envio</a></li>
            <li><a @click="showHelp('troubleshooting')">Solução de Problemas</a></li>
            <li><a @click="showHelp('agents')">Como Funcionam os Agentes IA</a></li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Upload Instructions -->
    <div v-if="currentView === 'upload'" class="alert alert-info">
      <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
      </svg>
      <div>
        <h3 class="font-bold">Processamento Inteligente com IA</h3>
        <div class="text-sm">
          • <strong>Formatos:</strong> XML NF-e e NFS-e (máximo 10MB por arquivo)<br>
          • <strong>Agentes IA:</strong> Processamento automático, categorização e análise semântica<br>
          • <strong>Tempo:</strong> 2-5 minutos por arquivo com insights executivos<br>
          • <strong>Resultados:</strong> Dados estruturados, relatórios e recomendações de negócio
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div v-if="currentView === 'upload'" class="space-y-6">
      <!-- File Upload Component -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h2 class="card-title mb-4">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
            </svg>
            Envio de Arquivos
          </h2>
          <FileUpload 
            @document-uploaded="handleDocumentUploaded"
            @upload-complete="handleUploadComplete"
            @upload-error="handleUploadError"
          />
        </div>
      </div>
    </div>

    <!-- Document Management View -->
    <div v-else-if="currentView === 'documents'" class="space-y-6">
      <DocumentList 
        @document-selected="handleDocumentSelected"
        @upload-requested="currentView = 'upload'"
      />
    </div>

    <!-- Real-time Processing Monitor -->
    <div v-if="currentView === 'upload'">
      <ProcessingMonitor />
    </div>

    <!-- Recent Activity and Quick Stats -->
    <div v-if="currentView === 'upload'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Quick Stats -->
      <div class="card bg-base-100 shadow">
        <div class="card-body">
          <h3 class="card-title text-base">Estatísticas Hoje</h3>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-base-content/70">Processados:</span>
              <span class="font-semibold">{{ dailyStats.processed }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/70">Sucesso:</span>
              <span class="text-success">{{ dailyStats.successful }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/70">Tempo médio:</span>
              <span>{{ dailyStats.averageTime }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card bg-base-100 shadow lg:col-span-2">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title text-base">Atividade Recente</h3>
            <button class="btn btn-ghost btn-sm" @click="loadRecentActivity">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
          
          <div v-if="recentActivity.length === 0" class="text-center py-4 text-base-content/50">
            Nenhuma atividade recente
          </div>
          
          <div v-else class="space-y-2">
            <div
              v-for="activity in recentActivity.slice(0, 5)"
              :key="activity.id"
              class="flex items-center space-x-3 p-2 hover:bg-base-200 rounded cursor-pointer"
              @click="viewDocumentDetails(activity.documentId)"
            >
              <div class="w-2 h-2 rounded-full"
                   :class="{
                     'bg-green-500': activity.type === 'completed',
                     'bg-blue-500': activity.type === 'processing',
                     'bg-red-500': activity.type === 'error',
                     'bg-yellow-500': activity.type === 'uploaded'
                   }"></div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">{{ activity.message }}</p>
                <p class="text-xs text-base-content/50">{{ formatRelativeTime(activity.timestamp) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Help Modal -->
    <div v-if="showHelpModal" class="modal modal-open">
      <div class="modal-box max-w-2xl">
        <h3 class="font-bold text-lg mb-4">{{ helpContent.title }}</h3>
        <div class="prose max-w-none" v-html="helpContent.content"></div>
        <div class="modal-action">
          <button class="btn" @click="showHelpModal = false">Fechar</button>
        </div>
      </div>
      <div class="modal-backdrop" @click="showHelpModal = false"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

definePageMeta({
  layout: 'default'
})

interface QueueItem {
  id: string
  filename: string
  type: string
  size: string
  status: string
  progress: number
  currentStep?: string
  estimatedTime?: string
  emitente?: string
  agentStatuses?: Array<{
    name: string
    displayName: string
    status: string
  }>
}

interface ActivityItem {
  id: string
  documentId: string
  type: string
  message: string
  timestamp: Date
}

interface DailyStats {
  processed: number
  successful: number
  averageTime: string
}

interface HelpContent {
  title: string
  content: string
}

// Reactive state
const currentView = ref<'upload' | 'documents'>('upload')
const processingQueue = ref<QueueItem[]>([])
const recentActivity = ref<ActivityItem[]>([])
const isRefreshing = ref(false)
const showHelpModal = ref(false)
const helpContent = ref<HelpContent>({ title: '', content: '' })

// Daily stats
const dailyStats = ref<DailyStats>({
  processed: 0,
  successful: 0,
  averageTime: '0s'
})

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Computed properties
const queueStats = computed(() => {
  const processing = processingQueue.value.filter(item => 
    item.status === 'processing' || item.status === 'pending'
  ).length
  const completed = processingQueue.value.filter(item => 
    item.status === 'completed'
  ).length
  
  return { processing, completed }
})

// Event handlers
const handleDocumentUploaded = (documentId: string, filename: string) => {
  // Add to processing queue
  const queueItem: QueueItem = {
    id: documentId,
    filename,
    type: getDocumentType(filename),
    size: 'Calculando...',
    status: 'pending',
    progress: 0,
    currentStep: 'Iniciando processamento...',
    estimatedTime: '2-5 min',
    agentStatuses: [
      { name: 'xml_processing_agent', displayName: 'XML', status: 'pending' },
      { name: 'ai_categorization_agent', displayName: 'IA', status: 'pending' },
      { name: 'sql_agent', displayName: 'SQL', status: 'pending' },
      { name: 'report_agent', displayName: 'Relatório', status: 'pending' }
    ]
  }
  
  processingQueue.value.unshift(queueItem)
  
  // Add to recent activity
  addActivity({
    documentId,
    type: 'uploaded',
    message: `Arquivo ${filename} enviado para processamento`
  })
  
  // Start monitoring this document
  monitorDocument(documentId)
}

const handleUploadComplete = (results: any[]) => {
  // Update daily stats
  dailyStats.value.processed += results.filter(r => r.status === 'success').length
  dailyStats.value.successful += results.filter(r => r.status === 'success').length
}

const handleUploadError = (error: string) => {
  addActivity({
    documentId: 'error',
    type: 'error',
    message: `Erro no upload: ${error}`
  })
}

const handleDocumentSelected = (documentId: string) => {
  navigateTo(`/documents/${documentId}`)
}

// Queue management
const refreshQueue = async () => {
  try {
    isRefreshing.value = true
    
    // Load recent documents with processing status
    const response = await fetch(`${apiBaseUrl}/api/documents?limit=20&status_filter=processing,pending`)
    
    if (response.ok) {
      const data = await response.json()
      
      // Update processing queue with real data
      processingQueue.value = data.documents.map((doc: any) => ({
        id: doc.id,
        filename: doc.filename,
        type: doc.document_type || 'XML',
        size: formatFileSize(doc.file_size),
        status: doc.processing_status,
        progress: calculateProgress(doc.processing_status),
        currentStep: getProcessingStep(doc.processing_status),
        estimatedTime: getEstimatedTime(doc.processing_status),
        emitente: doc.nome_emitente,
        agentStatuses: [] // TODO: Load from status endpoint
      }))
    }
  } catch (error) {
    console.error('Error refreshing queue:', error)
  } finally {
    isRefreshing.value = false
  }
}

const monitorDocument = async (documentId: string) => {
  // Monitor document processing status
  const checkStatus = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}/status`)
      if (response.ok) {
        const status = await response.json()
        updateQueueItem(documentId, status)
        
        // Continue monitoring if still processing
        if (status.overall_status === 'processing' || status.overall_status === 'pending') {
          setTimeout(checkStatus, 5000) // Check every 5 seconds
        } else {
          // Processing completed
          addActivity({
            documentId,
            type: status.overall_status === 'completed' ? 'completed' : 'error',
            message: `Processamento ${status.overall_status === 'completed' ? 'concluído' : 'falhou'} para ${getQueueItem(documentId)?.filename}`
          })
        }
      }
    } catch (error) {
      console.error('Error monitoring document:', error)
    }
  }
  
  // Start monitoring after a short delay
  setTimeout(checkStatus, 2000)
}

const updateQueueItem = (documentId: string, status: any) => {
  const item = processingQueue.value.find(item => item.id === documentId)
  if (item) {
    item.status = status.overall_status
    item.progress = calculateProgressFromStatus(status)
    item.currentStep = getCurrentStepFromStatus(status)
    
    // Update agent statuses
    if (status.agent_statuses) {
      item.agentStatuses = status.agent_statuses.map((agent: any) => ({
        name: agent.agent_name,
        displayName: getAgentDisplayName(agent.agent_name),
        status: agent.status
      }))
    }
  }
}

const getQueueItem = (documentId: string) => {
  return processingQueue.value.find(item => item.id === documentId)
}

// Navigation
const viewDocumentDetails = (documentId: string) => {
  navigateTo(`/documents/${documentId}`)
}

// Activity management
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

const loadRecentActivity = async () => {
  // TODO: Load from API
  console.log('Loading recent activity...')
}

// Help system
const showHelp = (topic: string) => {
  const helpTopics: Record<string, HelpContent> = {
    formats: {
      title: 'Formatos Suportados',
      content: `
        <h4>Tipos de Arquivo Aceitos:</h4>
        <ul>
          <li><strong>NF-e (Nota Fiscal Eletrônica):</strong> Arquivos XML de notas fiscais eletrônicas</li>
          <li><strong>NFS-e (Nota Fiscal de Serviços Eletrônica):</strong> Arquivos XML de notas fiscais de serviços</li>
          <li><strong>RPS (Recibo Provisório de Serviços):</strong> Arquivos XML de recibos provisórios</li>
        </ul>
        <h4>Limitações:</h4>
        <ul>
          <li>Tamanho máximo: 10MB por arquivo</li>
          <li>Formato: Apenas arquivos .xml</li>
          <li>Codificação: UTF-8 recomendada</li>
        </ul>
      `
    },
    guidelines: {
      title: 'Diretrizes de Envio',
      content: `
        <h4>Melhores Práticas:</h4>
        <ul>
          <li>Verifique se os arquivos XML estão válidos antes do envio</li>
          <li>Envie arquivos em lotes pequenos para melhor performance</li>
          <li>Aguarde o processamento completo antes de enviar novos lotes</li>
          <li>Mantenha nomes de arquivo descritivos</li>
        </ul>
        <h4>Processamento:</h4>
        <ul>
          <li>Tempo médio: 2-5 minutos por arquivo</li>
          <li>Processamento automático com 4 agentes IA</li>
          <li>Resultados disponíveis em tempo real</li>
        </ul>
      `
    },
    troubleshooting: {
      title: 'Solução de Problemas',
      content: `
        <h4>Problemas Comuns:</h4>
        <ul>
          <li><strong>Arquivo muito grande:</strong> Reduza o tamanho ou divida em partes menores</li>
          <li><strong>Formato inválido:</strong> Verifique se é um arquivo XML válido</li>
          <li><strong>Erro de processamento:</strong> Verifique se o XML contém dados fiscais válidos</li>
          <li><strong>Upload lento:</strong> Verifique sua conexão de internet</li>
        </ul>
        <h4>Suporte:</h4>
        <p>Se o problema persistir, entre em contato com o suporte técnico.</p>
      `
    },
    agents: {
      title: 'Como Funcionam os Agentes IA',
      content: `
        <h4>Pipeline de Processamento:</h4>
        <ol>
          <li><strong>Processamento XML:</strong> Análise semântica e extração de dados</li>
          <li><strong>Categorização IA:</strong> Classificação inteligente de produtos e serviços</li>
          <li><strong>Agente SQL:</strong> Armazenamento estruturado dos dados</li>
          <li><strong>Geração de Relatórios:</strong> Insights executivos e recomendações</li>
        </ol>
        <h4>Benefícios:</h4>
        <ul>
          <li>Processamento automático e inteligente</li>
          <li>Detecção de anomalias e padrões</li>
          <li>Insights de negócio em tempo real</li>
          <li>Relatórios executivos personalizados</li>
        </ul>
      `
    }
  }
  
  helpContent.value = helpTopics[topic] || { title: 'Ajuda', content: 'Tópico não encontrado.' }
  showHelpModal.value = true
}

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatRelativeTime = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Agora mesmo'
  if (minutes < 60) return `há ${minutes}m`
  if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`
  return date.toLocaleDateString('pt-BR')
}

const getDocumentType = (filename: string): string => {
  const name = filename.toLowerCase()
  if (name.includes('nfe') || name.includes('nf-e')) return 'NF-e'
  if (name.includes('nfse') || name.includes('nfs-e') || name.includes('rps')) return 'NFS-e'
  return 'XML'
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': 'Pendente',
    'processing': 'Processando',
    'completed': 'Concluído',
    'error': 'Erro',
    'failed': 'Falhou',
    'queued': 'Na Fila'
  }
  return statusMap[status] || status
}

const getStatusDescription = (status: string): string => {
  const descriptions: Record<string, string> = {
    'pending': 'Aguardando início do processamento...',
    'processing': 'Sendo processado pelos agentes IA...',
    'completed': 'Processamento concluído com sucesso',
    'error': 'Erro durante o processamento',
    'failed': 'Processamento falhou',
    'queued': 'Na fila de processamento...'
  }
  return descriptions[status] || 'Status desconhecido'
}

const calculateProgress = (status: string): number => {
  const progressMap: Record<string, number> = {
    'pending': 0,
    'processing': 50,
    'completed': 100,
    'error': 0,
    'failed': 0
  }
  return progressMap[status] || 0
}

const calculateProgressFromStatus = (status: any): number => {
  if (status.overall_status === 'completed') return 100
  if (status.overall_status === 'error' || status.overall_status === 'failed') return 0
  
  // Calculate based on agent completion
  const totalAgents = status.agent_statuses?.length || 4
  const completedAgents = status.agent_statuses?.filter((a: any) => a.status === 'completed').length || 0
  
  return Math.round((completedAgents / totalAgents) * 100)
}

const getCurrentStepFromStatus = (status: any): string => {
  const inProgressAgent = status.agent_statuses?.find((a: any) => a.status === 'in_progress')
  if (inProgressAgent) {
    return `${getAgentDisplayName(inProgressAgent.agent_name)} em andamento...`
  }
  
  const pendingAgent = status.agent_statuses?.find((a: any) => a.status === 'pending')
  if (pendingAgent) {
    return `Aguardando ${getAgentDisplayName(pendingAgent.agent_name)}...`
  }
  
  return getStatusDescription(status.overall_status)
}

const getProcessingStep = (status: string): string => {
  return getStatusDescription(status)
}

const getEstimatedTime = (status: string): string => {
  if (status === 'completed') return 'Concluído'
  if (status === 'error' || status === 'failed') return 'Falhou'
  if (status === 'processing') return '1-3 min restantes'
  return '2-5 min estimados'
}

const getAgentDisplayName = (agentName: string): string => {
  const agentMap: Record<string, string> = {
    'xml_processing_agent': 'Processamento XML',
    'ai_categorization_agent': 'Categorização IA',
    'sql_agent': 'Agente SQL',
    'report_agent': 'Geração de Relatórios'
  }
  return agentMap[agentName] || agentName
}

// Lifecycle
onMounted(() => {
  refreshQueue()
  loadRecentActivity()
  
  // Load daily stats
  dailyStats.value = {
    processed: 12,
    successful: 11,
    averageTime: '3.2min'
  }
})

// Auto-refresh queue every 30 seconds
let refreshInterval: NodeJS.Timeout
onMounted(() => {
  refreshInterval = setInterval(() => {
    if (!isRefreshing.value && processingQueue.value.some(item => 
      item.status === 'processing' || item.status === 'pending'
    )) {
      refreshQueue()
    }
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>