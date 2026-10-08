# EduKit Windows 开发环境初始化 (PowerShell)
# 用法: 以管理员运行 PowerShell，执行: .\scripts\setup.ps1

Write-Host "=== EduKit Windows 开发环境初始化 ===" -ForegroundColor Cyan

# 检查 pnpm
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "安装 pnpm..."
    corepack enable pnpm
    if ($LASTEXITCODE -ne 0) {
        npm install -g pnpm
    }
}

# 检查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "请先安装 Python 3.11+ 并加入 PATH" -ForegroundColor Red
    exit 1
}

# 根目录前端依赖
Write-Host "安装前端依赖 (pnpm)..."
pnpm install

# 后端虚拟环境
if (Test-Path "./backend") {
    Write-Host "创建 Python 虚拟环境..."
    Push-Location backend
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }
    Write-Host "激活虚拟环境并安装依赖..."
    & .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Pop-Location
}

# 环境变量
if (-not (Test-Path ".env")) {
    Write-Host "复制 .env.example -> .env"
    Copy-Item .env.example .env
}

Write-Host ""
Write-Host "初始化完成！请编辑 .env 后继续。" -ForegroundColor Green
