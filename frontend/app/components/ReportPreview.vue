<template>
  <div class="space-y-4">
    <!-- Report Header -->
    <div class="flex justify-between items-center">
      <div>
        <h3 class="text-xl font-bold">{{ report.title }}</h3>
        <p class="text-base-content/70">{{ report.description }}</p>
      </div>
      <div class="dropdown dropdown-end">
        <div tabindex="0" role="button" class="btn btn-primary">
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
          Exportar
        </div>
        <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
          <li><a @click="exportReport('pdf')">Exportar como PDF</a></li>
          <li><a @click="exportReport('xlsx')">Exportar como Excel</a></li>
          <li><a @click="exportReport('docx')">Exportar como Word</a></li>
        </ul>
      </div>
    </div>

    <!-- Report Metadata -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Gerado</div>
        <div class="stat-value text-sm">{{ formatDate(report.generatedAt) }}</div>
      </div>
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Período dos Dados</div>
        <div class="stat-value text-sm">{{ report.dataPeriod }}</div>
      </div>
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Registros</div>
        <div class="stat-value text-sm">{{ report.recordCount.toLocaleString() }}</div>
      </div>
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Formato</div>
        <div class="stat-value text-sm">{{ report.format.toUpperCase() }}</div>
      </div>
    </div>

    <!-- Report Content Preview -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <div class="tabs tabs-bordered mb-4">
          <a 
            class="tab"
            :class="{ 'tab-active': activeTab === 'preview' }"
            @click="activeTab = 'preview'"
          >
            Visualização
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeTab === 'data' }"
            @click="activeTab = 'data'"
          >
            Dados Brutos
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeTab === 'charts' }"
            @click="activeTab = 'charts'"
          >
            Gráficos
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeTab === 'viewer' }"
            @click="activeTab = 'viewer'"
          >
            Visualizador
          </a>
        </div>

        <!-- Preview Tab -->
        <div v-if="activeTab === 'preview'" class="space-y-6">
          <!-- Executive Summary -->
          <div class="prose max-w-none">
            <h4>Resumo Executivo</h4>
            <p>{{ report.executiveSummary }}</p>
          </div>

          <!-- Key Metrics -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div 
              v-for="metric in report.keyMetrics"
              :key="metric.label"
              class="stat bg-base-200 rounded-lg"
            >
              <div class="stat-title">{{ metric.label }}</div>
              <div class="stat-value" :class="getMetricColor(metric.trend)">
                {{ metric.value }}
              </div>
              <div class="stat-desc">
                <span :class="getTrendColor(metric.trend)">
                  {{ metric.change }}
                </span>
                vs período anterior
              </div>
            </div>
          </div>

          <!-- Top Insights -->
          <div>
            <h5 class="text-lg font-semibold mb-3">Principais Insights</h5>
            <div class="space-y-2">
              <div 
                v-for="insight in report.insights"
                :key="insight.id"
                class="alert"
                :class="getInsightClass(insight.type)"
              >
                <div>
                  <h6 class="font-semibold">{{ insight.title }}</h6>
                  <p class="text-sm">{{ insight.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Tab -->
        <div v-if="activeTab === 'data'" class="space-y-4">
          <div class="flex justify-between items-center">
            <h5 class="text-lg font-semibold">Tabela de Dados</h5>
            <div class="join">
              <input 
                v-model="searchTerm"
                class="input input-bordered input-sm join-item" 
                placeholder="Buscar..."
              />
              <button class="btn btn-sm join-item">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
                </svg>
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="table table-zebra table-sm">
              <thead>
                <tr>
                  <th v-for="column in report.dataColumns" :key="column">
                    {{ column }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in filteredData" :key="index">
                  <td v-for="(value, colIndex) in row" :key="colIndex">
                    {{ value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex justify-center">
            <div class="join">
              <button class="join-item btn btn-sm" :disabled="currentPage === 1" @click="currentPage--">
                «
              </button>
              <button class="join-item btn btn-sm">
                Página {{ currentPage }} de {{ totalPages }}
              </button>
              <button class="join-item btn btn-sm" :disabled="currentPage === totalPages" @click="currentPage++">
                »
              </button>
            </div>
          </div>
        </div>

        <!-- Charts Tab -->
        <div v-if="activeTab === 'charts'" class="space-y-6">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Chart placeholders - will be replaced with actual Chart.js components -->
            <div 
              v-for="chart in report.charts"
              :key="chart.id"
              class="card bg-base-200"
            >
              <div class="card-body">
                <h6 class="card-title text-base">{{ chart.title }}</h6>
                <div class="h-64 bg-base-100 rounded flex items-center justify-center">
                  <div class="text-center">
                    <svg class="w-12 h-12 mx-auto text-base-content/30 mb-2" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                    </svg>
                    <p class="text-sm text-base-content/50">{{ chart.type }} Chart</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Document Viewer Tab -->
        <div v-if="activeTab === 'viewer'" class="space-y-4">
          <div class="flex justify-between items-center">
            <h5 class="text-lg font-semibold">Visualizador de Documento</h5>
            <div class="join">
              <button 
                v-for="format in ['pdf', 'xlsx', 'docx']"
                :key="format"
                class="join-item btn btn-sm"
                :class="{ 'btn-active': viewerFormat === format }"
                @click="viewerFormat = format"
              >
                {{ format.toUpperCase() }}
              </button>
            </div>
          </div>

          <!-- PDF Viewer -->
          <div v-if="viewerFormat === 'pdf'" class="bg-base-100 rounded-lg p-4">
            <div class="flex justify-between items-center mb-4">
              <div class="flex items-center space-x-2">
                <svg class="w-5 h-5 text-error" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                </svg>
                <span class="font-medium">{{ report.title }}.pdf</span>
              </div>
              <div class="flex items-center space-x-2">
                <button class="btn btn-sm btn-ghost" @click="pdfZoom -= 0.1" :disabled="pdfZoom <= 0.5">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clip-rule="evenodd"></path>
                  </svg>
                </button>
                <span class="text-sm">{{ Math.round(pdfZoom * 100) }}%</span>
                <button class="btn btn-sm btn-ghost" @click="pdfZoom += 0.1" :disabled="pdfZoom >= 2">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="border border-base-300 rounded-lg overflow-hidden" :style="`transform: scale(${pdfZoom}); transform-origin: top left;`">
              <div class="bg-white p-8 min-h-96">
                <!-- PDF Preview Content -->
                <div class="space-y-6">
                  <div class="text-center border-b pb-4">
                    <h1 class="text-2xl font-bold text-gray-800">{{ report.title }}</h1>
                    <p class="text-gray-600">{{ report.description }}</p>
                    <p class="text-sm text-gray-500">Gerado em {{ formatDate(report.generatedAt) }}</p>
                  </div>
                  
                  <div class="grid grid-cols-3 gap-4">
                    <div v-for="metric in report.keyMetrics" :key="metric.label" class="text-center p-4 bg-gray-50 rounded">
                      <div class="text-2xl font-bold text-gray-800">{{ metric.value }}</div>
                      <div class="text-sm text-gray-600">{{ metric.label }}</div>
                      <div class="text-xs" :class="metric.trend === 'up' ? 'text-green-600' : 'text-red-600'">
                        {{ metric.change }}
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 class="text-lg font-semibold text-gray-800 mb-3">Resumo Executivo</h3>
                    <p class="text-gray-700 leading-relaxed">{{ report.executiveSummary }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Excel Viewer -->
          <div v-if="viewerFormat === 'xlsx'" class="bg-base-100 rounded-lg p-4">
            <div class="flex justify-between items-center mb-4">
              <div class="flex items-center space-x-2">
                <svg class="w-5 h-5 text-success" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                </svg>
                <span class="font-medium">{{ report.title }}.xlsx</span>
              </div>
              <div class="tabs tabs-boxed">
                <a 
                  v-for="(sheet, index) in excelSheets"
                  :key="sheet"
                  class="tab tab-sm"
                  :class="{ 'tab-active': activeExcelSheet === index }"
                  @click="activeExcelSheet = index"
                >
                  {{ sheet }}
                </a>
              </div>
            </div>
            
            <div class="overflow-x-auto border border-base-300 rounded-lg">
              <table class="table table-xs table-pin-rows table-pin-cols">
                <thead>
                  <tr class="bg-base-200">
                    <th></th>
                    <th v-for="(column, index) in report.dataColumns" :key="index" class="font-bold">
                      {{ column }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in report.data" :key="rowIndex">
                    <th class="bg-base-200 font-bold">{{ rowIndex + 1 }}</th>
                    <td v-for="(cell, cellIndex) in row" :key="cellIndex">
                      {{ cell }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Word Viewer -->
          <div v-if="viewerFormat === 'docx'" class="bg-base-100 rounded-lg p-4">
            <div class="flex justify-between items-center mb-4">
              <div class="flex items-center space-x-2">
                <svg class="w-5 h-5 text-info" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                </svg>
                <span class="font-medium">{{ report.title }}.docx</span>
              </div>
              <div class="flex items-center space-x-2">
                <button class="btn btn-sm btn-ghost">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="border border-base-300 rounded-lg bg-white p-8 min-h-96">
              <!-- Word Document Preview -->
              <div class="prose max-w-none">
                <div class="text-center mb-8">
                  <h1 class="text-3xl font-bold text-gray-800 mb-2">{{ report.title }}</h1>
                  <p class="text-lg text-gray-600 mb-1">{{ report.description }}</p>
                  <p class="text-sm text-gray-500">Relatório gerado em {{ formatDate(report.generatedAt) }}</p>
                  <hr class="my-4">
                </div>
                
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Resumo Executivo</h2>
                <p class="text-gray-700 mb-6 leading-relaxed">{{ report.executiveSummary }}</p>
                
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Métricas Principais</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div v-for="metric in report.keyMetrics" :key="metric.label" class="border border-gray-200 p-4 rounded">
                    <h3 class="font-semibold text-gray-800">{{ metric.label }}</h3>
                    <p class="text-2xl font-bold text-gray-900">{{ metric.value }}</p>
                    <p class="text-sm" :class="metric.trend === 'up' ? 'text-green-600' : 'text-red-600'">
                      {{ metric.change }} vs período anterior
                    </p>
                  </div>
                </div>
                
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Principais Insights</h2>
                <div class="space-y-3">
                  <div v-for="insight in report.insights" :key="insight.id" class="border-l-4 pl-4" 
                       :class="{
                         'border-green-500': insight.type === 'success',
                         'border-yellow-500': insight.type === 'warning',
                         'border-blue-500': insight.type === 'info',
                         'border-red-500': insight.type === 'error'
                       }">
                    <h4 class="font-semibold text-gray-800">{{ insight.title }}</h4>
                    <p class="text-gray-700">{{ insight.description }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Report Actions -->
    <div class="flex justify-between items-center">
      <div class="space-x-2">
        <button class="btn btn-ghost" @click="$emit('close')">
          Fechar Visualização
        </button>
        <button class="btn btn-secondary" @click="scheduleReport">
          Agendar Relatório
        </button>
      </div>
      <div class="space-x-2">
        <button class="btn btn-primary" @click="generateReport">
          Gerar Relatório Completo
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface ReportData {
  title: string
  description: string
  generatedAt: Date
  dataPeriod: string
  recordCount: number
  format: string
  executiveSummary: string
  keyMetrics: Array<{
    label: string
    value: string
    change: string
    trend: 'up' | 'down' | 'stable'
  }>
  insights: Array<{
    id: string
    type: 'success' | 'warning' | 'info' | 'error'
    title: string
    description: string
  }>
  dataColumns: string[]
  data: any[][]
  charts: Array<{
    id: string
    title: string
    type: string
  }>
}

// Props
const props = defineProps<{
  report: ReportData
}>()

// Emits
const emit = defineEmits<{
  close: []
  export: [format: string]
  schedule: []
  generate: []
}>()

// Reactive state
const activeTab = ref('preview')
const searchTerm = ref('')
const currentPage = ref(1)
const itemsPerPage = 10
const viewerFormat = ref('pdf')
const pdfZoom = ref(1)
const activeExcelSheet = ref(0)

// Excel sheets simulation
const excelSheets = ['Dados Principais', 'Resumo', 'Gráficos']

// Computed properties
const filteredData = computed(() => {
  let data = props.report.data
  
  if (searchTerm.value) {
    data = data.filter(row => 
      row.some(cell => 
        String(cell).toLowerCase().includes(searchTerm.value.toLowerCase())
      )
    )
  }
  
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return data.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(props.report.data.length / itemsPerPage)
})

// Methods
const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getMetricColor = (trend: string): string => {
  switch (trend) {
    case 'up': return 'text-success'
    case 'down': return 'text-error'
    default: return 'text-base-content'
  }
}

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

const exportReport = (format: string) => {
  emit('export', format)
}

const scheduleReport = () => {
  emit('schedule')
}

const generateReport = () => {
  emit('generate')
}
</script>