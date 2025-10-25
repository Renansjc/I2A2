# AI Agents Invoice System - Makefile

.PHONY: help install dev-setup redis-start redis-stop redis-test clean

# Cores para output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(BLUE)AI Agents Invoice System - Comandos Disponíveis$(NC)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependências Python
	@echo "$(YELLOW)📦 Instalando dependências...$(NC)"
	cd backend && pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependências instaladas!$(NC)"

dev-setup: install ## Configuração completa para desenvolvimento
	@echo "$(YELLOW)🛠️ Configurando ambiente de desenvolvimento...$(NC)"
	@if [ ! -f backend/.env ]; then \
		echo "$(YELLOW)📝 Criando arquivo .env...$(NC)"; \
		cp backend/.env backend/.env.example 2>/dev/null || true; \
	fi
	@echo "$(GREEN)✅ Ambiente configurado!$(NC)"

redis-start: ## Inicia Redis com Docker
	@echo "$(YELLOW)🚀 Iniciando Redis...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Redis iniciado!$(NC)"
	@echo "$(BLUE)📊 Redis Commander: http://localhost:8081$(NC)"

redis-stop: ## Para Redis
	@echo "$(YELLOW)🛑 Parando Redis...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Redis parado!$(NC)"

redis-test: ## Testa conexão com Redis
	@echo "$(YELLOW)🧪 Testando Redis...$(NC)"
	cd backend && python test_redis.py

redis-logs: ## Mostra logs do Redis
	docker-compose -f docker-compose.dev.yml logs -f redis

redis-cli: ## Conecta ao Redis CLI
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

clean: ## Limpa containers e volumes Docker
	@echo "$(YELLOW)🧹 Limpando containers e volumes...$(NC)"
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

# Comandos para Windows (usando PowerShell)
install-win: ## Instala dependências (Windows)
	@powershell -Command "cd backend; pip install -r requirements.txt"

redis-start-win: ## Inicia Redis (Windows)
	@powershell -Command "docker-compose -f docker-compose.dev.yml up -d"

redis-test-win: ## Testa Redis (Windows)
	@powershell -Command "cd backend; python test_redis.py"