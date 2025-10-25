# Docker Setup - AI Agents Invoice System

Este diretório contém a configuração Docker para o sistema de análise de faturas com agentes de IA.

## 🐳 Serviços Disponíveis

### Redis
- **Porta**: 6379
- **Uso**: Cache, filas de tarefas, comunicação entre agentes
- **Versão**: Redis 7 Alpine
- **Persistência**: Dados salvos em volume Docker

### Redis Commander (Opcional)
- **Porta**: 8081
- **Uso**: Interface web para monitorar Redis
- **Credenciais**: admin/admin (apenas em desenvolvimento)

## 🚀 Como Usar

### Opção 1: Scripts Automatizados

**Windows:**
```bash
scripts/start-redis.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/start-redis.sh
./scripts/start-redis.sh
```

### Opção 2: Docker Compose Manual

**Desenvolvimento:**
```bash
# Iniciar
docker-compose -f docker-compose.dev.yml up -d

# Parar
docker-compose -f docker-compose.dev.yml down

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f
```

**Produção:**
```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Ver logs
docker-compose logs -f
```

## 🔧 Configuração

### Variáveis de Ambiente

O Redis está configurado para usar a URL padrão:
```
REDIS_URL=redis://localhost:6379
```

### Volumes

- **Desenvolvimento**: `redis_dev_data`
- **Produção**: `redis_data`

Os dados são persistidos automaticamente.

## 🛠️ Comandos Úteis

### Conectar ao Redis CLI
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli
```

### Monitorar Redis
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli monitor
```

### Ver informações do Redis
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli info
```

### Limpar cache Redis
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli flushall
```

## 📊 Monitoramento

### Redis Commander
Acesse http://localhost:8081 para uma interface web completa do Redis.

### Health Check
O Redis tem health check configurado que verifica a cada 5-10 segundos.

## 🔒 Segurança

### Desenvolvimento
- Redis Commander protegido com usuário/senha básicos
- Redis sem autenticação (apenas localhost)

### Produção
- Considere adicionar autenticação Redis
- Use redes Docker isoladas
- Configure firewall adequadamente

## 🐛 Troubleshooting

### Redis não inicia
```bash
# Verificar logs
docker-compose -f docker-compose.dev.yml logs redis

# Verificar se a porta está em uso
netstat -an | grep 6379
```

### Problemas de conexão
```bash
# Testar conectividade
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# Verificar configuração de rede
docker network ls
```

### Limpar tudo
```bash
# Parar e remover containers, volumes e redes
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f
```