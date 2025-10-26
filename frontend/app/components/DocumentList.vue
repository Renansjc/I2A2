<template>
  <div class="space-y-4">
    <!-- Header with filters and search -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h3 class="text-lg font-semibold">Documentos Fiscais</h3>
        <p class="text-sm text-base-content/70">
          {{ totalCount }} documento(s) encontrado(s)
        </p>
      </div>
      
      <div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
        <!-- Search -->
        <div class="join">
          <input 
            v-model="searchQuery"
            class="input input-bordered input-sm join-item w-full sm:w-64" 
            placeholder="Buscar por nome, CNPJ..."
            @input="debouncedSearch"
          />
          <button class="btn btn-sm join-item">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
        
        <!-- Status Filter -->
        <select 
          v-model="statusFilter" 
          class="select select-bordered select-sm"
          @change="loadDocuments"
        >
          <option value="">Todos os Status</option>
          <option value="pending">Pendente</option>
          <option value="processing">Processando</option>
          <option value="completed">Concluído</option>
          <option value="error">Erro</option>
        </select>
        
        <!-- Document Type Filter -->
        <select 
          v-model="typeFilter" 
          class="select select-bordered select-sm"
          @change="loadDocuments"
        >
          <option value="">Todos os Tipos</option>
          <option value="NFE">NF-e</option>
          <option value="NFSE">NFS-e</option>
        </select>
        
        <!-- Refresh Button -->
        <button 
          class="btn btn-sm btn-ghost"
          :disabled="isLoading"
          @click="refreshDocuments"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': isLoading }" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
          </svg>
          Atualizar
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && documents.length === 0" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Empty State -->
    <div v-else-if="!isLoading && documents.length === 0" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
      </svg>
      <h3 class="text-lg font-semibold mb-2">Nenhum documento encontrado</h3>
      <p class="text-base-content/70 mb-4">
        {{ searchQuery || statusFilter || typeFilter ? 'Tente ajustar os filtros de busca' : 'Faça upload de arquivos XML para começar' }}
      </p>
      <button v-if="!searchQuery && !statusFilter && !typeFilter" class="btn btn-primary" @click="$emit('uploadRequested')">
        <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
        </svg>
        Fazer Upload
      </button>
    </div>

    <!-- Document List -->
    <div v-else class="space-y-3">
      <div
        v-for="document in documents"
        :key="document.id"
        class="card bg-base-100 shadow hover:shadow-md transition-shadow cursor-pointer"
        @click="viewDocument(document.id)"
      >
        <div class="card-body p-4">
          <div class="flex items-start justify-between">
            <!-- Document Info -->
            <div class="flex items-start space-x-3 flex-1 min-w-0">
              <!-- Document Type Icon -->
              <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                   :class="{
                     'bg-blue-100 text-blue-600': document.document_type === 'NFE',
                     'bg-green-100 text-green-600': document.document_type === 'NFSE',
                     'bg-gray-100 text-gray-600': !document.document_type
                   }">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
                </svg>
              </div>
              
              <!-- Document Details -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center space-x-2 mb-1">
                  <h4 class="font-semibold truncate">{{ document.filename }}</h4>
                  <div class="badge badge-outline badge-sm">{{ document.document_type || 'XML' }}</div>
                </div>
                
                <div class="text-sm text-base-content/70 space-y-1">
                  <div class="flex items-center space-x-4">
                    <span>{{ formatFileSize(document.file_size) }}</span>
                    <span>{{ formatDate(document.upload_timestamp) }}</span>
                  </div>
                  
                  <div v-if="document.nome_emitente" class="flex items-center space-x-2">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="truncate">{{ document.nome_emitente }}</span>
                  </div>
                  
                  <div v-if="document.valor_total" class="flex items-center space-x-2 text-success">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"></path>
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"></path>
                    </svg>
                    <span>{{ formatCurrency(document.valor_total) }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Status and Actions -->
            <div class="flex items-center space-x-3 flex-shrink-0">
              <!-- Processing Status -->
              <div class="text-right">
                <div 
                  class="badge"
                  :class="{
                    'badge-warning': document.processing_status === 'pending',
                    'badge-info': document.processing_status === 'processing',
                    'badge-success': document.processing_status === 'completed',
                    'badge-error': document.processing_status === 'error'
                  }"
                >
                  {{ getStatusText(document.processing_status) }}
                </div>
                <div class="text-xs text-base-content/50 mt-1">
                  ID: {{ document.id.slice(0, 8) }}...
                </div>
              </div>
              
              <!-- Actions Menu -->
              <div class="dropdown dropdown-end">
                <div tabindex="0" role="button" class="btn btn-ghost btn-sm" @click.stop>
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                  </svg>
                </div>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                  <li><a @click.stop="viewDocument(document.id)">Ver Detalhes</a></li>
                  <li><a @click.stop="viewProcessingStatus(document.id)">Status de Processamento</a></li>
                  <li v-if="document.processing_status === 'completed'">
                    <a @click.stop="downloadResults(document.id)">Baixar Resultados</a>
                  </li>
                  <li v-if="document.processing_status === 'error'">
                    <a @click.stop="retryProcessing(document.id)">Tentar Novamente</a>
                  </li>
                  <li><a class="text-error" @click.stop="deleteDocument(document.id)">Excluir</a></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalCount > pageSize" class="flex justify-center">
      <div class="join">
        <button 
          class="join-item btn btn-sm"
          :disabled="currentPage === 1 || isLoading"
          @click="goToPage(currentPage - 1)"
        >
          «
        </button>
        
        <button 
          v-for="page in visiblePages"
          :key="page"
          class="join-item btn btn-sm"
          :class="{ 'btn-active': page === currentPage }"
          :disabled="isLoading"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        
        <button 
          class="join-item btn btn-sm"
          :disabled="!hasNextPage || isLoading"
          @click="goToPage(currentPage + 1)"
        >
          »
        </button>
      </div>
    </div>

    <!-- Loading overlay for refresh -->
    <div v-if="isLoading && documents.length > 0" class="absolute inset-0 bg-base-100/50 flex items-center justify-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface DocumentItem {
  id: string
  filename: string
  document_type: string
  processing_status: string
  upload_timestamp: string
  file_size: number
  nome_emitente?: string
  valor_total?: number
  data_emissao?: string
}

interface DocumentListResponse {
  documents: DocumentItem[]
  total_count: number
  page: number
  page_size: number
  has_next: boolean
}

// Props and emits
const emit = defineEmits<{
  documentSelected: [documentId: string]
  uploadRequested: []
}>()

// Reactive state
const documents = ref<DocumentItem[]>([])
const isLoading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const hasNextPage = ref(false)

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Computed properties
const visiblePages = computed(() => {
  const totalPages = Math.ceil(totalCount.value / pageSize.value)
  const current = currentPage.value
  const pages: number[] = []
  
  // Show up to 5 pages around current page
  const start = Math.max(1, current - 2)
  const end = Math.min(totalPages, current + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Debounced search
let searchTimeout: NodeJS.Timeout
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadDocuments()
  }, 500)
}

// Load documents from API
const loadDocuments = async () => {
  try {
    isLoading.value = true
    
    const params = new URLSearchParams({
      skip: ((currentPage.value - 1) * pageSize.value).toString(),
      limit: pageSize.value.toString()
    })
    
    if (statusFilter.value) {
      params.append('status_filter', statusFilter.value)
    }
    
    if (typeFilter.value) {
      params.append('document_type_filter', typeFilter.value)
    }
    
    if (searchQuery.value.trim()) {
      params.append('search', searchQuery.value.trim())
    }
    
    const response = await fetch(`${apiBaseUrl}/api/documents?${params}`)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data: DocumentListResponse = await response.json()
    
    documents.value = data.documents
    totalCount.value = data.total_count
    hasNextPage.value = data.has_next
    
  } catch (error) {
    console.error('Error loading documents:', error)
    // TODO: Show error toast/notification
  } finally {
    isLoading.value = false
  }
}

// Refresh documents
const refreshDocuments = () => {
  loadDocuments()
}

// Navigation
const goToPage = (page: number) => {
  currentPage.value = page
  loadDocuments()
}

const viewDocument = (documentId: string) => {
  emit('documentSelected', documentId)
  navigateTo(`/documents/${documentId}`)
}

const viewProcessingStatus = (documentId: string) => {
  navigateTo(`/documents/${documentId}/status`)
}

// Actions
const downloadResults = (documentId: string) => {
  // TODO: Implement download functionality
  console.log('Download results for:', documentId)
}

const retryProcessing = async (documentId: string) => {
  // TODO: Implement retry functionality
  console.log('Retry processing for:', documentId)
}

const deleteDocument = async (documentId: string) => {
  if (!confirm('Tem certeza que deseja excluir este documento?')) {
    return
  }
  
  try {
    const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      // Remove from local list
      documents.value = documents.value.filter(d => d.id !== documentId)
      totalCount.value--
      // TODO: Show success toast
    } else {
      throw new Error('Failed to delete document')
    }
  } catch (error) {
    console.error('Error deleting document:', error)
    // TODO: Show error toast
  }
}

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': 'Pendente',
    'processing': 'Processando',
    'completed': 'Concluído',
    'error': 'Erro'
  }
  return statusMap[status] || status
}

// Watchers
watch([statusFilter, typeFilter], () => {
  currentPage.value = 1
  loadDocuments()
})

// Lifecycle
onMounted(() => {
  loadDocuments()
})

// Auto-refresh every 30 seconds for processing documents
let refreshInterval: NodeJS.Timeout
onMounted(() => {
  refreshInterval = setInterval(() => {
    const hasProcessingDocs = documents.value.some(d => 
      d.processing_status === 'processing' || d.processing_status === 'pending'
    )
    if (hasProcessingDocs && !isLoading.value) {
      loadDocuments()
    }
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>