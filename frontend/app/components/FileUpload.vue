<template>
  <div class="space-y-4">
    <!-- Drag and Drop Area -->
    <div
      class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
      :class="{
        'border-primary bg-primary/10': isDragOver,
        'border-base-300 hover:border-primary/50': !isDragOver
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
            @click="$refs.fileInput?.click()"
          >
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8 4a3 3 0 00-6 0v4a5 5 0 0010 0V4a3 3 0 00-6 0v4a1 1 0 102 0V4a1 1 0 10-2 0v4a3 3 0 106 0V4a5 5 0 00-10 0z" clip-rule="evenodd"></path>
            </svg>
            Escolher Arquivos
          </button>
          <p class="text-sm text-base-content/50">
            Formatos suportados: .xml (NF-e, NFS-e)
          </p>
        </div>
      </div>
    </div>

    <!-- File List -->
    <div v-if="files.length > 0" class="space-y-3">
      <h4 class="font-semibold">Arquivos Selecionados ({{ files.length }})</h4>
      
      <div class="space-y-2">
        <div
          v-for="(file, index) in files"
          :key="index"
          class="flex items-center justify-between p-3 bg-base-200 rounded-lg"
        >
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-primary/20 rounded flex items-center justify-center">
              <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
              </svg>
            </div>
            
            <div>
              <p class="font-medium">{{ file.name }}</p>
              <p class="text-sm text-base-content/70">
                {{ formatFileSize(file.size) }} • {{ getFileType(file.name) }}
              </p>
            </div>
          </div>
          
          <div class="flex items-center space-x-2">
            <div
              v-if="file.status === 'uploading'"
              class="flex items-center space-x-2"
            >
              <span class="loading loading-spinner loading-sm"></span>
              <span class="text-sm">{{ file.progress }}%</span>
            </div>
            
            <div
              v-else-if="file.status === 'completed'"
              class="flex items-center space-x-2 text-success"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              <span class="text-sm">Concluído</span>
            </div>
            
            <div
              v-else-if="file.status === 'error'"
              class="flex items-center space-x-2 text-error"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
              </svg>
              <span class="text-sm">Erro</span>
            </div>
            
            <button
              class="btn btn-ghost btn-sm"
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
        <button
          class="btn btn-ghost"
          @click="clearFiles"
        >
          Limpar Tudo
        </button>
        
        <div class="space-x-2">
          <button
            class="btn btn-secondary"
            :disabled="files.length === 0 || isUploading"
            @click="validateFiles"
          >
            Validar XML
          </button>
          <button
            class="btn btn-primary"
            :disabled="files.length === 0 || isUploading"
            @click="uploadFiles"
          >
            <span v-if="isUploading" class="loading loading-spinner loading-sm mr-2"></span>
            {{ isUploading ? 'Enviando...' : 'Enviar Arquivos' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Results -->
    <div v-if="uploadResults.length > 0" class="card bg-base-100 shadow">
      <div class="card-body">
        <h4 class="card-title">Resultados do Envio</h4>
        <div class="space-y-2">
          <div
            v-for="result in uploadResults"
            :key="result.filename"
            class="alert"
            :class="{
              'alert-success': result.status === 'success',
              'alert-error': result.status === 'error',
              'alert-warning': result.status === 'warning'
            }"
          >
            <div>
              <h5 class="font-semibold">{{ result.filename }}</h5>
              <p class="text-sm">{{ result.message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface FileItem {
  name: string
  size: number
  file: File
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress: number
}

interface UploadResult {
  filename: string
  status: 'success' | 'error' | 'warning'
  message: string
}

// Reactive state
const files = ref<FileItem[]>([])
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadResults = ref<UploadResult[]>([])

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
}

// Add files to the list
const addFiles = (newFiles: File[]) => {
  const xmlFiles = newFiles.filter(file => 
    file.name.toLowerCase().endsWith('.xml')
  )
  
  xmlFiles.forEach(file => {
    // Check if file already exists
    if (!files.value.some(f => f.name === file.name && f.size === file.size)) {
      files.value.push({
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
  files.value.splice(index, 1)
}

// Clear all files
const clearFiles = () => {
  files.value = []
  uploadResults.value = []
}

// Validate XML files
const validateFiles = async () => {
  uploadResults.value = []
  
  for (const fileItem of files.value) {
    try {
      const text = await fileItem.file.text()
      
      // Basic XML validation
      if (!text.includes('<?xml') || !text.includes('<')) {
        uploadResults.value.push({
          filename: fileItem.name,
          status: 'error',
          message: 'Formato XML inválido'
        })
        continue
      }
      
      // Check for NF-e or NFS-e indicators
      const isNFe = text.includes('NFe') || text.includes('nfeProc')
      const isNFSe = text.includes('NFSe') || text.includes('nfse')
      
      if (!isNFe && !isNFSe) {
        uploadResults.value.push({
          filename: fileItem.name,
          status: 'warning',
          message: 'Formato XML não reconhecido como NF-e ou NFS-e'
        })
      } else {
        uploadResults.value.push({
          filename: fileItem.name,
          status: 'success',
          message: `Formato ${isNFe ? 'NF-e' : 'NFS-e'} válido detectado`
        })
      }
    } catch (error) {
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'error',
        message: 'Falha ao ler arquivo'
      })
    }
  }
}

// Upload files
const uploadFiles = async () => {
  isUploading.value = true
  uploadResults.value = []
  
  for (const fileItem of files.value) {
    fileItem.status = 'uploading'
    fileItem.progress = 0
    
    try {
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        fileItem.progress = i
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // Simulate API call - will be replaced with actual backend integration
      await new Promise(resolve => setTimeout(resolve, 500))
      
      fileItem.status = 'completed'
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'success',
        message: 'Arquivo enviado e na fila para processamento'
      })
      
    } catch (error) {
      fileItem.status = 'error'
      uploadResults.value.push({
        filename: fileItem.name,
        status: 'error',
        message: 'Falha no envio. Tente novamente.'
      })
    }
  }
  
  isUploading.value = false
}

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileType = (filename: string): string => {
  if (filename.toLowerCase().includes('nfe')) return 'NF-e'
  if (filename.toLowerCase().includes('nfse')) return 'NFS-e'
  return 'XML'
}
</script>