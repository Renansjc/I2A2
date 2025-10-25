<template>
  <div class="space-y-6">
    <!-- User Profile Section -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <div class="flex items-center space-x-4 mb-6">
          <div class="avatar">
            <div class="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
              <svg class="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path>
              </svg>
            </div>
          </div>
          <div>
            <h3 class="text-xl font-bold">{{ userProfile.name || 'Usuário' }}</h3>
            <p class="text-base-content/70">{{ userProfile.email || 'usuario@empresa.com' }}</p>
            <div class="badge badge-primary">{{ userProfile.role || 'Executivo' }}</div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Nome Completo</span>
            </label>
            <input 
              v-model="userProfile.name"
              type="text" 
              placeholder="Seu nome completo"
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">E-mail</span>
            </label>
            <input 
              v-model="userProfile.email"
              type="email" 
              placeholder="seu@email.com"
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Cargo</span>
            </label>
            <select v-model="userProfile.role" class="select select-bordered">
              <option value="CEO">CEO</option>
              <option value="CFO">CFO</option>
              <option value="COO">COO</option>
              <option value="Diretor Financeiro">Diretor Financeiro</option>
              <option value="Gerente">Gerente</option>
              <option value="Analista">Analista</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Empresa</span>
            </label>
            <input 
              v-model="userProfile.company"
              type="text" 
              placeholder="Nome da empresa"
              class="input input-bordered"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Report Preferences -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Preferências de Relatórios</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Formato Padrão</span>
              </label>
              <select v-model="preferences.defaultFormat" class="select select-bordered">
                <option value="pdf">PDF</option>
                <option value="xlsx">Excel</option>
                <option value="docx">Word</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Idioma</span>
              </label>
              <select v-model="preferences.language" class="select select-bordered">
                <option value="pt-BR">Português (Brasil)</option>
                <option value="en-US">English (US)</option>
                <option value="es-ES">Español</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Fuso Horário</span>
              </label>
              <select v-model="preferences.timezone" class="select select-bordered">
                <option value="America/Sao_Paulo">São Paulo (GMT-3)</option>
                <option value="America/New_York">New York (GMT-5)</option>
                <option value="Europe/London">London (GMT+0)</option>
                <option value="Asia/Tokyo">Tokyo (GMT+9)</option>
              </select>
            </div>
          </div>

          <div class="space-y-4">
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Auto-salvar rascunhos</span>
                <input 
                  v-model="preferences.autoSave"
                  type="checkbox" 
                  class="toggle toggle-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Incluir gráficos por padrão</span>
                <input 
                  v-model="preferences.includeCharts"
                  type="checkbox" 
                  class="toggle toggle-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Modo escuro automático</span>
                <input 
                  v-model="preferences.autoDarkMode"
                  type="checkbox" 
                  class="toggle toggle-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Compressão de arquivos grandes</span>
                <input 
                  v-model="preferences.compressLargeFiles"
                  type="checkbox" 
                  class="toggle toggle-primary"
                />
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notification Settings -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Configurações de Notificação</h3>
        
        <div class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">E-mail para notificações</span>
            </label>
            <input 
              v-model="preferences.notificationEmail"
              type="email" 
              placeholder="notificacoes@empresa.com"
              class="input input-bordered"
            />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-3">
              <h4 class="font-semibold">Notificações por E-mail</h4>
              
              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Relatório pronto</span>
                  <input 
                    v-model="preferences.notifications.reportReady"
                    type="checkbox" 
                    class="toggle toggle-primary"
                  />
                </label>
              </div>

              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Falhas de processamento</span>
                  <input 
                    v-model="preferences.notifications.processingFailed"
                    type="checkbox" 
                    class="toggle toggle-primary"
                  />
                </label>
              </div>

              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Resumo semanal</span>
                  <input 
                    v-model="preferences.notifications.weeklyDigest"
                    type="checkbox" 
                    class="toggle toggle-primary"
                  />
                </label>
              </div>
            </div>

            <div class="space-y-3">
              <h4 class="font-semibold">Notificações no Sistema</h4>
              
              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Novos dados disponíveis</span>
                  <input 
                    v-model="preferences.notifications.newDataAvailable"
                    type="checkbox" 
                    class="toggle toggle-primary"
                  />
                </label>
              </div>

              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Atualizações do sistema</span>
                  <input 
                    v-model="preferences.notifications.systemUpdates"
                    type="checkbox" 
                    class="toggle toggle-primary"
                  />
                </label>
              </div>

              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Lembretes de agendamento</span>
                  <input 
                    v-model="preferences.notifications.scheduleReminders"
                    type="checkbox" 
                    class="toggle toggle-primary"
                  />
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Preferences -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Preferências de Dados</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Período padrão para relatórios</span>
              </label>
              <select v-model="preferences.defaultPeriod" class="select select-bordered">
                <option value="last-30-days">Últimos 30 dias</option>
                <option value="last-quarter">Último trimestre</option>
                <option value="last-year">Último ano</option>
                <option value="current-month">Mês atual</option>
                <option value="current-year">Ano atual</option>
                <option value="custom">Personalizado</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Moeda padrão</span>
              </label>
              <select v-model="preferences.defaultCurrency" class="select select-bordered">
                <option value="BRL">Real (R$)</option>
                <option value="USD">Dólar ($)</option>
                <option value="EUR">Euro (€)</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Formato de data</span>
              </label>
              <select v-model="preferences.dateFormat" class="select select-bordered">
                <option value="DD/MM/YYYY">DD/MM/AAAA</option>
                <option value="MM/DD/YYYY">MM/DD/AAAA</option>
                <option value="YYYY-MM-DD">AAAA-MM-DD</option>
              </select>
            </div>
          </div>

          <div class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Precisão decimal</span>
              </label>
              <select v-model="preferences.decimalPrecision" class="select select-bordered">
                <option value="0">Sem decimais</option>
                <option value="2">2 casas decimais</option>
                <option value="4">4 casas decimais</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Separador de milhares</span>
              </label>
              <select v-model="preferences.thousandSeparator" class="select select-bordered">
                <option value=".">Ponto (.)</option>
                <option value=",">Vírgula (,)</option>
                <option value=" ">Espaço ( )</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Incluir dados zerados</span>
                <input 
                  v-model="preferences.includeZeroValues"
                  type="checkbox" 
                  class="toggle toggle-primary"
                />
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Security Settings -->
    <div class="card bg-base-200 shadow-lg">
      <div class="card-body">
        <h3 class="card-title mb-4">Configurações de Segurança</h3>
        
        <div class="space-y-4">
          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Autenticação de dois fatores (2FA)</span>
              <input 
                v-model="preferences.security.twoFactorAuth"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Logout automático após inatividade</span>
              <input 
                v-model="preferences.security.autoLogout"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>

          <div v-if="preferences.security.autoLogout" class="form-control">
            <label class="label">
              <span class="label-text">Tempo de inatividade (minutos)</span>
            </label>
            <select v-model="preferences.security.inactivityTimeout" class="select select-bordered">
              <option value="15">15 minutos</option>
              <option value="30">30 minutos</option>
              <option value="60">1 hora</option>
              <option value="120">2 horas</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">Registrar atividades de acesso</span>
              <input 
                v-model="preferences.security.logAccess"
                type="checkbox" 
                class="toggle toggle-primary"
              />
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex justify-between items-center">
      <button class="btn btn-ghost" @click="resetToDefaults">
        Restaurar Padrões
      </button>
      <div class="space-x-2">
        <button class="btn btn-secondary" @click="exportSettings">
          Exportar Configurações
        </button>
        <button class="btn btn-primary" @click="savePreferences" :disabled="isSaving">
          <span v-if="isSaving" class="loading loading-spinner loading-sm mr-2"></span>
          Salvar Alterações
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

// Props and emits
const emit = defineEmits<{
  save: [preferences: any]
  reset: []
}>()

// Reactive state
const isSaving = ref(false)

const userProfile = ref({
  name: '',
  email: '',
  role: 'Executivo',
  company: ''
})

const preferences = reactive({
  defaultFormat: 'pdf',
  language: 'pt-BR',
  timezone: 'America/Sao_Paulo',
  autoSave: true,
  includeCharts: true,
  autoDarkMode: false,
  compressLargeFiles: true,
  notificationEmail: '',
  notifications: {
    reportReady: true,
    processingFailed: true,
    weeklyDigest: false,
    newDataAvailable: true,
    systemUpdates: false,
    scheduleReminders: true
  },
  defaultPeriod: 'last-30-days',
  defaultCurrency: 'BRL',
  dateFormat: 'DD/MM/YYYY',
  decimalPrecision: '2',
  thousandSeparator: '.',
  includeZeroValues: false,
  security: {
    twoFactorAuth: false,
    autoLogout: true,
    inactivityTimeout: '30',
    logAccess: true
  }
})

// Methods
const savePreferences = async () => {
  isSaving.value = true
  
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Here you would integrate with Supabase to save preferences
    // await supabase.from('user_preferences').upsert({
    //   user_id: user.id,
    //   preferences: preferences
    // })
    
    emit('save', { userProfile: userProfile.value, preferences })
    
    // Show success message
    alert('Configurações salvas com sucesso!')
    
  } catch (error) {
    console.error('Error saving preferences:', error)
    alert('Erro ao salvar configurações. Tente novamente.')
  } finally {
    isSaving.value = false
  }
}

const resetToDefaults = () => {
  if (confirm('Tem certeza que deseja restaurar todas as configurações para os valores padrão?')) {
    // Reset to default values
    Object.assign(preferences, {
      defaultFormat: 'pdf',
      language: 'pt-BR',
      timezone: 'America/Sao_Paulo',
      autoSave: true,
      includeCharts: true,
      autoDarkMode: false,
      compressLargeFiles: true,
      notificationEmail: '',
      notifications: {
        reportReady: true,
        processingFailed: true,
        weeklyDigest: false,
        newDataAvailable: true,
        systemUpdates: false,
        scheduleReminders: true
      },
      defaultPeriod: 'last-30-days',
      defaultCurrency: 'BRL',
      dateFormat: 'DD/MM/YYYY',
      decimalPrecision: '2',
      thousandSeparator: '.',
      includeZeroValues: false,
      security: {
        twoFactorAuth: false,
        autoLogout: true,
        inactivityTimeout: '30',
        logAccess: true
      }
    })
    
    emit('reset')
  }
}

const exportSettings = () => {
  const settingsData = {
    userProfile: userProfile.value,
    preferences
  }
  
  const dataStr = JSON.stringify(settingsData, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  
  const link = document.createElement('a')
  link.href = URL.createObjectURL(dataBlob)
  link.download = 'configuracoes-sistema.json'
  link.click()
}
</script>