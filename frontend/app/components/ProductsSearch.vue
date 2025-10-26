<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path>
          </svg>
          Buscar Produtos
        </h3>
        <div class="flex items-center gap-2">
          <button 
            @click="exportProducts('excel')" 
            class="btn btn-sm btn-outline"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Excel
          </button>
          <button 
            @click="exportProducts('pdf')" 
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
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Buscar produto</span>
          </label>
          <div class="input-group">
            <input 
              v-model="searchTerm"
              @keyup.enter="performSearch"
              type="text" 
              placeholder="Descrição ou código..." 
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
            <span class="label-text">Categoria</span>
          </label>
          <select 
            v-model="selectedCategory" 
            @change="performSearch"
            class="select select-bordered"
          >
            <option value="">Todas as categorias</option>
            <option v-for="category in availableCategories" :key="category" :value="category">
              {{ category }}
            </option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">NCM</span>
          </label>
          <input 
            v-model="ncmFilter"
            @keyup.enter="performSearch"
            type="text" 
            placeholder="Código NCM..." 
            class="input input-bordered"
          />
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
            <option value="descricao">Descrição</option>
            <option value="codigo_produto">Código</option>
            <option value="categoria">Categoria</option>
            <option value="total_vendas">Total de Vendas</option>
            <option value="quantidade_total">Quantidade</option>
          </select>
        </div>
      </div>

      <!-- Period Filter -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Período de análise</span>
          </label>
          <select 
            v-model="selectedPeriod" 
            @change="performSearch"
            class="select select-bordered"
          >
            <option value="last_30_days">Últimos 30 dias</option>
            <option value="last_90_days">Últimos 90 dias</option>
            <option value="last_6_months">Últimos 6 meses</option>
            <option value="last_12_months">Últimos 12 meses</option>
            <option value="current_year">Ano atual</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Data início (personalizada)</span>
          </label>
          <input 
            v-model="startDate"
            @change="performSearch"
            type="date" 
            class="input input-bordered"
          />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Data fim (personalizada)</span>
          </label>
          <input 
            v-model="endDate"
            @change="performSearch"
            type="date" 
            class="input input-bordered"
          />
        </div>
      </div>

      <!-- Active Filters -->
      <div v-if="hasFilters" class="flex flex-wrap gap-2 mb-4">
        <div class="badge badge-primary gap-2" v-if="searchTerm">
          Busca: {{ searchTerm }}
          <button @click="clearSearch" class="btn btn-xs btn-circle btn-ghost">×</button>
        </div>
        <div class="badge badge-secondary gap-2" v-if="selectedCategory">
          Categoria: {{ selectedCategory }}
          <button @click="clearCategory" class="btn btn-xs btn-circle btn-ghost">×</button>
        </div>
        <div class="badge badge-accent gap-2" v-if="ncmFilter">
          NCM: {{ ncmFilter }}
          <button @click="clearNCM" class="btn btn-xs btn-circle btn-ghost">×</button>
        </div>
        <div class="badge badge-info gap-2" v-if="selectedPeriod !== 'last_90_days'">
          Período: {{ getPeriodLabel(selectedPeriod) }}
          <button @click="clearPeriod" class="btn btn-xs btn-circle btn-ghost">×</button>
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
            Mostrando {{ searchResults.items.length }} de {{ searchResults.totalCount }} produtos
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

        <!-- Products List -->
        <div class="overflow-x-auto">
          <table class="table table-sm bg-base-100">
            <thead>
              <tr>
                <th>Produto</th>
                <th>Categoria</th>
                <th>NCM</th>
                <th>Total Vendas</th>
                <th>Quantidade</th>
                <th>Preço Médio</th>
                <th>Fornecedores</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="product in searchResults.items" :key="product.codigo_produto" class="hover">
                <td>
                  <div>
                    <div class="font-semibold text-sm">{{ product.descricao }}</div>
                    <div class="text-xs opacity-70">Código: {{ product.codigo_produto }}</div>
                    <div class="text-xs opacity-60" v-if="product.ean">EAN: {{ product.ean }}</div>
                  </div>
                </td>
                <td>
                  <div>
                    <div class="text-sm">{{ product.categoria || 'Sem categoria' }}</div>
                    <div class="text-xs opacity-70" v-if="product.subcategoria">{{ product.subcategoria }}</div>
                  </div>
                </td>
                <td>{{ product.ncm || '-' }}</td>
                <td>{{ formatCurrency(product.total_vendas) }}</td>
                <td>{{ formatNumber(product.quantidade_total) }}</td>
                <td>{{ formatCurrency(product.preco_medio) }}</td>
                <td>{{ product.fornecedores_count }}</td>
                <td>
                  <div class="flex gap-1">
                    <button class="btn btn-xs btn-ghost" @click="viewProductDetails(product)">
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
          <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path>
        </svg>
        <p class="text-base-content opacity-70">Faça uma busca para encontrar produtos</p>
        <p class="text-sm text-base-content opacity-50">Use os filtros acima para refinar sua pesquisa</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Reactive state
const searchTerm = ref('')
const selectedCategory = ref('')
const ncmFilter = ref('')
const selectedPeriod = ref('last_90_days')
const startDate = ref('')
const endDate = ref('')
const orderBy = ref('descricao')
const pageSize = ref(50)
const searchResults = ref<any>(null)
const availableCategories = ref<string[]>([])

// Use dimensional search composable
const {
  isLoading,
  error,
  searchProducts,
  exportData,
  resetFilters,
  formatCurrency,
  formatNumber,
  currentPage
} = useDimensionalSearch()

// Computed properties
const hasFilters = computed(() => {
  return searchTerm.value || selectedCategory.value || ncmFilter.value || 
         selectedPeriod.value !== 'last_90_days' || startDate.value || endDate.value
})

const visiblePages = computed(() => {
  if (!searchResults.value) return []
  
  const total = searchResults.value.totalPages
  const current = currentPage.value
  const pages = []
  
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
    if (selectedCategory.value) {
      filters.category = selectedCategory.value
    }
    if (ncmFilter.value) {
      filters.ncm = ncmFilter.value
    }
    if (selectedPeriod.value) {
      filters.period = selectedPeriod.value
    }
    if (startDate.value) {
      filters.startDate = startDate.value
    }
    if (endDate.value) {
      filters.endDate = endDate.value
    }
    
    const paginationOptions = {
      page: 1,
      pageSize: pageSize.value,
      orderBy: orderBy.value,
      orderDirection: 'asc' as const
    }
    
    searchResults.value = await searchProducts(filters, paginationOptions)
    
    // Update available categories from results
    if (searchResults.value?.items) {
      const categories = new Set<string>()
      searchResults.value.items.forEach((item: any) => {
        if (item.categoria) {
          categories.add(item.categoria)
        }
      })
      availableCategories.value = Array.from(categories).sort()
    }
  } catch (err) {
    // Error handled by composable
  }
}

const goToPage = async (page: number) => {
  if (!searchResults.value || page < 1 || page > searchResults.value.totalPages) return
  
  try {
    const filters: any = {}
    
    if (searchTerm.value) filters.search = searchTerm.value
    if (selectedCategory.value) filters.category = selectedCategory.value
    if (ncmFilter.value) filters.ncm = ncmFilter.value
    if (selectedPeriod.value) filters.period = selectedPeriod.value
    if (startDate.value) filters.startDate = startDate.value
    if (endDate.value) filters.endDate = endDate.value
    
    const paginationOptions = {
      page,
      pageSize: pageSize.value,
      orderBy: orderBy.value,
      orderDirection: 'asc' as const
    }
    
    searchResults.value = await searchProducts(filters, paginationOptions)
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

const clearCategory = () => {
  selectedCategory.value = ''
  performSearch()
}

const clearNCM = () => {
  ncmFilter.value = ''
  performSearch()
}

const clearPeriod = () => {
  selectedPeriod.value = 'last_90_days'
  startDate.value = ''
  endDate.value = ''
  performSearch()
}

const clearAllFilters = () => {
  searchTerm.value = ''
  selectedCategory.value = ''
  ncmFilter.value = ''
  selectedPeriod.value = 'last_90_days'
  startDate.value = ''
  endDate.value = ''
  orderBy.value = 'descricao'
  resetFilters()
  searchResults.value = null
}

const exportProducts = async (format: 'excel' | 'pdf') => {
  try {
    await exportData('products', format)
    // Show success message or handle download
  } catch (err) {
    // Error handled by composable
  }
}

const viewProductDetails = (product: any) => {
  // Navigate to product details or show modal
  console.log('View product details:', product)
}

const getPeriodLabel = (period: string): string => {
  const labels: Record<string, string> = {
    'last_30_days': 'Últimos 30 dias',
    'last_90_days': 'Últimos 90 dias',
    'last_6_months': 'Últimos 6 meses',
    'last_12_months': 'Últimos 12 meses',
    'current_year': 'Ano atual'
  }
  return labels[period] || period
}

// Load initial categories
onMounted(async () => {
  // Load categories from products API
  try {
    const response = await $fetch('/api/dashboard/products', {
      query: { period: 'last_12_months', limit: 1000 }
    })
    
    if (response.categories_distribution) {
      availableCategories.value = Object.keys(response.categories_distribution).sort()
    }
  } catch (err) {
    console.error('Error loading categories:', err)
  }
})
</script>