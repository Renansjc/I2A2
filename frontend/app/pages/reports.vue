<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Relatórios</h1>
        <p class="text-base-content/70">Gere e gerencie relatórios executivos</p>
      </div>
      <div class="flex space-x-2">
        <button class="btn btn-outline" @click="showSettingsModal = true">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"></path>
          </svg>
          Configurações
        </button>
        <button class="btn btn-primary" @click="showNewReportModal = true">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"></path>
          </svg>
          Novo Relatório
        </button>
      </div>
    </div>

    <!-- Main Navigation Tabs -->
    <div class="tabs tabs-bordered">
      <a 
        class="tab tab-lg"
        :class="{ 'tab-active': activeMainTab === 'templates' }"
        @click="activeMainTab = 'templates'"
      >
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
        </svg>
        Modelos de Relatório
      </a>
      <a 
        class="tab tab-lg"
        :class="{ 'tab-active': activeMainTab === 'history' }"
        @click="activeMainTab = 'history'"
      >
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
        </svg>
        Histórico
      </a>
      <a 
        class="tab tab-lg"
        :class="{ 'tab-active': activeMainTab === 'downloads' }"
        @click="activeMainTab = 'downloads'"
      >
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
        Downloads
      </a>
    </div>

    <!-- Templates Tab Content -->
    <div v-if="activeMainTab === 'templates'" class="space-y-6">
      <!-- Report Templates -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="template in templates"
          :key="template.id"
          class="card bg-base-200 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
          @click="selectTemplate(template)"
        >
          <div class="card-body">
            <div class="flex items-start justify-between">
              <div class="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div class="badge badge-outline">{{ template.category }}</div>
            </div>
            
            <h3 class="card-title text-lg">{{ template.name }}</h3>
            <p class="text-sm text-base-content/70">{{ template.description }}</p>
            
            <div class="card-actions justify-end mt-4">
              <div class="badge badge-ghost">{{ template.estimatedTime }}</div>
              <button class="btn btn-primary btn-sm">Gerar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Reports -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h2 class="card-title">Relatórios Recentes</h2>
            <div class="join">
              <input 
                v-model="searchReports"
                class="input input-bordered input-sm join-item" 
                placeholder="Buscar relatórios..."
              />
              <button class="btn btn-sm join-item">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
                </svg>
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="table table-zebra">
              <thead>
                <tr>
                  <th>Nome do Relatório</th>
                  <th>Tipo</th>
                  <th>Gerado</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="report in filteredReports" :key="report.id">
                  <td>
                    <div class="flex items-center space-x-3">
                      <div class="w-8 h-8 bg-primary/20 rounded flex items-center justify-center">
                        <svg class="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                        </svg>
                      </div>
                      <div>
                        <div class="font-bold">{{ report.name }}</div>
                        <div class="text-sm text-base-content/70">{{ report.description }}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div class="badge badge-outline">{{ report.type }}</div>
                  </td>
                  <td>{{ formatDate(report.generatedAt) }}</td>
                  <td>
                    <div 
                      class="badge"
                      :class="{
                        'badge-success': report.status === 'completed',
                        'badge-warning': report.status === 'processing',
                        'badge-error': report.status === 'failed'
                      }"
                    >
                      {{ report.status === 'completed' ? 'concluído' : report.status === 'processing' ? 'processando' : 'falhou' }}
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
                        <li><a @click="viewReport(report)">Visualizar</a></li>
                        <li><a @click="downloadReport(report)">Baixar</a></li>
                        <li><a @click="scheduleReport(report)">Agendar</a></li>
                        <li><a @click="duplicateReport(report)">Duplicar</a></li>
                        <li><a class="text-error" @click="deleteReport(report)">Excluir</a></li>
                      </ul>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- History Tab Content -->
    <div v-if="activeMainTab === 'history'">
      <ReportHistory />
    </div>

    <!-- Downloads Tab Content -->
    <div v-if="activeMainTab === 'downloads'">
      <DownloadManager />
    </div>

    <!-- New Report Modal -->
    <div v-if="showNewReportModal" class="modal modal-open">
      <div class="modal-box max-w-4xl">
        <h3 class="font-bold text-lg mb-4">Criar Novo Relatório</h3>
        
        <div class="tabs tabs-bordered mb-6">
          <a 
            class="tab"
            :class="{ 'tab-active': activeReportTab === 'basic' }"
            @click="activeReportTab = 'basic'"
          >
            Informações Básicas
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeReportTab === 'data' }"
            @click="activeReportTab = 'data'"
          >
            Fonte de Dados
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeReportTab === 'schedule' }"
            @click="activeReportTab = 'schedule'"
          >
            Agendamento
          </a>
        </div>

        <!-- Basic Information Tab -->
        <div v-if="activeReportTab === 'basic'" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Nome do Relatório *</span>
            </label>
            <input 
              v-model="newReport.name"
              type="text" 
              placeholder="Digite o nome do relatório" 
              class="input input-bordered"
              :class="{ 'input-error': formErrors.name }"
            />
            <label v-if="formErrors.name" class="label">
              <span class="label-text-alt text-error">{{ formErrors.name }}</span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Descrição</span>
            </label>
            <textarea 
              v-model="newReport.description"
              placeholder="Descreva o propósito do relatório"
              class="textarea textarea-bordered h-24"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Modelo *</span>
            </label>
            <select 
              v-model="newReport.templateId" 
              class="select select-bordered"
              :class="{ 'select-error': formErrors.templateId }"
            >
              <option value="">Selecione um modelo</option>
              <option 
                v-for="template in templates"
                :key="template.id"
                :value="template.id"
              >
                {{ template.name }}
              </option>
            </select>
            <label v-if="formErrors.templateId" class="label">
              <span class="label-text-alt text-error">{{ formErrors.templateId }}</span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Formato de Saída *</span>
            </label>
            <div class="flex flex-wrap gap-4">
              <label class="label cursor-pointer">
                <input 
                  v-model="newReport.formats"
                  type="checkbox" 
                  value="pdf"
                  class="checkbox checkbox-primary"
                />
                <span class="label-text ml-2">PDF</span>
              </label>
              <label class="label cursor-pointer">
                <input 
                  v-model="newReport.formats"
                  type="checkbox" 
                  value="xlsx"
                  class="checkbox checkbox-primary"
                />
                <span class="label-text ml-2">Excel</span>
              </label>
              <label class="label cursor-pointer">
                <input 
                  v-model="newReport.formats"
                  type="checkbox" 
                  value="docx"
                  class="checkbox checkbox-primary"
                />
                <span class="label-text ml-2">Word</span>
              </label>
            </div>
            <label v-if="formErrors.formats" class="label">
              <span class="label-text-alt text-error">{{ formErrors.formats }}</span>
            </label>
          </div>
        </div>

        <!-- Data Source Tab -->
        <div v-if="activeReportTab === 'data'" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Período dos Dados *</span>
            </label>
            <div class="grid grid-cols-2 gap-2">
              <input 
                v-model="newReport.startDate"
                type="date" 
                class="input input-bordered"
                :class="{ 'input-error': formErrors.startDate }"
              />
              <input 
                v-model="newReport.endDate"
                type="date" 
                class="input input-bordered"
                :class="{ 'input-error': formErrors.endDate }"
              />
            </div>
            <label v-if="formErrors.startDate || formErrors.endDate" class="label">
              <span class="label-text-alt text-error">
                {{ formErrors.startDate || formErrors.endDate }}
              </span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Filtros Adicionais</span>
            </label>
            <div class="space-y-3">
              <div class="form-control">
                <label class="label">
                  <span class="label-text">Tipo de Documento</span>
                </label>
                <div class="flex space-x-4">
                  <label class="label cursor-pointer">
                    <input 
                      v-model="newReport.filters.documentTypes"
                      type="checkbox" 
                      value="nfe"
                      class="checkbox checkbox-primary"
                    />
                    <span class="label-text ml-2">NF-e</span>
                  </label>
                  <label class="label cursor-pointer">
                    <input 
                      v-model="newReport.filters.documentTypes"
                      type="checkbox" 
                      value="nfse"
                      class="checkbox checkbox-primary"
                    />
                    <span class="label-text ml-2">NFS-e</span>
                  </label>
                </div>
              </div>

              <div class="form-control">
                <label class="label">
                  <span class="label-text">Estados (UF)</span>
                </label>
                <input 
                  v-model="newReport.filters.states"
                  type="text" 
                  placeholder="Ex: SP, RJ, MG (deixe vazio para todos)"
                  class="input input-bordered"
                />
              </div>

              <div class="form-control">
                <label class="label">
                  <span class="label-text">Valor Mínimo (R$)</span>
                </label>
                <input 
                  v-model="newReport.filters.minValue"
                  type="number" 
                  step="0.01"
                  placeholder="0.00"
                  class="input input-bordered"
                />
              </div>
            </div>
          </div>

          <!-- XML Upload for Custom Data -->
          <div class="divider">OU</div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">Enviar Arquivos XML Específicos</span>
            </label>
            <div class="border-2 border-dashed border-base-300 rounded-lg p-4">
              <FileUpload @files-uploaded="handleCustomXMLFiles" />
            </div>
          </div>
        </div>

        <!-- Schedule Tab -->
        <div v-if="activeReportTab === 'schedule'" class="space-y-4">
          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Agendar Relatório Recorrente</span>
              <input 
                v-model="newReport.isScheduled"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div v-if="newReport.isScheduled" class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Frequência *</span>
              </label>
              <select 
                v-model="newReport.schedule.frequency" 
                class="select select-bordered"
                :class="{ 'select-error': formErrors.frequency }"
              >
                <option value="">Selecione a frequência</option>
                <option value="daily">Diário</option>
                <option value="weekly">Semanal</option>
                <option value="monthly">Mensal</option>
                <option value="quarterly">Trimestral</option>
                <option value="yearly">Anual</option>
              </select>
              <label v-if="formErrors.frequency" class="label">
                <span class="label-text-alt text-error">{{ formErrors.frequency }}</span>
              </label>
            </div>

            <div v-if="newReport.schedule.frequency === 'weekly'" class="form-control">
              <label class="label">
                <span class="label-text">Dia da Semana</span>
              </label>
              <select v-model="newReport.schedule.dayOfWeek" class="select select-bordered">
                <option value="1">Segunda-feira</option>
                <option value="2">Terça-feira</option>
                <option value="3">Quarta-feira</option>
                <option value="4">Quinta-feira</option>
                <option value="5">Sexta-feira</option>
                <option value="6">Sábado</option>
                <option value="0">Domingo</option>
              </select>
            </div>

            <div v-if="newReport.schedule.frequency === 'monthly'" class="form-control">
              <label class="label">
                <span class="label-text">Dia do Mês</span>
              </label>
              <input 
                v-model="newReport.schedule.dayOfMonth"
                type="number" 
                min="1" 
                max="31"
                placeholder="1-31"
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Horário de Execução</span>
              </label>
              <input 
                v-model="newReport.schedule.time"
                type="time" 
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Destinatários (E-mail)</span>
              </label>
              <textarea 
                v-model="newReport.schedule.recipients"
                placeholder="Digite os e-mails separados por vírgula"
                class="textarea textarea-bordered h-20"
              ></textarea>
              <label class="label">
                <span class="label-text-alt">Exemplo: joao@empresa.com, maria@empresa.com</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Data de Início</span>
              </label>
              <input 
                v-model="newReport.schedule.startDate"
                type="date" 
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Data de Fim (Opcional)</span>
                <input 
                  v-model="newReport.schedule.hasEndDate"
                  type="checkbox" 
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>

            <div v-if="newReport.schedule.hasEndDate" class="form-control">
              <input 
                v-model="newReport.schedule.endDate"
                type="date" 
                class="input input-bordered"
              />
            </div>
          </div>
        </div>

        <div class="modal-action">
          <button class="btn btn-ghost" @click="closeNewReportModal">
            Cancelar
          </button>
          <button 
            v-if="activeReportTab !== 'schedule'"
            class="btn btn-secondary"
            @click="nextReportTab"
          >
            Próximo
          </button>
          <button 
            v-if="activeReportTab === 'schedule' || !newReport.isScheduled"
            class="btn btn-primary"
            :disabled="!isFormValid"
            @click="createReportFromForm"
          >
            <span v-if="isCreatingReport" class="loading loading-spinner loading-sm mr-2"></span>
            {{ newReport.isScheduled ? 'Agendar Relatório' : 'Gerar Relatório' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Report Preview Modal -->
    <div v-if="showPreviewModal && selectedReport" class="modal modal-open">
      <div class="modal-box max-w-6xl h-5/6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold text-lg">Visualização do Relatório</h3>
          <button class="btn btn-sm btn-circle btn-ghost" @click="showPreviewModal = false">✕</button>
        </div>
        <ReportPreview 
          :report="selectedReport" 
          @close="showPreviewModal = false"
          @export="handleReportExport"
          @schedule="handleReportSchedule"
          @generate="handleReportGenerate"
        />
      </div>
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettingsModal" class="modal modal-open">
      <div class="modal-box max-w-2xl">
        <h3 class="font-bold text-lg mb-4">Configurações de Relatórios</h3>
        
        <div class="tabs tabs-bordered mb-6">
          <a 
            class="tab"
            :class="{ 'tab-active': activeSettingsTab === 'preferences' }"
            @click="activeSettingsTab = 'preferences'"
          >
            Preferências
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeSettingsTab === 'templates' }"
            @click="activeSettingsTab = 'templates'"
          >
            Modelos
          </a>
          <a 
            class="tab"
            :class="{ 'tab-active': activeSettingsTab === 'notifications' }"
            @click="activeSettingsTab = 'notifications'"
          >
            Notificações
          </a>
        </div>

        <!-- Preferences Tab -->
        <div v-if="activeSettingsTab === 'preferences'" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Formato Padrão</span>
            </label>
            <select v-model="userSettings.defaultFormat" class="select select-bordered">
              <option value="pdf">PDF</option>
              <option value="xlsx">Excel</option>
              <option value="docx">Word</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Idioma dos Relatórios</span>
            </label>
            <select v-model="userSettings.language" class="select select-bordered">
              <option value="pt-BR">Português (Brasil)</option>
              <option value="en-US">English (US)</option>
              <option value="es-ES">Español</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Fuso Horário</span>
            </label>
            <select v-model="userSettings.timezone" class="select select-bordered">
              <option value="America/Sao_Paulo">São Paulo (GMT-3)</option>
              <option value="America/New_York">New York (GMT-5)</option>
              <option value="Europe/London">London (GMT+0)</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Auto-salvar rascunhos</span>
              <input 
                v-model="userSettings.autoSave"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Incluir gráficos por padrão</span>
              <input 
                v-model="userSettings.includeCharts"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>
        </div>

        <!-- Templates Tab -->
        <div v-if="activeSettingsTab === 'templates'" class="space-y-4">
          <div class="flex justify-between items-center">
            <h4 class="font-semibold">Modelos Personalizados</h4>
            <button class="btn btn-sm btn-primary">
              <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"></path>
              </svg>
              Novo Modelo
            </button>
          </div>

          <div class="space-y-2">
            <div 
              v-for="template in customTemplates"
              :key="template.id"
              class="flex items-center justify-between p-3 bg-base-200 rounded-lg"
            >
              <div>
                <h5 class="font-medium">{{ template.name }}</h5>
                <p class="text-sm text-base-content/70">{{ template.description }}</p>
              </div>
              <div class="dropdown dropdown-end">
                <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                  </svg>
                </div>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                  <li><a>Editar</a></li>
                  <li><a>Duplicar</a></li>
                  <li><a class="text-error">Excluir</a></li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Notifications Tab -->
        <div v-if="activeSettingsTab === 'notifications'" class="space-y-4">
          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Notificar quando relatório estiver pronto</span>
              <input 
                v-model="userSettings.notifications.reportReady"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Notificar falhas de processamento</span>
              <input 
                v-model="userSettings.notifications.processingFailed"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Resumo semanal de atividades</span>
              <input 
                v-model="userSettings.notifications.weeklyDigest"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">E-mail para notificações</span>
            </label>
            <input 
              v-model="userSettings.notificationEmail"
              type="email" 
              placeholder="seu@email.com"
              class="input input-bordered"
            />
          </div>
        </div>

        <div class="modal-action">
          <button class="btn btn-ghost" @click="showSettingsModal = false">
            Cancelar
          </button>
          <button class="btn btn-primary" @click="saveSettings">
            Salvar Configurações
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useReports } from '~/composables/useReports'
import ReportHistory from '~/components/ReportHistory.vue'
import DownloadManager from '~/components/DownloadManager.vue'

definePageMeta({
  layout: 'default'
})

// Composables
const { 
  reports, 
  templates, 
  recentReports,
  createReport,
  downloadReport: downloadReportFromStore,
  duplicateReport: duplicateReportFromStore,
  deleteReport: deleteReportFromStore
} = useReports()

// Reactive state
const showNewReportModal = ref(false)
const showPreviewModal = ref(false)
const showSettingsModal = ref(false)
const showDownloadManager = ref(false)
const showReportHistory = ref(false)
const searchReports = ref('')
const activeReportTab = ref('basic')
const activeSettingsTab = ref('preferences')
const activeMainTab = ref('templates')
const isCreatingReport = ref(false)
const selectedReport = ref(null)

// Form validation
const formErrors = reactive({
  name: '',
  templateId: '',
  formats: '',
  startDate: '',
  endDate: '',
  frequency: ''
})

// New report form data
const newReport = ref({
  name: '',
  description: '',
  templateId: '',
  startDate: '',
  endDate: '',
  formats: [] as string[],
  isScheduled: false,
  filters: {
    documentTypes: [] as string[],
    states: '',
    minValue: null as number | null
  },
  schedule: {
    frequency: '',
    dayOfWeek: '1',
    dayOfMonth: 1,
    time: '09:00',
    recipients: '',
    startDate: '',
    endDate: '',
    hasEndDate: false
  },
  customXMLFiles: [] as File[]
})

// User settings
const userSettings = ref({
  defaultFormat: 'pdf',
  language: 'pt-BR',
  timezone: 'America/Sao_Paulo',
  autoSave: true,
  includeCharts: true,
  notificationEmail: '',
  notifications: {
    reportReady: true,
    processingFailed: true,
    weeklyDigest: false
  }
})

// Custom templates
const customTemplates = ref([
  {
    id: 'custom-1',
    name: 'Relatório Executivo Personalizado',
    description: 'Modelo customizado para apresentações executivas'
  },
  {
    id: 'custom-2',
    name: 'Análise Fiscal Detalhada',
    description: 'Modelo com foco em análise fiscal aprofundada'
  }
])

// Mock data for backward compatibility
const mockRecentReports = [
  {
    id: '1',
    name: 'Análise de Fornecedores T4',
    description: 'Revisão trimestral de desempenho de fornecedores',
    type: 'Financeiro',
    generatedAt: new Date('2024-01-15'),
    status: 'completed'
  },
  {
    id: '2',
    name: 'Relatório Fiscal Dezembro',
    description: 'Análise mensal de eficiência fiscal',
    type: 'Fiscal',
    generatedAt: new Date('2024-01-10'),
    status: 'completed'
  },
  {
    id: '3',
    name: 'Tendências de Produtos 2024',
    description: 'Análise anual de categorias de produtos',
    type: 'Análises',
    generatedAt: new Date('2024-01-08'),
    status: 'processing'
  }
]

// Computed properties
const filteredReports = computed(() => {
  const reportsToFilter = recentReports.value.length > 0 ? recentReports.value : mockRecentReports
  
  if (!searchReports.value) return reportsToFilter
  
  return reportsToFilter.filter(report =>
    report.name.toLowerCase().includes(searchReports.value.toLowerCase()) ||
    report.description.toLowerCase().includes(searchReports.value.toLowerCase())
  )
})

const isFormValid = computed(() => {
  return newReport.value.name && 
         newReport.value.templateId && 
         newReport.value.formats.length > 0 &&
         newReport.value.startDate &&
         newReport.value.endDate &&
         (!newReport.value.isScheduled || newReport.value.schedule.frequency)
})

// Methods
const selectTemplate = (template: any) => {
  newReport.value.templateId = template.id
  newReport.value.name = `${template.name} - ${new Date().toLocaleDateString('pt-BR')}`
  showNewReportModal.value = true
}

const validateForm = (): boolean => {
  // Reset errors
  Object.keys(formErrors).forEach(key => {
    formErrors[key] = ''
  })

  let isValid = true

  if (!newReport.value.name.trim()) {
    formErrors.name = 'Nome do relatório é obrigatório'
    isValid = false
  }

  if (!newReport.value.templateId) {
    formErrors.templateId = 'Selecione um modelo'
    isValid = false
  }

  if (newReport.value.formats.length === 0) {
    formErrors.formats = 'Selecione pelo menos um formato'
    isValid = false
  }

  if (!newReport.value.startDate) {
    formErrors.startDate = 'Data de início é obrigatória'
    isValid = false
  }

  if (!newReport.value.endDate) {
    formErrors.endDate = 'Data de fim é obrigatória'
    isValid = false
  }

  if (newReport.value.startDate && newReport.value.endDate) {
    if (new Date(newReport.value.startDate) > new Date(newReport.value.endDate)) {
      formErrors.endDate = 'Data de fim deve ser posterior à data de início'
      isValid = false
    }
  }

  if (newReport.value.isScheduled && !newReport.value.schedule.frequency) {
    formErrors.frequency = 'Frequência é obrigatória para relatórios agendados'
    isValid = false
  }

  return isValid
}

const nextReportTab = () => {
  if (activeReportTab.value === 'basic') {
    activeReportTab.value = 'data'
  } else if (activeReportTab.value === 'data') {
    activeReportTab.value = 'schedule'
  }
}

const closeNewReportModal = () => {
  showNewReportModal.value = false
  activeReportTab.value = 'basic'
  
  // Reset form
  newReport.value = {
    name: '',
    description: '',
    templateId: '',
    startDate: '',
    endDate: '',
    formats: [],
    isScheduled: false,
    filters: {
      documentTypes: [],
      states: '',
      minValue: null
    },
    schedule: {
      frequency: '',
      dayOfWeek: '1',
      dayOfMonth: 1,
      time: '09:00',
      recipients: '',
      startDate: '',
      endDate: '',
      hasEndDate: false
    },
    customXMLFiles: []
  }
  
  // Reset errors
  Object.keys(formErrors).forEach(key => {
    formErrors[key] = ''
  })
}

const createReportFromForm = async () => {
  if (!validateForm()) {
    return
  }

  isCreatingReport.value = true

  try {
    const reportConfig = {
      name: newReport.value.name,
      description: newReport.value.description || 'Relatório gerado automaticamente',
      templateId: newReport.value.templateId,
      startDate: newReport.value.startDate,
      endDate: newReport.value.endDate,
      formats: newReport.value.formats,
      isScheduled: newReport.value.isScheduled,
      filters: newReport.value.filters,
      schedule: newReport.value.schedule,
      customXMLFiles: newReport.value.customXMLFiles
    }
    
    const reportId = await createReport(reportConfig)
    
    closeNewReportModal()
    
    // Show success message (you could use a toast library here)
    alert(newReport.value.isScheduled ? 'Relatório agendado com sucesso!' : 'Relatório sendo gerado...')
    
  } catch (error) {
    console.error('Error creating report:', error)
    alert('Erro ao criar relatório. Tente novamente.')
  } finally {
    isCreatingReport.value = false
  }
}

const handleCustomXMLFiles = (files: File[]) => {
  newReport.value.customXMLFiles = files
}

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const viewReport = (report: any) => {
  // Create mock report data for preview
  selectedReport.value = {
    title: report.name,
    description: report.description,
    generatedAt: report.generatedAt,
    dataPeriod: 'Jan 2024 - Dez 2024',
    recordCount: 1250,
    format: 'pdf',
    executiveSummary: 'Este relatório apresenta uma análise abrangente dos dados fiscais do período selecionado, destacando tendências importantes e oportunidades de otimização.',
    keyMetrics: [
      { label: 'Total de Notas', value: '1,250', change: '+12%', trend: 'up' },
      { label: 'Valor Total', value: 'R$ 2.5M', change: '+8%', trend: 'up' },
      { label: 'Fornecedores', value: '85', change: '-3%', trend: 'down' }
    ],
    insights: [
      {
        id: '1',
        type: 'success',
        title: 'Oportunidade de Economia',
        description: 'Identificadas oportunidades de economia fiscal de até R$ 50.000'
      },
      {
        id: '2',
        type: 'warning',
        title: 'Concentração de Fornecedores',
        description: '70% das compras concentradas em apenas 5 fornecedores'
      }
    ],
    dataColumns: ['Fornecedor', 'CNPJ', 'Valor Total', 'Qtd Notas', 'UF'],
    data: [
      ['Fornecedor A', '12.345.678/0001-90', 'R$ 500.000', '150', 'SP'],
      ['Fornecedor B', '98.765.432/0001-10', 'R$ 350.000', '89', 'RJ'],
      ['Fornecedor C', '11.222.333/0001-44', 'R$ 280.000', '67', 'MG']
    ],
    charts: [
      { id: '1', title: 'Evolução Mensal', type: 'line' },
      { id: '2', title: 'Distribuição por UF', type: 'pie' },
      { id: '3', title: 'Top Fornecedores', type: 'bar' },
      { id: '4', title: 'Categorias de Produtos', type: 'doughnut' }
    ]
  }
  
  showPreviewModal.value = true
}

const downloadReport = async (report: any) => {
  try {
    if (report.formats && report.formats.length > 0) {
      // Download the first available format
      await downloadReportFromStore(report.id, report.formats[0])
    } else {
      alert('Nenhum formato disponível para download')
    }
  } catch (error) {
    console.error('Error downloading report:', error)
    alert('Erro ao fazer download do relatório')
  }
}

const scheduleReport = (report: any) => {
  console.log('Scheduling report:', report)
  // Open scheduling modal or redirect to schedule page
  alert('Funcionalidade de agendamento será implementada')
}

const duplicateReport = async (report: any) => {
  try {
    await duplicateReportFromStore(report.id)
    alert('Relatório duplicado com sucesso!')
  } catch (error) {
    console.error('Error duplicating report:', error)
    alert('Erro ao duplicar relatório')
  }
}

const deleteReport = async (report: any) => {
  if (confirm('Tem certeza que deseja excluir este relatório?')) {
    try {
      await deleteReportFromStore(report.id)
    } catch (error) {
      console.error('Error deleting report:', error)
      alert('Erro ao excluir relatório')
    }
  }
}

const handleReportExport = (format: string) => {
  console.log('Exporting report as:', format)
  alert(`Exportando relatório como ${format.toUpperCase()}...`)
}

const handleReportSchedule = () => {
  console.log('Scheduling report from preview')
  alert('Abrindo configurações de agendamento...')
}

const handleReportGenerate = () => {
  console.log('Generating full report')
  alert('Gerando relatório completo...')
}

const saveSettings = async () => {
  try {
    // Simulate API call to save settings
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    console.log('Saving settings:', userSettings.value)
    
    // Here you would integrate with Supabase to save user preferences
    // await supabase.from('user_settings').upsert(userSettings.value)
    
    showSettingsModal.value = false
    alert('Configurações salvas com sucesso!')
    
  } catch (error) {
    console.error('Error saving settings:', error)
    alert('Erro ao salvar configurações. Tente novamente.')
  }
}
</script>