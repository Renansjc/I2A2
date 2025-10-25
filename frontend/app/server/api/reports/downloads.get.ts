export default defineEventHandler(async (event) => {
  // Mock API endpoint for getting download history
  // In a real implementation, this would connect to your backend API
  
  const mockDownloads = [
    {
      id: '1',
      reportId: '1',
      reportName: 'Análise de Fornecedores T4',
      format: 'pdf',
      downloadedAt: new Date('2024-01-20T14:20:00'),
      fileSize: 2048576,
      downloadUrl: '/api/reports/1/download/pdf',
      expiresAt: new Date('2024-01-27T14:20:00')
    },
    {
      id: '2',
      reportId: '1',
      reportName: 'Análise de Fornecedores T4',
      format: 'xlsx',
      downloadedAt: new Date('2024-01-19T10:15:00'),
      fileSize: 1024000,
      downloadUrl: '/api/reports/1/download/xlsx',
      expiresAt: new Date('2024-01-26T10:15:00')
    },
    {
      id: '3',
      reportId: '2',
      reportName: 'Relatório Fiscal Dezembro',
      format: 'pdf',
      downloadedAt: new Date('2024-01-18T11:45:00'),
      fileSize: 1536000,
      downloadUrl: '/api/reports/2/download/pdf',
      expiresAt: new Date('2024-01-25T11:45:00')
    },
    {
      id: '4',
      reportId: '1',
      reportName: 'Análise de Fornecedores T4',
      format: 'pdf',
      downloadedAt: new Date('2024-01-17T16:30:00'),
      fileSize: 2048576,
      downloadUrl: '/api/reports/1/download/pdf',
      expiresAt: new Date('2024-01-24T16:30:00')
    },
    {
      id: '5',
      reportId: '2',
      reportName: 'Relatório Fiscal Dezembro',
      format: 'pdf',
      downloadedAt: new Date('2024-01-16T09:20:00'),
      fileSize: 1536000,
      downloadUrl: '/api/reports/2/download/pdf',
      expiresAt: new Date('2024-01-23T09:20:00')
    }
  ]

  return {
    success: true,
    data: mockDownloads,
    total: mockDownloads.length
  }
})