<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="hero bg-gradient-to-r from-primary to-secondary text-primary-content rounded-lg">
      <div class="hero-content text-center py-8">
        <div class="max-w-md">
          <h1 class="text-4xl font-bold">Painel Executivo</h1>
          <p class="py-4 text-lg">Insights fiscais com IA para tomada de decisões estratégicas</p>
        </div>
      </div>
    </div>

    <!-- Quick Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-primary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"></path>
          </svg>
        </div>
        <div class="stat-title">Total de Notas</div>
        <div class="stat-value text-primary">--</div>
        <div class="stat-desc">Carregando...</div>
      </div>

      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-secondary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Valor Total</div>
        <div class="stat-value text-secondary">R$ --</div>
        <div class="stat-desc">Carregando...</div>
      </div>

      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-accent">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <div class="stat-title">Fornecedores Ativos</div>
        <div class="stat-value text-accent">--</div>
        <div class="stat-desc">Carregando...</div>
      </div>

      <div class="stat bg-base-200 rounded-lg shadow">
        <div class="stat-figure text-warning">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Eficiência Fiscal</div>
        <div class="stat-value text-warning">--%</div>
        <div class="stat-desc">Carregando...</div>
      </div>
    </div>

    <!-- Natural Language Query Section -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h2 class="card-title text-2xl mb-4">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
          </svg>
          Consulte Seus Dados Fiscais
        </h2>
        <QueryInput />
      </div>
    </div>

    <!-- Recent Activity and Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Activity -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title">Atividade Recente</h3>
          <div class="space-y-3">
            <div class="flex items-center space-x-3 p-3 bg-base-100 rounded-lg">
              <div class="w-2 h-2 bg-success rounded-full"></div>
              <div class="flex-1">
                <p class="text-sm font-medium">Processamento XML Concluído</p>
                <p class="text-xs text-base-content/70">5 arquivos NF-e processados com sucesso</p>
              </div>
              <div class="text-xs text-base-content/50">há 2 min</div>
            </div>
            <div class="flex items-center space-x-3 p-3 bg-base-100 rounded-lg">
              <div class="w-2 h-2 bg-info rounded-full"></div>
              <div class="flex-1">
                <p class="text-sm font-medium">Relatório Gerado</p>
                <p class="text-xs text-base-content/70">Análise mensal de fornecedores pronta</p>
              </div>
              <div class="text-xs text-base-content/50">há 15 min</div>
            </div>
            <div class="flex items-center space-x-3 p-3 bg-base-100 rounded-lg">
              <div class="w-2 h-2 bg-warning rounded-full"></div>
              <div class="flex-1">
                <p class="text-sm font-medium">Categorização IA</p>
                <p class="text-xs text-base-content/70">Novas categorias de produtos detectadas</p>
              </div>
              <div class="text-xs text-base-content/50">há 1 hora</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Placeholder -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title">Visão Geral Fiscal</h3>
          <div class="h-64 bg-base-100 rounded-lg flex items-center justify-center">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
              </svg>
              <p class="text-base-content/50">Visualização de gráficos aparecerá aqui</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Ações Rápidas</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <NuxtLink to="/upload" class="btn btn-primary btn-lg">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
            </svg>
            Enviar Arquivos XML
          </NuxtLink>
          <NuxtLink to="/reports" class="btn btn-secondary btn-lg">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>
            </svg>
            Gerar Relatório
          </NuxtLink>
          <NuxtLink to="/analytics" class="btn btn-accent btn-lg">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
            </svg>
            Ver Análises
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Dashboard page setup
definePageMeta({
  layout: 'default'
})
</script>