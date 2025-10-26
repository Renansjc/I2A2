<template>
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-title">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
          Atividade Recente
        </h3>
        <div class="badge badge-primary">{{ activities.length }} Eventos</div>
      </div>

      <!-- Activities List -->
      <div class="space-y-3 max-h-96 overflow-y-auto">
        <div
          v-for="activity in activities"
          :key="activity.id"
          class="flex items-center space-x-3 p-3 bg-base-100 rounded-lg hover:bg-base-300 transition-colors"
        >
          <div 
            class="w-3 h-3 rounded-full flex-shrink-0"
            :class="getActivityColorClass(activity.type)"
          ></div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">{{ activity.title }}</p>
            <p class="text-xs text-base-content/70 truncate">{{ activity.description }}</p>
          </div>
          <div class="text-xs text-base-content/50 flex-shrink-0">
            {{ formatActivityTime(activity.timestamp) }}
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="activities.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
          <p class="text-base-content/50">Nenhuma atividade recente</p>
        </div>
      </div>

      <!-- View All Button -->
      <div v-if="activities.length > 0" class="mt-4 pt-4 border-t border-base-300">
        <NuxtLink to="/activity" class="btn btn-sm btn-outline w-full">
          Ver Todas as Atividades
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RecentActivity } from '~/types/dashboard'

interface Props {
  activities: RecentActivity[]
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxItems: 10
})

// Use system activities composable for utility functions
const { formatActivityTime, getActivityColorClass } = useSystemActivities()

// Computed property to limit displayed activities
const displayedActivities = computed(() => {
  return props.activities.slice(0, props.maxItems)
})

// Use displayed activities in template
const activities = displayedActivities
</script>