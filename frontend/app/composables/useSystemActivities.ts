import { ref, computed } from "vue";
import type { RecentActivity } from "~/types/dashboard";
import { useApi } from "./useApi";

export interface SystemStatus {
  system_health: {
    overall_health: number;
    status: 'healthy' | 'warning' | 'critical';
    uptime_days: number;
    last_restart: string;
  };
  processing_stats: {
    total_documents: number;
    completed_documents: number;
    error_documents: number;
    success_rate: number;
    documents_today: number;
  };
  api_status: {
    dimensional_apis: string;
    search_apis: string;
    upload_api: string;
    export_api: string;
  };
  generated_at: string;
}

export const useSystemActivities = () => {
  // Reactive state
  const activities = ref<RecentActivity[]>([]);
  const systemStatus = ref<SystemStatus | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Load recent activities
  const loadActivities = async (limit: number = 10, hours: number = 24) => {
    try {
      isLoading.value = true;
      error.value = null;

      const { apiCall } = useApi()
      const response = await apiCall('/api/v1/api/activity/recent', {
        query: { limit, hours }
      });

      if (response && response.activities) {
        activities.value = response.activities.map((activity: any) => ({
          id: activity.id,
          type: activity.type as RecentActivity['type'],
          title: activity.title,
          description: activity.description,
          timestamp: new Date(activity.timestamp)
        }));
      }
    } catch (err: any) {
      console.error('Error loading activities:', err);
      error.value = err.data?.mensagem || 'Erro ao carregar atividades';
    } finally {
      isLoading.value = false;
    }
  };

  // Load system status
  const loadSystemStatus = async () => {
    try {
      const { apiCall } = useApi()
      const response = await apiCall('/api/v1/api/activity/system-status');
      systemStatus.value = response as SystemStatus;
    } catch (err: any) {
      console.error('Error loading system status:', err);
      error.value = err.data?.mensagem || 'Erro ao carregar status do sistema';
    }
  };

  // Add new activity
  const addActivity = (activity: Omit<RecentActivity, "id" | "timestamp">) => {
    const newActivity: RecentActivity = {
      ...activity,
      id: Date.now().toString(),
      timestamp: new Date(),
    };

    activities.value.unshift(newActivity);

    // Keep only the last 20 activities
    if (activities.value.length > 20) {
      activities.value = activities.value.slice(0, 20);
    }
  };

  // Utility functions
  const formatActivityTime = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return "Agora mesmo";
    if (minutes < 60) return `há ${minutes}m`;
    if (minutes < 1440) return `há ${Math.floor(minutes / 60)}h`;
    return timestamp.toLocaleDateString("pt-BR");
  };

  const getActivityIcon = (type: RecentActivity["type"]) => {
    switch (type) {
      case "success":
        return "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z";
      case "info":
        return "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z";
      case "warning":
        return "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z";
      case "error":
        return "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z";
      default:
        return "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z";
    }
  };

  const getActivityColorClass = (type: RecentActivity["type"]) => {
    switch (type) {
      case "success":
        return "bg-success";
      case "info":
        return "bg-info";
      case "warning":
        return "bg-warning";
      case "error":
        return "bg-error";
      default:
        return "bg-base-300";
    }
  };

  // Computed properties
  const recentActivities = computed(() => activities.value.slice(0, 10));
  
  const systemHealthStatus = computed(() => {
    if (!systemStatus.value) return 'unknown';
    return systemStatus.value.system_health.status;
  });

  const systemHealthScore = computed(() => {
    if (!systemStatus.value) return 0;
    return systemStatus.value.system_health.overall_health;
  });

  const processingSuccessRate = computed(() => {
    if (!systemStatus.value) return 0;
    return systemStatus.value.processing_stats.success_rate;
  });

  const documentsToday = computed(() => {
    if (!systemStatus.value) return 0;
    return systemStatus.value.processing_stats.documents_today;
  });

  return {
    // State
    activities,
    systemStatus,
    isLoading,
    error,

    // Methods
    loadActivities,
    loadSystemStatus,
    addActivity,

    // Utilities
    formatActivityTime,
    getActivityIcon,
    getActivityColorClass,

    // Computed
    recentActivities,
    systemHealthStatus,
    systemHealthScore,
    processingSuccessRate,
    documentsToday
  };
};