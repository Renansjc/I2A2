import type { 
  SystemStatusResponse,
  ActivityResponse,
  SystemMetricsResponse
} from '~/types/specialized-apis'
import type { ApiOptions } from '~/types/api'

/**
 * System API composable for monitoring and system metrics
 */
export const useSystemApi = () => {
  const { apiCall, apiCallWithState } = useApi()

  /**
   * Get overall system status and health
   */
  const getSystemStatus = (options?: ApiOptions) => {
    return apiCallWithState<SystemStatusResponse>('/api/v1/api/system/status', {
      ...options,
      cache: false, // Always get fresh system status
      timeout: 10000 // 10 seconds timeout
    })
  }

  /**
   * Get recent system activities
   */
  const getRecentActivities = (
    limit: number = 10,
    hours: number = 24,
    type?: 'success' | 'info' | 'warning' | 'error',
    options?: ApiOptions
  ) => {
    const query: Record<string, any> = { limit, hours }
    if (type) query.type = type

    return apiCallWithState<ActivityResponse>('/api/v1/api/activity/recent', {
      ...options,
      query,
      cache: true,
      cacheTTL: 60000 // 1 minute cache for activities
    })
  }

  /**
   * Get detailed system metrics
   */
  const getSystemMetrics = (
    period: 'realtime' | 'hour' | 'day' | 'week' = 'realtime',
    options?: ApiOptions
  ) => {
    return apiCallWithState<SystemMetricsResponse>('/api/v1/api/system/metrics', {
      ...options,
      query: { period },
      cache: period === 'realtime' ? false : true,
      cacheTTL: period === 'realtime' ? 0 : 300000 // 5 minutes cache for historical data
    })
  }

  /**
   * Get agent status and performance
   */
  const getAgentStatus = (options?: ApiOptions) => {
    return apiCallWithState<{
      agents: Array<{
        id: string
        name: string
        type: string
        status: 'online' | 'offline' | 'busy' | 'error'
        current_task?: string
        queue_size: number
        performance: {
          tasks_completed: number
          success_rate: number
          average_time: number
          uptime: string
        }
        health: {
          last_check: string
          response_time: number
          memory_usage: number
          cpu_usage: number
        }
        last_activity: string
      }>
      summary: {
        total_agents: number
        online_agents: number
        busy_agents: number
        error_agents: number
        total_queue_size: number
      }
    }>('/api/v1/api/agents/status', {
      ...options,
      cache: false, // Always get fresh agent status
      timeout: 15000 // 15 seconds timeout
    })
  }

  /**
   * Get database connection and performance metrics
   */
  const getDatabaseMetrics = (options?: ApiOptions) => {
    return apiCallWithState<{
      connection_pool: {
        active_connections: number
        idle_connections: number
        max_connections: number
        connection_usage: number
      }
      query_performance: {
        average_query_time: number
        slow_queries: number
        failed_queries: number
        queries_per_second: number
      }
      storage: {
        database_size: number
        table_sizes: Array<{
          table_name: string
          size_mb: number
          row_count: number
        }>
        index_usage: number
      }
    }>('/api/v1/api/system/database', {
      ...options,
      cache: true,
      cacheTTL: 300000 // 5 minutes cache
    })
  }

  /**
   * Get Redis cache metrics
   */
  const getCacheMetrics = (options?: ApiOptions) => {
    return apiCallWithState<{
      redis_info: {
        connected_clients: number
        used_memory: number
        used_memory_human: string
        keyspace_hits: number
        keyspace_misses: number
        hit_rate: number
      }
      cache_performance: {
        get_operations: number
        set_operations: number
        delete_operations: number
        expired_keys: number
      }
      queue_status: {
        pending_jobs: number
        active_jobs: number
        completed_jobs: number
        failed_jobs: number
      }
    }>('/api/v1/api/system/cache', {
      ...options,
      cache: true,
      cacheTTL: 120000 // 2 minutes cache
    })
  }

  /**
   * Get error logs and system issues
   */
  const getErrorLogs = (
    level: 'error' | 'warning' | 'info' = 'error',
    limit: number = 50,
    hours: number = 24,
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      logs: Array<{
        id: string
        timestamp: string
        level: 'error' | 'warning' | 'info'
        source: string
        message: string
        stack?: string
        context?: Record<string, any>
        resolved: boolean
        resolution_notes?: string
      }>
      summary: {
        total_errors: number
        unresolved_errors: number
        error_rate: number
        most_common_errors: Array<{
          message: string
          count: number
          last_occurrence: string
        }>
      }
    }>('/api/v1/api/system/logs', {
      ...options,
      query: { level, limit, hours },
      cache: true,
      cacheTTL: 180000 // 3 minutes cache
    })
  }

  /**
   * Mark error as resolved
   */
  const resolveError = async (
    errorId: string,
    resolutionNotes?: string,
    options?: ApiOptions
  ): Promise<{ success: boolean; message: string }> => {
    return apiCall<{ success: boolean; message: string }>(
      `/api/v1/api/system/logs/${errorId}/resolve`,
      {
        ...options,
        method: 'POST',
        body: { resolution_notes: resolutionNotes }
      }
    )
  }

  /**
   * Get API performance metrics
   */
  const getApiMetrics = (
    period: 'hour' | 'day' | 'week' = 'hour',
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      request_stats: {
        total_requests: number
        successful_requests: number
        failed_requests: number
        success_rate: number
      }
      response_times: {
        average: number
        p50: number
        p95: number
        p99: number
      }
      endpoint_performance: Array<{
        endpoint: string
        method: string
        request_count: number
        average_time: number
        error_rate: number
      }>
      rate_limiting: {
        requests_blocked: number
        top_blocked_ips: Array<{
          ip: string
          blocked_count: number
        }>
      }
    }>('/api/v1/api/system/api-metrics', {
      ...options,
      query: { period },
      cache: true,
      cacheTTL: 300000 // 5 minutes cache
    })
  }

  /**
   * Trigger system health check
   */
  const triggerHealthCheck = async (
    component?: 'database' | 'redis' | 'agents' | 'storage',
    options?: ApiOptions
  ): Promise<{
    success: boolean
    results: Record<string, {
      status: 'healthy' | 'degraded' | 'down'
      response_time: number
      details?: any
    }>
  }> => {
    const query = component ? { component } : {}
    
    return apiCall<{
      success: boolean
      results: Record<string, {
        status: 'healthy' | 'degraded' | 'down'
        response_time: number
        details?: any
      }>
    }>('/api/v1/api/system/health-check', {
      ...options,
      method: 'POST',
      query,
      timeout: 30000 // 30 seconds for health check
    })
  }

  /**
   * Get system configuration
   */
  const getSystemConfiguration = (options?: ApiOptions) => {
    return apiCallWithState<{
      version: string
      environment: string
      features: Record<string, boolean>
      limits: {
        max_file_size: number
        max_concurrent_processing: number
        rate_limit_per_minute: number
      }
      integrations: {
        openai: { enabled: boolean; model: string }
        supabase: { enabled: boolean; region: string }
        redis: { enabled: boolean; cluster_mode: boolean }
      }
    }>('/api/v1/api/system/config', {
      ...options,
      cache: true,
      cacheTTL: 1800000 // 30 minutes cache
    })
  }

  /**
   * Get storage usage statistics
   */
  const getStorageMetrics = (options?: ApiOptions) => {
    return apiCallWithState<{
      total_storage: number
      used_storage: number
      available_storage: number
      usage_percentage: number
      file_statistics: {
        total_files: number
        xml_files: number
        report_files: number
        average_file_size: number
      }
      storage_by_type: Array<{
        type: string
        size: number
        file_count: number
      }>
      cleanup_recommendations: Array<{
        type: string
        description: string
        potential_savings: number
      }>
    }>('/api/v1/api/system/storage', {
      ...options,
      cache: true,
      cacheTTL: 600000 // 10 minutes cache
    })
  }

  /**
   * Monitor system in real-time
   */
  const startRealTimeMonitoring = (
    onUpdate: (data: SystemStatusResponse) => void,
    interval: number = 5000 // 5 seconds
  ) => {
    let intervalId: NodeJS.Timeout | null = null
    let isRunning = false

    const poll = async () => {
      if (!isRunning) return

      try {
        const status = await apiCall<SystemStatusResponse>('/api/v1/api/system/status')
        onUpdate(status)
      } catch (error) {
        console.error('Real-time monitoring error:', error)
      }
    }

    const start = () => {
      if (isRunning) return
      
      isRunning = true
      poll() // Initial call
      intervalId = setInterval(poll, interval)
    }

    const stop = () => {
      isRunning = false
      if (intervalId) {
        clearInterval(intervalId)
        intervalId = null
      }
    }

    return { start, stop }
  }

  return {
    // System status and health
    getSystemStatus,
    getSystemMetrics,
    getSystemConfiguration,
    triggerHealthCheck,
    
    // Component-specific metrics
    getAgentStatus,
    getDatabaseMetrics,
    getCacheMetrics,
    getApiMetrics,
    getStorageMetrics,
    
    // Activities and logs
    getRecentActivities,
    getErrorLogs,
    resolveError,
    
    // Real-time monitoring
    startRealTimeMonitoring
  }
}