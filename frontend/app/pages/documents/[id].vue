<template>
  <div class="space-y-6">
    <!-- Breadcrumb Navigation -->
    <div class="breadcrumbs text-sm">
      <ul>
        <li><NuxtLink to="/">Início</NuxtLink></li>
        <li><NuxtLink to="/documents">Documentos</NuxtLink></li>
        <li>{{ documentId.slice(0, 8) }}...</li>
      </ul>
    </div>

    <!-- Document Details Component -->
    <DocumentDetails 
      :document-id="documentId"
      @document-deleted="handleDocumentDeleted"
      @processing-retried="handleProcessingRetried"
    />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const documentId = route.params.id as string

definePageMeta({
  layout: 'default'
})

// Event handlers
const handleDocumentDeleted = () => {
  navigateTo('/documents')
}

const handleProcessingRetried = () => {
  // Document details will auto-refresh
  console.log('Processing retried for document:', documentId)
}
</script>