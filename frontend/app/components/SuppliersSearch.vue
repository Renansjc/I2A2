<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
          </svg>
          Buscar Fornecedores
        </h3>
        <div class="flex items-center gap-2">
          <button 
            @click="exportSuppliers('excel')" 
            class="btn btn-sm btn-outline"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Excel
          </button>
          <button 
            @click="exportSuppliers('pdf')" 
            class="btn btn-sm btn-outline"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            PDF
          </button>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Buscar por nome ou CNPJ</span>
          </label>
          <div class="input-group">
            <input 
              v-model="searchTerm"
              @keyup.enter="performSearch"
              type="text" 
              placeholder="Digite o nome ou CNPJ..." 
              class="input input-bordered flex-1"
            />
            <button 
              @click="performSearch"
              class="btn btn-square"
              :disabled="isLoading"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Estado (UF)</span>
          </label>
          <select 
            v-model="selectedUF" 
            @change="performSearch"
            class="select select-bordered"
          >
            <option value="">Todos os estados</option>
            <option v-for="uf in brazilianStates" :key="uf" :value="uf">{{ uf }}</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Ordenar por</span>
          </label>
          <select 
            v-model="orderBy" 
            @change="performSearch"
            class="select select-bordered"
          >
            <option value="razao_social">Razão Social</option>
            <option value="cnpj">CNPJ</option>
            <option value="uf">Estado</option>
            <option value="total_documentos">Total de Documentos</option>
          </select>
        </div>
      </div>

      <!-- Active Filters -->
      <div v-if="hasFilters" class="flex flex-wrap gap-2 mb-4">
        <div class="badge badge-primary gap-2" v-if="searchTerm">
          Busca: {{ searchTerm }}
          <button @click="clearSearch" class="btn btn-xs btn-circle btn-ghost">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
        <div class="badge badge-secondary gap-2" v-if="selectedUF">
          UF: {{ selectedUF }}
          <button @click="clearUF" class="btn btn-xs btn-circle btn-ghost">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
        <button @click="clearAllFilters" class="btn btn-xs btn-outline">
          Limpar todos os filtros
        </button>
      </div>

      <!-- Error Alert -->
      <div v-if="error" class="alert alert-error mb-4">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center py-8">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <!-- Results -->
      <div v-else-if="searchResults" class="space-y-4">
        <!-- Results Header -->
        <div class="flex items-center justify-between">
          <div class="text-sm opacity-70">
            Mostrando {{ searchResults.items.length }} de {{ searchResults.totalCount }} fornecedores
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm">Itens por página:</span>
            <select 
              v-model="pageSize" 
              @change="changePageSize"
              class="select select-sm select-bordered"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        <!-- Suppliers List -->
        <div class="overflow-x-auto">
          <table class="table table-sm bg-base-100">
            <thead>
              <tr>
                <th>Razão Social</th>
                <th>CNPJ</th>
                <th>UF</th>
                <th>Documentos</th>
                <th>Valor Total</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="supplier in searchResults.items" :key="supplier.cnpj" class="hover">
                <td>
                  <div>
                    <div class="font-semibold">{{ supplier.razao_social }}</div>
                    <div class="text-xs opacity-70">{{ supplier.nome_fantasia || 'Sem nome fantasia' }}</div>
                  </div>
                </td>
                <td>{{ formatCNPJ(supplier.cnpj) }}</td>
                <td>{{ supplier.uf }}</td>
                <td>{{ formatNumber(supplier.total_documentos) }}</td>
                <td>{{ formatCurrency(supplier.valor_total_compras) }}</td>
                <td>
                  <div class="flex gap-1">
                    <button class="btn btn-xs btn-ghost" @click="viewSupplierDetails(supplier)">
                      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                        <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="searchResults.totalPages > 1" class="flex justify-center">
          <div class="join">
            <button 
              @click="goToPage(currentPage - 1)"
              :disabled="!searchResults.hasPrevious"
              class="join-item btn btn-sm"
            >
              «
            </button>
            <button 
              v-for="page in visiblePages" 
              :key="page"
              @click="goToPage(page)"
              :class="{ 'btn-active': page === currentPage }"
              class="join-item btn btn-sm"
            >
              {{ page }}
            </button>
            <button 
              @click="goToPage(currentPage + 1)"
              :disabled="!searchResults.hasNext"
              class="join-item btn btn-sm"
            >
              »
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-base-content opacity-50 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-base-content opacity-70">Faça uma busca para encontrar fornecedores</p>
        <p class="text-sm text-base-content opacity-50">Use os filtros acima para refinar sua pesquisa</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Reactive state
const searchTerm = ref('')
const selectedUF = ref('')
const orderBy = ref('razao_social')
const pageSize = ref(50)
const searchResults = ref<any>(null)

// Use dimensional search composable
const {
  isLoading,
  error,
  searchSuppliers,
  exportData,
  resetFilters,
  formatCNPJ,
  formatCurrency,
  formatNumber,
  currentPage
} = useDimensionalSearch()

// Brazilian states
const brazilianStates = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

// Computed properties
const hasFilters = computed(() => {
  return searchTerm.value || selectedUF.value
})

const visiblePages = computed(() => {
  if (!searchResults.value) return []
  
  const total = searchResults.value.totalPages
  const current = currentPage.value
  const pages = []
  
  // Show up to 5 pages around current page
  const start = Math.max(1, current - 2)
  const end = Math.min(total, current + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Methods
const performSearch = async () => {
  try {
    const filters: any = {}
    
    if (searchTerm.value) {
      filters.search = searchTerm.value
    }
    if (selectedUF.value) {
      filters.uf = selectedUF.value
    }
    
    const paginationOptions = {
      page: 1,
      pageSize: pageSize.value,
      orderBy: orderBy.value,
      orderDirection: 'asc' as const
    }
    
    searchResults.value = await searchSuppliers(filters, paginationOptions)
  } catch (err) {
    // Error handled by composable
  }
}

const goToPage = async (page: number) => {
  if (!searchResults.value || page < 1 || page > searchResults.value.totalPages) return
  
  try {
    const filters: any = {}
    
    if (searchTerm.value) {
      filters.search = searchTerm.value
    }
    if (selectedUF.value) {
      filters.uf = selectedUF.value
    }
    
    const paginationOptions = {
      page,
      pageSize: pageSize.value,
      orderBy: orderBy.value,
      orderDirection: 'asc' as const
    }
    
    searchResults.value = await searchSuppliers(filters, paginationOptions)
  } catch (err) {
    // Error handled by composable
  }
}

const changePageSize = () => {
  performSearch()
}

const clearSearch = () => {
  searchTerm.value = ''
  performSearch()
}

const clearUF = () => {
  selectedUF.value = ''
  performSearch()
}

const clearAllFilters = () => {
  searchTerm.value = ''
  selectedUF.value = ''
  orderBy.value = 'razao_social'
  resetFilters()
  searchResults.value = null
}

const exportSuppliers = async (format: 'excel' | 'pdf') => {
  try {
    await exportData('suppliers', format)
    // Show success message or handle download
  } catch (err) {
    // Error handled by composable
  }
}

const viewSupplierDetails = (supplier: any) => {
  // Navigate to supplier details or show modal
  console.log('View supplier details:', supplier)
}

// Load initial data
onMounted(() => {
  // Don't auto-search, wait for user input
})
</script>