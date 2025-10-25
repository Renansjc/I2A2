<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-base-content">Notas Fiscais</h1>
        <p class="text-base-content/70 mt-1">Gerencie e visualize todas as notas fiscais processadas</p>
      </div>
      
      <div class="flex gap-3">
        <button class="btn btn-outline btn-primary">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Exportar
        </button>
        <button class="btn btn-primary" @click="refreshData">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Atualizar
        </button>
      </div>
    </div>

    <!-- Filters and Search -->
    <div class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Buscar</span>
            </label>
            <input 
              type="text" 
              placeholder="Número, CNPJ, razão social..." 
              class="input input-bordered input-sm"
              v-model="searchTerm"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Tipo</span>
            </label>
            <select class="select select-bordered select-sm" v-model="filterType">
              <option value="">Todos</option>
              <option value="NFe">NF-e</option>
              <option value="NFSe">NFS-e</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Status</span>
            </label>
            <select class="select select-bordered select-sm" v-model="filterStatus">
              <option value="">Todos</option>
              <option value="processed">Processado</option>
              <option value="pending">Pendente</option>
              <option value="error">Erro</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Período</span>
            </label>
            <input 
              type="date" 
              class="input input-bordered input-sm"
              v-model="dateFilter"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Invoices Table -->
    <div class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-0">
        <div class="overflow-x-auto">
          <table class="table table-zebra table-pin-rows">
            <thead class="bg-base-200">
              <tr>
                <th class="w-12">
                  <input type="checkbox" class="checkbox checkbox-sm" @change="toggleSelectAll" />
                </th>
                <th class="font-semibold">Número</th>
                <th class="font-semibold">Tipo</th>
                <th class="font-semibold">Emitente</th>
                <th class="font-semibold">CNPJ</th>
                <th class="font-semibold">Data Emissão</th>
                <th class="font-semibold">Valor Total</th>
                <th class="font-semibold">Status</th>
                <th class="font-semibold text-center">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invoice in filteredInvoices" :key="invoice.id" class="hover">
                <td>
                  <input 
                    type="checkbox" 
                    class="checkbox checkbox-sm" 
                    v-model="selectedInvoices"
                    :value="invoice.id"
                  />
                </td>
                <td class="font-mono text-sm">{{ invoice.number }}</td>
                <td>
                  <div class="badge badge-outline badge-sm">{{ invoice.type }}</div>
                </td>
                <td class="max-w-xs truncate">{{ invoice.issuer }}</td>
                <td class="font-mono text-sm">{{ formatCNPJ(invoice.cnpj) }}</td>
                <td class="text-sm">{{ formatDate(invoice.issueDate) }}</td>
                <td class="font-semibold">{{ formatCurrency(invoice.totalValue) }}</td>
                <td>
                  <div :class="getStatusBadgeClass(invoice.status)">
                    {{ getStatusText(invoice.status) }}
                  </div>
                </td>
                <td>
                  <div class="flex justify-center gap-1">
                    <button 
                      class="btn btn-ghost btn-xs tooltip" 
                      data-tip="Visualizar"
                      @click="viewInvoice(invoice)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                      </svg>
                    </button>
                    <button 
                      class="btn btn-ghost btn-xs tooltip" 
                      data-tip="Editar"
                      @click="editInvoice(invoice)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                      </svg>
                    </button>
                    <button 
                      class="btn btn-ghost btn-xs text-error tooltip" 
                      data-tip="Excluir"
                      @click="deleteInvoice(invoice)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Pagination -->
        <div class="flex justify-between items-center p-4 border-t border-base-300">
          <div class="text-sm text-base-content/70">
            Mostrando {{ startIndex + 1 }} a {{ endIndex }} de {{ totalInvoices }} registros
          </div>
          <div class="join">
            <button class="join-item btn btn-sm" :disabled="currentPage === 1" @click="previousPage">
              «
            </button>
            <button class="join-item btn btn-sm btn-active">
              Página {{ currentPage }}
            </button>
            <button class="join-item btn btn-sm" :disabled="currentPage === totalPages" @click="nextPage">
              »
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="selectedInvoices.length > 0" class="fixed bottom-6 right-6">
      <div class="card bg-primary text-primary-content shadow-lg">
        <div class="card-body p-4">
          <div class="flex items-center gap-4">
            <span class="text-sm">{{ selectedInvoices.length }} selecionados</span>
            <div class="flex gap-2">
              <button class="btn btn-sm btn-ghost" @click="bulkExport">
                Exportar
              </button>
              <button class="btn btn-sm btn-error" @click="bulkDelete">
                Excluir
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Page metadata
definePageMeta({
  title: 'Notas Fiscais'
})

// Reactive data
const searchTerm = ref('')
const filterType = ref('')
const filterStatus = ref('')
const dateFilter = ref('')
const selectedInvoices = ref<string[]>([])
const currentPage = ref(1)
const itemsPerPage = 20

// Mock data - replace with actual API calls
const invoices = ref([
  {
    id: '1',
    number: '000000001',
    type: 'NFe',
    issuer: 'Empresa ABC Ltda',
    cnpj: '12345678000195',
    issueDate: '2024-01-15',
    totalValue: 1250.50,
    status: 'processed'
  },
  {
    id: '2',
    number: '000000002',
    type: 'NFSe',
    issuer: 'Prestadora XYZ S/A',
    cnpj: '98765432000123',
    issueDate: '2024-01-16',
    totalValue: 850.00,
    status: 'pending'
  },
  {
    id: '3',
    number: '000000003',
    type: 'NFe',
    issuer: 'Fornecedor 123 Eireli',
    cnpj: '11223344000156',
    issueDate: '2024-01-17',
    totalValue: 2100.75,
    status: 'error'
  }
])

// Computed properties
const filteredInvoices = computed(() => {
  let filtered = invoices.value

  if (searchTerm.value) {
    const search = searchTerm.value.toLowerCase()
    filtered = filtered.filter(invoice => 
      invoice.number.toLowerCase().includes(search) ||
      invoice.issuer.toLowerCase().includes(search) ||
      invoice.cnpj.includes(search)
    )
  }

  if (filterType.value) {
    filtered = filtered.filter(invoice => invoice.type === filterType.value)
  }

  if (filterStatus.value) {
    filtered = filtered.filter(invoice => invoice.status === filterStatus.value)
  }

  if (dateFilter.value) {
    filtered = filtered.filter(invoice => invoice.issueDate === dateFilter.value)
  }

  return filtered
})

const totalInvoices = computed(() => filteredInvoices.value.length)
const totalPages = computed(() => Math.ceil(totalInvoices.value / itemsPerPage))
const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage)
const endIndex = computed(() => Math.min(startIndex.value + itemsPerPage, totalInvoices.value))

// Methods
const formatCNPJ = (cnpj: string) => {
  return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('pt-BR')
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

const getStatusBadgeClass = (status: string) => {
  const classes = {
    processed: 'badge badge-success badge-sm',
    pending: 'badge badge-warning badge-sm',
    error: 'badge badge-error badge-sm'
  }
  return classes[status as keyof typeof classes] || 'badge badge-ghost badge-sm'
}

const getStatusText = (status: string) => {
  const texts = {
    processed: 'Processado',
    pending: 'Pendente',
    error: 'Erro'
  }
  return texts[status as keyof typeof texts] || status
}

const toggleSelectAll = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    selectedInvoices.value = filteredInvoices.value.map(invoice => invoice.id)
  } else {
    selectedInvoices.value = []
  }
}

const viewInvoice = (invoice: any) => {
  // Navigate to invoice detail page
  navigateTo(`/invoices/${invoice.id}`)
}

const editInvoice = (invoice: any) => {
  // Navigate to invoice edit page
  navigateTo(`/invoices/${invoice.id}/edit`)
}

const deleteInvoice = (invoice: any) => {
  if (confirm(`Tem certeza que deseja excluir a nota fiscal ${invoice.number}?`)) {
    // API call to delete invoice
    console.log('Deleting invoice:', invoice.id)
  }
}

const bulkExport = () => {
  console.log('Exporting invoices:', selectedInvoices.value)
}

const bulkDelete = () => {
  if (confirm(`Tem certeza que deseja excluir ${selectedInvoices.value.length} notas fiscais?`)) {
    console.log('Bulk deleting invoices:', selectedInvoices.value)
    selectedInvoices.value = []
  }
}

const refreshData = () => {
  // API call to refresh data
  console.log('Refreshing invoice data...')
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}
</script>