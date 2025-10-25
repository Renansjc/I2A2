<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Enviar Arquivos XML</h1>
        <p class="text-base-content/70">Envie arquivos XML NF-e e NFS-e para processamento</p>
      </div>
      <div class="dropdown dropdown-end">
        <div tabindex="0" role="button" class="btn btn-outline">
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          Ajuda
        </div>
        <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-64">
          <li><a>Formatos Suportados</a></li>
          <li><a>Diretrizes de Envio</a></li>
          <li><a>Solução de Problemas</a></li>
        </ul>
      </div>
    </div>

    <!-- Upload Instructions -->
    <div class="alert alert-info">
      <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
      </svg>
      <div>
        <h3 class="font-bold">Instruções de Envio</h3>
        <div class="text-sm">
          • Formatos suportados: arquivos XML NF-e e NFS-e<br>
          • Tamanho máximo: 10MB por arquivo<br>
          • Arquivos são automaticamente validados e processados por agentes IA<br>
          • Processamento tipicamente leva 2-5 minutos por arquivo
        </div>
      </div>
    </div>

    <!-- File Upload Component -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h2 class="card-title mb-4">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
          </svg>
          Envio de Arquivos
        </h2>
        <FileUpload />
      </div>
    </div>

    <!-- Processing Queue -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
            </svg>
            Fila de Processamento ({{ processingQueue.length }})
          </h2>
          <button 
            class="btn btn-sm btn-ghost"
            @click="refreshQueue"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
            Atualizar
          </button>
        </div>

        <div v-if="processingQueue.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
          </svg>
          <p class="text-base-content/50">Nenhum arquivo na fila de processamento</p>
        </div>

        <div v-else class="space-y-3">
          <div 
            v-for="item in processingQueue"
            :key="item.id"
            class="flex items-center justify-between p-4 bg-base-100 rounded-lg"
          >
            <div class="flex items-center space-x-4">
              <div class="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                </svg>
              </div>
              
              <div>
                <h4 class="font-semibold">{{ item.filename }}</h4>
                <p class="text-sm text-base-content/70">{{ item.type }} • {{ item.size }}</p>
                <p class="text-sm text-base-content/50">{{ item.currentStep }}</p>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <div class="text-right">
                <div class="text-sm font-medium">{{ item.progress }}%</div>
                <div class="text-xs text-base-content/50">{{ item.estimatedTime }}</div>
              </div>
              
              <div class="radial-progress text-primary" :style="`--value:${item.progress}`" role="progressbar">
                {{ item.progress }}%
              </div>
              
              <div 
                class="badge"
                :class="{
                  'badge-warning': item.status === 'processing',
                  'badge-success': item.status === 'completed',
                  'badge-error': item.status === 'failed',
                  'badge-ghost': item.status === 'queued'
                }"
              >
                {{ item.status === 'processing' ? 'processando' : item.status === 'completed' ? 'concluído' : item.status === 'failed' ? 'falhou' : 'na fila' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Processing History -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
            </svg>
            Histórico de Processamento
          </h2>
          <div class="join">
            <input 
              v-model="historySearch"
              class="input input-bordered input-sm join-item" 
              placeholder="Buscar histórico..."
            />
            <button class="btn btn-sm join-item">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Arquivo</th>
                <th>Tipo</th>
                <th>Processado</th>
                <th>Status</th>
                <th>Registros</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredHistory" :key="item.id">
                <td>
                  <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-primary/20 rounded flex items-center justify-center">
                      <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                      </svg>
                    </div>
                    <div>
                      <div class="font-bold">{{ item.filename }}</div>
                      <div class="text-sm text-base-content/70">{{ item.size }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="badge badge-outline">{{ item.type }}</div>
                </td>
                <td>{{ formatDate(item.processedAt) }}</td>
                <td>
                  <div 
                    class="badge"
                    :class="{
                      'badge-success': item.status === 'completed',
                      'badge-error': item.status === 'failed',
                      'badge-warning': item.status === 'partial'
                    }"
                  >
                    {{ item.status === 'completed' ? 'concluído' : item.status === 'failed' ? 'falhou' : 'parcial' }}
                  </div>
                </td>
                <td>{{ item.recordsExtracted }}</td>
                <td>
                  <div class="dropdown dropdown-end">
                    <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                      </svg>
                    </div>
                    <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                      <li><a @click="viewDetails(item)">Ver Detalhes</a></li>
                      <li><a @click="downloadProcessed(item)">Baixar Processado</a></li>
                      <li><a @click="reprocess(item)">Reprocessar</a></li>
                      <li><a class="text-error" @click="deleteRecord(item)">Excluir</a></li>
                    </ul>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

definePageMeta({
  layout: 'default'
})

// Reactive state
const historySearch = ref('')

// Mock data
const processingQueue = ref([
  {
    id: '1',
    filename: 'NFe_35240101234567890123550010000000011234567890.xml',
    type: 'NF-e',
    size: '2,3 MB',
    status: 'processing',
    progress: 65,
    currentStep: 'Categorização IA em andamento...',
    estimatedTime: '2 min restantes'
  },
  {
    id: '2',
    filename: 'NFSe_12345_2024_001.xml',
    type: 'NFS-e',
    size: '1,8 MB',
    status: 'queued',
    progress: 0,
    currentStep: 'Aguardando na fila...',
    estimatedTime: '5 min estimados'
  }
])

const processingHistory = [
  {
    id: '1',
    filename: 'NFe_35240101234567890123550010000000011234567890.xml',
    type: 'NF-e',
    size: '2,1 MB',
    processedAt: new Date('2024-01-15T14:30:00'),
    status: 'completed',
    recordsExtracted: 15
  },
  {
    id: '2',
    filename: 'NFSe_12345_2024_001.xml',
    type: 'NFS-e',
    size: '1,5 MB',
    processedAt: new Date('2024-01-15T13:45:00'),
    status: 'completed',
    recordsExtracted: 8
  },
  {
    id: '3',
    filename: 'NFe_arquivo_corrompido.xml',
    type: 'NF-e',
    size: '0,8 MB',
    processedAt: new Date('2024-01-15T12:20:00'),
    status: 'failed',
    recordsExtracted: 0
  },
  {
    id: '4',
    filename: 'NFe_lote_001.xml',
    type: 'NF-e',
    size: '5,2 MB',
    processedAt: new Date('2024-01-14T16:15:00'),
    status: 'partial',
    recordsExtracted: 42
  }
]

// Computed properties
const filteredHistory = computed(() => {
  if (!historySearch.value) return processingHistory
  
  return processingHistory.filter(item =>
    item.filename.toLowerCase().includes(historySearch.value.toLowerCase()) ||
    item.type.toLowerCase().includes(historySearch.value.toLowerCase())
  )
})

// Methods
const refreshQueue = () => {
  // Simulate queue refresh
  console.log('Refreshing processing queue...')
}

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const viewDetails = (item: any) => {
  console.log('Viewing details for:', item)
}

const downloadProcessed = (item: any) => {
  console.log('Downloading processed data for:', item)
}

const reprocess = (item: any) => {
  console.log('Reprocessing:', item)
}

const deleteRecord = (item: any) => {
  console.log('Deleting record:', item)
}
</script>