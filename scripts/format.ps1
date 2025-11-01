# PowerShell script to format Python files using ruff (matching CI pipeline)

Write-Host "🔧 Formatting Python files with ruff..." -ForegroundColor Blue

# Install ruff if needed
try {
    python -m ruff --version | Out-Null
} catch {
    Write-Host "📦 Installing ruff..." -ForegroundColor Yellow
    python -m pip install ruff
}

try {
    # Run ruff check with auto-fix
    Write-Host "🔍 Running ruff check --fix..." -ForegroundColor Cyan
    python -m ruff check . --fix
    
    # Run ruff format
    Write-Host "🎨 Running ruff format..." -ForegroundColor Cyan
    python -m ruff format .
    
    Write-Host "✅ Formatting completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error during formatting: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎯 Files have been formatted to match CI pipeline standards." -ForegroundColor Yellow