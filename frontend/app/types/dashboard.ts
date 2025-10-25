export interface DashboardStats {
  totalInvoices: number
  totalValue: number
  activeSuppliers: number
  fiscalEfficiency: number
}

export interface RecentActivity {
  id: string
  type: 'success' | 'info' | 'warning' | 'error'
  title: string
  description: string
  timestamp: Date
}

export interface Workflow {
  id: string
  name: string
  status: 'running' | 'completed' | 'error' | 'paused'
  progress: number
  currentStep: string
  currentAgent: string
  startTime: Date
  completedAt?: Date
  duration?: string
}

export interface AgentMetrics {
  cpu: number
  memory: number
  activeTasks: number
  uptime: string
}

export interface Agent {
  id: string
  name: string
  description: string
  status: 'online' | 'offline' | 'busy' | 'error'
  metrics: AgentMetrics
  lastActivity: Date
}

export interface SystemHealth {
  overallHealth: number
  totalRequests: number
  avgResponseTime: number
  successRate: number
}

export interface ChartDataItem {
  label: string
  value: number
}

export interface PieSegment {
  path: string
  percentage: number
}

// Natural Language Query Interface Types
export interface IntelligentSuggestion {
  text: string
  description: string
  category: string
  estimatedTime: string
}

export interface QuickAction {
  text: string
  icon: string
  query: string
}

export interface QueryPreview {
  interpretedQuery: string
  involvedAgents: string[]
  estimatedTime: string
}

export interface QueryInsight {
  title: string
  description: string
  impact?: string
}

export interface QueryRecommendation {
  title: string
  description: string
  priority: 'alta' | 'média' | 'baixa'
  timeline?: string
  impact?: string
}

export interface QueryResult {
  originalQuery: string
  executionTime: string
  confidence: number
  executiveSummary: string
  keyInsights: QueryInsight[]
  chartData?: ChartDataItem[]
  recommendations: QueryRecommendation[]
}

export interface QueryHistoryItem {
  query: string
  timestamp: Date
  status: 'concluída' | 'processando' | 'erro'
}