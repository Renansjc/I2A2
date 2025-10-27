@echo off
echo ========================================
echo   MVP Sistema Simplificado Setup
echo ========================================
echo.

echo 🔧 Criando ambiente virtual Python 3.12...
py -3.12 -m venv backend\venv
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar ambiente virtual
    pause
    exit /b 1
)

echo ✅ Ambiente virtual criado!
echo.

echo 📦 Ativando ambiente e instalando dependências...
call backend\venv\Scripts\activate.bat
cd backend
pip install --upgrade pip
pip install -r requirements_minimal.txt
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)

echo ✅ Dependências instaladas!
echo.

echo 📄 Configurando arquivo .env...
if not exist .env (
    copy .env.example .env
    echo ⚠️  Configure OPENAI_API_KEY no arquivo .env
) else (
    echo ✅ Arquivo .env já existe
)

echo.
echo 🧪 Testando servidor...
timeout /t 2 /nobreak > nul
python test_mvp.py

echo.
echo ========================================
echo   Setup Concluído!
echo ========================================
echo.
echo 📋 Próximos passos:
echo   1. Configure OPENAI_API_KEY no backend\.env
echo   2. Execute: cd backend ^&^& activate_venv.bat
echo   3. Inicie: python main.py
echo   4. Teste: python test_mvp.py
echo.
echo 🌐 Frontend: cd frontend ^&^& npm install ^&^& npm run dev
echo.
pause