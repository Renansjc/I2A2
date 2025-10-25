<template>
  <div class="space-y-6">
    <!-- Report History Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold">Histórico de Relatórios</h2>
        <p class="text-base-content/70">Acompanhe todos os relatórios gerados e seus status</p>
      </div>
      <div class="flex space-x-2">
        <button class="btn btn-outline btn-sm" @click="refreshHistory">
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
          </svg>
          Atualizar
        </button>
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-outline btn-sm">
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            Exportar
          </div>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
            <li><a @click="exportHistory('csv')">Exportar como CSV</a></li>
            <li><a @click="exportHistory('xlsx')">Exportar como Excel</a></li>
            <li><a @click="exportHistory('pdf')">Exportar como PDF</a></li>
          </ul>
        </div>
      </div>
    </div>

    <!-- History Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-primary">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Total</div>
        <div class="stat-value text-primary">{{ totalReports }}</div>
        <div class="stat-desc">Relatórios gerados</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-success">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Concluídos</div>
        <div class="stat-value text-success">{{ completedReports.length }}</div>
        <div class="stat-desc">{{ completionRate }}% taxa de sucesso</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-warning">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Processando</div>
        <div class="stat-value text-warning">{{ processingReports.length }}</div>
        <div class="stat-desc">Em andamento</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-error">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Falhas</div>
        <div class="stat-value text-error">{{ failedReports.length }}</div>
        <div class="stat-desc">Requer atenção</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg">
        <div class="stat-figure text-info">
          <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="stat-title">Downloads</div>
        <div class="stat-value text-info">{{ totalDownloads }}</div>
        <div class="stat-desc">Total de downloads</div>
      </div>
    </div>

    <!-- History Filters -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex flex-wrap gap-4 items-center">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Buscar</span>
            </label>
            <input 
              v-model="searchTerm"
              type="text" 
              placeholder="Nome do relatório..."
              class="input input-bordered input-sm w-64"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Status</span>
            </label>
            <select v-model="filterStatus" class="select select-bordered select-sm">
              <option value="">Todos os status</option>
              <option value="completed">Concluído</option>
              <option value="processing">Processando</option>
              <option value="failed">Falhou</option>
              <option value="pending">Pendente</option>
              <option value="cancelled">Cancelado</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Categoria</span>
            </label>
            <select v-model="filterCategory" class="select select-bordered select-sm">
              <option value="">Todas as categorias</option>
              <option v-for="category in categories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Período</span>
            </label>
            <select v-model="filterPeriod" class="select select-bordered select-sm">
              <option value="">Todos os períodos</option>
              <option value="today">Hoje</option>
              <option value="week">Última semana</option>
              <option value="month">Último mês</option>
              <option value="quarter">Último trimestre</option>
              <option value="year">Último ano</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">&nbsp;</span>
            </label>
            <button class="btn btn-ghost btn-sm" @click="clearFilters">
              Limpar Filtros
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- History Timeline View Toggle -->
    <div class="flex justify-between items-center">
      <div class="tabs tabs-boxed">
        <a 
          class="tab"
          :class="{ 'tab-active': viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 16a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
          </svg>
          Lista
        </a>
        <a 
          class="tab"
          :class="{ 'tab-active': viewMode === 'timeline' }"
          @click="viewMode = 'timeline'"
        >
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
          </svg>
          Timeline
        </a>
        <a 
          class="tab"
          :class="{ 'tab-active': viewMode === 'calendar' }"
          @click="viewMode = 'calendar'"
        >
          <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"></path>
          </svg>
          Calendário
        </a>
      </div>
      
      <div class="flex items-center space-x-2">
        <span class="text-sm text-base-content/70">Ordenar por:</span>
        <select v-model="sortBy" class="select select-bordered select-sm">
          <option value="generatedAt">Data de Geração</option>
          <option value="completedAt">Data de Conclusão</option>
          <option value="name">Nome</option>
          <option value="type">Categoria</option>
          <option value="executionTime">Tempo de Execução</option>
          <option value="downloadCount">Downloads</option>
        </select>
        <button 
          class="btn btn-ghost btn-sm"
          @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
        >
          <svg 
            class="w-4 h-4" 
            :class="{ 'rotate-180': sortOrder === 'desc' }"
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- List View -->
    <div v-if="viewMode === 'list'" class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <div class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>
                  <label>
                    <input 
                      type="checkbox" 
                      class="checkbox checkbox-sm"
                      :checked="selectedReports.length === paginatedReports.length && paginatedReports.length > 0"
                      @change="toggleSelectAll"
                    />
                  </label>
                </th>
                <th>Relatório</th>
                <th>Status</th>
                <th>Gerado</th>
                <th>Concluído</th>
                <th>Tempo</th>
                <th>Downloads</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in paginatedReports" :key="report.id">
                <td>
                  <label>
                    <input 
                      type="checkbox" 
                      class="checkbox checkbox-sm"
                      :checked="selectedReports.includes(report.id)"
                      @change="toggleReportSelection(report.id)"
                    />
                  </label>
                </td>
                <td>
                  <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                      <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>
                      </svg>
                    </div>
                    <div>
                      <div class="font-bold">{{ report.name }}</div>
                      <div class="text-sm text-base-content/70">{{ report.description }}</div>
                      <div class="flex space-x-2 mt-1">
                        <div class="badge badge-outline badge-sm">{{ report.type }}</div>
                        <div v-for="format in report.formats" :key="format" class="badge badge-ghost badge-sm">
                          {{ format.toUpperCase() }}
                        </div>
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="flex flex-col space-y-1">
                    <div class="badge" :class="getStatusColor(report.status)">
                      {{ getStatusText(report.status) }}
                    </div>
                    <div v-if="report.status === 'processing' && report.progress !== undefined" class="w-full">
                      <div class="text-xs text-base-content/70 mb-1">{{ report.progress }}%</div>
                      <progress class="progress progress-primary w-full h-2" :value="report.progress" max="100"></progress>
                    </div>
                    <div v-if="report.error" class="text-xs text-error">
                      {{ report.error }}
                    </div>
                  </div>
                </td>
                <td>
                  <div class="text-sm">
                    {{ formatDate(report.generatedAt) }}
                  </div>
                </td>
                <td>
                  <div class="text-sm">
                    {{ report.completedAt ? formatDate(report.completedAt) : '-' }}
                  </div>
                </td>
                <td>
                  <div class="text-sm">
                    {{ report.executionTime ? formatExecutionTime(report.executionTime) : '-' }}
                  </div>
                </td>
                <td>
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium">{{ report.downloadCount }}</span>
                    <div v-if="report.lastDownloaded" class="text-xs text-base-content/70">
                      Último: {{ formatDate(report.lastDownloaded) }}
                    </div>
                  </div>
                </td>
                <td>
                  <div class="dropdown dropdown-end">
                    <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                      </svg>
                    </div>
                    <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                      <li v-if="report.status === 'completed'">
                        <a @click="viewReport(report)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                            <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                          </svg>
                          Visualizar
                        </a>
                      </li>
                      <li v-if="report.status === 'completed'">
                        <a @click="downloadReport(report)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                          </svg>
                          Baixar
                        </a>
                      </li>
                      <li>
                        <a @click="duplicateReport(report)">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M7 9a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H9a2 2 0 01-2-2V9z"></path>
                            <path d="M5 3a2 2 0 00-2 2v6a2 2 0 002 2V5h8a2 2 0 00-2-2H5z"></path>
                          </svg>
                          Duplicar
                        </a>
                      </li>
                      <li v-if="report.status === 'processing' || report.status === 'pending'">
                        <a @click="cancelReport(report)" class="text-warning">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                          </svg>
                          Cancelar
                        </a>
                      </li>
                      <li v-if="report.status === 'failed'">
                        <a @click="retryReport(report)" class="text-info">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                          </svg>
                          Tentar Novamente
                        </a>
                      </li>
                      <li>
                        <a @click="deleteReport(report)" class="text-error">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zM12 7a1 1 0 112 0v4a1 1 0 11-2 0V7z" clip-rule="evenodd"></path>
                          </svg>
                          Excluir
                        </a>
                      </li>
                    </ul>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="flex justify-center mt-6">
          <div class="join">
            <button 
              class="join-item btn btn-sm" 
              :disabled="currentPage === 1" 
              @click="currentPage--"
            >
              «
            </button>
            <button class="join-item btn btn-sm">
              Página {{ currentPage }} de {{ totalPages }}
            </button>
            <button 
              class="join-item btn btn-sm" 
              :disabled="currentPage === totalPages" 
              @click="currentPage++"
            >
              »
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Timeline View -->
    <div v-if="viewMode === 'timeline'" class="space-y-4">
      <div v-for="(group, date) in groupedByDate" :key="date" class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h3 class="card-title text-lg">{{ formatDateGroup(date) }}</h3>
          <div class="space-y-3">
            <div 
              v-for="report in group" 
              :key="report.id"
              class="flex items-center space-x-4 p-3 bg-base-200 rounded-lg"
            >
              <div class="w-2 h-2 rounded-full" :class="getStatusDotColor(report.status)"></div>
              <div class="flex-1">
                <div class="font-semibold">{{ report.name }}</div>
                <div class="text-sm text-base-content/70">{{ report.description }}</div>
                <div class="flex items-center space-x-2 mt-1">
                  <div class="badge badge-outline badge-sm">{{ report.type }}</div>
                  <div class="badge" :class="getStatusColor(report.status)">
                    {{ getStatusText(report.status) }}
                  </div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm font-medium">{{ formatTime(report.generatedAt) }}</div>
                <div v-if="report.executionTime" class="text-xs text-base-content/70">
                  {{ formatExecutionTime(report.executionTime) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Calendar View -->
    <div v-if="viewMode === 'calendar'" class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <div class="text-center text-base-content/70 py-12">
          <svg class="w-16 h-16 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"></path>
          </svg>
          <h3 class="text-lg font-semibold mb-2">Visualização de Calendário</h3>
          <p>A visualização de calendário será implementada em uma próxima versão</p>
        </div>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="selectedReports.length > 0" class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex justify-between items-center">
          <div>
            <h4 class="font-semibold">{{ selectedReports.length }} relatório(s) selecionado(s)</h4>
            <p class="text-sm text-base-content/70">Ações em lote disponíveis</p>
          </div>
          <div class="flex space-x-2">
            <button class="btn btn-sm btn-outline" @click="clearSelection">
              Limpar Seleção
            </button>
            <button class="btn btn-sm btn-warning" @click="bulkCancel">
              Cancelar Selecionados
            </button>
            <button class="btn btn-sm btn-error" @click="bulkDelete">
              Excluir Selecionados
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useReports, type ReportHistory } from '~/composables/useReports'

// Composables
const { 
  reports, 
  completedReports, 
  processingReports, 
  failedReports,
  formatExecutionTime,
  loadReports,
  deleteReport: deleteReportFromStore,
  cancelReport: cancelReportFromStore,
  duplicateReport: duplicateReportFromStore
} = useReports()

// Reactive state
const searchTerm = ref('')
const filterStatus = ref('')
const filterCategory = ref('')
const filterPeriod = ref('')
const sortBy = ref('generatedAt')
const sortOrder = ref<'asc' | 'desc'>('desc')
const viewMode = ref<'list' | 'timeline' | 'calendar'>('list')
const currentPage = ref(1)
const itemsPerPage = 10
const selectedReports = ref<string[]>([])

// Computed properties
const totalReports = computed(() => reports.value.length)

const totalDownloads = computed(() => {
  return reports.value.reduce((total, report) => total + report.downloadCount, 0)
})

const completionRate = computed(() => {
  if (totalReports.value === 0) return 0
  return Math.round((completedReports.value.length / totalReports.value) * 100)
})

const categories = computed(() => {
  const cats = new Set(reports.value.map(report => report.type))
  return Array.from(cats).sort()
})

const filteredReports = computed(() => {
  let filtered = [...reports.value]
  
  // Search filter
  if (searchTerm.value) {
    filtered = filtered.filter(report =>
      report.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      report.description.toLowerCase().includes(searchTerm.value.toLowerCase())
    )
  }
  
  // Status filter
  if (filterStatus.value) {
    filtered = filtered.filter(report => report.status === filterStatus.value)
  }
  
  // Category filter
  if (filterCategory.value) {
    filtered = filtered.filter(report => report.type === filterCategory.value)
  }
  
  // Period filter
  if (filterPeriod.value) {
    const now = new Date()
    filtered = filtered.filter(report => {
      const reportDate = new Date(report.generatedAt)
      switch (filterPeriod.value) {
        case 'today':
          return reportDate.toDateString() === now.toDateString()
        case 'week':
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          return reportDate >= weekAgo
        case 'month':
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          return reportDate >= monthAgo
        case 'quarter':
          const quarterAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
          return reportDate >= quarterAgo
        case 'year':
          const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
          return reportDate >= yearAgo
        default:
          return true
      }
    })
  }
  
  // Sort
  filtered.sort((a, b) => {
    let aValue: any = a[sortBy.value as keyof ReportHistory]
    let bValue: any = b[sortBy.value as keyof ReportHistory]
    
    if (sortBy.value === 'generatedAt' || sortBy.value === 'completedAt') {
      aValue = aValue ? new Date(aValue).getTime() : 0
      bValue = bValue ? new Date(bValue).getTime() : 0
    }
    
    if (sortOrder.value === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })
  
  return filtered
})

const paginatedReports = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredReports.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredReports.value.length / itemsPerPage)
})

const groupedByDate = computed(() => {
  const groups: Record<string, ReportHistory[]> = {}
  
  filteredReports.value.forEach(report => {
    const date = new Date(report.generatedAt).toDateString()
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(report)
  })
  
  return groups
})

// Watch for page changes when filters change
watch([searchTerm, filterStatus, filterCategory, filterPeriod], () => {
  currentPage.value = 1
})

// Methods
const formatDate = (date: Date): string => {
  return new Date(date).toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (date: Date): string => {
  return new Date(date).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDateGroup = (dateString: string): string => {
  const date = new Date(dateString)
  const today = new Date()
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  
  if (date.toDateString() === today.toDateString()) {
    return 'Hoje'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Ontem'
  } else {
    return date.toLocaleDateString('pt-BR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'completed': 'Concluído',
    'processing': 'Processando',
    'failed': 'Falhou',
    'pending': 'Pendente',
    'cancelled': 'Cancelado'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    'completed': 'badge-success',
    'processing': 'badge-warning',
    'failed': 'badge-error',
    'pending': 'badge-info',
    'cancelled': 'badge-ghost'
  }
  return colorMap[status] || 'badge-ghost'
}

const getStatusDotColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    'completed': 'bg-success',
    'processing': 'bg-warning',
    'failed': 'bg-error',
    'pending': 'bg-info',
    'cancelled': 'bg-base-content/30'
  }
  return colorMap[status] || 'bg-base-content/30'
}

const clearFilters = () => {
  searchTerm.value = ''
  filterStatus.value = ''
  filterCategory.value = ''
  filterPeriod.value = ''
}

const refreshHistory = async () => {
  await loadReports()
}

const toggleSelectAll = () => {
  if (selectedReports.value.length === paginatedReports.value.length) {
    selectedReports.value = []
  } else {
    selectedReports.value = paginatedReports.value.map(report => report.id)
  }
}

const toggleReportSelection = (reportId: string) => {
  const index = selectedReports.value.indexOf(reportId)
  if (index > -1) {
    selectedReports.value.splice(index, 1)
  } else {
    selectedReports.value.push(reportId)
  }
}

const clearSelection = () => {
  selectedReports.value = []
}

const viewReport = (report: ReportHistory) => {
  // Emit event or navigate to report view
  console.log('Viewing report:', report.id)
}

const downloadReport = (report: ReportHistory) => {
  // Handle download logic
  console.log('Downloading report:', report.id)
}

const duplicateReport = async (report: ReportHistory) => {
  try {
    await duplicateReportFromStore(report.id)
    alert('Relatório duplicado com sucesso!')
  } catch (error) {
    console.error('Error duplicating report:', error)
    alert('Erro ao duplicar relatório')
  }
}

const cancelReport = async (report: ReportHistory) => {
  if (confirm('Tem certeza que deseja cancelar este relatório?')) {
    try {
      await cancelReportFromStore(report.id)
    } catch (error) {
      console.error('Error cancelling report:', error)
      alert('Erro ao cancelar relatório')
    }
  }
}

const retryReport = (report: ReportHistory) => {
  // Implement retry logic
  console.log('Retrying report:', report.id)
  alert('Funcionalidade de retry será implementada')
}

const deleteReport = async (report: ReportHistory) => {
  if (confirm('Tem certeza que deseja excluir este relatório?')) {
    try {
      await deleteReportFromStore(report.id)
    } catch (error) {
      console.error('Error deleting report:', error)
      alert('Erro ao excluir relatório')
    }
  }
}

const bulkCancel = async () => {
  if (confirm(`Tem certeza que deseja cancelar ${selectedReports.value.length} relatório(s)?`)) {
    try {
      for (const reportId of selectedReports.value) {
        await cancelReportFromStore(reportId)
      }
      clearSelection()
    } catch (error) {
      console.error('Error cancelling reports:', error)
      alert('Erro ao cancelar relatórios')
    }
  }
}

const bulkDelete = async () => {
  if (confirm(`Tem certeza que deseja excluir ${selectedReports.value.length} relatório(s)?`)) {
    try {
      for (const reportId of selectedReports.value) {
        await deleteReportFromStore(reportId)
      }
      clearSelection()
    } catch (error) {
      console.error('Error deleting reports:', error)
      alert('Erro ao excluir relatórios')
    }
  }
}

const exportHistory = (format: string) => {
  // Export history in specified format
  console.log('Exporting history as:', format)
  
  if (format === 'csv') {
    const csvContent = [
      ['Nome', 'Descrição', 'Categoria', 'Status', 'Gerado', 'Concluído', 'Tempo de Execução', 'Downloads'].join(','),
      ...filteredReports.value.map(report => [
        report.name,
        report.description,
        report.type,
        getStatusText(report.status),
        formatDate(report.generatedAt),
        report.completedAt ? formatDate(report.completedAt) : '',
        report.executionTime ? formatExecutionTime(report.executionTime) : '',
        report.downloadCount.toString()
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `historico-relatorios-${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } else {
    alert(`Exportação em formato ${format.toUpperCase()} será implementada`)
  }
}
</script>