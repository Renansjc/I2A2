<template>
  <div class="space-y-6">
    <!-- Query Input with Intelligent Suggestions -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-lg font-semibold">Faça sua pergunta em linguagem natural</span>
        <span class="label-text-alt text-sm opacity-70">Powered by IA</span>
      </label>
      
      <div class="relative">
        <div class="input-group">
          <input
            ref="queryInput"
            v-model="query"
            type="text"
            placeholder="Ex: 'Quais fornecedores tiveram maior crescimento neste trimestre?' ou 'Mostre o resumo fiscal de outubro'"
            class="input input-bordered input-lg flex-1 pr-12"
            :class="{ 'input-warning': showSuggestions && intelligentSuggestions.length > 0 }"
            @keyup.enter="handleSubmit"
            @input="handleQueryInput"
            @focus="showSuggestions = true"
            @blur="hideSuggestionsDelayed"
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

        <!-- Intelligent Suggestions Dropdown -->
        <div 
          v-if="showSuggestions && filteredSuggestions.length > 0"
          class="absolute top-full left-0 right-0 z-50 mt-1 bg-base-100 border border-base-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
        >
          <div class="p-2">
            <div class="text-xs text-base-content/60 mb-2 px-2">Sugestões inteligentes baseadas no contexto:</div>
            <div
              v-for="(suggestion, index) in filteredSuggestions"
              :key="index"
              class="flex items-start gap-3 p-3 hover:bg-base-200 rounded cursor-pointer transition-colors"
              @mousedown.prevent="selectSuggestion(suggestion)"
            >
              <div class="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-base-content">{{ suggestion.text }}</div>
                <div class="text-xs text-base-content/60 mt-1">{{ suggestion.description }}</div>
                <div class="flex items-center gap-2 mt-2">
                  <span class="badge badge-xs badge-primary">{{ suggestion.category }}</span>
                  <span class="text-xs text-base-content/50">~{{ suggestion.estimatedTime }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Action Buttons -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      <button
        v-for="quickAction in quickActions"
        :key="quickAction.text"
        class="btn btn-outline btn-sm justify-start gap-2"
        @click="selectQuickAction(quickAction)"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path :d="quickAction.icon"></path>
        </svg>
        {{ quickAction.text }}
      </button>
    </div>

    <!-- Query Preview and Confirmation -->
    <div v-if="showPreview && queryPreview" class="card bg-warning/10 border border-warning/20">
      <div class="card-body">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0">
            <svg class="w-6 h-6 text-warning" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="flex-1">
            <h4 class="font-semibold text-warning mb-2">Confirmar Consulta</h4>
            <div class="space-y-3">
              <div>
                <div class="text-sm font-medium mb-1">Pergunta interpretada:</div>
                <div class="text-sm bg-base-100 p-3 rounded border">{{ queryPreview.interpretedQuery }}</div>
              </div>
              <div>
                <div class="text-sm font-medium mb-1">Agentes que serão acionados:</div>
                <div class="flex flex-wrap gap-2">
                  <span 
                    v-for="agent in queryPreview.involvedAgents"
                    :key="agent"
                    class="badge badge-primary badge-sm"
                  >
                    {{ agent }}
                  </span>
                </div>
              </div>
              <div>
                <div class="text-sm font-medium mb-1">Tempo estimado:</div>
                <div class="text-sm text-base-content/70">{{ queryPreview.estimatedTime }}</div>
              </div>
            </div>
            <div class="card-actions justify-end mt-4">
              <button class="btn btn-sm btn-ghost" @click="cancelQuery">Cancelar</button>
              <button class="btn btn-sm btn-primary" @click="confirmQuery">Confirmar e Executar</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Query History -->
    <div v-if="queryHistory.length > 0" class="collapse collapse-arrow bg-base-100 border border-base-300">
      <input type="checkbox" />
      <div class="collapse-title text-sm font-medium">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
          Consultas Recentes ({{ queryHistory.length }})
        </div>
      </div>
      <div class="collapse-content">
        <div class="space-y-2">
          <div
            v-for="(historyItem, index) in queryHistory.slice(0, 8)"
            :key="index"
            class="flex items-center justify-between p-3 bg-base-200 rounded-lg cursor-pointer hover:bg-base-300 transition-colors"
            @click="selectHistoryItem(historyItem)"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">{{ historyItem.query }}</div>
              <div class="text-xs text-base-content/60 mt-1">
                {{ historyItem.status }} • {{ formatTime(historyItem.timestamp) }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span 
                class="badge badge-xs"
                :class="getStatusBadgeClass(historyItem.status)"
              >
                {{ historyItem.status }}
              </span>
              <button 
                class="btn btn-ghost btn-xs"
                @click.stop="removeHistoryItem(index)"
              >
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Executive Results Display -->
    <div v-if="queryResult" class="card bg-base-100 shadow-lg border border-base-300">
      <div class="card-body">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h4 class="card-title text-xl flex items-center gap-2">
              <svg class="w-6 h-6 text-success" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              Resultado da Análise
            </h4>
            <div class="text-sm text-base-content/70 mt-1">
              Consulta: "{{ queryResult.originalQuery }}"
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="badge badge-success badge-sm">{{ queryResult.executionTime }}</span>
            <span class="badge badge-info badge-sm">{{ queryResult.confidence }}% confiança</span>
          </div>
        </div>

        <!-- Executive Summary -->
        <div v-if="queryResult.executiveSummary" class="mb-6">
          <h5 class="font-semibold text-lg mb-3 flex items-center gap-2">
            <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
            </svg>
            Resumo Executivo
          </h5>
          <div class="prose prose-sm max-w-none">
            <div class="bg-primary/5 p-4 rounded-lg border-l-4 border-primary">
              {{ queryResult.executiveSummary }}
            </div>
          </div>
        </div>

        <!-- Key Insights -->
        <div v-if="queryResult.keyInsights && queryResult.keyInsights.length > 0" class="mb-6">
          <h5 class="font-semibold text-lg mb-3 flex items-center gap-2">
            <svg class="w-5 h-5 text-secondary" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
            </svg>
            Principais Insights
          </h5>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="(insight, index) in queryResult.keyInsights"
              :key="index"
              class="bg-base-200 p-4 rounded-lg"
            >
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-8 h-8 bg-secondary/20 rounded-full flex items-center justify-center">
                  <span class="text-sm font-bold text-secondary">{{ index + 1 }}</span>
                </div>
                <div class="flex-1">
                  <div class="font-medium text-sm mb-1">{{ insight.title }}</div>
                  <div class="text-sm text-base-content/80">{{ insight.description }}</div>
                  <div v-if="insight.impact" class="text-xs text-base-content/60 mt-2">
                    Impacto: {{ insight.impact }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Visualization -->
        <div v-if="queryResult.chartData" class="mb-6">
          <h5 class="font-semibold text-lg mb-3 flex items-center gap-2">
            <svg class="w-5 h-5 text-accent" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
            </svg>
            Visualização dos Dados
          </h5>
          <div class="bg-base-200 p-4 rounded-lg">
            <!-- This would be replaced with actual chart component -->
            <div class="text-center text-base-content/60 py-8">
              <svg class="w-16 h-16 mx-auto mb-4 text-base-content/30" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
              </svg>
              <div class="text-sm">Gráfico será renderizado aqui</div>
              <div class="text-xs mt-1">Dados: {{ queryResult.chartData.length }} pontos</div>
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div v-if="queryResult.recommendations && queryResult.recommendations.length > 0" class="mb-6">
          <h5 class="font-semibold text-lg mb-3 flex items-center gap-2">
            <svg class="w-5 h-5 text-warning" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"></path>
            </svg>
            Recomendações Estratégicas
          </h5>
          <div class="space-y-3">
            <div
              v-for="(recommendation, index) in queryResult.recommendations"
              :key="index"
              class="alert"
              :class="getRecommendationClass(recommendation.priority)"
            >
              <div class="flex-1">
                <div class="font-medium">{{ recommendation.title }}</div>
                <div class="text-sm mt-1">{{ recommendation.description }}</div>
                <div class="flex items-center gap-4 mt-2 text-xs">
                  <span>Prioridade: {{ recommendation.priority }}</span>
                  <span v-if="recommendation.timeline">Prazo: {{ recommendation.timeline }}</span>
                  <span v-if="recommendation.impact">Impacto: {{ recommendation.impact }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="card-actions justify-between">
          <div class="flex gap-2">
            <button class="btn btn-sm btn-ghost" @click="shareResult">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"></path>
              </svg>
              Compartilhar
            </button>
            <button class="btn btn-sm btn-ghost" @click="saveResult">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
              </svg>
              Salvar
            </button>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-sm btn-secondary" @click="generateReport">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>
              </svg>
              Gerar Relatório
            </button>
            <button class="btn btn-sm btn-primary" @click="refineQuery">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
              </svg>
              Refinar Consulta
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'

// Use the natural language query composable
const {
  query,
  isLoading,
  showSuggestions,
  showPreview,
  queryPreview,
  queryResult,
  queryHistory,
  filteredSuggestions,
  intelligentSuggestions,
  quickActions,
  loadQueryHistory,
  generateQueryPreview,
  executeQuery,
  removeHistoryItem,
  formatTime,
  getStatusBadgeClass
} = useNaturalLanguageQuery()

const queryInput = ref<HTMLInputElement>()

// Load query history on mount
onMounted(() => {
  loadQueryHistory()
})

// Handle query input changes for intelligent suggestions
const handleQueryInput = () => {
  // Show suggestions when user types
  if (query.value.length > 0) {
    showSuggestions.value = true
  } else {
    showSuggestions.value = false
  }
}

// Hide suggestions with delay to allow for clicks
const hideSuggestionsDelayed = () => {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

// Select a suggestion
const selectSuggestion = (suggestion: any) => {
  query.value = suggestion.text
  showSuggestions.value = false
  nextTick(() => {
    queryInput.value?.focus()
  })
}

// Select quick action
const selectQuickAction = (action: any) => {
  query.value = action.query
  nextTick(() => {
    queryInput.value?.focus()
  })
}

// Select history item
const selectHistoryItem = (historyItem: any) => {
  query.value = historyItem.query
}

// Handle query submission with preview
const handleSubmit = async () => {
  if (!query.value.trim()) return
  
  // Show preview first
  queryPreview.value = generateQueryPreview(query.value)
  showPreview.value = true
}

// Confirm and execute query
const confirmQuery = async () => {
  showPreview.value = false
  isLoading.value = true
  
  try {
    queryResult.value = await executeQuery(query.value)
  } catch (error) {
    console.error('Query failed:', error)
  } finally {
    isLoading.value = false
  }
}

// Cancel query
const cancelQuery = () => {
  showPreview.value = false
  queryPreview.value = null
}

const getRecommendationClass = (priority: string) => {
  switch (priority) {
    case 'alta': return 'alert-error'
    case 'média': return 'alert-warning'
    case 'baixa': return 'alert-info'
    default: return 'alert-info'
  }
}

// Action handlers
const shareResult = () => {
  // Implementation for sharing results
  console.log('Sharing result...')
}

const saveResult = () => {
  // Implementation for saving results
  console.log('Saving result...')
}

const generateReport = () => {
  // Implementation for generating report
  console.log('Generating report...')
}

const refineQuery = () => {
  // Implementation for refining query
  queryResult.value = null
  nextTick(() => {
    queryInput.value?.focus()
  })
}


</script>