import type { 
  QueryOptions,
  ConsultaNaturalResponse,
  QuerySuggestion
} from '~/types/specialized-apis'
import type { ApiOptions } from '~/types/api'

/**
 * Natural Language API composable for LLM-powered queries (GPT-4o-mini)
 */
export const useNaturalLanguageApi = () => {
  const { apiCall, apiCallWithState } = useApi()

  /**
   * Process natural language query with GPT-4o-mini
   */
  const processLLMQuery = async (
    query: string,
    queryOptions?: QueryOptions,
    apiOptions?: ApiOptions
  ): Promise<ConsultaNaturalResponse> => {
    const requestBody = {
      consulta: query,
      nivel_executivo: queryOptions?.executiveLevel || 'gerencial',
      incluir_insights: queryOptions?.includeInsights ?? true,
      contexto_usuario: queryOptions?.userContext,
      periodo_inicio: queryOptions?.startDate,
      periodo_fim: queryOptions?.endDate,
      max_resultados: queryOptions?.maxResults || 100,
      llm_model: 'gpt-4o-mini' // Fixed model for cost optimization
    }

    return apiCall<ConsultaNaturalResponse>('/agentes/consulta-natural', {
      ...apiOptions,
      method: 'POST',
      body: requestBody,
      timeout: 120000, // 2 minutes timeout for LLM processing
      retry: 1 // Only retry once for LLM queries
    })
  }

  /**
   * Get query suggestions based on available data and context
   */
  const getQuerySuggestions = (
    category?: 'suppliers' | 'products' | 'financial' | 'taxes' | 'trends',
    userContext?: string,
    options?: ApiOptions
  ) => {
    const query: Record<string, any> = {}
    if (category) query.category = category
    if (userContext) query.context = userContext

    return apiCallWithState<{
      suggestions: QuerySuggestion[]
      contextual_examples: string[]
      quick_actions: Array<{
        text: string
        icon: string
        query: string
        description: string
      }>
    }>('/agentes/exemplos-consultas', { // Using examples endpoint as suggestions
      ...options,
      query,
      cache: true,
      cacheTTL: 1800000 // 30 minutes cache for suggestions
    })
  }

  /**
   * Get query examples for different business scenarios
   */
  const getQueryExamples = (
    executiveLevel: 'operacional' | 'gerencial' | 'estrategico' = 'gerencial',
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      examples: Array<{
        category: string
        title: string
        query: string
        description: string
        expected_insights: string[]
      }>
      templates: Array<{
        name: string
        template: string
        variables: string[]
        description: string
      }>
    }>('/agentes/exemplos-consultas', {
      ...options,
      query: { executive_level: executiveLevel },
      cache: true,
      cacheTTL: 3600000 // 1 hour cache for examples
    })
  }

  /**
   * Validate query before processing
   */
  const validateQuery = async (
    query: string,
    options?: ApiOptions
  ): Promise<{
    valid: boolean
    confidence: number
    interpretation: string
    suggestions?: string[]
    warnings?: string[]
  }> => {
    return apiCall<{
      valid: boolean
      confidence: number
      interpretation: string
      suggestions?: string[]
      warnings?: string[]
    }>('/api/v1/api/nlp/validate', {
      ...options,
      method: 'POST',
      body: { query },
      timeout: 30000 // 30 seconds for validation
    })
  }

  /**
   * Get query history for user
   */
  const getQueryHistory = (
    limit: number = 20,
    offset: number = 0,
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      queries: Array<{
        id: string
        query: string
        interpretation: string
        executed_at: string
        execution_time: number
        success: boolean
        results_count: number
        saved: boolean
      }>
      total: number
      hasMore: boolean
    }>('/api/v1/api/nlp/history', {
      ...options,
      query: { limit, offset },
      cache: true,
      cacheTTL: 300000 // 5 minutes cache
    })
  }

  /**
   * Save query as favorite
   */
  const saveQueryAsFavorite = async (
    queryId: string,
    name: string,
    description?: string,
    options?: ApiOptions
  ): Promise<{ success: boolean; favorite_id: string }> => {
    return apiCall<{ success: boolean; favorite_id: string }>(
      '/api/v1/api/nlp/favorites',
      {
        ...options,
        method: 'POST',
        body: {
          query_id: queryId,
          name,
          description
        }
      }
    )
  }

  /**
   * Get saved favorite queries
   */
  const getFavoriteQueries = (options?: ApiOptions) => {
    return apiCallWithState<{
      favorites: Array<{
        id: string
        name: string
        description: string
        query: string
        interpretation: string
        created_at: string
        last_used: string
        usage_count: number
      }>
    }>('/api/v1/api/nlp/favorites', {
      ...options,
      cache: true,
      cacheTTL: 600000 // 10 minutes cache
    })
  }

  /**
   * Execute saved favorite query
   */
  const executeFavoriteQuery = async (
    favoriteId: string,
    queryOptions?: QueryOptions,
    apiOptions?: ApiOptions
  ): Promise<ConsultaNaturalResponse> => {
    const requestBody = {
      favorite_id: favoriteId,
      nivel_executivo: queryOptions?.executiveLevel || 'gerencial',
      incluir_insights: queryOptions?.includeInsights ?? true,
      contexto_usuario: queryOptions?.userContext,
      periodo_inicio: queryOptions?.startDate,
      periodo_fim: queryOptions?.endDate,
      max_resultados: queryOptions?.maxResults || 100
    }

    return apiCall<ConsultaNaturalResponse>('/api/v1/api/nlp/favorites/execute', {
      ...apiOptions,
      method: 'POST',
      body: requestBody,
      timeout: 120000
    })
  }

  /**
   * Get query insights and recommendations
   */
  const getQueryInsights = async (
    queryId: string,
    options?: ApiOptions
  ): Promise<{
    insights: Array<{
      type: 'pattern' | 'anomaly' | 'trend' | 'recommendation'
      title: string
      description: string
      confidence: number
      impact: 'high' | 'medium' | 'low'
      actionable: boolean
      suggested_actions?: string[]
    }>
    related_queries: string[]
    optimization_suggestions: string[]
  }> => {
    return apiCall<{
      insights: Array<{
        type: 'pattern' | 'anomaly' | 'trend' | 'recommendation'
        title: string
        description: string
        confidence: number
        impact: 'high' | 'medium' | 'low'
        actionable: boolean
        suggested_actions?: string[]
      }>
      related_queries: string[]
      optimization_suggestions: string[]
    }>(`/api/v1/api/nlp/queries/${queryId}/insights`, {
      ...options,
      cache: true,
      cacheTTL: 1800000 // 30 minutes cache
    })
  }

  /**
   * Export query results in different formats
   */
  const exportQueryResults = async (
    queryId: string,
    format: 'xlsx' | 'pdf' | 'csv' | 'json',
    options?: ApiOptions
  ): Promise<Blob> => {
    const response = await fetch(`${useRuntimeConfig().public.apiBaseUrl}/api/v1/api/nlp/queries/${queryId}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ format })
    })

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }

    return response.blob()
  }

  /**
   * Get LLM performance metrics
   */
  const getLLMMetrics = (
    period: 'hour' | 'day' | 'week' | 'month' = 'day',
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      total_queries: number
      successful_queries: number
      failed_queries: number
      success_rate: number
      average_response_time: number
      average_confidence: number
      token_usage: {
        total_tokens: number
        prompt_tokens: number
        completion_tokens: number
        estimated_cost: number
      }
      query_categories: Array<{
        category: string
        count: number
        success_rate: number
      }>
    }>('/api/v1/api/nlp/metrics', {
      ...options,
      query: { period },
      cache: true,
      cacheTTL: 300000 // 5 minutes cache
    })
  }

  /**
   * Sanitize and validate query input
   */
  const sanitizeQuery = (query: string): string => {
    return query
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/[<>]/g, '')
      .trim()
      .substring(0, 1000) // Limit length
  }

  return {
    // Core query processing
    processLLMQuery,
    validateQuery,
    sanitizeQuery,
    
    // Query suggestions and examples
    getQuerySuggestions,
    getQueryExamples,
    
    // Query management
    getQueryHistory,
    saveQueryAsFavorite,
    getFavoriteQueries,
    executeFavoriteQuery,
    
    // Insights and analytics
    getQueryInsights,
    getLLMMetrics,
    
    // Export functionality
    exportQueryResults
  }
}