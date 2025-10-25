<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
      <button class="btn btn-ghost btn-sm" @click="$router.back()">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
        </svg>
        Voltar
      </button>
      <div>
        <h1 class="text-3xl font-bold text-base-content">Nota Fiscal {{ invoice?.number }}</h1>
        <p class="text-base-content/70">Detalhes da nota fiscal</p>
      </div>
    </div>

    <!-- Invoice Details -->
    <div v-if="invoice" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Basic Info -->
      <div class="card bg-base-100 shadow-sm border border-base-300">
        <div class="card-body">
          <h2 class="card-title text-lg">Informações Básicas</h2>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-base-content/70">Número:</span>
              <span class="font-mono">{{ invoice.number }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/70">Tipo:</span>
              <div class="badge badge-outline">{{ invoice.type }}</div>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/70">Data de Emissão:</span>
              <span>{{ formatDate(invoice.issueDate) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/70">Status:</span>
              <div :class="getStatusBadgeClass(invoice.status)">
                {{ getStatusText(invoice.status) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Issuer Info -->
      <div class="card bg-base-100 shadow-sm border border-base-300">
        <div class="card-body">
          <h2 class="card-title text-lg">Emitente</h2>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-base-content/70">Razão Social:</span>
              <span>{{ invoice.issuer }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/70">CNPJ:</span>
              <span class="font-mono">{{ formatCNPJ(invoice.cnpj) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Financial Info -->
      <div class="card bg-base-100 shadow-sm border border-base-300 lg:col-span-2">
        <div class="card-body">
          <h2 class="card-title text-lg">Informações Financeiras</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="stat">
              <div class="stat-title">Valor Total</div>
              <div class="stat-value text-2xl">{{ formatCurrency(invoice.totalValue) }}</div>
            </div>
            <div class="stat">
              <div class="stat-title">Impostos</div>
              <div class="stat-value text-2xl">{{ formatCurrency(invoice.totalValue * 0.15) }}</div>
            </div>
            <div class="stat">
              <div class="stat-title">Valor Líquido</div>
              <div class="stat-value text-2xl">{{ formatCurrency(invoice.totalValue * 0.85) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="flex justify-center items-center h-64">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const invoiceId = route.params.id

// Mock data - replace with actual API call
const invoice = ref({
  id: invoiceId,
  number: '000000001',
  type: 'NFe',
  issuer: 'Empresa ABC Ltda',
  cnpj: '12345678000195',
  issueDate: '2024-01-15',
  totalValue: 1250.50,
  status: 'processed'
})

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
    processed: 'badge badge-success',
    pending: 'badge badge-warning',
    error: 'badge badge-error'
  }
  return classes[status as keyof typeof classes] || 'badge badge-ghost'
}

const getStatusText = (status: string) => {
  const texts = {
    processed: 'Processado',
    pending: 'Pendente',
    error: 'Erro'
  }
  return texts[status as keyof typeof texts] || status
}
</script>