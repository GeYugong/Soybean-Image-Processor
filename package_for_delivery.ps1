# Build and Package Script
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Soybean Tool Packaging" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build
Write-Host "[1/4] Building batch_process.py ..." -ForegroundColor Yellow
pyinstaller batch_process.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Build completed" -ForegroundColor Green
Write-Host ""

# Step 2: Create delivery directory
Write-Host "[2/4] Creating delivery directory..." -ForegroundColor Yellow
$deliveryDir = "Soybean-Tool"

if (Test-Path $deliveryDir) {
    Remove-Item $deliveryDir -Recurse -Force
}

New-Item -ItemType Directory -Path $deliveryDir -Force | Out-Null
New-Item -ItemType Directory -Path "$deliveryDir\images\bg" -Force | Out-Null
New-Item -ItemType Directory -Path "$deliveryDir\images\pod" -Force | Out-Null
New-Item -ItemType Directory -Path "$deliveryDir\images\seed" -Force | Out-Null

Write-Host "[OK] Directory structure created" -ForegroundColor Green
Write-Host ""

# Step 3: Copy files
Write-Host "[3/4] Copying files..." -ForegroundColor Yellow
Copy-Item "dist\batch_process.exe" "$deliveryDir\" -Force
Copy-Item "使用说明.txt" "$deliveryDir\" -Force

Write-Host "[OK] Files copied" -ForegroundColor Green
Write-Host ""

# Step 4: Show results
Write-Host "[4/4] Packaging completed!" -ForegroundColor Green
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Delivery Directory Structure" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "$deliveryDir\"
Write-Host "  batch_process.exe"
Write-Host "  使用说明.txt"
Write-Host "  images\"
Write-Host "    bg\"
Write-Host "    pod\"
Write-Host "    seed\"
Write-Host ""

$exeSize = [math]::Round((Get-Item "$deliveryDir\batch_process.exe").Length / 1MB, 2)
Write-Host "EXE Size: $exeSize MB" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Compress $deliveryDir to ZIP" -ForegroundColor White
Write-Host "2. Add sample images (optional)" -ForegroundColor White
Write-Host "3. Deliver to customer" -ForegroundColor White
Write-Host ""

# Ask to open directory
$response = Read-Host "Open delivery directory? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    explorer $deliveryDir
}
