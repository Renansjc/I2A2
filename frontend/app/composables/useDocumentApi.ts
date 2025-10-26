import type { 
  ProcessarXMLResponse,
  DocumentStatusResponse,
  DocumentDetailResponse
} from '~/types/specialized-apis'
import type { ApiOptions } from '~/types/api'

/**
 * Document API composable for XML processing and document management
 */
export const useDocumentApi = () => {
  const { apiCall, apiCallWithState } = useApi()

  /**
   * Upload XML file for processing
   */
  const uploadXML = async (
    file: File,
    options?: ApiOptions
  ): Promise<ProcessarXMLResponse> => {
    const formData = new FormData()
    formData.append('arquivo', file)
    
    return apiCall<ProcessarXMLResponse>('/agentes/upload-xml', {
      ...options,
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type, let browser set it with boundary for FormData
      },
      timeout: 60000, // 1 minute timeout for file upload
      retry: 1 // Only retry once for uploads
    })
  }

  /**
   * Upload multiple XML files
   */
  const uploadMultipleXML = async (
    files: File[],
    options?: ApiOptions
  ): Promise<ProcessarXMLResponse[]> => {
    const uploadPromises = files.map(file => uploadXML(file, options))
    
    try {
      return await Promise.all(uploadPromises)
    } catch (error) {
      console.error('Error uploading multiple files:', error)
      throw error
    }
  }

  /**
   * Get document processing status
   */
  const getDocumentStatus = (
    documentId: string,
    options?: ApiOptions
  ) => {
    return apiCallWithState<DocumentStatusResponse>(
      `/api/v1/api/documents/${documentId}/status`,
      {
        ...options,
        cache: false, // Always get fresh status
        retry: 2
      }
    )
  }

  /**
   * Get detailed document information
   */
  const getDocumentDetails = (
    documentId: string,
    options?: ApiOptions
  ) => {
    return apiCallWithState<DocumentDetailResponse>(
      `/api/v1/api/documents/${documentId}`,
      {
        ...options,
        cache: true,
        cacheTTL: 600000 // 10 minutes cache for document details
      }
    )
  }

  /**
   * Get list of documents with filtering and pagination
   */
  const getDocumentsList = (
    filters?: {
      status?: 'pending' | 'processing' | 'completed' | 'error'
      type?: 'nfe' | 'nfse'
      startDate?: string
      endDate?: string
      search?: string
    },
    pagination?: {
      page?: number
      limit?: number
      sortBy?: string
      sortOrder?: 'asc' | 'desc'
    },
    options?: ApiOptions
  ) => {
    const query: Record<string, any> = {}
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          query[key] = value
        }
      })
    }
    
    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          query[key] = value
        }
      })
    }

    return apiCallWithState<{
      documents: DocumentDetailResponse[]
      total: number
      page: number
      limit: number
      hasMore: boolean
    }>('/api/v1/api/documents', {
      ...options,
      query,
      cache: true,
      cacheTTL: 120000 // 2 minutes cache for document lists
    })
  }

  /**
   * Poll document status until completion
   */
  const pollDocumentStatus = async (
    documentId: string,
    onUpdate?: (status: DocumentStatusResponse) => void,
    maxAttempts: number = 60, // 5 minutes with 5-second intervals
    interval: number = 5000
  ): Promise<DocumentStatusResponse> => {
    let attempts = 0
    
    const poll = async (): Promise<DocumentStatusResponse> => {
      attempts++
      
      try {
        const status = await apiCall<DocumentStatusResponse>(
          `/api/v1/api/documents/${documentId}/status`
        )
        
        if (onUpdate) {
          onUpdate(status)
        }
        
        // Check if processing is complete
        if (status.status === 'completed' || status.status === 'error') {
          return status
        }
        
        // Check if we've exceeded max attempts
        if (attempts >= maxAttempts) {
          throw new Error(`Polling timeout after ${maxAttempts} attempts`)
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, interval))
        
        // Recursive poll
        return poll()
      } catch (error) {
        console.error(`Polling attempt ${attempts} failed:`, error)
        
        if (attempts >= maxAttempts) {
          throw error
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, interval))
        return poll()
      }
    }
    
    return poll()
  }

  /**
   * Cancel document processing
   */
  const cancelDocumentProcessing = async (
    documentId: string,
    options?: ApiOptions
  ): Promise<{ success: boolean; message: string }> => {
    return apiCall<{ success: boolean; message: string }>(
      `/api/v1/api/documents/${documentId}/cancel`,
      {
        ...options,
        method: 'POST'
      }
    )
  }

  /**
   * Retry failed document processing
   */
  const retryDocumentProcessing = async (
    documentId: string,
    options?: ApiOptions
  ): Promise<ProcessarXMLResponse> => {
    return apiCall<ProcessarXMLResponse>(
      `/api/v1/api/documents/${documentId}/retry`,
      {
        ...options,
        method: 'POST'
      }
    )
  }

  /**
   * Delete document
   */
  const deleteDocument = async (
    documentId: string,
    options?: ApiOptions
  ): Promise<{ success: boolean; message: string }> => {
    return apiCall<{ success: boolean; message: string }>(
      `/api/v1/api/documents/${documentId}`,
      {
        ...options,
        method: 'DELETE'
      }
    )
  }

  /**
   * Get document processing logs
   */
  const getDocumentLogs = (
    documentId: string,
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      logs: Array<{
        timestamp: string
        level: 'info' | 'warning' | 'error'
        agent: string
        message: string
        details?: any
      }>
    }>(`/api/v1/api/documents/${documentId}/logs`, {
      ...options,
      cache: false
    })
  }

  /**
   * Validate XML file before upload
   */
  const validateXMLFile = (file: File): { valid: boolean; error?: string } => {
    const maxSize = 10 * 1024 * 1024 // 10MB
    const allowedTypes = ['application/xml', 'text/xml']
    const allowedExtensions = ['.xml']
    
    // Check file size
    if (file.size > maxSize) {
      return { valid: false, error: 'Arquivo muito grande (máximo 10MB)' }
    }
    
    // Check file type
    if (!allowedTypes.includes(file.type) && file.type !== '') {
      return { valid: false, error: 'Apenas arquivos XML são permitidos' }
    }
    
    // Check file extension
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!allowedExtensions.includes(extension)) {
      return { valid: false, error: 'Apenas arquivos com extensão .xml são permitidos' }
    }
    
    // Check if file is empty
    if (file.size === 0) {
      return { valid: false, error: 'Arquivo está vazio' }
    }
    
    return { valid: true }
  }

  /**
   * Get processing statistics
   */
  const getProcessingStatistics = (
    period?: 'today' | 'week' | 'month' | 'year',
    options?: ApiOptions
  ) => {
    return apiCallWithState<{
      total_documents: number
      successful_processing: number
      failed_processing: number
      success_rate: number
      average_processing_time: number
      processing_by_type: {
        nfe: number
        nfse: number
      }
      processing_by_status: {
        pending: number
        processing: number
        completed: number
        error: number
      }
    }>('/api/v1/api/documents/statistics', {
      ...options,
      query: period ? { period } : {},
      cache: true,
      cacheTTL: 300000 // 5 minutes cache
    })
  }

  return {
    // File upload
    uploadXML,
    uploadMultipleXML,
    validateXMLFile,
    
    // Document management
    getDocumentStatus,
    getDocumentDetails,
    getDocumentsList,
    getDocumentLogs,
    
    // Processing control
    pollDocumentStatus,
    cancelDocumentProcessing,
    retryDocumentProcessing,
    deleteDocument,
    
    // Statistics
    getProcessingStatistics
  }
}