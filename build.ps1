# Gera o executável do Gerador de Recibos
# Uso: .\build.ps1

$ErrorActionPreference = "Stop"

# Ativa o ambiente virtual
& .\.venv\Scripts\Activate.ps1

pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "GeradorRecibos" `
    --icon "assets\icon.ico" `
    --add-data "assets\icon.ico;assets" `
    --version-file "version_info.txt" `
    --collect-submodules num2words `
    main.py

Write-Host ""
Write-Host "Pronto! Executavel em: dist\GeradorRecibos.exe" -ForegroundColor Green