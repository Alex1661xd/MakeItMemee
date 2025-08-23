# Script de inicio para Windows PowerShell
Write-Host "Iniciando Make It Meme en modo desarrollo..." -ForegroundColor Green

# Verificar si Python esta instalado
try {
    python --version | Out-Null
    Write-Host "Python encontrado" -ForegroundColor Green
} catch {
    Write-Host "Python no encontrado. Por favor instala Python 3.8 o superior." -ForegroundColor Red
    exit 1
}

# Activar entorno virtual si existe
if (Test-Path "venv") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Verificar que las dependencias esten instaladas
Write-Host "Verificando dependencias..." -ForegroundColor Blue
python verify_setup.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Todo listo! Ejecutando la aplicacion..." -ForegroundColor Green
    python run.py
} else {
    Write-Host "Error en la verificacion. Revisa la configuracion." -ForegroundColor Red
    exit 1
}
