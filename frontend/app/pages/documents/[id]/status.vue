<template>
  <div class="space-y-6">
    <!-- Breadcrumb Navigation -->
    <div class="breadcrumbs text-sm">
      <ul>
        <li><NuxtLink to="/">Início</NuxtLink></li>
        <li><NuxtLink to="/documents">Documentos</NuxtLink></li>
        <li><NuxtLink :to="`/documents/${documentId}`">{{ documentId.slice(0, 8) }}...</NuxtLink></li>
        <li>Status</li>
      </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Status de Processamento</h1>
        <p class="text-base-content/70">Acompanhe o progresso detalhado dos agentes IA</p>
      </div>
      
      <div class="flex items-center space-x-2">
        <button 
          class="btn btn-outline"
          @click="navigateTo(`/documents/${documentId}`)"
        >
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"></path>
          </svg>
          Voltar aos Detalhes
        </button>
      </div>
    </div>

    <!-- Processing Status Component -->
    <ProcessingStatus :document-id="documentId" />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const documentId = route.params.id as string

definePageMeta({
  layout: 'default'
})
</script>