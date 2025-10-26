import type { 
  PeriodFilter,
  FinancialSummaryResponse,
  SuppliersResponse,
  ProductsResponse,
  TrendsResponse,
  DashboardMetricsResponse
} from '~/types/specialized-apis'
import type { ApiOptions } from '~/types/api'
import { useApi } from './useApi'

/**
 * Dashboard API composable for executive dashboard data
 */
export const useDashboardApi = () => {
  const { apiCall, apiCallWithState } = useApi()

  /**
   * Get financial summary data
   */
  const getFinancialSummary = (
    period: PeriodFilter['value'] = 'last_90_days',
    options?: ApiOptions
  ) => {
    return apiCallWithState<FinancialSummaryResponse>(
      '/api/v1/api/dashboard/financial-summary',
      {
        ...options,
        query: { period },
        cache: true,
        cacheTTL: 300000 // 5 minutes cache
      }
    )
  }

  /**
   * Get suppliers data with top suppliers and concentration metrics
   */
  const getSuppliersData = (
    period: PeriodFilter['value'] = 'last_90_days',
    limit: number = 10,
    options?: ApiOptions
  ) => {
    return apiCallWithState<SuppliersResponse>(
      '/api/v1/api/dashboard/suppliers',
      {
        ...options,
        query: { period, limit },
        cache: true,
        cacheTTL: 300000
      }
    )
  }

  /**
   * Get products analysis with categories and top products
   */
  const getProductsAnalysis = (
    period: PeriodFilter['value'] = 'last_90_days',
    category?: string,
    options?: ApiOptions
  ) => {
    const query: Record<string, any> = { period }
    if (category) query.category = category

    return apiCallWithState<ProductsResponse>(
      '/api/v1/api/dashboard/products',
      {
        ...options,
        query,
        cache: true,
        cacheTTL: 300000
      }
    )
  }

  /**
   * Get trends analysis with monthly data and projections
   */
  const getTrendsAnalysis = (
    period: PeriodFilter['value'] = 'last_12_months',
    trendType: 'volume' | 'value' | 'suppliers' = 'value',
    options?: ApiOptions
  ) => {
    return apiCallWithState<TrendsResponse>(
      '/api/v1/api/dashboard/trends',
      {
        ...options,
        query: { period, trend_type: trendType },
        cache: true,
        cacheTTL: 600000 // 10 minutes cache for trends
      }
    )
  }

  /**
   * Get executive dashboard metrics and KPIs
   */
  const getDashboardMetrics = (
    period: PeriodFilter['value'] = 'last_90_days',
    options?: ApiOptions
  ) => {
    return apiCallWithState<DashboardMetricsResponse>(
      '/api/v1/api/dashboard/metrics',
      {
        ...options,
        query: { period },
        cache: true,
        cacheTTL: 180000 // 3 minutes cache for metrics
      }
    )
  }

  /**
   * Refresh all dashboard data
   */
  const refreshAllDashboardData = async (period: PeriodFilter['value'] = 'last_90_days') => {
    try {
      const [financial, suppliers, products, trends, metrics] = await Promise.allSettled([
        apiCall<FinancialSummaryResponse>('/api/v1/api/dashboard/financial-summary', {
          query: { period },
          cache: false // Force refresh
        }),
        apiCall<SuppliersResponse>('/api/v1/api/dashboard/suppliers', {
          query: { period, limit: 10 },
          cache: false
        }),
        apiCall<ProductsResponse>('/api/v1/api/dashboard/products', {
          query: { period },
          cache: false
        }),
        apiCall<TrendsResponse>('/api/v1/api/dashboard/trends', {
          query: { period, trend_type: 'value' },
          cache: false
        }),
        apiCall<DashboardMetricsResponse>('/api/v1/api/dashboard/metrics', {
          query: { period },
          cache: false
        })
      ])

      return {
        financial: financial.status === 'fulfilled' ? financial.value : null,
        suppliers: suppliers.status === 'fulfilled' ? suppliers.value : null,
        products: products.status === 'fulfilled' ? products.value : null,
        trends: trends.status === 'fulfilled' ? trends.value : null,
        metrics: metrics.status === 'fulfilled' ? metrics.value : null,
        errors: [
          financial.status === 'rejected' ? financial.reason : null,
          suppliers.status === 'rejected' ? suppliers.reason : null,
          products.status === 'rejected' ? products.reason : null,
          trends.status === 'rejected' ? trends.reason : null,
          metrics.status === 'rejected' ? metrics.reason : null
        ].filter(Boolean)
      }
    } catch (error) {
      console.error('Error refreshing dashboard data:', error)
      throw error
    }
  }

  /**
   * Get comparative data for different periods
   */
  const getComparativeData = async (
    currentPeriod: PeriodFilter['value'],
    previousPeriod: PeriodFilter['value']
  ) => {
    try {
      const [current, previous] = await Promise.all([
        apiCall<FinancialSummaryResponse>('/api/v1/api/dashboard/financial-summary', {
          query: { period: currentPeriod }
        }),
        apiCall<FinancialSummaryResponse>('/api/v1/api/dashboard/financial-summary', {
          query: { period: previousPeriod }
        })
      ])

      return {
        current,
        previous,
        comparison: {
          value_growth: current.total_value && previous.total_value 
            ? ((current.total_value - previous.total_value) / previous.total_value) * 100
            : 0,
          invoice_growth: current.total_invoices && previous.total_invoices
            ? ((current.total_invoices - previous.total_invoices) / previous.total_invoices) * 100
            : 0,
          average_value_growth: current.average_invoice_value && previous.average_invoice_value
            ? ((current.average_invoice_value - previous.average_invoice_value) / previous.average_invoice_value) * 100
            : 0
        }
      }
    } catch (error) {
      console.error('Error getting comparative data:', error)
      throw error
    }
  }

  return {
    // Individual data fetchers
    getFinancialSummary,
    getSuppliersData,
    getProductsAnalysis,
    getTrendsAnalysis,
    getDashboardMetrics,
    
    // Bulk operations
    refreshAllDashboardData,
    getComparativeData
  }
}