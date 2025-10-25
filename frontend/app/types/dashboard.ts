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

// Agent Monitoring Types
export interface Conversation {
  id: string
  title: string
  status: 'active' | 'completed' | 'error' | 'paused'
  lastActivity: Date
  lastMessage: string
  primaryAgent: string
  messageCount: number
  hasContext: boolean
  priority: 'high' | 'medium' | 'low'
  userId: string
  startTime: Date
}

export interface ConversationMessage {
  id: string
  conversationId: string
  sender: 'user' | 'agent'
  content: string
  timestamp: Date
  metadata?: {
    agent?: string
    executionTime?: string
    confidence?: number
  }
}

export interface AgentPerformanceMetrics {
  id: string
  name: string
  type: string
  performance: number
  tasksCompleted: number
  totalTasks: number
  avgTime: number
  successRate: number
  uptime: string
  lastActivity: Date
  lastTask: string
}

export interface PerformanceAlert {
  id: string
  severity: 'error' | 'warning' | 'info'
  title: string
  description: string
  timestamp: Date
}

export interface WorkflowExecution {
  id: string
  name: string
  status: 'running' | 'completed' | 'error' | 'paused'
  progress: number
  currentStep: string
  currentAgent: string
  startTime: Date
  completedAt?: Date
  duration?: string
  steps: WorkflowStep[]
  metadata?: Record<string, any>
}

export interface WorkflowStep {
  id: string
  name: string
  agent: string
  status: 'pending' | 'running' | 'completed' | 'error'
  startTime?: Date
  completedAt?: Date
  duration?: string
  input?: any
  output?: any
  error?: string
}

export interface AgentStatus {
  id: string
  name: string
  type: string
  status: 'online' | 'offline' | 'busy' | 'error'
  currentTask?: string
  queueSize: number
  performance: AgentPerformanceMetrics
  healthCheck: {
    lastCheck: Date
    responseTime: number
    memoryUsage: number
    cpuUsage: number
  }
}

export interface SystemMetrics {
  timestamp: Date
  cpu: number
  memory: number
  disk: number
  network: {
    inbound: number
    outbound: number
  }
  database: {
    connections: number
    queryTime: number
  }
  redis: {
    connections: number
    memoryUsage: number
  }
}

export interface ErrorLog {
  id: string
  timestamp: Date
  level: 'error' | 'warning' | 'info'
  source: string
  message: string
  stack?: string
  context?: Record<string, any>
  resolved: boolean
}

export interface ContextData {
  conversationId: string
  userId: string
  sessionData: Record<string, any>
  preferences: Record<string, any>
  history: ConversationMessage[]
  metadata: Record<string, any>
}