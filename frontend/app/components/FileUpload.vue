<template>
  <div class="space-y-4">
    <!-- Drag and Drop Area -->
    <div
      class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
      :class="{
        'border-primary bg-primary/10': isDragOver,
        'border-base-300 hover:border-primary/50': !isDragOver,
        'border-error bg-error/10': hasError
      }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <div class="space-y-4">
        <div class="mx-auto w-16 h-16 text-base-content/50">
          <svg fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
          </svg>
        </div>
        
        <div>
          <h3 class="text-lg font-semibold">Enviar Arquivos XML</h3>
          <p class="text-base-content/70">
            Arraste e solte seus arquivos XML NF-e ou NFS-e aqui, ou clique para navegar
          </p>
          <p class="text-sm text-base-content/50 mt-2">
            Máximo: 10MB por arquivo • Processamento automático com IA
          </p>
        </div>
        
        <div class="space-y-2">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".xml"
            class="hidden"
            @change="handleFileSelect"
          />
          <button
            class="btn btn-primary"
            :disabled="isUploading"
            @click="$refs.fileInput?.click()"
          >
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8 4a3 3 0 00-6 0v4a5 5 0 0010 0V4a3 3 0 00-6 0v4a1 1 0 102 0V4a1 1 0 10-2 0v4a3 3 0 106 0V4a5 5 0 00-10 0z" clip-rule="evenodd"></path>
            </svg>
            {{ isUploading ? 'Processando...' : 'Escolher Arquivos' }}
          </button>
          <p class="text-sm text-base-content/50">
            Formatos suportados: .xml (NF-e, NFS-e)
          </p>
        </div>
      </div>
    </div>

    <!-- File List -->
    <div v-if="files.length > 0" class="space-y-3">
      <div class="flex justify-between items-center">
        <h4 class="font-semibold">Arquivos Selecionados ({{ files.length }})</h4>
        <div class="text-sm text-base-content/60">
          Total: {{ formatFileSize(totalFileSize) }}
        </div>
      </div>
      
      <div class="space-y-2">
        <div
          v-for="(file, index) in files"
          :key="file.id || index"
          class="flex items-center justify-between p-3 bg-base-200 rounded-lg transition-all"
          :class="{
            'border-l-4 border-success': file.status === 'completed',
            'border-l-4 border-error': file.status === 'error',
            'border-l-4 border-warning': file.status === 'uploading'
          }"
        >
          <div class="flex items-center space-x-3 flex-1">
            <div class="w-8 h-8 bg-primary/20 rounded flex items-center justify-center">
              <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
              </svg>
            </div>
            
            <div class="flex-1 min-w-0">
              <p class="font-medium truncate">{{ file.name }}</p>
              <div class="flex items-center space-x-2 text-sm text-base-content/70">
                <span>{{ formatFileSize(file.size) }}</span>
                <span>•</span>
                <span>{{ getFileType(file.name) }}</span>
                <span v-if="file.metadata?.nome_emitente" class="text-primary">
                  • {{ file.metadata.nome_emitente }}
                </span>
              </div>
              <div v-if="file.metadata?.valor_total" class="text-sm text-success">
                Valor: {{ formatCurrency(file.metadata.valor_total) }}
              </div>
            </div>
          </div>
          
          <div class="flex items-center space-x-3">
            <!-- Upload Progress -->
            <div
              v-if="file.status === 'uploading'"
              class="flex items-center space-x-2"
            >
              <div class="radial-progress text-primary" :style="`--value:${file.progress}`" role="progressbar">
                <span class="text-xs">{{ file.progress }}%</span>
              </div>
              <span class="text-sm text-base-content/70">{{ file.currentStep || 'Enviando...' }}</span>
            </div>
            
            <!-- Completed Status -->
            <div
              v-else-if="file.status === 'completed'"
              class="flex items-center space-x-2 text-success"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              <div class="text-right">
                <div class="text-sm font-medium">Processando</div>
                <div class="text-xs text-base-content/50">ID: {{ file.documentId?.slice(0, 8) }}...</div>
              </div>
            </div>
            
            <!-- Error Status -->
            <div
              v-else-if="file.status === 'error'"
              class="flex items-center space-x-2 text-error"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
              </svg>
              <div class="text-right">
                <div class="text-sm font-medium">Erro</div>
                <div class="text-xs text-base-content/50" :title="file.errorMessage">
                  {{ file.errorMessage?.slice(0, 30) }}...
                </div>
              </div>
            </div>
            
            <!-- Remove Button -->
            <button
              class="btn btn-ghost btn-sm"
              :disabled="file.status === 'uploading'"
              @click="removeFile(index)"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Upload Actions -->
      <div class="flex justify-between items-center pt-4">
        <div class="flex items-center space-x-2">
          <button
            class="btn btn-ghost"
            :disabled="isUploading"
            @click="clearFiles"
          >
            Limpar Tudo
          </button>
          <div v-if="uploadStats.total > 0" class="text-sm text-base-content/60">
            {{ uploadStats.completed }}/{{ uploadStats.total }} concluídos
          </div>
        </div>
        
        <div class="space-x-2">
          <button
            class="btn btn-secondary"
            :disabled="files.length === 0 || isUploading"
            @click="validateFiles"
          >
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
            Validar XML
          </button>
          <button
            class="btn btn-primary"
            :disabled="files.length === 0 || isUploading || hasActiveUploads"
            @click="uploadFiles"
          >
            <span v-if="isUploading" class="loading loading-spinner loading-sm mr-2"></span>
            <svg v-else class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
            </svg>
            {{ isUploading ? 'Enviando...' : 'Enviar Arquivos' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Results -->
    <div v-if="uploadResults.length > 0" class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h4 class="card-title">Resultados do Envio</h4>
          <button 
            class="btn btn-ghost btn-sm"
            @click="clearResults"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Limpar
          </button>
        </div>
        <div class="space-y-2">
          <div
            v-for="result in uploadResults"
            :key="result.filename"
            class="alert"
            :class="{
              'alert-success': result.status === 'success',
              'alert-error': result.status === 'error',
              'alert-warning': result.status === 'warning',
              'alert-info': result.status === 'info'
            }"
          >
            <div class="flex-1">
              <div class="flex justify-between items-start">
                <h5 class="font-semibold">{{ result.filename }}</h5>
                <div v-if="result.documentId" class="text-xs text-base-content/50">
                  ID: {{ result.documentId.slice(0, 8) }}...
                </div>
              </div>
              <p class="text-sm">{{ result.message }}</p>
              <div v-if="result.metadata" class="text-xs text-base-content/60 mt-1">
                <span v-if="result.metadata.nome_emitente">{{ result.metadata.nome_emitente }}</span>
                <span v-if="result.metadata.valor_total"> • {{ formatCurrency(result.metadata.valor_total) }}</span>
              </div>
            </div>
            <div v-if="result.documentId" class="flex space-x-2">
              <button 
                class="btn btn-ghost btn-xs"
                @click="viewDocument(result.documentId)"
              >
                Ver Detalhes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="hasError" class="alert alert-error">
      <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
      </svg>
      <div>
        <h3 class="font-bold">Erro no Upload</h3>
        <div class="text-sm">{{ errorMessage }}</div>
      </div>
      <button class="btn btn-ghost btn-sm" @click="clearError">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface FileMetadata {
  nome_emitente?: string
  cnpj_emitente?: string
  numero_documento?: string
  data_emissao?: string
  valor_total?: number
  document_type?: string
}

interface FileItem {
  id?: string
  name: string
  size: number
  file: File
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress: number
  documentId?: string
  currentStep?: string
  errorMessage?: string
  metadata?: FileMetadata
}

interface UploadResult {
  filename: string
  status: 'success' | 'error' | 'warning' | 'info'
  message: string
  documentId?: string
  metadata?: FileMetadata
}

interface UploadStats {
  total: number
  completed: number
  failed: number
  uploading: number
}

// Props and emits
const emit = defineEmits<{
  documentUploaded: [documentId: string, filename: string]
  uploadComplete: [results: UploadResult[]]
  uploadError: [error: string]
}>()

// Reactive state
const files = ref<FileItem[]>([])
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadResults = ref<UploadResult[]>([])
const errorMessage = ref<string>('')
const hasError = ref(false)

// Runtime config for API base URL
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Computed properties
const totalFileSize = computed(() => {
  return files.value.reduce((total, file) => total + file.size, 0)
})

const uploadStats = computed((): UploadStats => {
  const total = files.value.length
  const completed = files.value.filter(f => f.status === 'completed').length
  const failed = files.value.filter(f => f.status === 'error').length
  const uploading = files.value.filter(f => f.status === 'uploading').length
  
  return { total, completed, failed, uploading }
})

const hasActiveUploads = computed(() => {
  return files.value.some(f => f.status === 'uploading')
})

// Drag and drop handlers
const handleDragOver = (e: DragEvent) => {
  isDragOver.value = true
}

const handleDragLeave = (e: DragEvent) => {
  isDragOver.value = false
}

const handleDrop = (e: DragEvent) => {
  isDragOver.value = false
  const droppedFiles = Array.from(e.dataTransfer?.files || [])
  addFiles(droppedFiles)
}

// File selection handler
const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  const selectedFiles = Array.from(target.files || [])
  addFiles(selectedFiles)
  // Clear the input so the same file can be selected again
  if (target) target.value = ''
}

// Add files to the list
const addFiles = (newFiles: File[]) => {
  clearError()
  
  const xmlFiles = newFiles.filter(file => 
    file.name.toLowerCase().endsWith('.xml')
  )
  
  // Check for non-XML files
  const nonXmlFiles = newFiles.filter(file => 
    !file.name.toLowerCase().endsWith('.xml')
  )
  
  if (nonXmlFiles.length > 0) {
    showError(`${nonXmlFiles.length} arquivo(s) ignorado(s). Apenas arquivos XML são aceitos.`)
  }
  
  // Check file size limit (10MB)
  const maxSize = 10 * 1024 * 1024 // 10MB
  const oversizedFiles = xmlFiles.filter(file => file.size > maxSize)
  
  if (oversizedFiles.length > 0) {
    showError(`${oversizedFiles.length} arquivo(s) muito grande(s). Máximo permitido: 10MB.`)
    return
  }
  
  xmlFiles.forEach(file => {
    // Check if file already exists (by name and size)
    const existingFile = files.value.find(f => f.name === file.name && f.size === file.size)
    if (!existingFile) {
      files.value.push({
        id: generateFileId(),
        name: file.name,
        size: file.size,
        file,
        status: 'pending',
        progress: 0
      })
    }
  })
  
  // Auto-validate new files
  if (xmlFiles.length > 0) {
    setTimeout(() => validateFiles(), 100)
  }
}

// Remove file from list
const removeFile = (index: number) => {
  const file = files.value[index]
  if (file.status === 'uploading') {
    // TODO: Cancel upload if possible
    return
  }
  files.value.splice(index, 1)
}

// Clear all files
const clearFiles = () => {
  // Only clear files that are not currently uploading
  files.value = files.value.filter(f => f.status === 'uploading')
  if (files.value.length === 0) {
    uploadResults.value = []
  }
  clearError()
}

// Clear upload results
const clearResults = () => {
  uploadResults.value = []
}

// Error handling
const showError = (message: string) => {
  errorMessage.value = message
  hasError.value = true
}

const clearError = () => {
  errorMessage.value = ''
  hasError.value = false
}

// Generate unique file ID
const generateFileId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

// Validate XML files
const validateFiles = async () => {
  clearError()
  uploadResults.value = []
  
  for (const fileItem of files.value) {
    try {
      const text = await fileItem.file.text()
      
      // Basic XML validation
      if (!text.includes('<?xml') || !text.includes('<')) {
        uploadResults.value.push({
          filename: fileItem.name,
          status: 'error',
          message: 'Formato XML inválido - não é um arquivo XML válido'
        })
        continue
      }
      
      // Check for NF-e or NFS-e indicators
      const isNFe = text.includes('NFe') || text.includes('nfeProc') || text.includes('infNFe')
      const isNFSe = text.includes('NFSe') || text.includes('nfse') || text.includes('RPS')
      
      // Extract basic metadata for preview
      const metadata: FileMetadata = {}
      
      if (isNFe) {
        // Try to extract basic NF-e info
        const emitMatch = text.match(/<xNome[^>]*>([^<]+)<\/xNome>/)
        if (emitMatch) metadata.nome_emitente = emitMatch[1]
        
        const cnpjMatch = text.match(/<CNPJ[^>]*>([^<]+)<\/CNPJ>/)
        if (cnpjMatch) metadata.cnpj_emitente = cnpjMatch[1]
        
        const valorMatch = text.match(/<vNF[^>]*>([^<]+)<\/vNF>/)
        if (valorMatch) metadata.valor_total = parseFloat(valorMatch[1])
        
        metadata.document_type = 'NFE'
      } else if (isNFSe) {
        metadata.document_type = 'NFSE'
        metadata.nome_emitente = 'Prestador de Serviços'
      }
      
      // Update file with metadata
      fileItem.metadata = metadata
      
      if (!isNFe && !isNFSe) {
        uploadResults.value.push({
          filename: fileItem.name,
          status: 'warning',
          message: 'Formato XML não reconhecido como NF-e ou NFS-e, mas será processado'
        })
      } else {
        uploadResults.value.push({
          filename: fileItem.name,
          status: 'success',
          message: `Formato ${isNFe ? 'NF-e' : 'NFS-e'} válido detectado`,
          metadata
        })
      }
    } catch (error) {
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'error',
        message: 'Falha ao ler arquivo - arquivo pode estar corrompido'
      })
    }
  }
}

// Upload files to Supabase via backend API
const uploadFiles = async () => {
  if (files.value.length === 0) return
  
  isUploading.value = true
  clearError()
  uploadResults.value = []
  
  // Filter only pending files
  const pendingFiles = files.value.filter(f => f.status === 'pending')
  
  for (const fileItem of pendingFiles) {
    fileItem.status = 'uploading'
    fileItem.progress = 0
    fileItem.currentStep = 'Preparando upload...'
    
    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('arquivo', fileItem.file)
      
      // Update progress
      fileItem.progress = 20
      fileItem.currentStep = 'Enviando arquivo...'
      
      // Upload to backend API
      const response = await fetch(`${apiBaseUrl}/agentes/upload-xml`, {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type, let browser set it with boundary for FormData
        }
      })
      
      fileItem.progress = 60
      fileItem.currentStep = 'Processando resposta...'
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail?.mensagem || `HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      fileItem.progress = 100
      fileItem.currentStep = 'Concluído'
      fileItem.status = 'completed'
      fileItem.documentId = result.id_processamento
      
      // Update file metadata with response data
      if (result.documento) {
        fileItem.metadata = {
          ...fileItem.metadata,
          nome_emitente: result.documento.fornecedor,
          valor_total: result.documento.valor_total,
          document_type: result.documento.tipo_documento
        }
      }
      
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'success',
        message: 'Arquivo enviado com sucesso! Processamento iniciado pelos agentes IA.',
        documentId: result.id_processamento,
        metadata: fileItem.metadata
      })
      
      // Emit event for parent components
      emit('documentUploaded', result.id_processamento, fileItem.name)
      
    } catch (error) {
      fileItem.status = 'error'
      fileItem.progress = 0
      fileItem.currentStep = ''
      fileItem.errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'
      
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'error',
        message: `Falha no envio: ${fileItem.errorMessage}`
      })
      
      console.error('Upload error:', error)
    }
    
    // Small delay between uploads to avoid overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  
  isUploading.value = false
  
  // Emit completion event
  emit('uploadComplete', uploadResults.value)
  
  // Show summary
  const successCount = uploadResults.value.filter(r => r.status === 'success').length
  const errorCount = uploadResults.value.filter(r => r.status === 'error').length
  
  if (errorCount === 0 && successCount > 0) {
    // All successful
    setTimeout(() => {
      // Auto-clear successful files after a delay
      files.value = files.value.filter(f => f.status === 'error')
    }, 3000)
  }
}

// Navigation and actions
const viewDocument = (documentId: string) => {
  // Navigate to document details page
  navigateTo(`/documents/${documentId}`)
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

const getFileType = (filename: string): string => {
  const name = filename.toLowerCase()
  if (name.includes('nfe') || name.includes('nf-e')) return 'NF-e'
  if (name.includes('nfse') || name.includes('nfs-e') || name.includes('rps')) return 'NFS-e'
  return 'XML'
}

// Lifecycle
onMounted(() => {
  // Any initialization logic
  clearError()
})
</script>