// API Types for Enhanced API System

export interface ApiOptions {
  retry?: number
  timeout?: number
  cache?: boolean
  cacheTTL?: number
  showLoading?: boolean
  showError?: boolean
  headers?: Record<string, string>
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: any
  query?: Record<string, any>
}

export interface ApiResponse<T> {
  data: Readonly<Ref<T | null>>
  error: Readonly<Ref<string | null>>
  isLoading: Readonly<Ref<boolean>>
  refresh: () => Promise<void>
  lastUpdated: Readonly<Ref<Date | null>>
}

export interface CacheEntry<T> {
  data: T
  timestamp: Date
  ttl: number
}

export interface ApiError extends Error {
  status: number
  code: string
  details?: any
}

export interface RetryOptions {
  maxRetries: number
  baseDelay: number
  maxDelay: number
  backoffFactor: number
}

export interface ApiInterceptor {
  request?: (config: any) => any
  response?: (response: any) => any
  error?: (error: any) => any
}

export interface ApiConfig {
  baseURL: string
  timeout: number
  retries: number
  cacheTTL: number
  interceptors: ApiInterceptor[]
}

// Performance monitoring types
export interface ApiMetrics {
  endpoint: string
  method: string
  duration: number
  status: number
  timestamp: Date
  cacheHit: boolean
  retryCount: number
}

export interface ApiPerformanceData {
  totalRequests: number
  averageResponseTime: number
  successRate: number
  cacheHitRate: number
  errorRate: number
  slowestEndpoints: Array<{
    endpoint: string
    averageTime: number
    requestCount: number
  }>
}