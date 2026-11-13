@echo off
setlocal
cd /d "%~dp0"
echo PRECIFICA PRO 5.0 CLARITY - Iniciando seu espaco de trabalho...
where python >nul 2>nul
if errorlevel 1 (
 echo Instale Python 3.10 ou superior e marque Add Python to PATH.
 pause
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
 python -m venv .venv
 if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
if not exist "frontend\dist\index.html" (
 where npm >nul 2>nul
 if errorlevel 1 (
  echo Compilacao ausente. Instale Node.js 20 ou superior para compilar.
  goto erro
 )
 pushd frontend
 call npm ci
 if errorlevel 1 goto erro_frontend
 call npm run build
 if errorlevel 1 goto erro_frontend
 popd
)
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto erro
goto fim
:erro_frontend
popd
:erro
echo Nao foi possivel iniciar. Confira a mensagem acima.
pause
exit /b 1
:fim
endlocal
