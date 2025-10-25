# AI Agents Invoice Analysis System - Frontend

Executive interface built with Next.js 14, TypeScript, and Shadcn/ui for C-level professionals to interact with the AI Agents Invoice Analysis System.

## Features

### Executive Dashboard
- Real-time fiscal data visualization
- Key performance indicators (KPIs)
- Supplier and product analytics
- Tax analysis and trends

### Natural Language Queries
- Intuitive query interface for business questions
- Real-time query suggestions and auto-completion
- Query history and favorites management
- Preview and confirmation workflow

### Report Management
- Multi-format report generation (.xlsx, .pdf, .docx)
- Executive-level report templates
- Report scheduling and automation
- Report preview and download

### File Management
- Drag-and-drop XML file upload
- Processing status tracking
- File history and management
- Bulk upload capabilities

### User Management
- Supabase Auth integration
- Role-based access control (CEO, CFO, COO)
- User profile management
- Session management with automatic logout

## Technology Stack

- **Next.js 14+**: React framework with App Router
- **TypeScript**: Type-safe development
- **Shadcn/ui**: Modern component library
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Data visualization library
- **Supabase**: Authentication and database
- **Zustand**: State management
- **React Dropzone**: File upload functionality

## Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── ui/               # Shadcn/ui components
│   │   ├── dashboard/        # Dashboard components
│   │   ├── reports/          # Report components
│   │   └── auth/             # Authentication components
│   ├── lib/                  # Utility functions
│   │   ├── utils.ts          # General utilities
│   │   ├── supabase.ts       # Supabase client
│   │   └── api.ts            # API client
│   ├── hooks/                # Custom React hooks
│   │   ├── useAuth.ts        # Authentication hook
│   │   ├── useQuery.ts       # Query management hook
│   │   └── useReports.ts     # Report management hook
│   ├── types/                # TypeScript type definitions
│   │   ├── fiscal.ts         # Fiscal data types
│   │   ├── auth.ts           # Authentication types
│   │   └── api.ts            # API response types
│   └── utils/                # Utility functions
│       ├── formatters.ts     # Data formatters
│       ├── validators.ts     # Input validation
│       └── constants.ts      # Application constants
├── public/                   # Static assets
├── package.json             # Dependencies and scripts
├── tailwind.config.js       # Tailwind configuration
├── tsconfig.json           # TypeScript configuration
└── next.config.js          # Next.js configuration
```

## Installation

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Configuration

### Environment Variables (.env.local)

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Application Configuration
NEXT_PUBLIC_APP_NAME="AI Agents Invoice Analysis System"
NEXT_PUBLIC_APP_VERSION="1.0.0"
```

## Development

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint

# Type checking
npm run type-check
```

### Component Development

#### Using Shadcn/ui Components
```tsx
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Executive Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        <Button>Generate Report</Button>
      </CardContent>
    </Card>
  )
}
```

#### Custom Hooks
```tsx
// hooks/useQuery.ts
import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/api'

export function useQuery() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const executeQuery = useCallback(async (query: string) => {
    setLoading(true)
    try {
      const response = await apiClient.post('/query/natural-language', { text: query })
      setResults(response.data)
    } finally {
      setLoading(false)
    }
  }, [])

  return { executeQuery, loading, results }
}
```

## Features Implementation

### Dashboard Components

#### KPI Cards
```tsx
// components/dashboard/KPICard.tsx
interface KPICardProps {
  title: string
  value: string | number
  change?: number
  icon: React.ReactNode
}

export function KPICard({ title, value, change, icon }: KPICardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <p className={`text-xs ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change > 0 ? '+' : ''}{change}% from last month
          </p>
        )}
      </CardContent>
    </Card>
  )
}
```

#### Data Visualization
```tsx
// components/dashboard/TaxChart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface TaxChartProps {
  data: Array<{
    period: string
    icms: number
    ipi: number
    pis: number
    cofins: number
    issqn: number
  }>
}

export function TaxChart({ data }: TaxChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="period" />
        <YAxis />
        <Tooltip formatter={(value) => [`R$ ${value.toLocaleString()}`, '']} />
        <Bar dataKey="icms" fill="#8884d8" name="ICMS" />
        <Bar dataKey="ipi" fill="#82ca9d" name="IPI" />
        <Bar dataKey="pis" fill="#ffc658" name="PIS" />
        <Bar dataKey="cofins" fill="#ff7300" name="COFINS" />
        <Bar dataKey="issqn" fill="#00ff00" name="ISSQN" />
      </BarChart>
    </ResponsiveContainer>
  )
}
```

### Query Interface

#### Natural Language Query Component
```tsx
// components/query/QueryInterface.tsx
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useQuery } from '@/hooks/useQuery'

export function QueryInterface() {
  const [query, setQuery] = useState('')
  const { executeQuery, loading, results } = useQuery()

  const handleSubmit = async () => {
    if (query.trim()) {
      await executeQuery(query)
    }
  }

  return (
    <div className="space-y-4">
      <Textarea
        placeholder="Ask a question about your fiscal data..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={4}
      />
      <Button onClick={handleSubmit} disabled={loading}>
        {loading ? 'Processing...' : 'Execute Query'}
      </Button>
      {results && (
        <div className="mt-4 p-4 border rounded-lg">
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
```

### File Upload

#### XML Upload Component
```tsx
// components/upload/XMLUpload.tsx
import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload } from 'lucide-react'

export function XMLUpload() {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      // Handle file upload
      console.log('Uploading:', file.name)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/xml': ['.xml']
    }
  })

  return (
    <div
      {...getRootProps()}
      className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-gray-400"
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
      {isDragActive ? (
        <p>Drop the XML files here...</p>
      ) : (
        <p>Drag and drop XML files here, or click to select</p>
      )}
    </div>
  )
}
```

## Authentication

### Supabase Auth Integration
```tsx
// lib/supabase.ts
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export const supabase = createClientComponentClient()

// hooks/useAuth.ts
import { useEffect, useState } from 'react'
import { User } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
      setLoading(false)
    }

    getUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null)
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  return { user, loading }
}
```

## State Management

### Zustand Store
```tsx
// lib/store.ts
import { create } from 'zustand'

interface AppState {
  user: User | null
  queries: Query[]
  reports: Report[]
  setUser: (user: User | null) => void
  addQuery: (query: Query) => void
  addReport: (report: Report) => void
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  queries: [],
  reports: [],
  setUser: (user) => set({ user }),
  addQuery: (query) => set((state) => ({ queries: [...state.queries, query] })),
  addReport: (report) => set((state) => ({ reports: [...state.reports, report] })),
}))
```

## API Integration

### API Client
```tsx
// lib/api.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('supabase.auth.token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

## Styling

### Tailwind CSS Classes
- Use semantic class names for consistency
- Follow the design system defined in `tailwind.config.js`
- Utilize Shadcn/ui components for common UI elements

### Custom Styles
```css
/* globals.css */
.executive-card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.metric-value {
  @apply text-3xl font-bold text-gray-900;
}

.metric-label {
  @apply text-sm font-medium text-gray-500 uppercase tracking-wide;
}
```

## Testing

### Component Testing
```tsx
// __tests__/components/KPICard.test.tsx
import { render, screen } from '@testing-library/react'
import { KPICard } from '@/components/dashboard/KPICard'

describe('KPICard', () => {
  it('renders title and value', () => {
    render(
      <KPICard
        title="Total Revenue"
        value="R$ 1,000,000"
        icon={<div>Icon</div>}
      />
    )

    expect(screen.getByText('Total Revenue')).toBeInTheDocument()
    expect(screen.getByText('R$ 1,000,000')).toBeInTheDocument()
  })
})
```

## Deployment

### Vercel Deployment
1. Connect repository to Vercel
2. Configure environment variables
3. Deploy automatically on push to main branch

### Build Optimization
- Enable Next.js image optimization
- Configure proper caching headers
- Optimize bundle size with tree shaking

## Performance

### Optimization Strategies
- Use Next.js Image component for optimized images
- Implement proper loading states
- Use React.memo for expensive components
- Implement virtual scrolling for large datasets

### Monitoring
- Implement error boundaries
- Use Sentry for error tracking
- Monitor Core Web Vitals
- Track user interactions and performance metrics