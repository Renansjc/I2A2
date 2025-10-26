<template>
  <div class="space-y-6">
    <!-- Simplified Drag and Drop Area -->
    <div
      class="border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200"
      :class="{
        'border-primary bg-primary/5 scale-105': isDragOver,
        'border-base-300 hover:border-primary/50 hover:bg-base-50': !isDragOver && !hasError,
        'border-error bg-error/5': hasError
      }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <div class="space-y-6">
        <!-- Upload Icon -->
        <div class="mx-auto w-20 h-20 text-primary/60">
          <svg fill="currentColor" viewBox="0 0 24 24" class="w-full h-full">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
          </svg>
        </div>
        
        <!-- Main Message -->
        <div>
          <h3 class="text-2xl font-bold text-base-content mb-2">
            {{ isDragOver ? 'Solte os arquivos aqui' : 'Envie seus arquivos XML' }}
          </h3>
          <p class="text-base-content/70 text-lg">
            {{ isDragOver ? 'Processamento automático com IA' : 'Arraste e solte ou clique para selecionar' }}
          </p>
        </div>
        
        <!-- Upload Button -->
        <div class="space-y-3">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".xml"
            class="hidden"
            @change="handleFileSelect"
          />
          <button
            class="btn btn-primary btn-lg"
            :disabled="isUploading"
            @click="($refs.fileInput as HTMLInputElement)?.click()"
          >
            <svg v-if="!isUploading" class="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
            </svg>
            <span v-if="isUploading" class="loading loading-spinner loading-md mr-2"></span>
            {{ isUploading ? 'Enviando...' : 'Selecionar Arquivos' }}
          </button>
          
          <!-- File Format Info -->
          <div class="flex items-center justify-center space-x-4 text-sm text-base-content/60">
            <span class="flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
              </svg>
              NF-e e NFS-e
            </span>
            <span>•</span>
            <span class="flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
              </svg>
              Máx. 10MB
            </span>
            <span>•</span>
            <span class="flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Processamento IA
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Simplified File List -->
    <div v-if="files.length > 0" class="space-y-4">
      <div class="flex justify-between items-center">
        <h4 class="text-lg font-semibold">Arquivos ({{ files.length }})</h4>
        <div class="text-sm text-base-content/60">
          Total: {{ formatFileSize(totalFileSize) }}
        </div>
      </div>
      
      <div class="space-y-3">
        <div
          v-for="(file, index) in files"
          :key="file.id || index"
          class="card bg-base-100 shadow-sm border transition-all"
          :class="{
            'border-success bg-success/5': file.status === 'completed',
            'border-error bg-error/5': file.status === 'error',
            'border-warning bg-warning/5': file.status === 'uploading',
            'border-base-300': file.status === 'pending'
          }"
        >
          <div class="card-body p-4">
            <div class="flex items-center justify-between">
              <!-- File Info -->
              <div class="flex items-center space-x-3 flex-1">
                <div class="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                  </svg>
                </div>
                
                <div class="flex-1 min-w-0">
                  <p class="font-semibold truncate text-base">{{ file.name }}</p>
                  <div class="flex items-center space-x-2 text-sm text-base-content/70">
                    <span>{{ formatFileSize(file.size) }}</span>
                    <span>•</span>
                    <span class="badge badge-outline badge-sm">{{ getFileType(file.name) }}</span>
                    <span v-if="file.metadata?.nome_emitente" class="text-primary font-medium">
                      • {{ file.metadata.nome_emitente }}
                    </span>
                  </div>
                  <div v-if="file.metadata?.valor_total" class="text-sm text-success font-medium mt-1">
                    Valor: {{ formatCurrency(file.metadata.valor_total) }}
                  </div>
                </div>
              </div>
          
              <!-- Status and Actions -->
              <div class="flex items-center space-x-3">
                <!-- Upload Progress -->
                <div v-if="file.status === 'uploading'" class="flex items-center space-x-3">
                  <div class="radial-progress text-primary" :style="`--value:${file.progress}`" role="progressbar">
                    <span class="text-xs font-bold">{{ file.progress }}%</span>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-medium">Enviando...</div>
                    <div class="text-xs text-base-content/60">{{ file.currentStep || 'Processando...' }}</div>
                  </div>
                  <button
                    class="btn btn-ghost btn-sm text-error"
                    @click="cancelUpload(file)"
                    title="Cancelar"
                  >
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                  </button>
                </div>
                
                <!-- Completed Status -->
                <div v-else-if="file.status === 'completed'" class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-success/20 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-success" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-medium text-success">Enviado com sucesso</div>
                    <div class="text-xs text-base-content/60">Processamento iniciado</div>
                  </div>
                </div>
                
                <!-- Error Status -->
                <div v-else-if="file.status === 'error'" class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-error/20 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-error" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-medium text-error">Erro no envio</div>
                    <div class="text-xs text-base-content/60" :title="file.errorMessage">
                      {{ file.errorMessage?.slice(0, 40) }}...
                    </div>
                  </div>
                </div>
                
                <!-- Pending Status -->
                <div v-else class="flex items-center space-x-2">
                  <button
                    class="btn btn-ghost btn-sm"
                    @click="removeFile(index)"
                    title="Remover arquivo"
                  >
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Simplified Upload Actions -->
      <div class="flex justify-between items-center pt-6">
        <div class="flex items-center space-x-4">
          <button
            class="btn btn-ghost"
            :disabled="isUploading"
            @click="clearFiles"
          >
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            </svg>
            Limpar Tudo
          </button>
          
          <div v-if="uploadStats.total > 0" class="stats stats-horizontal shadow-sm">
            <div class="stat py-2 px-4">
              <div class="stat-title text-xs">Total</div>
              <div class="stat-value text-sm">{{ uploadStats.total }}</div>
            </div>
            <div class="stat py-2 px-4">
              <div class="stat-title text-xs">Concluídos</div>
              <div class="stat-value text-sm text-success">{{ uploadStats.completed }}</div>
            </div>
            <div v-if="uploadStats.failed > 0" class="stat py-2 px-4">
              <div class="stat-title text-xs">Erros</div>
              <div class="stat-value text-sm text-error">{{ uploadStats.failed }}</div>
            </div>
          </div>
        </div>
        
        <button
          class="btn btn-primary btn-lg"
          :disabled="files.length === 0 || isUploading || hasActiveUploads"
          @click="uploadFiles"
        >
          <span v-if="isUploading" class="loading loading-spinner loading-md mr-2"></span>
          <svg v-else class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
            <path d="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z" />
          </svg>
          {{ isUploading ? 'Enviando...' : 'Enviar Todos os Arquivos' }}
        </button>
      </div>
    </div>

    <!-- Simplified Error Display -->
    <div v-if="hasError" class="alert alert-error shadow-lg">
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

    <!-- Success Messages -->
    <div v-if="uploadResults.length > 0" class="space-y-2">
      <div
        v-for="result in uploadResults"
        :key="result.filename"
        class="alert shadow-sm"
        :class="{
          'alert-success': result.status === 'success',
          'alert-error': result.status === 'error',
          'alert-warning': result.status === 'warning'
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '~/composables/useApi'

interface FileMetadata {
  nome_emitente?: string
  cnpj_emitente?: string
  numero_documento?: string
  data_emissao?: string
  valor_total?: number
  document_type?: string
}

interface FileItem {
  id: string
  name: string
  size: number
  file: File
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress: number
  documentId?: string
  currentStep?: string
  errorMessage?: string
  metadata?: FileMetadata
  uploadController?: AbortController
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

// Simplified state - removed preview modal and complex validation

// Use API composable for consistent configuration
const { apiBaseUrl } = useApi()

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

// Simplified file addition
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
}

// Remove file from list
const removeFile = (index: number) => {
  const file = files.value[index]
  if (!file) return
  
  if (file.status === 'uploading') {
    // Cancel upload if in progress
    cancelUpload(file)
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

// Cancel upload
const cancelUpload = (fileItem: FileItem) => {
  if (fileItem.uploadController) {
    fileItem.uploadController.abort()
  }
  fileItem.status = 'cancelled'
  fileItem.progress = 0
  fileItem.currentStep = 'Cancelado'
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
    // Create abort controller for cancellation
    fileItem.uploadController = new AbortController()
    
    fileItem.status = 'uploading'
    fileItem.progress = 0
    fileItem.currentStep = 'Preparando upload...'
    
    try {
      // Create FormData for file upload (MVP format)
      const formData = new FormData()
      formData.append('files', fileItem.file)
      
      // Update progress
      fileItem.progress = 20
      fileItem.currentStep = 'Enviando arquivo...'
      
      // Upload to MVP backend API with abort signal
      const response = await fetch(`${apiBaseUrl}/api/v1/documents/upload`, {
        method: 'POST',
        body: formData,
        signal: fileItem.uploadController.signal,
        headers: {
          // Don't set Content-Type, let browser set it with boundary for FormData
        }
      })
      
      fileItem.progress = 60
      fileItem.currentStep = 'Processando resposta...'
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        
        // Handle duplicate file error specifically
        if (response.status === 409 && errorData.detail?.codigo_erro === 'ARQUIVO_DUPLICADO') {
          throw new Error(`Arquivo duplicado: ${errorData.detail.mensagem}`)
        }
        
        throw new Error(errorData.detail?.mensagem || `HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      fileItem.progress = 100
      fileItem.currentStep = 'Concluído'
      fileItem.status = 'completed'
      
      // MVP response format - get first document ID
      const documentId = result.document_ids?.[0] || 'unknown'
      fileItem.documentId = documentId
      
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'success',
        message: result.message || 'Arquivo enviado com sucesso! Processamento iniciado pelos agentes IA.',
        documentId: documentId
      })
      
      // Emit event for parent components
      emit('documentUploaded', documentId, fileItem.name)
      
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Upload was cancelled
        fileItem.status = 'cancelled'
        fileItem.progress = 0
        fileItem.currentStep = 'Cancelado'
        continue
      }
      
      fileItem.status = 'error'
      fileItem.progress = 0
      fileItem.currentStep = ''
      fileItem.errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'
      
      // Determine error type for better user feedback
      let errorStatus: 'error' | 'success' | 'warning' | 'info' = 'error'
      let errorMessage = `Falha no envio: ${fileItem.errorMessage}`
      
      if (fileItem.errorMessage?.includes('Arquivo duplicado')) {
        errorStatus = 'warning'
        errorMessage = `Arquivo já existe: ${fileItem.errorMessage.replace('Arquivo duplicado: ', '')}`
      }
      
      uploadResults.value.push({
        filename: fileItem.name,
        status: errorStatus,
        message: errorMessage
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
const viewDocument = (documentId: string | undefined) => {
  if (!documentId) return
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