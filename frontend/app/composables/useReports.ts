import { ref, computed } from 'vue'

export interface ReportTemplate {
  id: string
  name: string
  description: string
  category: string
  estimatedTime: string
  fields: ReportField[]
  defaultFormat: string[]
  isCustom?: boolean
}

export interface ReportField {
  id: string
  name: string
  type: 'text' | 'date' | 'select' | 'multiselect' | 'number' | 'boolean'
  required: boolean
  options?: string[]
  defaultValue?: any
}

export interface ReportConfig {
  id?: string
  name: string
  description: string
  templateId: string
  startDate: string
  endDate: string
  formats: string[]
  isScheduled: boolean
  filters: {
    documentTypes: string[]
    states: string
    minValue: number | null
    maxValue: number | null
    suppliers: string[]
    categories: string[]
  }
  schedule?: {
    frequency: string
    dayOfWeek: string
    dayOfMonth: number
    time: string
    recipients: string
    startDate: string
    endDate: string
    hasEndDate: boolean
  }
  customXMLFiles: File[]
}

export interface ReportHistory {
  id: string
  name: string
  description: string
  type: string
  templateId: string
  config: ReportConfig
  generatedAt: Date
  completedAt?: Date
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  fileSize?: number
  downloadCount: number
  lastDownloaded?: Date
  formats: string[]
  downloadUrls: Record<string, string>
  error?: string
  executionTime?: number
}

export interface DownloadHistory {
  id: string
  reportId: string
  reportName: string
  format: string
  downloadedAt: Date
  fileSize: number
  downloadUrl: string
  expiresAt?: Date
}

export const useReports = () => {
  // State
  const reports = ref<ReportHistory[]>([])
  const templates = ref<ReportTemplate[]>([])
  const downloads = ref<DownloadHistory[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Default templates
  const defaultTemplates: ReportTemplate[] = [
    {
      id: '1',
      name: 'Análise de Fornecedores',
      description: 'Análise abrangente de desempenho e custos de fornecedores',
      category: 'Financeiro',
      estimatedTime: '5 min',
      defaultFormat: ['pdf', 'xlsx'],
      fields: [
        { id: 'period', name: 'Período de Análise', type: 'date', required: true },
        { id: 'minValue', name: 'Valor Mínimo', type: 'number', required: false },
        { id: 'states', name: 'Estados (UF)', type: 'multiselect', required: false, options: ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'GO', 'PE', 'CE'] },
        { id: 'includeCharts', name: 'Incluir Gráficos', type: 'boolean', required: false, defaultValue: true }
      ]
    },
    {
      id: '2',
      name: 'Relatório de Eficiência Fiscal',
      description: 'Análise de oportunidades de otimização fiscal',
      category: 'Fiscal',
      estimatedTime: '3 min',
      defaultFormat: ['pdf'],
      fields: [
        { id: 'period', name: 'Período Fiscal', type: 'date', required: true },
        { id: 'documentTypes', name: 'Tipos de Documento', type: 'multiselect', required: true, options: ['NF-e', 'NFS-e'], defaultValue: ['NF-e', 'NFS-e'] },
        { id: 'taxAnalysis', name: 'Análise Tributária Detalhada', type: 'boolean', required: false, defaultValue: true }
      ]
    },
    {
      id: '3',
      name: 'Tendências de Categorias de Produtos',
      description: 'Tendências e padrões em categorias de produtos',
      category: 'Análises',
      estimatedTime: '7 min',
      defaultFormat: ['pdf', 'xlsx'],
      fields: [
        { id: 'period', name: 'Período de Análise', type: 'date', required: true },
        { id: 'categories', name: 'Categorias Específicas', type: 'multiselect', required: false, options: ['Eletrônicos', 'Alimentação', 'Vestuário', 'Móveis', 'Automóveis', 'Serviços'] },
        { id: 'trendAnalysis', name: 'Análise de Tendências', type: 'boolean', required: false, defaultValue: true },
        { id: 'seasonalAnalysis', name: 'Análise Sazonal', type: 'boolean', required: false, defaultValue: false }
      ]
    },
    {
      id: '4',
      name: 'Resumo Executivo Mensal',
      description: 'Visão geral de alto nível para tomada de decisões executivas',
      category: 'Executivo',
      estimatedTime: '2 min',
      defaultFormat: ['pdf', 'docx'],
      fields: [
        { id: 'month', name: 'Mês de Referência', type: 'date', required: true },
        { id: 'executiveLevel', name: 'Nível Executivo', type: 'select', required: true, options: ['CEO', 'CFO', 'COO', 'Diretoria'], defaultValue: 'CEO' },
        { id: 'includeRecommendations', name: 'Incluir Recomendações', type: 'boolean', required: false, defaultValue: true }
      ]
    },
    {
      id: '5',
      name: 'Desempenho Regional',
      description: 'Análise de desempenho por região geográfica',
      category: 'Regional',
      estimatedTime: '4 min',
      defaultFormat: ['pdf', 'xlsx'],
      fields: [
        { id: 'period', name: 'Período de Análise', type: 'date', required: true },
        { id: 'regions', name: 'Regiões', type: 'multiselect', required: false, options: ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'] },
        { id: 'compareRegions', name: 'Comparar Regiões', type: 'boolean', required: false, defaultValue: true }
      ]
    },
    {
      id: '6',
      name: 'Painel de Conformidade',
      description: 'Visão geral de conformidade fiscal e regulatória',
      category: 'Conformidade',
      estimatedTime: '3 min',
      defaultFormat: ['pdf'],
      fields: [
        { id: 'period', name: 'Período de Conformidade', type: 'date', required: true },
        { id: 'complianceLevel', name: 'Nível de Detalhamento', type: 'select', required: true, options: ['Básico', 'Intermediário', 'Avançado'], defaultValue: 'Intermediário' },
        { id: 'includeRisks', name: 'Incluir Análise de Riscos', type: 'boolean', required: false, defaultValue: true }
      ]
    }
  ]

  // Initialize templates
  if (templates.value.length === 0) {
    templates.value = [...defaultTemplates]
  }

  // Computed properties
  const recentReports = computed(() => {
    return reports.value
      .sort((a, b) => b.generatedAt.getTime() - a.generatedAt.getTime())
      .slice(0, 10)
  })

  const completedReports = computed(() => {
    return reports.value.filter(report => report.status === 'completed')
  })

  const processingReports = computed(() => {
    return reports.value.filter(report => report.status === 'processing')
  })

  const failedReports = computed(() => {
    return reports.value.filter(report => report.status === 'failed')
  })

  const recentDownloads = computed(() => {
    return downloads.value
      .sort((a, b) => b.downloadedAt.getTime() - a.downloadedAt.getTime())
      .slice(0, 20)
  })

  const reportsByCategory = computed(() => {
    const categories: Record<string, ReportHistory[]> = {}
    reports.value.forEach(report => {
      const template = templates.value.find(t => t.id === report.templateId)
      const category = template?.category || 'Outros'
      if (!categories[category]) {
        categories[category] = []
      }
      categories[category].push(report)
    })
    return categories
  })

  // Methods
  const loadReports = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await $fetch('/api/reports') as { success: boolean; data: any[] }
      
      if (response.success) {
        reports.value = response.data.map((report: any) => ({
          ...report,
          generatedAt: new Date(report.generatedAt),
          completedAt: report.completedAt ? new Date(report.completedAt) : undefined,
          lastDownloaded: report.lastDownloaded ? new Date(report.lastDownloaded) : undefined
        }))
      } else {
        throw new Error('Failed to load reports')
      }
      
    } catch (err) {
      error.value = 'Erro ao carregar relatórios'
      console.error('Error loading reports:', err)
      
      // Fallback to mock data for development
      reports.value = [
        {
          id: '1',
          name: 'Análise de Fornecedores T4',
          description: 'Revisão trimestral de desempenho de fornecedores',
          type: 'Financeiro',
          templateId: '1',
          config: {} as ReportConfig,
          generatedAt: new Date('2024-01-15T10:30:00'),
          completedAt: new Date('2024-01-15T10:35:00'),
          status: 'completed',
          fileSize: 2048576, // 2MB
          downloadCount: 5,
          lastDownloaded: new Date('2024-01-20T14:20:00'),
          formats: ['pdf', 'xlsx'],
          downloadUrls: {
            pdf: '/api/reports/1/download/pdf',
            xlsx: '/api/reports/1/download/xlsx'
          },
          executionTime: 300 // 5 minutes
        }
      ]
    } finally {
      isLoading.value = false
    }
  }

  const loadDownloadHistory = async () => {
    try {
      const response = await $fetch('/api/reports/downloads') as { success: boolean; data: any[] }
      
      if (response.success) {
        downloads.value = response.data.map((download: any) => ({
          ...download,
          downloadedAt: new Date(download.downloadedAt),
          expiresAt: download.expiresAt ? new Date(download.expiresAt) : undefined
        }))
      } else {
        throw new Error('Failed to load download history')
      }
      
    } catch (err) {
      console.error('Error loading download history:', err)
      
      // Fallback to mock data for development
      downloads.value = [
        {
          id: '1',
          reportId: '1',
          reportName: 'Análise de Fornecedores T4',
          format: 'pdf',
          downloadedAt: new Date('2024-01-20T14:20:00'),
          fileSize: 2048576,
          downloadUrl: '/api/reports/1/download/pdf',
          expiresAt: new Date('2024-01-27T14:20:00')
        }
      ]
    }
  }

  const createReport = async (config: ReportConfig): Promise<string> => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await $fetch('/api/reports', {
        method: 'POST',
        body: config
      }) as { success: boolean; data: any; message?: string }
      
      if (response.success) {
        const newReport: ReportHistory = {
          ...response.data,
          generatedAt: new Date(response.data.generatedAt),
          completedAt: response.data.completedAt ? new Date(response.data.completedAt) : undefined,
          lastDownloaded: response.data.lastDownloaded ? new Date(response.data.lastDownloaded) : undefined
        }
        
        reports.value.unshift(newReport)
        
        // Simulate processing for immediate reports (in real app, this would be handled by backend)
        if (!config.isScheduled) {
          setTimeout(() => {
            const report = reports.value.find(r => r.id === newReport.id)
            if (report) {
              report.status = 'completed'
              report.completedAt = new Date()
              report.progress = 100
              report.fileSize = Math.floor(Math.random() * 5000000) + 1000000 // 1-5MB
              report.executionTime = Math.floor(Math.random() * 300) + 60 // 1-5 minutes
              
              // Generate download URLs
              config.formats.forEach(format => {
                report.downloadUrls[format] = `/api/reports/${report.id}/download/${format}`
              })
            }
          }, 5000) // Complete after 5 seconds for demo
        }
        
        return newReport.id
      } else {
        throw new Error(response.message || 'Failed to create report')
      }
      
    } catch (err) {
      error.value = 'Erro ao criar relatório'
      console.error('Error creating report:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const downloadReport = async (reportId: string, format: string): Promise<void> => {
    try {
      const report = reports.value.find(r => r.id === reportId)
      if (!report) {
        throw new Error('Relatório não encontrado')
      }
      
      if (report.status !== 'completed') {
        throw new Error('Relatório ainda não está pronto para download')
      }
      
      const downloadUrl = report.downloadUrls[format]
      if (!downloadUrl) {
        throw new Error(`Formato ${format} não disponível para este relatório`)
      }
      
      // Simulate download - replace with actual download logic
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `${report.name}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Update download count and history
      report.downloadCount++
      report.lastDownloaded = new Date()
      
      const downloadRecord: DownloadHistory = {
        id: Date.now().toString(),
        reportId: report.id,
        reportName: report.name,
        format,
        downloadedAt: new Date(),
        fileSize: report.fileSize || 0,
        downloadUrl,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
      
      downloads.value.unshift(downloadRecord)
      
    } catch (err) {
      error.value = 'Erro ao fazer download do relatório'
      console.error('Error downloading report:', err)
      throw err
    }
  }

  const deleteReport = async (reportId: string): Promise<void> => {
    try {
      // Simulate API call - replace with actual API integration
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const index = reports.value.findIndex(r => r.id === reportId)
      if (index > -1) {
        reports.value.splice(index, 1)
      }
      
      // Also remove from download history
      downloads.value = downloads.value.filter(d => d.reportId !== reportId)
      
    } catch (err) {
      error.value = 'Erro ao excluir relatório'
      console.error('Error deleting report:', err)
      throw err
    }
  }

  const cancelReport = async (reportId: string): Promise<void> => {
    try {
      // Simulate API call - replace with actual API integration
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const report = reports.value.find(r => r.id === reportId)
      if (report && (report.status === 'pending' || report.status === 'processing')) {
        report.status = 'cancelled'
      }
      
    } catch (err) {
      error.value = 'Erro ao cancelar relatório'
      console.error('Error cancelling report:', err)
      throw err
    }
  }

  const duplicateReport = async (reportId: string): Promise<string> => {
    try {
      const originalReport = reports.value.find(r => r.id === reportId)
      if (!originalReport) {
        throw new Error('Relatório não encontrado')
      }
      
      const duplicatedConfig: ReportConfig = {
        ...originalReport.config,
        name: `${originalReport.name} (Cópia)`,
        isScheduled: false // Reset scheduling for duplicated reports
      }
      
      return await createReport(duplicatedConfig)
      
    } catch (err) {
      error.value = 'Erro ao duplicar relatório'
      console.error('Error duplicating report:', err)
      throw err
    }
  }

  const getReportProgress = (reportId: string): number => {
    const report = reports.value.find(r => r.id === reportId)
    return report?.progress || 0
  }

  const getReportStatus = (reportId: string): string => {
    const report = reports.value.find(r => r.id === reportId)
    return report?.status || 'unknown'
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatExecutionTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
    }
  }

  // Initialize data
  loadReports()
  loadDownloadHistory()

  return {
    // State
    reports: readonly(reports),
    templates: readonly(templates),
    downloads: readonly(downloads),
    isLoading: readonly(isLoading),
    error: readonly(error),
    
    // Computed
    recentReports,
    completedReports,
    processingReports,
    failedReports,
    recentDownloads,
    reportsByCategory,
    
    // Methods
    loadReports,
    loadDownloadHistory,
    createReport,
    downloadReport,
    deleteReport,
    cancelReport,
    duplicateReport,
    getReportProgress,
    getReportStatus,
    formatFileSize,
    formatExecutionTime
  }
}