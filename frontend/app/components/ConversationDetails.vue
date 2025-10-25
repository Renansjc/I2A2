<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div v-if="conversation" class="space-y-4">
        <!-- Conversation Header -->
        <div class="flex items-center justify-between pb-4 border-b border-base-300">
          <div>
            <h3 class="card-title">{{ conversation.title }}</h3>
            <div class="flex items-center gap-2 mt-1">
              <div class="badge badge-outline badge-sm">{{ conversation.primaryAgent }}</div>
              <div 
                class="badge badge-sm"
                :class="getStatusBadgeClass(conversation.status)"
              >
                {{ getStatusText(conversation.status) }}
              </div>
              <span class="text-sm text-base-content/50">
                {{ conversation.messageCount }} mensagens
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button 
              @click="exportConversation"
              class="btn btn-ghost btn-sm"
              title="Exportar conversa"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
              </svg>
            </button>
            <button 
              @click="refreshConversation"
              class="btn btn-ghost btn-sm"
              :disabled="isRefreshing"
              title="Atualizar conversa"
            >
              <svg 
                class="w-4 h-4" 
                :class="{ 'animate-spin': isRefreshing }"
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- Conversation Timeline -->
        <div class="space-y-4 max-h-96 overflow-y-auto">
          <div
            v-for="message in messages"
            :key="message.id"
            class="flex gap-3"
            :class="{ 'flex-row-reverse': message.sender === 'user' }"
          >
            <!-- Avatar -->
            <div class="avatar">
              <div 
                class="w-8 h-8 rounded-full"
                :class="getAvatarClass(message.sender)"
              >
                <div class="flex items-center justify-center h-full">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path :d="getAvatarIcon(message.sender)"></path>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Message Content -->
            <div 
              class="flex-1 max-w-xs lg:max-w-md"
              :class="{ 'text-right': message.sender === 'user' }"
            >
              <div 
                class="p-3 rounded-lg"
                :class="getMessageBubbleClass(message.sender)"
              >
                <p class="text-sm">{{ message.content }}</p>
                
                <!-- Message Metadata -->
                <div v-if="message.metadata" class="mt-2 pt-2 border-t border-base-300/50">
                  <div class="text-xs space-y-1">
                    <div v-if="message.metadata.agent" class="flex items-center gap-1">
                      <span class="text-base-content/50">Agente:</span>
                      <span class="font-medium">{{ message.metadata.agent }}</span>
                    </div>
                    <div v-if="message.metadata.executionTime" class="flex items-center gap-1">
                      <span class="text-base-content/50">Tempo:</span>
                      <span class="font-medium">{{ message.metadata.executionTime }}</span>
                    </div>
                    <div v-if="message.metadata.confidence" class="flex items-center gap-1">
                      <span class="text-base-content/50">Confiança:</span>
                      <span class="font-medium">{{ message.metadata.confidence }}%</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="text-xs text-base-content/50 mt-1">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Context Information -->
        <div v-if="conversation.hasContext" class="bg-base-100 rounded-lg p-4">
          <h4 class="font-semibold mb-2 flex items-center gap-2">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
            </svg>
            Contexto da Conversa
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-base-content/50">Usuário:</span>
              <span class="font-medium ml-1">{{ conversation.userId }}</span>
            </div>
            <div>
              <span class="text-base-content/50">Duração:</span>
              <span class="font-medium ml-1">{{ getConversationDuration() }}</span>
            </div>
            <div>
              <span class="text-base-content/50">Agentes envolvidos:</span>
              <span class="font-medium ml-1">{{ getInvolvedAgents() }}</span>
            </div>
            <div>
              <span class="text-base-content/50">Prioridade:</span>
              <span 
                class="font-medium ml-1"
                :class="getPriorityClass(conversation.priority)"
              >
                {{ getPriorityText(conversation.priority) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2 pt-4 border-t border-base-300">
          <button 
            v-if="conversation.status === 'active'"
            @click="pauseConversation"
            class="btn btn-warning btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            Pausar
          </button>
          <button 
            v-if="conversation.status === 'error'"
            @click="retryConversation"
            class="btn btn-primary btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
            </svg>
            Tentar Novamente
          </button>
          <button 
            @click="archiveConversation"
            class="btn btn-ghost btn-sm"
          >
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z"></path>
              <path fill-rule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clip-rule="evenodd"></path>
            </svg>
            Arquivar
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
        </svg>
        <p class="text-base-content/50">Selecione uma conversa para ver os detalhes</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Conversation, ConversationMessage } from '~/types/dashboard'

// Props
const props = defineProps<{
  conversation: Conversation | null
}>()

// Reactive state
const isRefreshing = ref(false)
const messages = ref<ConversationMessage[]>([])

// Mock messages data
const mockMessages: ConversationMessage[] = [
  {
    id: '1',
    conversationId: '1',
    sender: 'user',
    content: 'Quais são os principais fornecedores por volume de transações no último trimestre?',
    timestamp: new Date(Date.now() - 25 * 60 * 1000),
    metadata: null
  },
  {
    id: '2',
    conversationId: '1',
    sender: 'agent',
    content: 'Vou analisar os dados fiscais do último trimestre para identificar os principais fornecedores por volume de transações. Aguarde um momento...',
    timestamp: new Date(Date.now() - 24 * 60 * 1000),
    metadata: {
      agent: 'Master Agent',
      executionTime: '2.3s',
      confidence: 95
    }
  },
  {
    id: '3',
    conversationId: '1',
    sender: 'agent',
    content: 'Baseado na análise dos dados fiscais de outubro a dezembro de 2024, identifiquei os top 5 fornecedores:\n\n1. Fornecedor ABC Ltda - R$ 2.847.650 (23% do volume)\n2. Distribuidora XYZ S.A. - R$ 1.923.400 (16% do volume)\n3. Comercial DEF - R$ 1.456.200 (12% do volume)\n4. Indústria GHI - R$ 1.234.800 (10% do volume)\n5. Serviços JKL - R$ 987.300 (8% do volume)',
    timestamp: new Date(Date.now() - 20 * 60 * 1000),
    metadata: {
      agent: 'SQL Agent',
      executionTime: '15.7s',
      confidence: 98
    }
  },
  {
    id: '4',
    conversationId: '1',
    sender: 'user',
    content: 'Ótimo! Pode me mostrar a evolução mensal desses fornecedores?',
    timestamp: new Date(Date.now() - 18 * 60 * 1000),
    metadata: null
  },
  {
    id: '5',
    conversationId: '1',
    sender: 'agent',
    content: 'Claro! Vou gerar um gráfico mostrando a evolução mensal dos top 5 fornecedores. Isso me ajudará a identificar tendências e sazonalidades.',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    metadata: {
      agent: 'Report Agent',
      executionTime: '8.2s',
      confidence: 92
    }
  }
]

// Watch for conversation changes
watch(() => props.conversation, (newConversation) => {
  if (newConversation) {
    loadMessages(newConversation.id)
  }
}, { immediate: true })

// Methods
const loadMessages = async (conversationId: string) => {
  // In a real implementation, this would fetch messages from API
  // For now, use mock data
  messages.value = mockMessages.filter(msg => msg.conversationId === conversationId)
}

const refreshConversation = async () => {
  if (!props.conversation) return
  
  isRefreshing.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    await loadMessages(props.conversation.id)
  } finally {
    isRefreshing.value = false
  }
}

const exportConversation = () => {
  // Implementation for exporting conversation
  console.log('Exporting conversation:', props.conversation?.id)
}

const pauseConversation = () => {
  // Implementation for pausing conversation
  console.log('Pausing conversation:', props.conversation?.id)
}

const retryConversation = () => {
  // Implementation for retrying conversation
  console.log('Retrying conversation:', props.conversation?.id)
}

const archiveConversation = () => {
  // Implementation for archiving conversation
  console.log('Archiving conversation:', props.conversation?.id)
}

const getConversationDuration = () => {
  if (!props.conversation) return 'N/A'
  
  const start = props.conversation.startTime
  const end = props.conversation.lastActivity
  const diff = end.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

const getInvolvedAgents = () => {
  const agents = new Set(messages.value
    .filter(msg => msg.metadata?.agent)
    .map(msg => msg.metadata!.agent))
  
  return Array.from(agents).join(', ') || props.conversation?.primaryAgent || 'N/A'
}

// Helper functions
const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'active': return 'badge-primary'
    case 'completed': return 'badge-success'
    case 'error': return 'badge-error'
    default: return 'badge-ghost'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return 'Ativa'
    case 'completed': return 'Concluída'
    case 'error': return 'Erro'
    default: return 'Desconhecido'
  }
}

const getAvatarClass = (sender: string) => {
  return sender === 'user' ? 'bg-primary text-primary-content' : 'bg-secondary text-secondary-content'
}

const getAvatarIcon = (sender: string) => {
  return sender === 'user' 
    ? 'M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z'
    : 'M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z'
}

const getMessageBubbleClass = (sender: string) => {
  return sender === 'user' 
    ? 'bg-primary text-primary-content' 
    : 'bg-base-100 border border-base-300'
}

const getPriorityClass = (priority: string) => {
  switch (priority) {
    case 'high': return 'text-error'
    case 'medium': return 'text-warning'
    case 'low': return 'text-success'
    default: return 'text-base-content'
  }
}

const getPriorityText = (priority: string) => {
  switch (priority) {
    case 'high': return 'Alta'
    case 'medium': return 'Média'
    case 'low': return 'Baixa'
    default: return 'Normal'
  }
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('pt-BR', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>