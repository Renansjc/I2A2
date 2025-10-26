// Specialized API Types for Domain-Specific Composables

// Dashboard API Types
export interface PeriodFilter {
  value: 'last_30_days' | 'last_90_days' | 'last_6_months' | 'last_12_months' | 'current_year' | 'custom'
  label: string
  startDate?: Date
  endDate?: Date
}

export interface FinancialSummaryResponse {
  total_invoices: number
  total_value: number
  average_invoice_value: number
  tax_total: number
  period_start: string
  period_end: string
  growth_percentage?: number
  previous_period_value?: number
}

export interface SuppliersResponse {
  total_suppliers: number
  active_suppliers: number
  top_suppliers: Array<{
    cnpj: string
    razao_social: string
    total_value: number
    invoice_count: number
    percentage_of_total: number
  }>
  supplier_concentration: {
    top_5_percentage: number
    top_10_percentage: number
  }
}

export interface ProductsResponse {
  total_products: number
  categories: Array<{
    category: string
    product_count: number
    total_value: number
    percentage: number
  }>
  top_products: Array<{
    description: string
    ncm_code: string
    total_quantity: number
    total_value: number
    supplier_count: number
  }>
}

export interface TrendsResponse {
  monthly_trends: Array<{
    month: string
    total_value: number
    invoice_count: number
    supplier_count: number
    growth_rate: number
  }>
  seasonal_patterns: {
    peak_months: string[]
    low_months: string[]
    seasonality_index: number
  }
  projections: {
    next_month_estimate: number
    confidence_level: number
  }
}

export interface DashboardMetricsResponse {
  kpis: {
    fiscal_efficiency: number
    supplier_diversity: number
    processing_accuracy: number
    confiabilidade_dados: number
  }
  alerts: Array<{
    type: 'warning' | 'info' | 'error'
    message: string
    priority: 'high' | 'medium' | 'low'
  }>
}

// Document API Types
export interface ProcessarXMLResponse {
  success: boolean
  document_id: string
  message: string
  processing_status: 'initiated' | 'processing' | 'completed' | 'error'
  estimated_completion?: string
}

export interface DocumentStatusResponse {
  document_id: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress: number
  current_agent: string
  agents_completed: string[]
  agents_pending: string[]
  results: Record<string, any>
  error_message?: string
  started_at: string
  completed_at?: string
}

export interface DocumentDetailResponse {
  document_id: string
  filename: string
  file_size: number
  upload_date: string
  processing_status: string
  metadata: {
    cnpj_emitente: string
    razao_social_emitente: string
    numero_nf: string
    serie_nf: string
    data_emissao: string
    valor_total: number
    tipo_documento: 'nfe' | 'nfse'
  }
  processing_results: {
    xml_processing: any
    categorization: any
    dimensional_processing: any
    sql_analysis: any
    report_generation: any
  }
  insights: Array<{
    type: 'anomaly' | 'recommendation' | 'pattern'
    title: string
    description: string
    confidence: number
  }>
}

// Natural Language API Types
export interface QueryOptions {
  executiveLevel?: 'operacional' | 'gerencial' | 'estrategico'
  includeInsights?: boolean
  userContext?: string
  startDate?: string
  endDate?: string
  maxResults?: number
}

export interface ConsultaNaturalResponse {
  success: boolean
  query_id: string
  interpretation: {
    business_objective: string
    sql_generated: string
    confidence: number
    reasoning: string
    parameters: Record<string, any>
  }
  results: {
    data: any[]
    columns: Array<{
      name: string
      type: string
      description: string
    }>
    total_rows: number
    execution_time: number
  }
  insights: {
    executive_summary: string
    key_findings: string[]
    recommendations: Array<{
      title: string
      description: string
      priority: 'high' | 'medium' | 'low'
      impact: string
    }>
    visualizations: Array<{
      type: 'chart' | 'table' | 'metric'
      config: Record<string, any>
      data: any[]
    }>
  }
}

export interface QuerySuggestion {
  text: string
  category: 'suppliers' | 'products' | 'financial' | 'taxes' | 'trends'
  description: string
  example_query: string
}

// System API Types
export interface SystemStatusResponse {
  overall_health: number
  services: Array<{
    name: string
    status: 'healthy' | 'degraded' | 'down'
    response_time: number
    last_check: string
  }>
  processing_stats: {
    total_documents: number
    success_rate: number
    average_processing_time: number
    queue_size: number
  }
  resource_usage: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
  }
}

export interface ActivityResponse {
  activities: Array<{
    id: string
    type: 'success' | 'info' | 'warning' | 'error'
    title: string
    description: string
    timestamp: string
    metadata?: Record<string, any>
  }>
  total_count: number
  has_more: boolean
}

export interface SystemMetricsResponse {
  timestamp: string
  performance: {
    api_response_time: number
    database_query_time: number
    agent_processing_time: number
    cache_hit_rate: number
  }
  usage: {
    active_users: number
    requests_per_minute: number
    documents_processed_today: number
    storage_used: number
  }
  errors: {
    error_rate: number
    critical_errors: number
    warnings: number
  }
}