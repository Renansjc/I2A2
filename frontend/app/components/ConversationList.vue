<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
          Conversas Recentes
        </h3>
        <div class="badge badge-primary">{{ conversations.length }}</div>
      </div>

      <!-- Search and Filter -->
      <div class="mb-4 space-y-2">
        <div class="form-control">
          <div class="input-group">
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="Buscar conversas..." 
              class="input input-bordered input-sm flex-1"
            >
            <button class="btn btn-square btn-sm">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="flex gap-2">
          <select v-model="statusFilter" class="select select-bordered select-xs">
            <option value="">Todos os status</option>
            <option value="active">Ativa</option>
            <option value="completed">Concluída</option>
            <option value="error">Com erro</option>
          </select>
          <select v-model="agentFilter" class="select select-bordered select-xs">
            <option value="">Todos os agentes</option>
            <option value="master">Master Agent</option>
            <option value="xml">XML Agent</option>
            <option value="sql">SQL Agent</option>
            <option value="report">Report Agent</option>
          </select>
        </div>
      </div>

      <!-- Conversation List -->
      <div class="space-y-2 max-h-96 overflow-y-auto">
        <div
          v-for="conversation in filteredConversations"
          :key="conversation.id"
          @click="selectConversation(conversation)"
          class="p-3 bg-base-100 rounded-lg cursor-pointer hover:bg-base-300 transition-colors"
          :class="{ 'ring-2 ring-primary': selectedConversationId === conversation.id }"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-2">
              <div 
                class="w-3 h-3 rounded-full"
                :class="getStatusColor(conversation.status)"
              ></div>
              <h4 class="font-semibold text-sm truncate">{{ conversation.title }}</h4>
            </div>
            <div class="text-xs text-base-content/50">
              {{ formatTime(conversation.lastActivity) }}
            </div>
          </div>

          <p class="text-xs text-base-content/70 mb-2 line-clamp-2">
            {{ conversation.lastMessage }}
          </p>

          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="badge badge-outline badge-xs">
                {{ conversation.primaryAgent }}
              </div>
              <span class="text-xs text-base-content/50">
                {{ conversation.messageCount }} mensagens
              </span>
            </div>
            <div class="flex items-center gap-1">
              <div 
                v-if="conversation.hasContext"
                class="tooltip tooltip-left" 
                data-tip="Contexto preservado"
              >
                <svg class="w-3 h-3 text-success" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div 
                v-if="conversation.priority === 'high'"
                class="tooltip tooltip-left" 
                data-tip="Alta prioridade"
              >
                <svg class="w-3 h-3 text-warning" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="filteredConversations.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
          <p class="text-base-content/50">
            {{ searchQuery || statusFilter || agentFilter ? 'Nenhuma conversa encontrada' : 'Nenhuma conversa disponível' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Conversation } from '~/types/dashboard'

// Props and emits
const emit = defineEmits<{
  selectConversation: [conversation: Conversation]
}>()

// Reactive state
const searchQuery = ref('')
const statusFilter = ref('')
const agentFilter = ref('')
const selectedConversationId = ref<string | null>(null)

// Mock conversations data
const conversations = ref<Conversation[]>([
  {
    id: '1',
    title: 'Análise de fornecedores Q4 2024',
    status: 'active',
    lastActivity: new Date(Date.now() - 5 * 60 * 1000),
    lastMessage: 'Quais são os principais fornecedores por volume de transações no último trimestre?',
    primaryAgent: 'SQL Agent',
    messageCount: 8,
    hasContext: true,
    priority: 'high',
    userId: 'exec-001',
    startTime: new Date(Date.now() - 25 * 60 * 1000)
  },
  {
    id: '2',
    title: 'Processamento XML - Lote Janeiro',
    status: 'completed',
    lastActivity: new Date(Date.now() - 15 * 60 * 1000),
    lastMessage: 'Processamento concluído com sucesso. 45 documentos NF-e processados.',
    primaryAgent: 'XML Agent',
    messageCount: 12,
    hasContext: true,
    priority: 'medium',
    userId: 'exec-001',
    startTime: new Date(Date.now() - 45 * 60 * 1000)
  },
  {
    id: '3',
    title: 'Relatório executivo mensal',
    status: 'active',
    lastActivity: new Date(Date.now() - 30 * 60 * 1000),
    lastMessage: 'Gere um relatório executivo com os principais KPIs fiscais do mês.',
    primaryAgent: 'Report Agent',
    messageCount: 6,
    hasContext: true,
    priority: 'medium',
    userId: 'exec-002',
    startTime: new Date(Date.now() - 60 * 60 * 1000)
  },
  {
    id: '4',
    title: 'Categorização de produtos novos',
    status: 'error',
    lastActivity: new Date(Date.now() - 2 * 60 * 60 * 1000),
    lastMessage: 'Erro na categorização automática. Revisão manual necessária.',
    primaryAgent: 'AI Categorization Agent',
    messageCount: 4,
    hasContext: false,
    priority: 'high',
    userId: 'exec-001',
    startTime: new Date(Date.now() - 3 * 60 * 60 * 1000)
  },
  {
    id: '5',
    title: 'Consulta sobre compliance fiscal',
    status: 'completed',
    lastActivity: new Date(Date.now() - 4 * 60 * 60 * 1000),
    lastMessage: 'Análise de compliance concluída. Taxa de conformidade: 94.2%',
    primaryAgent: 'Master Agent',
    messageCount: 15,
    hasContext: true,
    priority: 'low',
    userId: 'exec-003',
    startTime: new Date(Date.now() - 5 * 60 * 60 * 1000)
  }
])

// Computed properties
const filteredConversations = computed(() => {
  return conversations.value.filter(conversation => {
    const matchesSearch = !searchQuery.value || 
      conversation.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      conversation.lastMessage.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesStatus = !statusFilter.value || conversation.status === statusFilter.value
    const matchesAgent = !agentFilter.value || conversation.primaryAgent.toLowerCase().includes(agentFilter.value)
    
    return matchesSearch && matchesStatus && matchesAgent
  }).sort((a, b) => b.lastActivity.getTime() - a.lastActivity.getTime())
})

// Methods
const selectConversation = (conversation: Conversation) => {
  selectedConversationId.value = conversation.id
  emit('selectConversation', conversation)
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'bg-primary animate-pulse'
    case 'completed': return 'bg-success'
    case 'error': return 'bg-error'
    default: return 'bg-base-300'
  }
}

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Agora mesmo'
  if (minutes < 60) return `há ${minutes}m`
  if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`
  return timestamp.toLocaleDateString('pt-BR')
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>