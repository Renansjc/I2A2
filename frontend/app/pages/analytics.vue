<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Análises</h1>
        <p class="text-base-content/70">Análise avançada de dados fiscais e insights</p>
      </div>
      <div class="dropdown dropdown-end">
        <div tabindex="0" role="button" class="btn btn-primary">
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
          </svg>
          Exportar Painel
        </div>
        <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
          <li><a>Exportar como PDF</a></li>
          <li><a>Exportar como Excel</a></li>
          <li><a>Agendar Relatório</a></li>
        </ul>
      </div>
    </div>

    <!-- Time Period Selector -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center space-x-4">
            <h3 class="text-lg font-semibold">Período</h3>
            <div class="join">
              <button 
                v-for="period in timePeriods"
                :key="period.value"
                class="join-item btn btn-sm"
                :class="{ 'btn-active': selectedPeriod === period.value }"
                @click="selectedPeriod = period.value"
              >
                {{ period.label }}
              </button>
            </div>
          </div>
          
          <div class="flex items-center space-x-2">
            <input 
              v-model="customStartDate"
              type="date" 
              class="input input-bordered input-sm"
            />
            <span>até</span>
            <input 
              v-model="customEndDate"
              type="date" 
              class="input input-bordered input-sm"
            />
            <button class="btn btn-sm btn-primary">Aplicar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Key Performance Indicators -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div 
        v-for="kpi in kpis"
        :key="kpi.label"
        class="stat bg-base-200 rounded-lg shadow hover:shadow-lg transition-shadow"
      >
        <div class="stat-figure" :class="kpi.color">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20" v-html="kpi.icon"></svg>
        </div>
        <div class="stat-title">{{ kpi.label }}</div>
        <div class="stat-value" :class="kpi.color">{{ kpi.value }}</div>
        <div class="stat-desc">
          <span :class="getTrendColor(kpi.trend)">
            {{ kpi.change }}
          </span>
          {{ kpi.period }}
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Revenue Trend Chart -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title">Tendência de Receita</h3>
            <div class="dropdown dropdown-end">
              <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                </svg>
              </div>
              <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
                <li><a>View Details</a></li>
                <li><a>Export Chart</a></li>
              </ul>
            </div>
          </div>
          <div class="h-64 bg-base-100 rounded flex items-center justify-center">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
              </svg>
              <p class="text-base-content/50">Gráfico de Linha - Receita ao longo do tempo</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Supplier Distribution -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title">Distribuição de Fornecedores</h3>
            <div class="dropdown dropdown-end">
              <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                </svg>
              </div>
              <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
                <li><a>View Details</a></li>
                <li><a>Export Chart</a></li>
              </ul>
            </div>
          </div>
          <div class="h-64 bg-base-100 rounded flex items-center justify-center">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"></path>
              </svg>
              <p class="text-base-content/50">Gráfico de Pizza - Distribuição de fornecedores</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Product Categories -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title">Categorias de Produtos</h3>
            <div class="dropdown dropdown-end">
              <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                </svg>
              </div>
              <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
                <li><a>View Details</a></li>
                <li><a>Export Chart</a></li>
              </ul>
            </div>
          </div>
          <div class="h-64 bg-base-100 rounded flex items-center justify-center">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
              </svg>
              <p class="text-base-content/50">Gráfico de Barras - Desempenho por categoria</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tax Analysis -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title">Análise Fiscal</h3>
            <div class="dropdown dropdown-end">
              <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                </svg>
              </div>
              <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
                <li><a>View Details</a></li>
                <li><a>Export Chart</a></li>
              </ul>
            </div>
          </div>
          <div class="h-64 bg-base-100 rounded flex items-center justify-center">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
              </svg>
              <p class="text-base-content/50">Gráfico Empilhado - Detalhamento fiscal</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Tables -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Top Suppliers -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Principais Fornecedores</h3>
          <div class="overflow-x-auto">
            <table class="table table-zebra table-sm">
              <thead>
                <tr>
                  <th>Fornecedor</th>
                  <th>Volume</th>
                  <th>Crescimento</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="supplier in topSuppliers" :key="supplier.id">
                  <td>
                    <div class="font-semibold">{{ supplier.name }}</div>
                    <div class="text-sm text-base-content/70">{{ supplier.location }}</div>
                  </td>
                  <td>{{ supplier.volume }}</td>
                  <td>
                    <span 
                      class="badge badge-sm"
                      :class="{
                        'badge-success': supplier.growth > 0,
                        'badge-error': supplier.growth < 0,
                        'badge-ghost': supplier.growth === 0
                      }"
                    >
                      {{ supplier.growth > 0 ? '+' : '' }}{{ supplier.growth }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Recent Insights -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Insights da IA</h3>
          <div class="space-y-3">
            <div 
              v-for="insight in aiInsights"
              :key="insight.id"
              class="alert"
              :class="getInsightClass(insight.type)"
            >
              <div>
                <h5 class="font-semibold">{{ insight.title }}</h5>
                <p class="text-sm">{{ insight.description }}</p>
                <div class="text-xs text-base-content/50 mt-1">
                  {{ formatDate(insight.generatedAt) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({
  layout: 'default'
})

// Reactive state
const selectedPeriod = ref('30d')
const customStartDate = ref('')
const customEndDate = ref('')

// Mock data
const timePeriods = [
  { label: '7D', value: '7d' },
  { label: '30D', value: '30d' },
  { label: '90D', value: '90d' },
  { label: '1Y', value: '1y' }
]

const kpis = [
  {
    label: 'Receita Total',
    value: 'R$ 2,4M',
    change: '+12,5%',
    trend: 'up',
    period: 'vs mês anterior',
    color: 'text-success',
    icon: '<path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>'
  },
  {
    label: 'Quantidade de Notas',
    value: '1.247',
    change: '+8,3%',
    trend: 'up',
    period: 'vs mês anterior',
    color: 'text-primary',
    icon: '<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>'
  },
  {
    label: 'Eficiência Fiscal',
    value: '94,2%',
    change: '+2,1%',
    trend: 'up',
    period: 'vs mês anterior',
    color: 'text-warning',
    icon: '<path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>'
  },
  {
    label: 'Fornecedores Ativos',
    value: '89',
    change: '-3,2%',
    trend: 'down',
    period: 'vs mês anterior',
    color: 'text-info',
    icon: '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
  }
]

const topSuppliers = [
  { id: 1, name: 'Fornecedor ABC Ltda', location: 'São Paulo, SP', volume: 'R$ 450K', growth: 15.2 },
  { id: 2, name: 'Empresa XYZ S.A.', location: 'Rio de Janeiro, RJ', volume: 'R$ 320K', growth: -2.1 },
  { id: 3, name: 'Distribuidora 123', location: 'Belo Horizonte, MG', volume: 'R$ 280K', growth: 8.7 },
  { id: 4, name: 'Comercial DEF', location: 'Porto Alegre, RS', volume: 'R$ 195K', growth: 22.3 },
  { id: 5, name: 'Indústria GHI', location: 'Curitiba, PR', volume: 'R$ 175K', growth: 0 }
]

const aiInsights = [
  {
    id: 1,
    type: 'success',
    title: 'Oportunidade de Otimização Fiscal',
    description: 'Economia potencial de R$ 45K identificada nos cálculos de ICMS para categoria eletrônicos.',
    generatedAt: new Date('2024-01-15T10:30:00')
  },
  {
    id: 2,
    type: 'warning',
    title: 'Alerta de Risco de Fornecedor',
    description: 'Fornecedor ABC Ltda apresenta padrões irregulares de pagamento. Considere diversificação.',
    generatedAt: new Date('2024-01-14T15:45:00')
  },
  {
    id: 3,
    type: 'info',
    title: 'Padrão Sazonal Detectado',
    description: 'Compras de material de escritório tipicamente aumentam 30% no T1. Planeje adequadamente.',
    generatedAt: new Date('2024-01-13T09:15:00')
  }
]

// Methods
const getTrendColor = (trend: string): string => {
  switch (trend) {
    case 'up': return 'text-success'
    case 'down': return 'text-error'
    default: return 'text-base-content/70'
  }
}

const getInsightClass = (type: string): string => {
  switch (type) {
    case 'success': return 'alert-success'
    case 'warning': return 'alert-warning'
    case 'error': return 'alert-error'
    default: return 'alert-info'
  }
}

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>