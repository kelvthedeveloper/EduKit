# Django 数据库迁移 (Windows PowerShell)
# 用法: .\scripts\migrate.ps1

Write-Host "=== 执行数据库迁移 ===" -ForegroundColor Cyan

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$useDocker = $false
try {
    $running = docker compose ps --services --filter "status=running" 2>$null
    if ($running -match "backend") {
        $useDocker = $true
    }
} catch {
    $useDocker = $false
}

if ($useDocker) {
    Write-Host "通过 Docker Compose 执行..."
    docker compose exec backend python manage.py makemigrations
    docker compose exec backend python manage.py migrate
} else {
    Write-Host "本地执行..."
    if (Test-Path "./backend") {
        Set-Location backend
        if (Test-Path ".venv\Scripts\Activate.ps1") {
            & .\.venv\Scripts\Activate.ps1
        }
        python manage.py makemigrations
        python manage.py migrate
    } else {
        Write-Host "未找到 backend 目录" -ForegroundColor Red
        exit 1
    }
}

Write-Host "迁移完成 ✓" -ForegroundColor Green
