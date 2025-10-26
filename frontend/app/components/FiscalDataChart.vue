<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
          </svg>
          {{ title }}
        </h3>
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-sm btn-ghost">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
            </svg>
          </div>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
            <li><a @click="changeChartType('bar')">Gráfico de Barras</a></li>
            <li><a @click="changeChartType('line')">Gráfico de Linha</a></li>
            <li><a @click="changeChartType('pie')">Gráfico de Pizza</a></li>
            <li><hr class="my-1"></li>
            <li><a @click="exportChart">Exportar Dados</a></li>
          </ul>
        </div>
      </div>

      <!-- Chart Container -->
      <div class="relative">
        <!-- Loading State -->
        <div v-if="isLoading" class="h-64 bg-base-100 rounded-lg flex items-center justify-center">
          <div class="text-center">
            <span class="loading loading-spinner loading-lg text-primary"></span>
            <p class="text-base-content/50 mt-2">Carregando dados...</p>
          </div>
        </div>

        <!-- Chart Display -->
        <div v-else-if="chartData.length > 0" class="h-64 bg-base-100 rounded-lg p-4">
          <!-- Bar Chart -->
          <div v-if="chartType === 'bar'" class="h-full flex items-end justify-between gap-2">
            <div
              v-for="(item, index) in chartData"
              :key="index"
              class="flex-1 flex flex-col items-center"
            >
              <div class="text-xs text-base-content/70 mb-1">{{ formatValue(item.value) }}</div>
              <div
                class="w-full rounded-t transition-all duration-500 ease-out"
                :class="getBarColor(index)"
                :style="{ height: `${(item.value / maxValue) * 100}%` }"
              ></div>
              <div class="text-xs text-base-content/50 mt-2 text-center">{{ item.label }}</div>
            </div>
          </div>

          <!-- Line Chart (Simplified) -->
          <div v-else-if="chartType === 'line'" class="h-full flex items-end justify-between">
            <svg class="w-full h-full" viewBox="0 0 400 200">
              <polyline
                :points="getLinePoints()"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                class="text-primary"
              />
              <g v-for="(item, index) in chartData" :key="index">
                <circle
                  :cx="(index / (chartData.length - 1)) * 380 + 10"
                  :cy="200 - (item.value / maxValue) * 180"
                  r="4"
                  class="fill-primary"
                />
                <text
                  :x="(index / (chartData.length - 1)) * 380 + 10"
                  :y="195"
                  text-anchor="middle"
                  class="text-xs fill-current text-base-content/50"
                >
                  {{ item.label }}
                </text>
              </g>
            </svg>
          </div>

          <!-- Pie Chart (Simplified) -->
          <div v-else-if="chartType === 'pie'" class="h-full flex items-center justify-center">
            <div class="relative">
              <svg class="w-48 h-48" viewBox="0 0 200 200">
                <g v-for="(segment, index) in pieSegments" :key="index">
                  <path
                    :d="segment.path"
                    :class="getPieColor(index)"
                    class="stroke-base-100 stroke-2"
                  />
                </g>
              </svg>
              <!-- Legend -->
              <div class="absolute -right-32 top-0 space-y-2">
                <div
                  v-for="(item, index) in chartData.slice(0, 5)"
                  :key="index"
                  class="flex items-center gap-2 text-xs"
                >
                  <div class="w-3 h-3 rounded" :class="getPieColorBg(index)"></div>
                  <span>{{ item.label }}</span>
                  <span class="text-base-content/50">{{ formatValue(item.value) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="h-64 bg-base-100 rounded-lg flex items-center justify-center">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
            </svg>
            <p class="text-base-content/50">Nenhum dado disponível</p>
          </div>
        </div>
      </div>

      <!-- Chart Summary -->
      <div v-if="chartData.length > 0" class="mt-4 p-3 bg-base-100 rounded-lg">
        <div class="grid grid-cols-3 gap-4 text-center text-sm">
          <div>
            <div class="font-semibold text-primary">{{ formatValue(totalValue) }}</div>
            <div class="text-base-content/50">Total</div>
          </div>
          <div>
            <div class="font-semibold text-secondary">{{ formatValue(averageValue) }}</div>
            <div class="text-base-content/50">Média</div>
          </div>
          <div>
            <div class="font-semibold text-accent">{{ chartData.length }}</div>
            <div class="text-base-content/50">Itens</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { ChartDataItem, PieSegment } from '~/types/dashboard'

// Props
interface Props {
  title: string
  dataType: 'revenue' | 'suppliers' | 'categories' | 'regions'
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Dados Fiscais',
  dataType: 'revenue'
})

// Reactive state
const chartData = ref<ChartDataItem[]>([])
const chartType = ref<'bar' | 'line' | 'pie'>('bar')
const isLoading = ref(true)

// Mock data based on type
const mockData = {
  revenue: [
    { label: 'Jan', value: 125000 },
    { label: 'Fev', value: 142000 },
    { label: 'Mar', value: 138000 },
    { label: 'Abr', value: 156000 },
    { label: 'Mai', value: 167000 },
    { label: 'Jun', value: 145000 }
  ],
  suppliers: [
    { label: 'Fornecedor A', value: 45 },
    { label: 'Fornecedor B', value: 32 },
    { label: 'Fornecedor C', value: 28 },
    { label: 'Fornecedor D', value: 22 },
    { label: 'Fornecedor E', value: 18 }
  ],
  categories: [
    { label: 'Materiais', value: 35 },
    { label: 'Serviços', value: 28 },
    { label: 'Equipamentos', value: 22 },
    { label: 'Software', value: 15 }
  ],
  regions: [
    { label: 'Sudeste', value: 45 },
    { label: 'Sul', value: 25 },
    { label: 'Nordeste', value: 18 },
    { label: 'Centro-Oeste', value: 12 }
  ]
}

// Computed properties
const maxValue = computed(() => Math.max(...chartData.value.map(item => item.value)))
const totalValue = computed(() => chartData.value.reduce((sum, item) => sum + item.value, 0))
const averageValue = computed(() => totalValue.value / chartData.value.length || 0)

const pieSegments = computed(() => {
  const segments: PieSegment[] = []
  let currentAngle = 0
  const total = totalValue.value

  chartData.value.forEach(item => {
    const percentage = (item.value / total) * 100
    const angle = (item.value / total) * 360
    const startAngle = currentAngle
    const endAngle = currentAngle + angle

    const x1 = 100 + 80 * Math.cos((startAngle - 90) * Math.PI / 180)
    const y1 = 100 + 80 * Math.sin((startAngle - 90) * Math.PI / 180)
    const x2 = 100 + 80 * Math.cos((endAngle - 90) * Math.PI / 180)
    const y2 = 100 + 80 * Math.sin((endAngle - 90) * Math.PI / 180)

    const largeArcFlag = angle > 180 ? 1 : 0

    const path = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArcFlag} 1 ${x2} ${y2} Z`

    segments.push({ path, percentage })
    currentAngle += angle
  })

  return segments
})

// Load real data based on chart type
const loadChartData = async () => {
  try {
    isLoading.value = true;

    let data: ChartDataItem[] = [];

    switch (props.dataType) {
      case 'revenue':
        // Load financial trends data
        const trendsResponse = await $fetch('/api/v1/api/dashboard/trends', {
          query: { period: 'last_6_months', trend_type: 'valor' }
        });
        if (trendsResponse && trendsResponse.trend_data) {
          data = trendsResponse.trend_data.map((item: any) => ({
            label: new Date(item.periodo).toLocaleDateString('pt-BR', { month: 'short' }),
            value: Number(item.valor)
          }));
        }
        break;

      case 'suppliers':
        // Load top suppliers data
        const suppliersResponse = await $fetch('/api/v1/api/dashboard/suppliers', {
          query: { period: 'last_90_days', limit: 5 }
        });
        if (suppliersResponse && suppliersResponse.top_suppliers) {
          data = suppliersResponse.top_suppliers.map((supplier: any) => ({
            label: supplier.razao_social.substring(0, 15) + (supplier.razao_social.length > 15 ? '...' : ''),
            value: Number(supplier.valor_total)
          }));
        }
        break;

      case 'categories':
        // Load product categories data
        const productsResponse = await $fetch('/api/v1/api/dashboard/products', {
          query: { period: 'last_90_days' }
        });
        if (productsResponse && productsResponse.categories_distribution) {
          data = Object.entries(productsResponse.categories_distribution).map(([category, dist]: [string, any]) => ({
            label: category,
            value: dist.total_produtos
          }));
        }
        break;

      case 'regions':
        // Load suppliers by state (mock data for now)
        const regionResponse = { items: [
          { uf: 'SP' }, { uf: 'SP' }, { uf: 'RJ' }, { uf: 'MG' }, { uf: 'RS' },
          { uf: 'SP' }, { uf: 'RJ' }, { uf: 'PR' }, { uf: 'SC' }, { uf: 'GO' }
        ] };
        if (regionResponse && regionResponse.items) {
          const stateCount: Record<string, number> = {};
          regionResponse.items.forEach((emitente: any) => {
            stateCount[emitente.uf] = (stateCount[emitente.uf] || 0) + 1;
          });
          
          data = Object.entries(stateCount)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([state, count]) => ({
              label: state,
              value: count
            }));
        }
        break;

      default:
        data = [];
    }

    // If no real data, use mock data as fallback
    if (data.length === 0) {
      data = mockData[props.dataType] || [];
    }

    chartData.value = data;
  } catch (err: any) {
    console.error('Error loading chart data:', err);
    
    // Fallback to mock data on error
    chartData.value = mockData[props.dataType] || [];
  } finally {
    isLoading.value = false;
  }
};

// Initialize data
onMounted(() => {
  loadChartData();
})

// Methods
const changeChartType = (type: 'bar' | 'line' | 'pie') => {
  chartType.value = type
}

const exportChart = () => {
  const dataStr = JSON.stringify(chartData.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.title.toLowerCase().replace(/\s+/g, '_')}_data.json`
  link.click()
  URL.revokeObjectURL(url)
}

const formatValue = (value: number) => {
  if (props.dataType === 'revenue') {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0
    }).format(value)
  }
  return value.toLocaleString('pt-BR')
}

const getBarColor = (index: number) => {
  const colors = ['bg-primary', 'bg-secondary', 'bg-accent', 'bg-info', 'bg-success', 'bg-warning']
  return colors[index % colors.length]
}

const getPieColor = (index: number) => {
  const colors = ['fill-primary', 'fill-secondary', 'fill-accent', 'fill-info', 'fill-success', 'fill-warning']
  return colors[index % colors.length]
}

const getPieColorBg = (index: number) => {
  const colors = ['bg-primary', 'bg-secondary', 'bg-accent', 'bg-info', 'bg-success', 'bg-warning']
  return colors[index % colors.length]
}

const getLinePoints = () => {
  return chartData.value
    .map((item, index) => {
      const x = (index / (chartData.value.length - 1)) * 380 + 10
      const y = 200 - (item.value / maxValue.value) * 180
      return `${x},${y}`
    })
    .join(' ')
}
</script>