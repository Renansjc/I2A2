<template>
  <div class="min-h-screen bg-base-100 flex">
    <!-- Sidebar -->
    <div class="drawer lg:drawer-open">
      <input id="drawer-toggle" type="checkbox" class="drawer-toggle" />
      
      <!-- Sidebar -->
      <div class="drawer-side">
        <label for="drawer-toggle" aria-label="close sidebar" class="drawer-overlay"></label>
        <aside class="min-h-full w-64 bg-base-200 text-base-content">
          <!-- Logo -->
          <div class="p-4 border-b border-base-300">
            <NuxtLink to="/" class="text-xl font-bold text-primary">
              Sistema I2A2
            </NuxtLink>
            <p class="text-sm text-base-content/70 mt-1">Análise de Notas Fiscais</p>
          </div>
          
          <!-- Navigation Menu -->
          <ul class="menu p-4 space-y-2">
            <li>
              <NuxtLink to="/" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z"></path>
                </svg>
                Painel
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/invoices" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                Notas Fiscais
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/upload" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                Enviar XML
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/reports" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
                Relatórios
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/search" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                Busca Avançada
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/analytics" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                Análises
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/settings" class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-300 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                Configurações
              </NuxtLink>
            </li>

          </ul>
        </aside>
      </div>
      
      <!-- Main Content -->
      <div class="drawer-content flex flex-col flex-1">
        <!-- Top Header -->
        <header class="navbar bg-base-100 border-b border-base-300 px-4">
          <div class="navbar-start">
            <label for="drawer-toggle" class="btn btn-square btn-ghost lg:hidden">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
              </svg>
            </label>
          </div>
          
          <div class="navbar-end gap-4">
            <!-- Theme Toggle -->
            <ThemeToggle />
            
            <!-- User Menu -->
            <div class="dropdown dropdown-end">
              <div tabindex="0" role="button" class="btn btn-ghost btn-circle avatar">
                <div class="w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span v-if="userInfo?.initials" class="text-primary font-semibold text-sm">
                    {{ userInfo.initials }}
                  </span>
                  <svg v-else class="w-6 h-6 text-primary" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path>
                  </svg>
                </div>
              </div>
              <ul tabindex="0" class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52 border border-base-300">
                <li class="menu-title">
                  <span class="text-xs">{{ userInfo?.name }}</span>
                  <span class="text-xs text-base-content/50">{{ getRoleDisplayName(userInfo?.role) }}</span>
                </li>
                <li><a class="text-base-content">Perfil (Em breve)</a></li>
                <li><NuxtLink to="/settings" class="text-base-content">Configurações</NuxtLink></li>
                <li><hr class="my-1"></li>
                <li>
                  <button @click="handleSignOut" class="text-base-content/50" disabled>
                    <span>Sair (Desabilitado)</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </header>

        <!-- Page Content -->
        <main class="flex-1 p-6 bg-base-50">
          <slot />
        </main>

        <!-- Footer -->
        <footer class="footer footer-center p-4 bg-base-200 text-base-content border-t border-base-300">
          <aside>
            <p class="text-sm">© 2025 - Sistema de Análise de Notas Fiscais com IA</p>
          </aside>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Layout setup for executive interface

// Mock user info for development
const userInfo = ref({
  name: 'Administrador',
  initials: 'AD',
  role: 'ceo'
})

const isSigningOut = ref(false)

const getRoleDisplayName = (role: string) => {
  const roleNames = {
    'ceo': 'CEO',
    'cfo': 'CFO',
    'coo': 'COO',
    'finance_director': 'Diretor Financeiro',
    'finance_manager': 'Gerente Financeiro',
    'controller': 'Controller',
    'analyst': 'Analista Financeiro',
    'other': 'Outro'
  }
  return roleNames[role as keyof typeof roleNames] || 'Usuário'
}

// Methods
const handleSignOut = async () => {
  console.log('Sign out (funcionalidade desabilitada)')
}
</script>