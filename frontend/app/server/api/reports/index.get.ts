export default defineEventHandler(async (event) => {
  // Mock API endpoint for getting reports
  // In a real implementation, this would connect to your backend API
  
  const mockReports = [
    {
      id: '1',
      name: 'Análise de Fornecedores T4',
      description: 'Revisão trimestral de desempenho de fornecedores',
      type: 'Financeiro',
      templateId: '1',
      generatedAt: new Date('2024-01-15T10:30:00'),
      completedAt: new Date('2024-01-15T10:35:00'),
      status: 'completed',
      fileSize: 2048576, // 2MB
      downloadCount: 5,
      lastDownloaded: new Date('2024-01-20T14:20:00'),
      formats: ['pdf', 'xlsx'],
      downloadUrls: {
        pdf: '/api/reports/1/download/pdf',
        xlsx: '/api/reports/1/download/xlsx'
      },
      executionTime: 300, // 5 minutes
      config: {
        startDate: '2023-10-01',
        endDate: '2023-12-31',
        formats: ['pdf', 'xlsx'],
        filters: {
          documentTypes: ['nfe', 'nfse'],
          states: 'SP,RJ,MG',
          minValue: 1000
        }
      }
    },
    {
      id: '2',
      name: 'Relatório Fiscal Dezembro',
      description: 'Análise mensal de eficiência fiscal',
      type: 'Fiscal',
      templateId: '2',
      generatedAt: new Date('2024-01-10T09:15:00'),
      completedAt: new Date('2024-01-10T09:18:00'),
      status: 'completed',
      fileSize: 1536000, // 1.5MB
      downloadCount: 3,
      lastDownloaded: new Date('2024-01-18T11:45:00'),
      formats: ['pdf'],
      downloadUrls: {
        pdf: '/api/reports/2/download/pdf'
      },
      executionTime: 180, // 3 minutes
      config: {
        startDate: '2023-12-01',
        endDate: '2023-12-31',
        formats: ['pdf'],
        filters: {
          documentTypes: ['nfe', 'nfse']
        }
      }
    },
    {
      id: '3',
      name: 'Tendências de Produtos 2024',
      description: 'Análise anual de categorias de produtos',
      type: 'Análises',
      templateId: '3',
      generatedAt: new Date('2024-01-08T16:00:00'),
      status: 'processing',
      progress: 75,
      formats: ['pdf', 'xlsx'],
      downloadUrls: {},
      downloadCount: 0,
      config: {
        startDate: '2023-01-01',
        endDate: '2023-12-31',
        formats: ['pdf', 'xlsx'],
        filters: {
          documentTypes: ['nfe'],
          categories: ['Eletrônicos', 'Alimentação']
        }
      }
    }
  ]

  return {
    success: true,
    data: mockReports,
    total: mockReports.length
  }
})