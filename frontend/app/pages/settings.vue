<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Configurações</h1>
        <p class="text-base-content/70">
          Gerencie suas preferências e configurações do sistema
        </p>
      </div>
      <div class="flex space-x-2">
        <button class="btn btn-outline" @click="importSettings">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z"
              clip-rule="evenodd"
            ></path>
          </svg>
          Importar
        </button>
        <NuxtLink to="/reports" class="btn btn-primary">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clip-rule="evenodd"
            ></path>
          </svg>
          Voltar aos Relatórios
        </NuxtLink>
      </div>
    </div>

    <!-- Settings Navigation -->
    <div class="tabs tabs-bordered">
      <a
        class="tab"
        :class="{ 'tab-active': activeTab === 'preferences' }"
        @click="activeTab = 'preferences'"
      >
        Preferências
      </a>
      <a
        class="tab"
        :class="{ 'tab-active': activeTab === 'account' }"
        @click="activeTab = 'account'"
      >
        Conta
      </a>
      <a
        class="tab"
        :class="{ 'tab-active': activeTab === 'integrations' }"
        @click="activeTab = 'integrations'"
      >
        Integrações
      </a>
      <a
        class="tab"
        :class="{ 'tab-active': activeTab === 'advanced' }"
        @click="activeTab = 'advanced'"
      >
        Avançado
      </a>
    </div>

    <!-- Preferences Tab -->
    <div v-if="activeTab === 'preferences'">
      <UserPreferences
        @save="handleSavePreferences"
        @reset="handleResetPreferences"
      />
    </div>

    <!-- Account Tab -->
    <div v-if="activeTab === 'account'" class="space-y-6">
      <!-- Account Information -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Informações da Conta</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">ID da Conta</span>
              </label>
              <input
                type="text"
                value="usr_1234567890abcdef"
                class="input input-bordered"
                readonly
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Plano Atual</span>
              </label>
              <div class="flex items-center space-x-2">
                <div class="badge badge-primary">Executivo Pro</div>
                <button class="btn btn-sm btn-outline">Alterar Plano</button>
              </div>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Data de Criação</span>
              </label>
              <input
                type="text"
                value="15 de Janeiro, 2024"
                class="input input-bordered"
                readonly
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Último Acesso</span>
              </label>
              <input
                type="text"
                :value="formatDate(new Date())"
                class="input input-bordered"
                readonly
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Statistics -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Estatísticas de Uso</h3>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="stat bg-base-100 rounded-lg">
              <div class="stat-title">Relatórios Gerados</div>
              <div class="stat-value text-primary">127</div>
              <div class="stat-desc">Este mês</div>
            </div>

            <div class="stat bg-base-100 rounded-lg">
              <div class="stat-title">Arquivos Processados</div>
              <div class="stat-value text-secondary">2,450</div>
              <div class="stat-desc">Total</div>
            </div>

            <div class="stat bg-base-100 rounded-lg">
              <div class="stat-title">Armazenamento</div>
              <div class="stat-value text-accent">1.2 GB</div>
              <div class="stat-desc">de 10 GB</div>
            </div>

            <div class="stat bg-base-100 rounded-lg">
              <div class="stat-title">API Calls</div>
              <div class="stat-value text-warning">8,450</div>
              <div class="stat-desc">Este mês</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Password Change -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Alterar Senha</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Senha Atual</span>
              </label>
              <input
                v-model="passwordForm.currentPassword"
                type="password"
                placeholder="Digite sua senha atual"
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Nova Senha</span>
              </label>
              <input
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="Digite a nova senha"
                class="input input-bordered"
              />
            </div>

            <div class="form-control md:col-span-2">
              <label class="label">
                <span class="label-text">Confirmar Nova Senha</span>
              </label>
              <input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="Confirme a nova senha"
                class="input input-bordered"
              />
            </div>
          </div>

          <div class="card-actions justify-end mt-4">
            <button class="btn btn-primary" @click="changePassword">
              Alterar Senha
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Integrations Tab -->
    <div v-if="activeTab === 'integrations'" class="space-y-6">
      <!-- Supabase Integration -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h3 class="card-title">Supabase</h3>
              <p class="text-base-content/70">
                Autenticação e armazenamento de dados
              </p>
            </div>
            <div class="badge badge-success">Conectado</div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">URL do Projeto</span>
              </label>
              <input
                type="text"
                value="https://seu-projeto.supabase.co"
                class="input input-bordered"
                readonly
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Status da Conexão</span>
              </label>
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-success rounded-full"></div>
                <span class="text-success">Ativo</span>
              </div>
            </div>
          </div>

          <div class="card-actions justify-end mt-4">
            <button class="btn btn-outline">Testar Conexão</button>
            <button class="btn btn-secondary">Reconfigurar</button>
          </div>
        </div>
      </div>

      <!-- Email Integration -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h3 class="card-title">Integração de E-mail</h3>
              <p class="text-base-content/70">
                Configurações para envio de relatórios por e-mail
              </p>
            </div>
            <div class="badge badge-warning">Configuração Necessária</div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Servidor SMTP</span>
              </label>
              <input
                v-model="emailConfig.smtpServer"
                type="text"
                placeholder="smtp.gmail.com"
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Porta</span>
              </label>
              <input
                v-model="emailConfig.port"
                type="number"
                placeholder="587"
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">E-mail de Envio</span>
              </label>
              <input
                v-model="emailConfig.fromEmail"
                type="email"
                placeholder="relatorios@empresa.com"
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Senha/Token</span>
              </label>
              <input
                v-model="emailConfig.password"
                type="password"
                placeholder="••••••••"
                class="input input-bordered"
              />
            </div>
          </div>

          <div class="card-actions justify-end mt-4">
            <button class="btn btn-outline">Testar E-mail</button>
            <button class="btn btn-primary">Salvar Configuração</button>
          </div>
        </div>
      </div>

      <!-- API Keys -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h3 class="card-title">Chaves de API</h3>
              <p class="text-base-content/70">
                Gerencie suas chaves de acesso à API
              </p>
            </div>
            <button class="btn btn-primary btn-sm" @click="generateApiKey">
              <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                  clip-rule="evenodd"
                ></path>
              </svg>
              Nova Chave
            </button>
          </div>

          <div class="space-y-3">
            <div
              v-for="apiKey in apiKeys"
              :key="apiKey.id"
              class="flex items-center justify-between p-3 bg-base-100 rounded-lg"
            >
              <div>
                <h5 class="font-medium">{{ apiKey.name }}</h5>
                <p class="text-sm text-base-content/70 font-mono">
                  {{ apiKey.key }}
                </p>
                <p class="text-xs text-base-content/50">
                  Criada em {{ formatDate(apiKey.createdAt) }}
                </p>
              </div>
              <div class="dropdown dropdown-end">
                <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                    ></path>
                  </svg>
                </div>
                <ul
                  tabindex="0"
                  class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52"
                >
                  <li><a @click="copyApiKey(apiKey.key)">Copiar</a></li>
                  <li><a @click="regenerateApiKey(apiKey.id)">Regenerar</a></li>
                  <li>
                    <a class="text-error" @click="deleteApiKey(apiKey.id)"
                      >Excluir</a
                    >
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Advanced Tab -->
    <div v-if="activeTab === 'advanced'" class="space-y-6">
      <!-- System Information -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Informações do Sistema</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Versão do Sistema</span>
              </label>
              <input
                type="text"
                value="v2.1.0"
                class="input input-bordered"
                readonly
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Última Atualização</span>
              </label>
              <input
                type="text"
                value="15 de Janeiro, 2024"
                class="input input-bordered"
                readonly
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Ambiente</span>
              </label>
              <div class="badge badge-success">Produção</div>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Região</span>
              </label>
              <input
                type="text"
                value="São Paulo, Brasil"
                class="input input-bordered"
                readonly
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Data Management -->
      <div class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <h3 class="card-title mb-4">Gerenciamento de Dados</h3>

          <div class="space-y-4">
            <div class="alert alert-warning">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clip-rule="evenodd"
                ></path>
              </svg>
              <div>
                <h4 class="font-bold">Atenção!</h4>
                <div class="text-sm">
                  As operações abaixo são irreversíveis. Certifique-se antes de
                  prosseguir.
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="card bg-base-100">
                <div class="card-body">
                  <h4 class="card-title text-base">Exportar Dados</h4>
                  <p class="text-sm text-base-content/70">
                    Baixe todos os seus dados em formato JSON
                  </p>
                  <div class="card-actions justify-end">
                    <button
                      class="btn btn-primary btn-sm"
                      @click="exportAllData"
                    >
                      Exportar
                    </button>
                  </div>
                </div>
              </div>

              <div class="card bg-base-100">
                <div class="card-body">
                  <h4 class="card-title text-base">Limpar Cache</h4>
                  <p class="text-sm text-base-content/70">
                    Remove dados temporários e cache do sistema
                  </p>
                  <div class="card-actions justify-end">
                    <button
                      class="btn btn-secondary btn-sm"
                      @click="clearCache"
                    >
                      Limpar
                    </button>
                  </div>
                </div>
              </div>

              <div class="card bg-base-100">
                <div class="card-body">
                  <h4 class="card-title text-base">Reprocessar Dados</h4>
                  <p class="text-sm text-base-content/70">
                    Reprocessa todos os arquivos XML com novos algoritmos
                  </p>
                  <div class="card-actions justify-end">
                    <button
                      class="btn btn-warning btn-sm"
                      @click="reprocessData"
                    >
                      Reprocessar
                    </button>
                  </div>
                </div>
              </div>

              <div class="card bg-base-100">
                <div class="card-body">
                  <h4 class="card-title text-base text-error">Excluir Conta</h4>
                  <p class="text-sm text-base-content/70">
                    Remove permanentemente sua conta e todos os dados
                  </p>
                  <div class="card-actions justify-end">
                    <button class="btn btn-error btn-sm" @click="deleteAccount">
                      Excluir
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Import Settings Modal -->
    <input
      ref="fileInput"
      type="file"
      accept=".json"
      class="hidden"
      @change="handleFileImport"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

definePageMeta({
  layout: "default",
});

// Reactive state
const activeTab = ref("preferences");
const fileInput = ref<HTMLInputElement>();

const passwordForm = ref({
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const emailConfig = ref({
  smtpServer: "",
  port: 587,
  fromEmail: "",
  password: "",
});

const apiKeys = ref([
  {
    id: "1",
    name: "Chave Principal",
    key: "sk_live_1234567890abcdef...",
    createdAt: new Date("2024-01-15"),
  },
  {
    id: "2",
    name: "Chave de Desenvolvimento",
    key: "sk_test_abcdef1234567890...",
    createdAt: new Date("2024-01-10"),
  },
]);

// Methods
const handleSavePreferences = (data: any) => {
  console.log("Saving preferences:", data);
  // Here you would integrate with Supabase to save user preferences
};

const handleResetPreferences = () => {
  console.log("Resetting preferences to defaults");
};

const importSettings = () => {
  fileInput.value?.click();
};

const handleFileImport = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const settings = JSON.parse(e.target?.result as string);
        console.log("Importing settings:", settings);
        alert("Configurações importadas com sucesso!");
      } catch (error) {
        alert(
          "Erro ao importar configurações. Verifique o formato do arquivo."
        );
      }
    };
    reader.readAsText(file);
  }
};

const formatDate = (date: Date): string => {
  return date.toLocaleDateString("pt-BR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

const changePassword = () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    alert("As senhas não coincidem!");
    return;
  }

  console.log("Changing password...");
  alert("Senha alterada com sucesso!");

  // Reset form
  passwordForm.value = {
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  };
};

const generateApiKey = () => {
  const newKey = {
    id: Date.now().toString(),
    name: `Chave ${apiKeys.value.length + 1}`,
    key: `sk_live_${Math.random().toString(36).substring(2)}...`,
    createdAt: new Date(),
  };

  apiKeys.value.push(newKey);
  alert("Nova chave de API gerada!");
};

const copyApiKey = (key: string) => {
  navigator.clipboard.writeText(key);
  alert("Chave copiada para a área de transferência!");
};

const regenerateApiKey = (id: string) => {
  if (
    confirm(
      "Tem certeza que deseja regenerar esta chave? A chave atual será invalidada."
    )
  ) {
    const keyIndex = apiKeys.value.findIndex((k) => k.id === id);
    if (keyIndex > -1) {
      apiKeys.value[keyIndex].key = `sk_live_${Math.random()
        .toString(36)
        .substring(2)}...`;
      alert("Chave regenerada com sucesso!");
    }
  }
};

const deleteApiKey = (id: string) => {
  if (confirm("Tem certeza que deseja excluir esta chave?")) {
    const keyIndex = apiKeys.value.findIndex((k) => k.id === id);
    if (keyIndex > -1) {
      apiKeys.value.splice(keyIndex, 1);
      alert("Chave excluída com sucesso!");
    }
  }
};

const exportAllData = () => {
  console.log("Exporting all data...");
  alert("Exportação iniciada. Você receberá um e-mail quando estiver pronta.");
};

const clearCache = () => {
  if (confirm("Tem certeza que deseja limpar o cache?")) {
    console.log("Clearing cache...");
    alert("Cache limpo com sucesso!");
  }
};

const reprocessData = () => {
  if (
    confirm(
      "Tem certeza que deseja reprocessar todos os dados? Esta operação pode levar alguns minutos."
    )
  ) {
    console.log("Reprocessing data...");
    alert("Reprocessamento iniciado. Você será notificado quando concluído.");
  }
};

const deleteAccount = () => {
  const confirmation = prompt(
    'Digite "EXCLUIR" para confirmar a exclusão permanente da conta:'
  );
  if (confirmation === "EXCLUIR") {
    console.log("Deleting account...");
    alert("Conta excluída. Você será redirecionado para a página inicial.");
  }
};
</script>
