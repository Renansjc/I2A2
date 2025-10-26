<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-error">
      <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
      </svg>
      <div>
        <h3 class="font-bold">Erro ao carregar documento</h3>
        <div class="text-sm">{{ error }}</div>
      </div>
      <button class="btn btn-ghost btn-sm" @click="loadDocument">
        Tentar Novamente
      </button>
    </div>

    <!-- Document Details -->
    <div v-else-if="document" class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div>
          <div class="flex items-center space-x-3 mb-2">
            <div class="w-12 h-12 rounded-lg flex items-center justify-center"
                 :class="{
                   'bg-blue-100 text-blue-600': document.document_type === 'NFE',
                   'bg-green-100 text-green-600': document.document_type === 'NFSE',
                   'bg-gray-100 text-gray-600': !document.document_type
                 }">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
              </svg>
            </div>
            <div>
              <h1 class="text-2xl font-bold">{{ document.filename }}</h1>
              <div class="flex items-center space-x-2 text-base-content/70">
                <span class="badge badge-outline">{{ document.document_type || 'XML' }}</span>
                <span>•</span>
                <span>{{ formatFileSize(document.file_size) }}</span>
                <span>•</span>
                <span>{{ formatDate(document.upload_timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <!-- Processing Status -->
          <div 
            class="badge badge-lg"
            :class="{
              'badge-warning': document.processing_status === 'pending',
              'badge-info': document.processing_status === 'processing',
              'badge-success': document.processing_status === 'completed',
              'badge-error': document.processing_status === 'error'
            }"
          >
            {{ getStatusText(document.processing_status) }}
          </div>
          
          <!-- Actions -->
          <div class="dropdown dropdown-end">
            <div tabindex="0" role="button" class="btn btn-outline">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
              </svg>
              Ações
            </div>
            <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
              <li><a @click="viewProcessingStatus">Ver Status de Processamento</a></li>
              <li v-if="document.processing_status === 'completed'">
                <a @click="downloadResults">Baixar Resultados</a>
              </li>
              <li v-if="document.processing_status === 'error'">
                <a @click="retryProcessing">Tentar Novamente</a>
              </li>
              <li><a @click="refreshDocument">Atualizar</a></li>
              <li><a class="text-error" @click="deleteDocument">Excluir</a></li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Document Information Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Basic Information -->
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Informações Básicas</h2>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-base-content/70">ID do Documento:</span>
                <span class="font-mono text-sm">{{ document.id }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-base-content/70">Tipo:</span>
                <span>{{ document.document_type || 'XML' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-base-content/70">Tamanho:</span>
                <span>{{ formatFileSize(document.file_size) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-base-content/70">Upload:</span>
                <span>{{ formatDate(document.upload_timestamp) }}</span>
              </div>
              <div v-if="document.processing_started_at" class="flex justify-between">
                <span class="text-base-content/70">Processamento Iniciado:</span>
                <span>{{ formatDate(document.processing_started_at) }}</span>
              </div>
              <div v-if="document.processing_completed_at" class="flex justify-between">
                <span class="text-base-content/70">Processamento Concluído:</span>
                <span>{{ formatDate(document.processing_completed_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Fiscal Information -->
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Informações Fiscais</h2>
            <div class="space-y-3">
              <div v-if="document.numero_documento" class="flex justify-between">
                <span class="text-base-content/70">Número:</span>
                <span>{{ document.numero_documento }}</span>
              </div>
              <div v-if="document.serie_documento" class="flex justify-between">
                <span class="text-base-content/70">Série:</span>
                <span>{{ document.serie_documento }}</span>
              </div>
              <div v-if="document.data_emissao" class="flex justify-between">
                <span class="text-base-content/70">Data de Emissão:</span>
                <span>{{ formatDate(document.data_emissao) }}</span>
              </div>
              <div v-if="document.valor_total" class="flex justify-between">
                <span class="text-base-content/70">Valor Total:</span>
                <span class="text-success font-semibold">{{ formatCurrency(document.valor_total) }}</span>
              </div>
              <div v-if="document.valor_tributos" class="flex justify-between">
                <span class="text-base-content/70">Tributos:</span>
                <span>{{ formatCurrency(document.valor_tributos) }}</span>
              </div>
              <div v-if="document.natureza_operacao" class="flex justify-between">
                <span class="text-base-content/70">Natureza:</span>
                <span class="text-right">{{ document.natureza_operacao }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Emitter Information -->
        <div v-if="document.nome_emitente || document.cnpj_emitente" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Emitente</h2>
            <div class="space-y-3">
              <div v-if="document.nome_emitente" class="flex justify-between">
                <span class="text-base-content/70">Nome:</span>
                <span class="text-right">{{ document.nome_emitente }}</span>
              </div>
              <div v-if="document.cnpj_emitente" class="flex justify-between">
                <span class="text-base-content/70">CNPJ:</span>
                <span class="font-mono">{{ formatCNPJ(document.cnpj_emitente) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recipient Information -->
        <div v-if="document.nome_destinatario || document.cnpj_destinatario" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Destinatário</h2>
            <div class="space-y-3">
              <div v-if="document.nome_destinatario" class="flex justify-between">
                <span class="text-base-content/70">Nome:</span>
                <span class="text-right">{{ document.nome_destinatario }}</span>
              </div>
              <div v-if="document.cnpj_destinatario" class="flex justify-between">
                <span class="text-base-content/70">CNPJ:</span>
                <span class="font-mono">{{ formatCNPJ(document.cnpj_destinatario) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Information -->
      <div v-if="document.error_message" class="alert alert-error">
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
        </svg>
        <div>
          <h3 class="font-bold">Erro no Processamento</h3>
          <div class="text-sm">{{ document.error_message }}</div>
        </div>
      </div>

      <!-- Linked Documents -->
      <div v-if="document.chave_nfe || document.id_nfse" class="card bg-base-100 shadow">
        <div class="card-body">
          <h2 class="card-title">Documentos Vinculados</h2>
          <div class="space-y-3">
            <div v-if="document.chave_nfe" class="flex justify-between items-center">
              <span class="text-base-content/70">Chave NF-e:</span>
              <div class="flex items-center space-x-2">
                <span class="font-mono text-sm">{{ document.chave_nfe }}</span>
                <button class="btn btn-ghost btn-xs" @click="copyToClipboard(document.chave_nfe)">
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"></path>
                    <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div v-if="document.id_nfse" class="flex justify-between items-center">
              <span class="text-base-content/70">ID NFS-e:</span>
              <div class="flex items-center space-x-2">
                <span class="font-mono text-sm">{{ document.id_nfse }}</span>
                <button class="btn btn-ghost btn-xs" @click="copyToClipboard(document.id_nfse)">
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"></path>
                    <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Processing Status Component -->
      <div v-if="showProcessingStatus">
        <ProcessingStatus :document-id="documentId" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface DocumentDetail {
  id: string
  filename: string
  document_type: string
  processing_status: string
  upload_timestamp: string
  file_size: number
  cnpj_emitente?: string
  nome_emitente?: string
  cnpj_destinatario?: string
  nome_destinatario?: string
  numero_documento?: string
  serie_documento?: string
  data_emissao?: string
  valor_total?: number
  valor_tributos?: number
  natureza_operacao?: string
  processing_started_at?: string
  processing_completed_at?: string
  error_message?: string
  chave_nfe?: string
  id_nfse?: string
}

// Props
const props = defineProps<{
  documentId: string
}>()

// Emits
const emit = defineEmits<{
  documentDeleted: []
  processingRetried: []
}>()

// Reactive state
const document = ref<DocumentDetail | null>(null)
const isLoading = ref(false)
const error = ref<string>('')
const showProcessingStatus = ref(false)

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Load document details
const loadDocument = async () => {
  try {
    isLoading.value = true
    error.value = ''
    
    const response = await fetch(`${apiBaseUrl}/api/documents/${props.documentId}`)
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Documento não encontrado')
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    document.value = await response.json()
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Erro desconhecido'
    console.error('Error loading document:', err)
  } finally {
    isLoading.value = false
  }
}

// Actions
const refreshDocument = () => {
  loadDocument()
}

const viewProcessingStatus = () => {
  showProcessingStatus.value = !showProcessingStatus.value
}

const downloadResults = () => {
  // TODO: Implement download functionality
  console.log('Download results for:', props.documentId)
}

const retryProcessing = async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/api/documents/${props.documentId}/retry`, {
      method: 'POST'
    })
    
    if (response.ok) {
      emit('processingRetried')
      await loadDocument() // Refresh document data
      // TODO: Show success toast
    } else {
      throw new Error('Failed to retry processing')
    }
  } catch (err) {
    console.error('Error retrying processing:', err)
    // TODO: Show error toast
  }
}

const deleteDocument = async () => {
  if (!confirm('Tem certeza que deseja excluir este documento? Esta ação não pode ser desfeita.')) {
    return
  }
  
  try {
    const response = await fetch(`${apiBaseUrl}/api/documents/${props.documentId}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      emit('documentDeleted')
      navigateTo('/documents')
      // TODO: Show success toast
    } else {
      throw new Error('Failed to delete document')
    }
  } catch (err) {
    console.error('Error deleting document:', err)
    // TODO: Show error toast
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    // TODO: Show success toast
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
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
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatCNPJ = (cnpj: string): string => {
  // Format CNPJ as XX.XXX.XXX/XXXX-XX
  const cleaned = cnpj.replace(/\D/g, '')
  if (cleaned.length === 14) {
    return cleaned.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
  }
  return cnpj
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
watch(() => props.documentId, () => {
  if (props.documentId) {
    loadDocument()
  }
}, { immediate: true })

// Auto-refresh for processing documents
let refreshInterval: NodeJS.Timeout
onMounted(() => {
  refreshInterval = setInterval(() => {
    if (document.value && 
        (document.value.processing_status === 'processing' || document.value.processing_status === 'pending') &&
        !isLoading.value) {
      loadDocument()
    }
  }, 10000) // Refresh every 10 seconds for processing documents
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>