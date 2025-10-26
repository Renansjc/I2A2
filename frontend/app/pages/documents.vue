<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Documentos Fiscais</h1>
        <p class="text-base-content/70">Gerencie e acompanhe seus documentos XML processados</p>
      </div>
      
      <div class="flex items-center space-x-2">
        <button 
          class="btn btn-primary"
          @click="navigateTo('/upload')"
        >
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
          </svg>
          Novo Upload
        </button>
      </div>
    </div>

    <!-- Document List Component -->
    <DocumentList 
      @document-selected="handleDocumentSelected"
      @upload-requested="navigateTo('/upload')"
    />
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'default'
})

// Event handlers
const handleDocumentSelected = (documentId: string) => {
  navigateTo(`/documents/${documentId}`)
}
</script>