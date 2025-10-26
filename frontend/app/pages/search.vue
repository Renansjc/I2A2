<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="hero bg-gradient-to-r from-info to-accent text-info-content rounded-lg">
      <div class="hero-content py-6">
        <div class="max-w-4xl w-full text-center">
          <h1 class="text-3xl font-bold">Busca e Filtros Avançados</h1>
          <p class="py-2 text-lg">Encontre fornecedores e produtos com filtros personalizados</p>
        </div>
      </div>
    </div>

    <!-- Search Tabs -->
    <div class="tabs tabs-boxed bg-base-200 p-1">
      <button 
        @click="activeTab = 'suppliers'"
        :class="{ 'tab-active': activeTab === 'suppliers' }"
        class="tab tab-lg flex-1"
      >
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        Fornecedores
      </button>
      <button 
        @click="activeTab = 'products'"
        :class="{ 'tab-active': activeTab === 'products' }"
        class="tab tab-lg flex-1"
      >
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path>
        </svg>
        Produtos
      </button>
    </div>

    <!-- Search Components -->
    <div class="min-h-screen">
      <SuppliersSearch v-if="activeTab === 'suppliers'" />
      <ProductsSearch v-if="activeTab === 'products'" />
    </div>

    <!-- Quick Actions -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Ações Rápidas</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <button 
            @click="quickSearchTopSuppliers"
            class="btn btn-outline btn-primary"
            :disabled="isLoading"
          >
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"></path>
            </svg>
            Top Fornecedores
          </button>
          
          <button 
            @click="quickSearchNewProducts"
            class="btn btn-outline btn-secondary"
            :disabled="isLoading"
          >
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"></path>
            </svg>
            Produtos Recentes
          </button>
          
          <button 
            @click="quickSearchByState"
            class="btn btn-outline btn-accent"
            :disabled="isLoading"
          >
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
            </svg>
            Por Estado
          </button>
          
          <button 
            @click="quickSearchHighValue"
            class="btn btn-outline btn-warning"
            :disabled="isLoading"
          >
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
            </svg>
            Alto Valor
          </button>
        </div>
      </div>
    </div>

    <!-- Search Tips -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          Dicas de Busca
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="font-semibold mb-2">Busca de Fornecedores</h4>
            <ul class="list-disc list-inside space-y-1 text-sm opacity-80">
              <li>Use o CNPJ completo ou parcial para busca exata</li>
              <li>Digite parte da razão social para encontrar empresas</li>
              <li>Filtre por estado (UF) para análise regional</li>
              <li>Ordene por volume de documentos ou valor total</li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-2">Busca de Produtos</h4>
            <ul class="list-disc list-inside space-y-1 text-sm opacity-80">
              <li>Busque por descrição ou código do produto</li>
              <li>Use filtros de categoria para segmentar análises</li>
              <li>Filtre por código NCM para classificação fiscal</li>
              <li>Defina períodos personalizados para análise temporal</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Page setup
definePageMeta({
  layout: 'default'
})

// Reactive state
const activeTab = ref<'suppliers' | 'products'>('suppliers')
const isLoading = ref(false)

// Quick search methods
const quickSearchTopSuppliers = () => {
  activeTab.value = 'suppliers'
  // Trigger search for top suppliers
  nextTick(() => {
    // This would trigger the suppliers search component
    console.log('Quick search: Top suppliers')
  })
}

const quickSearchNewProducts = () => {
  activeTab.value = 'products'
  // Trigger search for recent products
  nextTick(() => {
    console.log('Quick search: New products')
  })
}

const quickSearchByState = () => {
  activeTab.value = 'suppliers'
  // Trigger search by state
  nextTick(() => {
    console.log('Quick search: By state')
  })
}

const quickSearchHighValue = () => {
  activeTab.value = 'products'
  // Trigger search for high value products
  nextTick(() => {
    console.log('Quick search: High value products')
  })
}
</script>