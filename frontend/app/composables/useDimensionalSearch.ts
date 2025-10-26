import { ref, computed } from "vue";

export interface SearchFilters {
  search?: string;
  category?: string;
  uf?: string;
  ncm?: string;
  period?: string;
  startDate?: string;
  endDate?: string;
}

export interface PaginationOptions {
  page: number;
  pageSize: number;
  orderBy?: string;
  orderDirection?: 'asc' | 'desc';
}

export interface SearchResult<T> {
  items: T[];
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export const useDimensionalSearch = () => {
  // Reactive state
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<SearchFilters>({});
  const pagination = ref<PaginationOptions>({
    page: 1,
    pageSize: 50,
    orderBy: 'razao_social',
    orderDirection: 'asc'
  });

  // Search suppliers with filters
  const searchSuppliers = async (searchFilters?: SearchFilters, paginationOptions?: Partial<PaginationOptions>) => {
    try {
      isLoading.value = true;
      error.value = null;

      // Merge filters and pagination
      const currentFilters = { ...filters.value, ...searchFilters };
      const currentPagination = { ...pagination.value, ...paginationOptions };

      // Build query parameters
      const query: any = {
        skip: (currentPagination.page - 1) * currentPagination.pageSize,
        limit: currentPagination.pageSize,
        order_by: currentPagination.orderBy,
        order_direction: currentPagination.orderDirection
      };

      if (currentFilters.search) {
        query.search = currentFilters.search;
      }
      if (currentFilters.uf) {
        query.uf = currentFilters.uf;
      }

      const response = await $fetch<SearchResult<any>>('/api/dimensional/emitentes', {
        query
      });

      // Update state
      filters.value = currentFilters;
      pagination.value = currentPagination;

      return response;
    } catch (err: any) {
      console.error('Error searching suppliers:', err);
      error.value = err.data?.mensagem || 'Erro ao buscar fornecedores';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  // Search products with filters
  const searchProducts = async (searchFilters?: SearchFilters, paginationOptions?: Partial<PaginationOptions>) => {
    try {
      isLoading.value = true;
      error.value = null;

      const currentFilters = { ...filters.value, ...searchFilters };
      const currentPagination = { ...pagination.value, ...paginationOptions };

      const query: any = {
        skip: (currentPagination.page - 1) * currentPagination.pageSize,
        limit: currentPagination.pageSize,
        order_by: currentPagination.orderBy || 'descricao',
        order_direction: currentPagination.orderDirection
      };

      if (currentFilters.search) {
        query.search = currentFilters.search;
      }
      if (currentFilters.category) {
        query.category = currentFilters.category;
      }
      if (currentFilters.ncm) {
        query.ncm = currentFilters.ncm;
      }

      const response = await $fetch<SearchResult<any>>('/api/dimensional/produtos', {
        query
      });

      filters.value = currentFilters;
      pagination.value = currentPagination;

      return response;
    } catch (err: any) {
      console.error('Error searching products:', err);
      error.value = err.data?.mensagem || 'Erro ao buscar produtos';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  // Search services with filters
  const searchServices = async (searchFilters?: SearchFilters, paginationOptions?: Partial<PaginationOptions>) => {
    try {
      isLoading.value = true;
      error.value = null;

      const currentFilters = { ...filters.value, ...searchFilters };
      const currentPagination = { ...pagination.value, ...paginationOptions };

      const query: any = {
        skip: (currentPagination.page - 1) * currentPagination.pageSize,
        limit: currentPagination.pageSize,
        order_by: currentPagination.orderBy || 'descricao',
        order_direction: currentPagination.orderDirection
      };

      if (currentFilters.search) {
        query.search = currentFilters.search;
      }
      if (currentFilters.category) {
        query.category = currentFilters.category;
      }

      const response = await $fetch<SearchResult<any>>('/api/dimensional/servicos', {
        query
      });

      filters.value = currentFilters;
      pagination.value = currentPagination;

      return response;
    } catch (err: any) {
      console.error('Error searching services:', err);
      error.value = err.data?.mensagem || 'Erro ao buscar serviços';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  // Export data functionality
  const exportData = async (exportType: 'suppliers' | 'products' | 'services', format: 'excel' | 'pdf' = 'excel') => {
    try {
      isLoading.value = true;
      error.value = null;

      const exportRequest = {
        type: exportType,
        format,
        filters: filters.value,
        include_summary: true
      };

      const response = await $fetch('/api/dimensional/export', {
        method: 'POST',
        body: exportRequest
      });

      return response;
    } catch (err: any) {
      console.error('Error exporting data:', err);
      error.value = err.data?.mensagem || 'Erro ao exportar dados';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  // Reset filters
  const resetFilters = () => {
    filters.value = {};
    pagination.value = {
      page: 1,
      pageSize: 50,
      orderBy: 'razao_social',
      orderDirection: 'asc'
    };
  };

  // Utility functions
  const formatCNPJ = (cnpj: string): string => {
    return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value: number): string => {
    return new Intl.NumberFormat('pt-BR').format(value);
  };

  // Computed properties
  const hasFilters = computed(() => {
    return Object.keys(filters.value).some(key => filters.value[key as keyof SearchFilters]);
  });

  const currentPage = computed(() => pagination.value.page);
  const pageSize = computed(() => pagination.value.pageSize);

  return {
    // State
    isLoading,
    error,
    filters,
    pagination,

    // Methods
    searchSuppliers,
    searchProducts,
    searchServices,
    exportData,
    resetFilters,

    // Utilities
    formatCNPJ,
    formatCurrency,
    formatNumber,

    // Computed
    hasFilters,
    currentPage,
    pageSize
  };
};