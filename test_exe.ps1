# 测试打包后的EXE是否正常工作
# 用于开发者验证

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  EXE测试脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查EXE文件
if (-not (Test-Path "dist\batch_process.exe")) {
    Write-Host "[错误] 找不到 dist\batch_process.exe" -ForegroundColor Red
    Write-Host "请先运行: pyinstaller --onefile batch_process.py" -ForegroundColor Yellow
    exit 1
}

$exeInfo = Get-Item "dist\batch_process.exe"
Write-Host "[成功] 找到EXE文件" -ForegroundColor Green
Write-Host "  路径: $($exeInfo.FullName)" -ForegroundColor Gray
Write-Host "  大小: $([math]::Round($exeInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
Write-Host "  修改时间: $($exeInfo.LastWriteTime)" -ForegroundColor Gray
Write-Host ""

# 检查必需的目录结构
$requiredDirs = @("images/bg", "images/pod", "images/seed")
$allDirsExist = $true

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        $count = (Get-ChildItem $dir -File).Count
        Write-Host "[成功] $dir ($count 个文件)" -ForegroundColor Green
    } else {
        Write-Host "[警告] $dir 不存在" -ForegroundColor Yellow
        $allDirsExist = $false
    }
}
Write-Host ""

# 询问是否运行测试
if (-not $allDirsExist) {
    Write-Host "警告：部分必需目录不存在，程序可能无法正常运行" -ForegroundColor Yellow
    Write-Host ""
}

$response = Read-Host "是否运行EXE进行测试？(y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "  启动 batch_process.exe" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    
    # 启动EXE
    & "dist\batch_process.exe"
    
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "  测试完成" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
} else {
    Write-Host "测试已取消" -ForegroundColor Yellow
}
