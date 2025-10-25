<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="hero bg-gradient-to-r from-primary to-secondary text-primary-content rounded-lg">
      <div class="hero-content py-6">
        <div class="max-w-4xl w-full">
          <div class="flex items-center justify-between">
            <div class="text-center lg:text-left">
              <h1 class="text-3xl font-bold">Monitoramento de Agentes</h1>
              <p class="py-2 text-lg">Acompanhe workflows, status e conversas em tempo real</p>
            </div>
            <div class="hidden lg:flex items-center gap-4">
              <button 
                @click="refreshAll" 
                class="btn btn-outline btn-primary-content"
                :disabled="isRefreshing"
              >
                <svg 
                  class="w-5 h-5" 
                  :class="{ 'animate-spin': isRefreshing }"
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                </svg>
                Atualizar Tudo
              </button>
              <div class="text-sm opacity-75">
                Última atualização: {{ lastUpdateTime }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tabs tabs-boxed bg-base-200 p-1">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        class="tab"
        :class="{ 'tab-active': activeTab === tab.id }"
      >
        <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path :d="tab.icon"></path>
        </svg>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Workflow Monitoring Tab -->
      <div v-if="activeTab === 'workflows'" class="space-y-6">
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <WorkflowMonitor />
          <WorkflowDetails :selected-workflow="selectedWorkflow" />
        </div>
        <WorkflowHistory />
      </div>

      <!-- Agent Status Tab -->
      <div v-if="activeTab === 'agents'" class="space-y-6">
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <AgentStatus />
          <AgentPerformanceMetrics />
        </div>
        <AgentInteractionLogs />
      </div>

      <!-- Conversation History Tab -->
      <div v-if="activeTab === 'conversations'" class="space-y-6">
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <ConversationList @select-conversation="selectConversation" />
          <ConversationDetails 
            :conversation="selectedConversation" 
            class="xl:col-span-2" 
          />
        </div>
        <ContextManagement />
      </div>

      <!-- System Health Tab -->
      <div v-if="activeTab === 'system'" class="space-y-6">
        <SystemHealthOverview />
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemMetrics />
          <ErrorAnalysis />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Workflow, Conversation } from '~/types/dashboard'

// Page metadata
definePageMeta({
  layout: 'default'
})

// Reactive state
const activeTab = ref('workflows')
const selectedWorkflow = ref<Workflow | null>(null)
const selectedConversation = ref<Conversation | null>(null)
const isRefreshing = ref(false)
const lastUpdateTime = ref(new Date().toLocaleTimeString('pt-BR'))

// Tab configuration
const tabs = [
  {
    id: 'workflows',
    label: 'Workflows',
    icon: 'M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z'
  },
  {
    id: 'agents',
    label: 'Agentes',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
  },
  {
    id: 'conversations',
    label: 'Conversas',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
  },
  {
    id: 'system',
    label: 'Sistema',
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z'
  }
]

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Methods
const refreshAll = async () => {
  isRefreshing.value = true
  try {
    // Simulate refresh delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    lastUpdateTime.value = new Date().toLocaleTimeString('pt-BR')
  } finally {
    isRefreshing.value = false
  }
}

const selectConversation = (conversation: Conversation) => {
  selectedConversation.value = conversation
}

// Lifecycle
onMounted(() => {
  // Set up auto-refresh every 30 seconds
  refreshInterval = setInterval(() => {
    if (!isRefreshing.value) {
      lastUpdateTime.value = new Date().toLocaleTimeString('pt-BR')
    }
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>