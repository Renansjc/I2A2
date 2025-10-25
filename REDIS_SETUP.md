# 🚀 Redis Setup - AI Agents Invoice System

Configuração completa do Redis para o sistema de análise de faturas com agentes de IA.

## ✅ Status da Instalação

- ✅ Docker Compose configurado
- ✅ Redis 7 Alpine rodando na porta 6379
- ✅ Redis Commander disponível na porta 8081
- ✅ Conexão testada e funcionando
- ✅ Variável de ambiente configurada: `REDIS_URL=redis://localhost:6379`

## 🐳 Serviços Rodando

### Redis
- **Container**: `ai-agents-redis-dev`
- **Porta**: 6379
- **Versão**: Redis 7.4.6
- **Persistência**: Volume Docker `redis_dev_data`
- **Health Check**: Ativo (ping a cada 5s)

### Redis Commander
- **Container**: `ai-agents-redis-commander-dev`
- **Porta**: 8081
- **URL**: http://localhost:8081
- **Credenciais**: admin/admin
- **Interface**: Web para monitoramento

## 🎯 Como Usar

### Iniciar Redis
```bash
# Opção 1: Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Opção 2: Script Windows
scripts/start-redis.bat

# Opção 3: Script Linux/Mac
./scripts/start-redis.sh
```

### Parar Redis
```bash
docker-compose -f docker-compose.dev.yml down
```

### Testar Conexão
```bash
cd backend
python test_redis.py
```

## 📊 Monitoramento

### Redis Commander (Interface Web)
- Acesse: http://localhost:8081
- Usuário: `admin`
- Senha: `admin`

### Comandos CLI
```bash
# Conectar ao Redis CLI
docker-compose -f docker-compose.dev.yml exec redis redis-cli

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f redis

# Monitorar comandos em tempo real
docker-compose -f docker-compose.dev.yml exec redis redis-cli monitor

# Informações do servidor
docker-compose -f docker-compose.dev.yml exec redis redis-cli info
```

## 🔧 Configuração

### Variáveis de Ambiente
O arquivo `backend/.env` já está configurado com:
```env
REDIS_URL=redis://localhost:6379
```

### Configuração Docker
- **Rede**: `ai-agents-dev-network`
- **Volume**: `redis_dev_data` (persistente)
- **Memória**: Limitada a 256MB
- **Política**: `allkeys-lru` (remove chaves menos usadas)

## 🛠️ Comandos Úteis

### Makefile (se disponível)
```bash
make redis-start    # Inicia Redis
make redis-stop     # Para Redis
make redis-test     # Testa conexão
make redis-logs     # Ver logs
make redis-cli      # Conectar CLI
```

### Limpeza Completa
```bash
# Para containers e remove volumes
docker-compose -f docker-compose.dev.yml down -v

# Limpeza geral do Docker
docker system prune -f
```

## 🔍 Troubleshooting

### Redis não inicia
1. Verificar se Docker está rodando
2. Verificar se porta 6379 está livre
3. Ver logs: `docker-compose -f docker-compose.dev.yml logs redis`

### Problemas de conexão
1. Testar ping: `docker-compose -f docker-compose.dev.yml exec redis redis-cli ping`
2. Verificar variável REDIS_URL no .env
3. Executar teste: `python backend/test_redis.py`

### Porta em uso
```bash
# Windows
netstat -an | findstr 6379

# Linux/Mac
netstat -an | grep 6379
```

## 📁 Arquivos Criados

```
├── docker-compose.yml              # Configuração produção
├── docker-compose.dev.yml          # Configuração desenvolvimento
├── scripts/
│   ├── start-redis.sh              # Script Linux/Mac
│   └── start-redis.bat             # Script Windows
├── docker/
│   └── README.md                   # Documentação Docker
├── backend/
│   └── test_redis.py               # Teste de conexão
├── Makefile                        # Comandos automatizados
└── REDIS_SETUP.md                  # Esta documentação
```

## 🎉 Próximos Passos

Com o Redis funcionando, você pode:

1. **Implementar Cache**: Usar Redis para cache de dados
2. **Filas de Tarefas**: Configurar Celery com Redis
3. **Sessões**: Armazenar sessões de usuário
4. **Comunicação entre Agentes**: Usar pub/sub do Redis
5. **Métricas**: Armazenar métricas temporárias

## 🔗 Links Úteis

- **Redis Commander**: http://localhost:8081
- **Documentação Redis**: https://redis.io/docs/
- **Docker Compose**: https://docs.docker.com/compose/