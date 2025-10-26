/**
 * Composable for API calls with proper base URL configuration
 */
export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBaseUrl = config.public.apiBaseUrl

  const apiCall = async <T>(endpoint: string, options?: any): Promise<T> => {
    const url = `${apiBaseUrl}${endpoint}`
    return await $fetch<T>(url, options)
  }

  return {
    apiCall,
    apiBaseUrl
  }
}