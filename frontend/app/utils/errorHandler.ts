import type { ApiError } from '~/types/api'

/**
 * Enhanced API Error class with standardized error codes
 */
export class EnhancedApiError extends Error implements ApiError {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'EnhancedApiError'
  }
}

/**
 * Error code mappings for different scenarios
 */
export const ERROR_CODES = {
  // Network errors
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  CONNECTION_ERROR: 'CONNECTION_ERROR',
  
  // Authentication errors
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  
  // Validation errors
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INVALID_INPUT: 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',
  
  // Business logic errors
  BUSINESS_RULE_VIOLATION: 'BUSINESS_RULE_VIOLATION',
  DUPLICATE_RESOURCE: 'DUPLICATE_RESOURCE',
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  
  // Server errors
  SERVER_ERROR: 'SERVER_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  
  // File processing errors
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  INVALID_FILE_TYPE: 'INVALID_FILE_TYPE',
  FILE_PROCESSING_ERROR: 'FILE_PROCESSING_ERROR',
  
  // Agent processing errors
  AGENT_PROCESSING_ERROR: 'AGENT_PROCESSING_ERROR',
  LLM_SERVICE_ERROR: 'LLM_SERVICE_ERROR',
  PROCESSING_TIMEOUT: 'PROCESSING_TIMEOUT',
  
  // Unknown errors
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const

/**
 * User-friendly error messages in Portuguese
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  [ERROR_CODES.NETWORK_ERROR]: 'Problema de conexão com o servidor. Verifique sua internet e tente novamente.',
  [ERROR_CODES.TIMEOUT_ERROR]: 'A operação demorou muito para responder. Tente novamente.',
  [ERROR_CODES.CONNECTION_ERROR]: 'Não foi possível conectar ao servidor. Tente novamente em alguns instantes.',
  
  // Authentication errors
  [ERROR_CODES.AUTHENTICATION_ERROR]: 'Credenciais inválidas. Verifique seu login e senha.',
  [ERROR_CODES.AUTHORIZATION_ERROR]: 'Você não tem permissão para realizar esta ação.',
  [ERROR_CODES.SESSION_EXPIRED]: 'Sua sessão expirou. Faça login novamente.',
  
  // Validation errors
  [ERROR_CODES.VALIDATION_ERROR]: 'Dados inválidos. Verifique os campos preenchidos.',
  [ERROR_CODES.INVALID_INPUT]: 'Formato de dados inválido. Verifique as informações inseridas.',
  [ERROR_CODES.MISSING_REQUIRED_FIELD]: 'Campos obrigatórios não preenchidos.',
  
  // Business logic errors
  [ERROR_CODES.BUSINESS_RULE_VIOLATION]: 'Operação não permitida pelas regras de negócio.',
  [ERROR_CODES.DUPLICATE_RESOURCE]: 'Este recurso já existe no sistema.',
  [ERROR_CODES.RESOURCE_NOT_FOUND]: 'Recurso não encontrado.',
  
  // Server errors
  [ERROR_CODES.SERVER_ERROR]: 'Erro interno do servidor. Nossa equipe foi notificada.',
  [ERROR_CODES.SERVICE_UNAVAILABLE]: 'Serviço temporariamente indisponível. Tente novamente em alguns minutos.',
  [ERROR_CODES.RATE_LIMIT_EXCEEDED]: 'Muitas requisições. Aguarde um momento antes de tentar novamente.',
  
  // File processing errors
  [ERROR_CODES.FILE_TOO_LARGE]: 'Arquivo muito grande. O tamanho máximo permitido é 10MB.',
  [ERROR_CODES.INVALID_FILE_TYPE]: 'Tipo de arquivo não suportado. Apenas arquivos XML são aceitos.',
  [ERROR_CODES.FILE_PROCESSING_ERROR]: 'Erro ao processar o arquivo. Verifique se o formato está correto.',
  
  // Agent processing errors
  [ERROR_CODES.AGENT_PROCESSING_ERROR]: 'Erro no processamento pelos agentes IA. Tente novamente.',
  [ERROR_CODES.LLM_SERVICE_ERROR]: 'Serviço de IA temporariamente indisponível.',
  [ERROR_CODES.PROCESSING_TIMEOUT]: 'Processamento demorou muito. O arquivo pode estar sendo processado em segundo plano.',
  
  // Unknown errors
  [ERROR_CODES.UNKNOWN_ERROR]: 'Erro inesperado. Tente novamente ou entre em contato com o suporte.'
}

/**
 * Map HTTP status codes to error codes
 */
export const mapHttpStatusToErrorCode = (status: number): string => {
  switch (status) {
    case 400:
      return ERROR_CODES.VALIDATION_ERROR
    case 401:
      return ERROR_CODES.AUTHENTICATION_ERROR
    case 403:
      return ERROR_CODES.AUTHORIZATION_ERROR
    case 404:
      return ERROR_CODES.RESOURCE_NOT_FOUND
    case 408:
      return ERROR_CODES.TIMEOUT_ERROR
    case 409:
      return ERROR_CODES.DUPLICATE_RESOURCE
    case 413:
      return ERROR_CODES.FILE_TOO_LARGE
    case 415:
      return ERROR_CODES.INVALID_FILE_TYPE
    case 422:
      return ERROR_CODES.VALIDATION_ERROR
    case 429:
      return ERROR_CODES.RATE_LIMIT_EXCEEDED
    case 500:
      return ERROR_CODES.SERVER_ERROR
    case 502:
    case 503:
      return ERROR_CODES.SERVICE_UNAVAILABLE
    case 504:
      return ERROR_CODES.TIMEOUT_ERROR
    default:
      if (status >= 400 && status < 500) {
        return ERROR_CODES.VALIDATION_ERROR
      } else if (status >= 500) {
        return ERROR_CODES.SERVER_ERROR
      }
      return ERROR_CODES.UNKNOWN_ERROR
  }
}

/**
 * Enhanced error handler that creates standardized API errors
 */
export const handleApiError = (error: any): EnhancedApiError => {
  // Handle fetch/network errors
  if (error.name === 'AbortError') {
    return new EnhancedApiError(
      408,
      ERROR_CODES.TIMEOUT_ERROR,
      ERROR_MESSAGES[ERROR_CODES.TIMEOUT_ERROR],
      { originalError: error }
    )
  }
  
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return new EnhancedApiError(
      0,
      ERROR_CODES.NETWORK_ERROR,
      ERROR_MESSAGES[ERROR_CODES.NETWORK_ERROR],
      { originalError: error }
    )
  }
  
  // Handle HTTP response errors
  if (error.response) {
    const status = error.response.status
    const responseData = error.response.data || error.response._data
    
    let errorCode = mapHttpStatusToErrorCode(status)
    let message = ERROR_MESSAGES[errorCode]
    
    // Try to extract more specific error information from response
    if (responseData) {
      if (responseData.codigo_erro) {
        errorCode = responseData.codigo_erro
      }
      
      if (responseData.mensagem) {
        message = responseData.mensagem
      } else if (responseData.message) {
        message = responseData.message
      } else if (responseData.error) {
        message = responseData.error
      }
    }
    
    return new EnhancedApiError(
      status,
      errorCode,
      message,
      {
        responseData,
        originalError: error
      }
    )
  }
  
  // Handle request errors (no response received)
  if (error.request) {
    return new EnhancedApiError(
      0,
      ERROR_CODES.CONNECTION_ERROR,
      ERROR_MESSAGES[ERROR_CODES.CONNECTION_ERROR],
      { originalError: error }
    )
  }
  
  // Handle other errors
  return new EnhancedApiError(
    500,
    ERROR_CODES.UNKNOWN_ERROR,
    error.message || ERROR_MESSAGES[ERROR_CODES.UNKNOWN_ERROR],
    { originalError: error }
  )
}

/**
 * Get user-friendly error message
 */
export const getUserFriendlyErrorMessage = (error: EnhancedApiError | Error): string => {
  if (error instanceof EnhancedApiError) {
    return ERROR_MESSAGES[error.code] || error.message
  }
  
  return error.message || ERROR_MESSAGES[ERROR_CODES.UNKNOWN_ERROR]
}

/**
 * Check if error is retryable
 */
export const isRetryableError = (error: EnhancedApiError): boolean => {
  const retryableCodes = [
    ERROR_CODES.NETWORK_ERROR,
    ERROR_CODES.TIMEOUT_ERROR,
    ERROR_CODES.CONNECTION_ERROR,
    ERROR_CODES.SERVER_ERROR,
    ERROR_CODES.SERVICE_UNAVAILABLE,
    ERROR_CODES.RATE_LIMIT_EXCEEDED
  ]
  
  return retryableCodes.includes(error.code) || 
         (error.status >= 500 && error.status < 600) ||
         error.status === 429 ||
         error.status === 408
}

/**
 * Get retry delay based on error type and attempt number
 */
export const getRetryDelay = (error: EnhancedApiError, attempt: number): number => {
  const baseDelay = 1000 // 1 second
  const maxDelay = 30000 // 30 seconds
  
  // Special handling for rate limiting
  if (error.code === ERROR_CODES.RATE_LIMIT_EXCEEDED) {
    return Math.min(baseDelay * Math.pow(3, attempt), maxDelay)
  }
  
  // Exponential backoff for other retryable errors
  return Math.min(baseDelay * Math.pow(2, attempt), maxDelay)
}

/**
 * Enhanced retry logic with exponential backoff
 */
export interface RetryOptions {
  maxRetries: number
  baseDelay: number
  maxDelay: number
  backoffFactor: number
  retryCondition?: (error: EnhancedApiError) => boolean
}

export const withRetry = async <T>(
  operation: () => Promise<T>,
  options: RetryOptions = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffFactor: 2,
    retryCondition: isRetryableError
  }
): Promise<T> => {
  let lastError: EnhancedApiError
  
  for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error instanceof EnhancedApiError ? error : handleApiError(error)
      
      // Don't retry on last attempt
      if (attempt === options.maxRetries) {
        throw lastError
      }
      
      // Check if error is retryable
      if (options.retryCondition && !options.retryCondition(lastError)) {
        throw lastError
      }
      
      // Calculate delay
      const delay = Math.min(
        options.baseDelay * Math.pow(options.backoffFactor, attempt),
        options.maxDelay
      )
      
      console.warn(`API call failed (attempt ${attempt + 1}/${options.maxRetries + 1}), retrying in ${delay}ms:`, lastError.message)
      
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw lastError!
}

/**
 * Error recovery strategies
 */
export interface ErrorRecoveryStrategy {
  canRecover: (error: EnhancedApiError) => boolean
  recover: (error: EnhancedApiError) => Promise<any> | any
}

export const createErrorRecoveryManager = () => {
  const strategies: ErrorRecoveryStrategy[] = []
  
  const addStrategy = (strategy: ErrorRecoveryStrategy) => {
    strategies.push(strategy)
  }
  
  const tryRecover = async (error: EnhancedApiError): Promise<any> => {
    for (const strategy of strategies) {
      if (strategy.canRecover(error)) {
        try {
          return await strategy.recover(error)
        } catch (recoveryError) {
          console.warn('Recovery strategy failed:', recoveryError)
        }
      }
    }
    
    throw error
  }
  
  return {
    addStrategy,
    tryRecover
  }
}

/**
 * Default error recovery strategies
 */
export const defaultRecoveryStrategies: ErrorRecoveryStrategy[] = [
  // Cache fallback strategy
  {
    canRecover: (error) => error.code === ERROR_CODES.NETWORK_ERROR || error.code === ERROR_CODES.SERVICE_UNAVAILABLE,
    recover: async (error) => {
      // This would be implemented by the API composable to return cached data
      console.log('Attempting cache fallback for:', error.message)
      return null
    }
  },
  
  // Session refresh strategy
  {
    canRecover: (error) => error.code === ERROR_CODES.SESSION_EXPIRED,
    recover: async (error) => {
      // This would trigger a session refresh
      console.log('Attempting session refresh for:', error.message)
      // Implementation would depend on authentication system
      return null
    }
  }
]