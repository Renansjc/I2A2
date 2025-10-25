<template>
  <div class="space-y-4">
    <!-- Query Input -->
    <div class="form-control">
      <div class="input-group">
        <input
          v-model="query"
          type="text"
          placeholder="Pergunte sobre seus dados fiscais... ex: 'Quais fornecedores tiveram maior crescimento neste trimestre?'"
          class="input input-bordered input-lg flex-1"
          @keyup.enter="handleSubmit"
        />
        <button 
          class="btn btn-primary btn-lg"
          :disabled="!query.trim() || isLoading"
          @click="handleSubmit"
        >
          <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
          <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Quick Suggestions -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion"
        class="btn btn-sm btn-outline"
        @click="query = suggestion"
      >
        {{ suggestion }}
      </button>
    </div>

    <!-- Query History -->
    <div v-if="queryHistory.length > 0" class="collapse collapse-arrow bg-base-100">
      <input type="checkbox" />
      <div class="collapse-title text-sm font-medium">
        Consultas Recentes ({{ queryHistory.length }})
      </div>
      <div class="collapse-content">
        <div class="space-y-2">
          <div
            v-for="(historyItem, index) in queryHistory.slice(0, 5)"
            :key="index"
            class="flex items-center justify-between p-2 bg-base-200 rounded cursor-pointer hover:bg-base-300"
            @click="query = historyItem.query"
          >
            <span class="text-sm">{{ historyItem.query }}</span>
            <span class="text-xs text-base-content/50">{{ formatTime(historyItem.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Preview -->
    <div v-if="lastResult" class="card bg-base-100 shadow">
      <div class="card-body">
        <h4 class="card-title text-lg">Resultado da Consulta</h4>
        <div class="mockup-code">
          <pre><code>{{ lastResult }}</code></pre>
        </div>
        <div class="card-actions justify-end">
          <button class="btn btn-sm btn-primary">Gerar Relatório</button>
          <button class="btn btn-sm btn-secondary">Salvar Consulta</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Reactive state
const query = ref('')
const isLoading = ref(false)
const lastResult = ref('')
const queryHistory = ref<Array<{query: string, timestamp: Date}>>([])

// Quick suggestions for executives
const suggestions = [
  "Top 5 fornecedores por volume este mês",
  "Tendências de eficiência fiscal último trimestre", 
  "Categorias de produtos com maior crescimento",
  "Distribuição regional de fornecedores",
  "Resumo mensal de processamento de notas"
]

// Load query history from localStorage
onMounted(() => {
  const saved = localStorage.getItem('queryHistory')
  if (saved) {
    queryHistory.value = JSON.parse(saved).map((item: any) => ({
      ...item,
      timestamp: new Date(item.timestamp)
    }))
  }
})

// Handle query submission
const handleSubmit = async () => {
  if (!query.value.trim()) return
  
  isLoading.value = true
  
  // Add to history
  const historyItem = {
    query: query.value,
    timestamp: new Date()
  }
  queryHistory.value.unshift(historyItem)
  
  // Keep only last 20 queries
  if (queryHistory.value.length > 20) {
    queryHistory.value = queryHistory.value.slice(0, 20)
  }
  
  // Save to localStorage
  localStorage.setItem('queryHistory', JSON.stringify(queryHistory.value))
  
  try {
    // Simulate API call - will be replaced with actual backend integration
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Mock response
    lastResult.value = `Consulta: "${query.value}"\n\nStatus: Processando...\nEste resultado será substituído pela resposta real do agente IA.`
    
  } catch (error) {
    console.error('Query failed:', error)
    lastResult.value = 'Erro ao processar consulta. Tente novamente.'
  } finally {
    isLoading.value = false
  }
}

// Format timestamp for display
const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Agora mesmo'
  if (minutes < 60) return `há ${minutes}m`
  if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`
  return timestamp.toLocaleDateString()
}
</script>