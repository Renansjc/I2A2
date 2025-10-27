# Sistema I2A2 - Frontend

Frontend do Sistema de Análise de Notas Fiscais com IA, construído com Nuxt.js 4, Vue 3, TypeScript, Tailwind CSS e DaisyUI.

## Funcionalidades

- **Navegação por Sidebar**: Menu lateral responsivo com navegação principal
- **Página de Notas Fiscais**: Visualização em formato tabular similar ao Excel com:
  - Filtros por tipo, status e período
  - Busca por número, CNPJ ou razão social
  - Ações de visualizar, editar e excluir
  - Seleção múltipla para ações em lote
  - Paginação
- **Toggle Dark/Light Mode**: Alternância de tema no canto superior direito
- **Temas Customizados**: Temas light e dark personalizados com DaisyUI
- **Interface Responsiva**: Adaptável para desktop e mobile

## Estrutura de Páginas

- `/` - Painel principal com estatísticas e consultas
- `/invoices` - Lista de notas fiscais
- `/invoices/[id]` - Detalhes de uma nota fiscal específica
- `/upload` - Upload de arquivos XML
- `/reports` - Geração de relatórios
- `/analytics` - Análises e insights

## Tecnologias

- **Nuxt.js 4** - Framework Vue.js com SSR/SSG
- **Vue 3** - Framework JavaScript reativo
- **TypeScript** - Tipagem estática
- **Tailwind CSS 4** - Framework CSS utilitário
- **DaisyUI** - Componentes UI para Tailwind CSS

## Setup

Make sure to install dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.
