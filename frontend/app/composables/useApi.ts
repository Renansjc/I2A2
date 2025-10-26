import type { 
  ApiOptions, 
  ApiResponse, 
  CacheEntry, 
  ApiError, 
  RetryOptions, 
  ApiInterceptor,
  ApiMetrics,
  ApiPerformanceData 
} from '~/types/api'
import { 
  handleApiError, 
  getUserFriendlyErrorMessage, 
  withRetry,
  isRetryableError,
  EnhancedApiError,
  createErrorRecoveryManager,
  defaultRecoveryStrategies
} from '~/utils/errorHandler'

/**
 * Enhanced API composable with retry, cache, error handling, and performance monitoring
 */
export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBaseUrl = config.public.apiBaseUrl

  // Cache storage
  const cache = new Map<string, CacheEntry<any>>()
  
  // Performance metrics storage
  const metrics = ref<ApiMetrics[]>([])
  
  // Global interceptors
  const interceptors = ref<ApiInterceptor[]>([])
  
  // Error recovery manager
  const errorRecovery = createErrorRecoveryManager()
  
  // Add default recovery strategies
  defaultRecoveryStrategies.forEach(strategy => {
    errorRecovery.addStrategy(strategy)
  })
  
  // Add cache fallback strategy
  errorRecovery.addStrategy({
    canRecover: (error) => error.code === 'NETWORK_ERROR' || error.code === 'SERVICE_UNAVAILABLE',
    recover: async (error) => {
      // Try to get cached data as fallback
      const cacheKey = error.details?.cacheKey
      if (cacheKey) {
        const cachedData = getFromCache(cacheKey)
        if (cachedData) {
          console.warn('Using cached data as fallback for:', error.message)
          return cachedData
        }
      }
      throw error
    }
  })

  // Default configuration
  const defaultConfig: Partial<ApiOptions> = {
    retry: 3,
    timeout: 30000,
    cache: false,
    cacheTTL: 300000, // 5 minutes
    showLoading: true,
    showError: true
  }

  /**
   * Cache management
   */
  const getCacheKey = (endpoint: string, options?: ApiOptions): string => {
    const query = options?.query ? JSON.stringify(options.query) : ''
    const method = options?.method || 'GET'
    return `${method}:${endpoint}:${query}`
  }

  const getFromCache = <T>(key: string): T | null => {
    const entry = cache.get(key)
    if (!entry) return null
    
    const now = new Date()
    const age = now.getTime() - entry.timestamp.getTime()
    
    if (age > entry.ttl) {
      cache.delete(key)
      return null
    }
    
    return entry.data
  }

  const setCache = <T>(key: string, data: T, ttl: number): void => {
    cache.set(key, {
      data,
      timestamp: new Date(),
      ttl
    })
  }

  const clearCache = (pattern?: string): void => {
    if (!pattern) {
      cache.clear()
      return
    }
    
    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key)
      }
    }
  }

  /**
   * Performance monitoring
   */
  const recordMetrics = (
    endpoint: string,
    method: string,
    duration: number,
    status: number,
    cacheHit: boolean,
    retryCount: number
  ): void => {
    const metric: ApiMetrics = {
      endpoint,
      method,
      duration,
      status,
      timestamp: new Date(),
      cacheHit,
      retryCount
    }
    
    metrics.value.push(metric)
    
    // Keep only last 1000 metrics
    if (metrics.value.length > 1000) {
      metrics.value = metrics.value.slice(-1000)
    }
  }

  /**
   * Get performance data
   */
  const getPerformanceData = (): ApiPerformanceData => {
    const recentMetrics = metrics.value.filter(
      m => Date.now() - m.timestamp.getTime() < 3600000 // Last hour
    )
    
    const totalRequests = recentMetrics.length
    const successfulRequests = recentMetrics.filter(m => m.status >= 200 && m.status < 400)
    const cacheHits = recentMetrics.filter(m => m.cacheHit)
    
    const averageResponseTime = totalRequests > 0 
      ? recentMetrics.reduce((sum, m) => sum + m.duration, 0) / totalRequests 
      : 0
    
    const successRate = totalRequests > 0 
      ? (successfulRequests.length / totalRequests) * 100 
      : 0
    
    const cacheHitRate = totalRequests > 0 
      ? (cacheHits.length / totalRequests) * 100 
      : 0
    
    const errorRate = totalRequests > 0 
      ? ((totalRequests - successfulRequests.length) / totalRequests) * 100 
      : 0
    
    // Calculate slowest endpoints
    const endpointStats = new Map<string, { totalTime: number, count: number }>()
    
    recentMetrics.forEach(m => {
      const key = `${m.method} ${m.endpoint}`
      const existing = endpointStats.get(key) || { totalTime: 0, count: 0 }
      endpointStats.set(key, {
        totalTime: existing.totalTime + m.duration,
        count: existing.count + 1
      })
    })
    
    const slowestEndpoints = Array.from(endpointStats.entries())
      .map(([endpoint, stats]) => ({
        endpoint,
        averageTime: stats.totalTime / stats.count,
        requestCount: stats.count
      }))
      .sort((a, b) => b.averageTime - a.averageTime)
      .slice(0, 5)
    
    return {
      totalRequests,
      averageResponseTime,
      successRate,
      cacheHitRate,
      errorRate,
      slowestEndpoints
    }
  }

  /**
   * Add interceptor
   */
  const addInterceptor = (interceptor: ApiInterceptor): void => {
    interceptors.value.push(interceptor)
  }

  /**
   * Enhanced API call with retry, cache, and error handling
   */
  const apiCall = async <T>(
    endpoint: string, 
    options: ApiOptions = {}
  ): Promise<T> => {
    const config = { ...defaultConfig, ...options }
    const startTime = Date.now()
    let retryCount = 0
    let cacheHit = false
    
    // Generate cache key
    const cacheKey = getCacheKey(endpoint, config)
    
    // Check cache first
    if (config.cache && config.method !== 'POST' && config.method !== 'PUT' && config.method !== 'DELETE') {
      const cachedData = getFromCache<T>(cacheKey)
      if (cachedData) {
        cacheHit = true
        recordMetrics(endpoint, config.method || 'GET', Date.now() - startTime, 200, cacheHit, retryCount)
        return cachedData
      }
    }
    
    // Apply request interceptors
    let requestConfig = { ...config }
    for (const interceptor of interceptors.value) {
      if (interceptor.request) {
        requestConfig = interceptor.request(requestConfig)
      }
    }
    
    const operation = async (): Promise<T> => {
      try {
        retryCount++
        
        const url = `${apiBaseUrl}${endpoint}`
        const fetchOptions: any = {
          method: requestConfig.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...requestConfig.headers
          }
        }
        
        // Add query parameters
        let finalUrl = url
        if (requestConfig.query) {
          const searchParams = new URLSearchParams()
          Object.entries(requestConfig.query).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
              searchParams.append(key, String(value))
            }
          })
          finalUrl = `${url}?${searchParams.toString()}`
        }
        
        // Add body for non-GET requests
        if (requestConfig.body && requestConfig.method !== 'GET') {
          fetchOptions.body = typeof requestConfig.body === 'string' 
            ? requestConfig.body 
            : JSON.stringify(requestConfig.body)
        }
        
        // Set timeout
        if (requestConfig.timeout) {
          fetchOptions.signal = AbortSignal.timeout(requestConfig.timeout)
        }
        
        const response = await $fetch<T>(finalUrl, fetchOptions)
        
        // Apply response interceptors
        let finalResponse = response
        for (const interceptor of interceptors.value) {
          if (interceptor.response) {
            finalResponse = interceptor.response(finalResponse)
          }
        }
        
        // Cache successful responses
        if (config.cache && config.cacheTTL) {
          setCache(cacheKey, finalResponse, config.cacheTTL)
        }
        
        return finalResponse
      } catch (error) {
        // Apply error interceptors
        let processedError = error
        for (const interceptor of interceptors.value) {
          if (interceptor.error) {
            processedError = interceptor.error(processedError)
          }
        }
        
        throw handleApiError(processedError)
      }
    }
    
    try {
      const result = await withRetry(operation, {
        maxRetries: config.retry || 0,
        baseDelay: 1000,
        maxDelay: 30000,
        backoffFactor: 2,
        retryCondition: isRetryableError
      })
      
      const duration = Date.now() - startTime
      recordMetrics(endpoint, config.method || 'GET', duration, 200, cacheHit, retryCount - 1)
      
      return result
    } catch (error) {
      const duration = Date.now() - startTime
      const apiError = error as EnhancedApiError
      recordMetrics(endpoint, config.method || 'GET', duration, apiError.status, cacheHit, retryCount - 1)
      
      // Try error recovery strategies
      try {
        // Add cache key to error details for recovery
        apiError.details = { ...apiError.details, cacheKey }
        const recoveredData = await errorRecovery.tryRecover(apiError)
        if (recoveredData !== null) {
          return recoveredData
        }
      } catch (recoveryError) {
        // Recovery failed, continue with original error
      }
      
      throw apiError
    }
  }

  /**
   * API call with reactive state management
   */
  const apiCallWithState = <T>(
    endpoint: string,
    options: ApiOptions = {}
  ): ApiResponse<T> => {
    const data = ref<T | null>(null)
    const error = ref<string | null>(null)
    const isLoading = ref(false)
    const lastUpdated = ref<Date | null>(null)
    
    const refresh = async (): Promise<void> => {
      try {
        isLoading.value = true
        error.value = null
        
        const result = await apiCall<T>(endpoint, options)
        data.value = result
        lastUpdated.value = new Date()
      } catch (err) {
        const apiError = err as EnhancedApiError
        error.value = getUserFriendlyErrorMessage(apiError)
        console.error('API call failed:', apiError)
      } finally {
        isLoading.value = false
      }
    }
    
    // Auto-load on creation
    refresh()
    
    return {
      data: readonly(data) as Readonly<Ref<T | null>>,
      error: readonly(error) as Readonly<Ref<string | null>>,
      isLoading: readonly(isLoading) as Readonly<Ref<boolean>>,
      lastUpdated: readonly(lastUpdated) as Readonly<Ref<Date | null>>,
      refresh
    }
  }

  return {
    // Core API methods
    apiCall,
    apiCallWithState,
    
    // Configuration
    apiBaseUrl,
    
    // Cache management
    clearCache,
    
    // Performance monitoring
    getPerformanceData,
    metrics: readonly(metrics),
    
    // Interceptors
    addInterceptor,
    
    // Error handling
    handleApiError,
    getUserFriendlyErrorMessage,
    errorRecovery
  }
}