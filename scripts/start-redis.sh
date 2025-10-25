#!/bin/bash

# Script para iniciar o Redis em desenvolvimento
echo "🚀 Iniciando Redis para desenvolvimento..."

# Verifica se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Para containers existentes
echo "🛑 Parando containers existentes..."
docker-compose -f docker-compose.dev.yml down

# Inicia os serviços
echo "▶️ Iniciando Redis e Redis Commander..."
docker-compose -f docker-compose.dev.yml up -d

# Aguarda o Redis ficar pronto
echo "⏳ Aguardando Redis ficar pronto..."
timeout=30
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose -f docker-compose.dev.yml exec redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis está pronto!"
        break
    fi
    sleep 1
    counter=$((counter + 1))
done

if [ $counter -eq $timeout ]; then
    echo "❌ Timeout aguardando Redis ficar pronto"
    exit 1
fi

echo ""
echo "🎉 Redis está rodando!"
echo "📊 Redis Commander: http://localhost:8081 (admin/admin)"
echo "🔗 Redis URL: redis://localhost:6379"
echo ""
echo "Para parar: docker-compose -f docker-compose.dev.yml down"
echo "Para logs: docker-compose -f docker-compose.dev.yml logs -f"