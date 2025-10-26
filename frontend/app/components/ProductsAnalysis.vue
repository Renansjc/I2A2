<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title text-lg">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path>
          </svg>
          Análise de Produtos
        </h3>
        <div class="flex items-center gap-2 flex-wrap">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="Buscar produtos..."
            class="input input-sm input-bordered"
          />
          <select 
            v-model="selectedCategory"
            class="select select-sm select-bordered"
          >
            <option value="">Todas as categorias</option>
            <option v-for="category in availableCategories" :key="category" :value="category">
              {{ category }}
            </option>
          </select>
          <select 
            v-model="selectedPeriod"
            class="select select-sm select-bordered"
          >
            <option value="last_30_days">Últimos 30 dias</option>
            <option value="last_90_days">Últimos 90 dias</option>
            <option value="last_6_months">Últimos 6 meses</option>
            <option value="last_12_months">Últimos 12 meses</option>
          </select>
          <select 
            v-model="productsLimit"
            class="select select-sm select-bordered"
          >
            <option :value="10">Top 10</option>
            <option :value="20">Top 20</option>
            <option :value="50">Top 50</option>
          </select>
          <div class="tooltip" data-tip="Atualização automática">
            <input 
              type="checkbox" 
              v-model="autoRefreshEnabled"
              @change="autoRefreshEnabled ? startAutoRefresh() : stopAutoRefresh()"
              class="toggle toggle-sm toggle-primary"
            />
          </div>
          <button 
            @click="loadProductsData" 
            class="btn btn-sm btn-ghost"
            :disabled="isLoading"
          >
            <svg 
              class="w-4 h-4" 
              :class="{ 'animate-spin': isLoading }"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
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

      <!-- Products Data -->
      <div v-else-if="productsData" class="space-y-6">
        <!-- Categories Distribution -->
        <div v-if="Object.keys(productsData.categories_distribution).length > 0">
          <h4 class="font-semibold mb-3">Distribuição por Categoria</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div 
              v-for="(distribution, category) in productsData.categories_distribution" 
              :key="category"
              class="stat bg-base-100 rounded-lg shadow-sm"
            >
              <div class="stat-title text-xs">{{ category }}</div>
              <div class="stat-value text-sm">{{ distribution.total_produtos }}</div>
              <div class="stat-desc text-xs">{{ formatCurrency(distribution.valor_total) }}</div>
            </div>
          </div>
        </div>

        <!-- Top Products -->
        <div v-if="productsData.top_products_by_value?.length > 0">
          <h4 class="font-semibold mb-3">Top Produtos por Valor</h4>
          <div class="space-y-2">
            <div 
              v-for="(product, index) in filteredProducts" 
              :key="product.codigo_produto"
              class="flex items-center justify-between p-3 bg-base-100 rounded-lg hover:bg-base-300 transition-colors cursor-pointer"
              @click="navigateToProductDetails(product.codigo_produto)"
            >
              <div class="flex items-center gap-3">
                <div class="avatar placeholder">
                  <div class="bg-secondary text-secondary-content rounded-full w-8">
                    <span class="text-xs font-bold">{{ index + 1 }}</span>
                  </div>
                </div>
                <div>
                  <div class="font-medium text-sm">{{ product.descricao }}</div>
                  <div class="text-xs opacity-70">
                    Código: {{ product.codigo_produto }}
                    <span v-if="product.categoria"> • {{ product.categoria }}</span>
                    <span v-if="product.ncm"> • NCM: {{ product.ncm }}</span>
                  </div>
                </div>
              </div>
              <div class="text-right">
                <div class="font-bold text-sm">{{ formatCurrency(product.valor_total) }}</div>
                <div class="text-xs opacity-70">
                  Qtd: {{ formatQuantity(product.quantidade_total) }}
                </div>
                <div class="text-xs opacity-60">
                  {{ product.fornecedores_distintos }} fornecedores
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="stats stats-horizontal bg-base-100 shadow">
          <div class="stat">
            <div class="stat-title text-xs">Total Produtos</div>
            <div class="stat-value text-lg">{{ productsData.total_products }}</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Categorias</div>
            <div class="stat-value text-lg">{{ Object.keys(productsData.categories_distribution).length }}</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Exibindo</div>
            <div class="stat-value text-lg">{{ filteredProducts.length }}</div>
          </div>
          <div class="stat">
            <div class="stat-title text-xs">Período</div>
            <div class="stat-desc text-xs">{{ productsData.periodo_analise }}</div>
          </div>
          <div v-if="lastUpdated" class="stat">
            <div class="stat-title text-xs">Última Atualização</div>
            <div class="stat-desc text-xs">{{ formatLastUpdated(lastUpdated) }}</div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-base-content opacity-50 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path>
        </svg>
        <p class="text-base-content opacity-70">Nenhum produto encontrado</p>
        <p class="text-sm text-base-content opacity-50">Processe alguns documentos fiscais para ver os dados</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface CategoryDistribution {
  total_produtos: number
  valor_total: number
}

interface ProductSummary {
  codigo_produto: string
  descricao: string
  categoria?: string
  subcategoria?: string
  ncm?: string
  total_documentos: number
  quantidade_total: number
  valor_total: number
  preco_medio: number
  fornecedores_distintos: number
}

interface ProductsResponse {
  total_products: number
  categories_distribution: Record<string, CategoryDistribution>
  top_products_by_value: ProductSummary[]
  periodo_analise: string
}

// Reactive state
const isLoading = ref(false)
const error = ref<string | null>(null)
const productsData = ref<ProductsResponse | null>(null)
const selectedPeriod = ref('last_90_days')
const selectedCategory = ref('')
const availableCategories = ref<string[]>([])
const productsLimit = ref(10)
const lastUpdated = ref<Date | null>(null)
const autoRefreshEnabled = ref(true)
const autoRefreshInterval = ref<NodeJS.Timeout | null>(null)
const searchQuery = ref('')

// Load products data from API
const loadProductsData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const query: any = {
      period: selectedPeriod.value,
      limit: productsLimit.value
    }

    if (selectedCategory.value) {
      query.category = selectedCategory.value
    }

    const { apiCall } = useApi()
    const data = await apiCall<ProductsResponse>('/api/v1/api/dashboard/products', {
      query,
      cache: true,
      cacheTTL: 300000, // 5 minutes cache
      retry: 3
    })

    productsData.value = data
    lastUpdated.value = new Date()
    
    // Update available categories
    if (data.categories_distribution) {
      availableCategories.value = Object.keys(data.categories_distribution)
    }
  } catch (err: any) {
    console.error('Error loading products data:', err)
    error.value = err.message || err.data?.mensagem || 'Erro ao carregar dados de produtos'
  } finally {
    isLoading.value = false
  }
}

// Utility functions
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

const formatQuantity = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(value)
}

const formatLastUpdated = (date: Date): string => {
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Navigation function
const navigateToProductDetails = (productCode: string) => {
  // TODO: Implement navigation to product details page
  console.log('Navigate to product details:', productCode)
  // navigateTo(`/products/${productCode}`)
}

// Computed property for filtered products
const filteredProducts = computed(() => {
  if (!productsData.value?.top_products_by_value) return []
  
  let products = productsData.value.top_products_by_value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    products = products.filter(product => 
      product.descricao.toLowerCase().includes(query) ||
      product.codigo_produto.toLowerCase().includes(query) ||
      product.categoria?.toLowerCase().includes(query) ||
      product.ncm?.includes(query)
    )
  }
  
  return products
})

// Auto-refresh functionality
const startAutoRefresh = () => {
  if (autoRefreshEnabled.value && !autoRefreshInterval.value) {
    autoRefreshInterval.value = setInterval(() => {
      loadProductsData()
    }, 300000) // Refresh every 5 minutes
  }
}

const stopAutoRefresh = () => {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value)
    autoRefreshInterval.value = null
  }
}

// Watch for changes to reload data
watch([selectedPeriod, selectedCategory, productsLimit], () => {
  loadProductsData()
})

// Search is handled by computed property, no debouncing needed
// The computed property automatically updates when searchQuery changes

// Load data on mount and start auto-refresh
onMounted(() => {
  loadProductsData()
  startAutoRefresh()
})

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>