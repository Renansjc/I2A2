import { ref, computed } from "vue";
import type { DashboardStats, RecentActivity } from "~/types/dashboard";

export const useDashboard = () => {
  // Reactive state
  const stats = ref<DashboardStats>({
    totalInvoices: 0,
    totalValue: 0,
    activeSuppliers: 0,
    fiscalEfficiency: 0,
  });

  const recentActivities = ref<RecentActivity[]>([]);
  const isLoading = ref(true);
  const error = ref<string | null>(null);

  // Mock data for development
  const mockStats: DashboardStats = {
    totalInvoices: 1247,
    totalValue: 2847650.0,
    activeSuppliers: 89,
    fiscalEfficiency: 94.2,
  };

  const mockActivities: RecentActivity[] = [
    {
      id: "1",
      type: "success",
      title: "Processamento XML Concluído",
      description: "5 arquivos NF-e processados com sucesso",
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
    },
    {
      id: "2",
      type: "info",
      title: "Relatório Gerado",
      description: "Análise mensal de fornecedores pronta",
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
    },
    {
      id: "3",
      type: "warning",
      title: "Categorização IA",
      description: "Novas categorias de produtos detectadas",
      timestamp: new Date(Date.now() - 60 * 60 * 1000),
    },
    {
      id: "4",
      type: "success",
      title: "Consulta SQL Executada",
      description: "Análise de tendências de fornecedores concluída",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    },
    {
      id: "5",
      type: "info",
      title: "Backup Automático",
      description: "Backup diário dos dados fiscais realizado",
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
    },
  ];

  // Computed properties
  const formattedTotalValue = computed(() => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 0,
    }).format(stats.value.totalValue);
  });

  const formattedTotalInvoices = computed(() => {
    return stats.value.totalInvoices.toLocaleString("pt-BR");
  });

  const formattedActiveSuppliers = computed(() => {
    return stats.value.activeSuppliers.toLocaleString("pt-BR");
  });

  const formattedFiscalEfficiency = computed(() => {
    return `${stats.value.fiscalEfficiency.toFixed(1)}%`;
  });

  // Methods
  const loadDashboardData = async () => {
    try {
      isLoading.value = true;
      error.value = null;

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // In a real implementation, this would be an API call
      // const response = await $fetch('/api/dashboard/stats')
      // stats.value = response.stats
      // recentActivities.value = response.activities

      // For now, use mock data
      stats.value = { ...mockStats };
      recentActivities.value = [...mockActivities];
    } catch (err) {
      error.value = "Erro ao carregar dados do dashboard";
      console.error("Dashboard data loading error:", err);
    } finally {
      isLoading.value = false;
    }
  };

  const refreshStats = async () => {
    // Simulate real-time updates
    stats.value.totalInvoices += Math.floor(Math.random() * 5);
    stats.value.totalValue += Math.random() * 50000;
    stats.value.fiscalEfficiency = Math.max(
      85,
      Math.min(100, stats.value.fiscalEfficiency + (Math.random() - 0.5) * 2)
    );
  };

  const addActivity = (activity: Omit<RecentActivity, "id" | "timestamp">) => {
    const newActivity: RecentActivity = {
      ...activity,
      id: Date.now().toString(),
      timestamp: new Date(),
    };

    recentActivities.value.unshift(newActivity);

    // Keep only the last 10 activities
    if (recentActivities.value.length > 10) {
      recentActivities.value = recentActivities.value.slice(0, 10);
    }
  };

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

  return {
    // State
    stats,
    recentActivities,
    isLoading,
    error,

    // Computed
    formattedTotalValue,
    formattedTotalInvoices,
    formattedActiveSuppliers,
    formattedFiscalEfficiency,

    // Methods
    loadDashboardData,
    refreshStats,
    addActivity,
    formatActivityTime,
    getActivityIcon,
    getActivityColorClass,
  };
};
