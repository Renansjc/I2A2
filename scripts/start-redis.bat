@echo off
REM Script para iniciar o Redis em desenvolvimento no Windows

echo 🚀 Iniciando Redis para desenvolvimento...

REM Verifica se o Docker está rodando
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker não está rodando. Por favor, inicie o Docker primeiro.
    pause
    exit /b 1
)

REM Para containers existentes
echo 🛑 Parando containers existentes...
docker-compose -f docker-compose.dev.yml down

REM Inicia os serviços
echo ▶️ Iniciando Redis e Redis Commander...
docker-compose -f docker-compose.dev.yml up -d

REM Aguarda o Redis ficar pronto
echo ⏳ Aguardando Redis ficar pronto...
set timeout=30
set counter=0

:wait_loop
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis está pronto!
    goto ready
)

timeout /t 1 /nobreak >nul
set /a counter+=1
if %counter% lss %timeout% goto wait_loop

echo ❌ Timeout aguardando Redis ficar pronto
pause
exit /b 1

:ready
echo.
echo 🎉 Redis está rodando!
echo 📊 Redis Commander: http://localhost:8081 (admin/admin)
echo 🔗 Redis URL: redis://localhost:6379
echo.
echo Para parar: docker-compose -f docker-compose.dev.yml down
echo Para logs: docker-compose -f docker-compose.dev.yml logs -f
echo.
pause