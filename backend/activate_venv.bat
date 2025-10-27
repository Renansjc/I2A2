@echo off
echo Ativando ambiente virtual Python 3.12...
call venv\Scripts\activate.bat
echo.
echo ✅ Ambiente virtual ativado!
echo 📁 Diretório: %CD%
echo 🐍 Python: 
python --version
echo.
echo 🚀 Para iniciar o servidor: python main.py
echo 🧪 Para testar a API: python test_mvp.py
echo 📦 Para instalar dependências: pip install -r requirements.txt
echo.
cmd /k