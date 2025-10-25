<template>
  <div class="space-y-6">
    <!-- Download Manager Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold">Gerenciador de Downloads</h2>
        <p class="text-base-content/70">Gerencie e acompanhe seus downloads de relatórios</p>
      </div>
      <div class="flex space-x-2">
        <button class="btn btn-outline btn-sm" @click="refreshDownloads">
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
          </svg>
          Atualizar
        </button>
        <button class="btn btn-outline btn-sm" @click="clearExpiredDownloads">
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zM12 7a1 1 0 112 0v4a1 1 0 11-2 0V7z" clip-rule="evenodd"></path>
          </svg>
          Limpar Expirados
        </button>
      </div>
    </div>

    <!-- Download Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-primary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Total de Downloads</div>
        <div class="stat-value text-primary">{{ totalDownloads }}</div>
        <div class="stat-desc">Últimos 30 dias</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-secondary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zM3 16a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
          </svg>
        </div>
        <div class="stat-title">Arquivos Disponíveis</div>
        <div class="stat-value text-secondary">{{ availableDownloads }}</div>
        <div class="stat-desc">Prontos para download</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-accent">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Tamanho Total</div>
        <div class="stat-value text-accent">{{ formatFileSize(totalSize) }}</div>
        <div class="stat-desc">Espaço utilizado</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-warning">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Expirando</div>
        <div class="stat-value text-warning">{{ expiringDownloads }}</div>
        <div class="stat-desc">Próximas 24h</div>
      </div>
    </div>

    <!-- Download Filters -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex flex-wrap gap-4 items-center">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Buscar</span>
            </label>
            <input 
              v-model="searchTerm"
              type="text" 
              placeholder="Nome do relatório..."
              class="input input-bordered input-sm w-64"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Formato</span>
            </label>
            <select v-model="filterFormat" class="select select-bordered select-sm">
              <option value="">Todos os formatos</option>
              <option value="pdf">PDF</option>
              <option value="xlsx">Excel</option>
              <option value="docx">Word</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Status</span>
            </label>
            <select v-model="filterStatus" class="select select-bordered select-sm">
              <option value="">Todos</option>
              <option value="available">Disponível</option>
              <option value="expiring">Expirando</option>
              <option value="expired">Expirado</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Período</span>
            </label>
            <select v-model="filterPeriod" class="select select-bordered select-sm">
              <option value="">Todos</option>
              <option value="today">Hoje</option>
              <option value="week">Última semana</option>
              <option value="month">Último mês</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">&nbsp;</span>
            </label>
            <button class="btn btn-ghost btn-sm" @click="clearFilters">
              Limpar Filtros
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Downloads List -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h3 class="card-title">Histórico de Downloads</h3>
          <div class="flex space-x-2">
            <div class="dropdown dropdown-end">
              <div tabindex="0" role="button" class="btn btn-sm btn-outline">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zM3 16a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
                </svg>
                Ordenar
              </div>
              <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                <li><a @click="sortBy = 'downloadedAt'; sortOrder = 'desc'">Mais recentes</a></li>
                <li><a @click="sortBy = 'downloadedAt'; sortOrder = 'asc'">Mais antigos</a></li>
                <li><a @click="sortBy = 'reportName'; sortOrder = 'asc'">Nome A-Z</a></li>
                <li><a @click="sortBy = 'reportName'; sortOrder = 'desc'">Nome Z-A</a></li>
                <li><a @click="sortBy = 'fileSize'; sortOrder = 'desc'">Maior tamanho</a></li>
                <li><a @click="sortBy = 'fileSize'; sortOrder = 'asc'">Menor tamanho</a></li>
              </ul>
            </div>
            
            <button class="btn btn-sm btn-primary" @click="exportDownloadHistory">
              <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
              </svg>
              Exportar Histórico
            </button>
          </div>
        </div>

        <!-- Downloads Table -->
        <div class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Relatório</th>
                <th>Formato</th>
                <th>Tamanho</th>
                <th>Download</th>
                <th>Expira</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="download in paginatedDownloads" :key="download.id">
                <td>
                  <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-primary/20 rounded flex items-center justify-center">
                      <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                      </svg>
                    </div>
                    <div>
                      <div class="font-bold">{{ download.reportName }}</div>
                      <div class="text-sm text-base-content/70">ID: {{ download.reportId }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="badge badge-outline" :class="getFormatColor(download.format)">
                    {{ download.format.toUpperCase() }}
                  </div>
                </td>
                <td>{{ formatFileSize(download.fileSize) }}</td>
                <td>{{ formatDate(download.downloadedAt) }}</td>
                <td>
                  <div v-if="download.expiresAt">
                    {{ formatDate(download.expiresAt) }}
                    <div class="text-xs" :class="getExpirationColor(download.expiresAt)">
                      {{ getTimeUntilExpiration(download.expiresAt) }}
                    </div>
                  </div>
                  <span v-else class="text-base-content/50">Sem expiração</span>
                </td>
                <td>
                  <div class="badge" :class="getStatusColor(download)">
                    {{ getDownloadStatus(download) }}
                  </div>
                </td>
                <td>
                  <div class="dropdown dropdown-end">
                    <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                      </svg>
                    </div>
                    <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                      <li v-if="!isExpired(download.expiresAt)">
                        <a @click="redownload(download)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                          </svg>
                          Baixar Novamente
                        </a>
                      </li>
                      <li>
                        <a @click="copyDownloadLink(download)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 00-1 1v.5a1 1 0 11-2 0V5a3 3 0 013-3h2a3 3 0 013 3v.5a1 1 0 11-2 0V5a1 1 0 00-1-1H9a1 1 0 01-1-1z"></path>
                            <path d="M6 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1z"></path>
                          </svg>
                          Copiar Link
                        </a>
                      </li>
                      <li>
                        <a @click="viewReportDetails(download.reportId)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                            <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                          </svg>
                          Ver Relatório
                        </a>
                      </li>
                      <li>
                        <a class="text-error" @click="removeFromHistory(download.id)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zM12 7a1 1 0 112 0v4a1 1 0 11-2 0V7z" clip-rule="evenodd"></path>
                          </svg>
                          Remover do Histórico
                        </a>
                      </li>
                    </ul>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="flex justify-center mt-6">
          <div class="join">
            <button 
              class="join-item btn btn-sm" 
              :disabled="currentPage === 1" 
              @click="currentPage--"
            >
              «
            </button>
            <button class="join-item btn btn-sm">
              Página {{ currentPage }} de {{ totalPages }}
            </button>
            <button 
              class="join-item btn btn-sm" 
              :disabled="currentPage === totalPages" 
              @click="currentPage++"
            >
              »
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="selectedDownloads.length > 0" class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex justify-between items-center">
          <div>
            <h4 class="font-semibold">{{ selectedDownloads.length }} item(s) selecionado(s)</h4>
            <p class="text-sm text-base-content/70">Ações em lote disponíveis</p>
          </div>
          <div class="flex space-x-2">
            <button class="btn btn-sm btn-outline" @click="clearSelection">
              Limpar Seleção
            </button>
            <button class="btn btn-sm btn-warning" @click="bulkRemoveFromHistory">
              Remover do Histórico
            </button>
            <button class="btn btn-sm btn-primary" @click="bulkDownload">
              Download em Lote
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useReports, type DownloadHistory } from '~/composables/useReports'

// Composables
const { downloads, formatFileSize, loadDownloadHistory } = useReports()

// Reactive state
const searchTerm = ref('')
const filterFormat = ref('')
const filterStatus = ref('')
const filterPeriod = ref('')
const sortBy = ref('downloadedAt')
const sortOrder = ref<'asc' | 'desc'>('desc')
const currentPage = ref(1)
const itemsPerPage = 10
const selectedDownloads = ref<string[]>([])

// Computed properties
const filteredDownloads = computed(() => {
  let filtered = [...downloads.value]
  
  // Search filter
  if (searchTerm.value) {
    filtered = filtered.filter(download =>
      download.reportName.toLowerCase().includes(searchTerm.value.toLowerCase())
    )
  }
  
  // Format filter
  if (filterFormat.value) {
    filtered = filtered.filter(download => download.format === filterFormat.value)
  }
  
  // Status filter
  if (filterStatus.value) {
    filtered = filtered.filter(download => {
      const status = getDownloadStatus(download)
      return status.toLowerCase() === filterStatus.value
    })
  }
  
  // Period filter
  if (filterPeriod.value) {
    const now = new Date()
    filtered = filtered.filter(download => {
      const downloadDate = new Date(download.downloadedAt)
      switch (filterPeriod.value) {
        case 'today':
          return downloadDate.toDateString() === now.toDateString()
        case 'week':
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          return downloadDate >= weekAgo
        case 'month':
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          return downloadDate >= monthAgo
        default:
          return true
      }
    })
  }
  
  // Sort
  filtered.sort((a, b) => {
    let aValue: any = a[sortBy.value as keyof DownloadHistory]
    let bValue: any = b[sortBy.value as keyof DownloadHistory]
    
    if (sortBy.value === 'downloadedAt' || sortBy.value === 'expiresAt') {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    }
    
    if (sortOrder.value === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })
  
  return filtered
})

const paginatedDownloads = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredDownloads.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredDownloads.value.length / itemsPerPage)
})

const totalDownloads = computed(() => downloads.value.length)

const availableDownloads = computed(() => {
  return downloads.value.filter(download => !isExpired(download.expiresAt)).length
})

const totalSize = computed(() => {
  return downloads.value.reduce((total, download) => total + download.fileSize, 0)
})

const expiringDownloads = computed(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  return downloads.value.filter(download => {
    if (!download.expiresAt) return false
    const expiresAt = new Date(download.expiresAt)
    return expiresAt <= tomorrow && expiresAt > new Date()
  }).length
})

// Watch for page changes when filters change
watch([searchTerm, filterFormat, filterStatus, filterPeriod], () => {
  currentPage.value = 1
})

// Methods
const formatDate = (date: Date): string => {
  return new Date(date).toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getFormatColor = (format: string): string => {
  switch (format.toLowerCase()) {
    case 'pdf': return 'badge-error'
    case 'xlsx': return 'badge-success'
    case 'docx': return 'badge-info'
    default: return 'badge-ghost'
  }
}

const getDownloadStatus = (download: DownloadHistory): string => {
  if (!download.expiresAt) return 'Disponível'
  
  const now = new Date()
  const expiresAt = new Date(download.expiresAt)
  
  if (expiresAt <= now) return 'Expirado'
  
  const hoursUntilExpiration = (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60)
  if (hoursUntilExpiration <= 24) return 'Expirando'
  
  return 'Disponível'
}

const getStatusColor = (download: DownloadHistory): string => {
  const status = getDownloadStatus(download)
  switch (status) {
    case 'Disponível': return 'badge-success'
    case 'Expirando': return 'badge-warning'
    case 'Expirado': return 'badge-error'
    default: return 'badge-ghost'
  }
}

const getExpirationColor = (expiresAt?: Date): string => {
  if (!expiresAt) return 'text-base-content/50'
  
  const now = new Date()
  const expiration = new Date(expiresAt)
  
  if (expiration <= now) return 'text-error'
  
  const hoursUntilExpiration = (expiration.getTime() - now.getTime()) / (1000 * 60 * 60)
  if (hoursUntilExpiration <= 24) return 'text-warning'
  
  return 'text-success'
}

const getTimeUntilExpiration = (expiresAt: Date): string => {
  const now = new Date()
  const expiration = new Date(expiresAt)
  const diffMs = expiration.getTime() - now.getTime()
  
  if (diffMs <= 0) return 'Expirado'
  
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffDays > 0) {
    return `${diffDays} dia${diffDays > 1 ? 's' : ''}`
  } else if (diffHours > 0) {
    return `${diffHours} hora${diffHours > 1 ? 's' : ''}`
  } else {
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    return `${diffMinutes} min`
  }
}

const isExpired = (expiresAt?: Date): boolean => {
  if (!expiresAt) return false
  return new Date(expiresAt) <= new Date()
}

const clearFilters = () => {
  searchTerm.value = ''
  filterFormat.value = ''
  filterStatus.value = ''
  filterPeriod.value = ''
}

const refreshDownloads = async () => {
  await loadDownloadHistory()
}

const clearExpiredDownloads = () => {
  if (confirm('Tem certeza que deseja remover todos os downloads expirados do histórico?')) {
    // This would call an API to remove expired downloads
    console.log('Clearing expired downloads...')
  }
}

const redownload = async (download: DownloadHistory) => {
  try {
    // Simulate download
    const link = document.createElement('a')
    link.href = download.downloadUrl
    link.download = `${download.reportName}.${download.format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // Update download count (this would be handled by the API)
    console.log('Re-downloading:', download.reportName)
    
  } catch (error) {
    console.error('Error re-downloading file:', error)
    alert('Erro ao fazer download do arquivo')
  }
}

const copyDownloadLink = async (download: DownloadHistory) => {
  try {
    await navigator.clipboard.writeText(download.downloadUrl)
    alert('Link copiado para a área de transferência!')
  } catch (error) {
    console.error('Error copying link:', error)
    alert('Erro ao copiar link')
  }
}

const viewReportDetails = (reportId: string) => {
  // Navigate to report details or open modal
  console.log('Viewing report details:', reportId)
  // This would typically use router.push() or emit an event
}

const removeFromHistory = (downloadId: string) => {
  if (confirm('Tem certeza que deseja remover este item do histórico?')) {
    // This would call an API to remove the download from history
    console.log('Removing from history:', downloadId)
  }
}

const exportDownloadHistory = () => {
  // Export download history as CSV or Excel
  const csvContent = [
    ['Relatório', 'Formato', 'Tamanho', 'Download', 'Expira', 'Status'].join(','),
    ...filteredDownloads.value.map(download => [
      download.reportName,
      download.format.toUpperCase(),
      formatFileSize(download.fileSize),
      formatDate(download.downloadedAt),
      download.expiresAt ? formatDate(download.expiresAt) : 'Sem expiração',
      getDownloadStatus(download)
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `historico-downloads-${new Date().toISOString().split('T')[0]}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

const clearSelection = () => {
  selectedDownloads.value = []
}

const bulkRemoveFromHistory = () => {
  if (confirm(`Tem certeza que deseja remover ${selectedDownloads.value.length} item(s) do histórico?`)) {
    // This would call an API to remove multiple downloads from history
    console.log('Bulk removing from history:', selectedDownloads.value)
    clearSelection()
  }
}

const bulkDownload = () => {
  // Implement bulk download functionality
  console.log('Bulk downloading:', selectedDownloads.value)
  alert('Funcionalidade de download em lote será implementada')
}
</script>