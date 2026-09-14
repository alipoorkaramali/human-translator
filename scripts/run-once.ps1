# ============================================================
# run-once.ps1 - پردازش یک‌بار همه فایل‌های data/input
#   .\scripts\run-once.ps1
#   .\scripts\run-once.ps1 -OpenExcel
# ============================================================
param([switch]$OpenExcel)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

$Paths  = Get-HTPaths
$Config = Get-HTConfig $Paths
Set-Location $Paths.ProjectRoot
Ensure-HTDirs $Paths

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Text Processor - One Shot                          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-HTImage $Paths)) {
    Write-HTLog "ایمیج نیست. اول setup.bat" "ERROR" $Paths
    Read-Host "Enter"; exit 1
}
if (-not (Test-Path $Paths.BookFile)) {
    Write-HTLog "Book1.xlsx پیدا نشد" "ERROR" $Paths
    exit 1
}

$files = @(Get-ChildItem -Path $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike "~*" -and $_.Name -notlike "_smoke*" -and $_.Length -gt 0 })

if ($files.Count -eq 0) {
    Write-HTLog "هیچ فایل .txt معتبری در data\input نیست" "WARN" $Paths
    Read-Host "Enter"; exit 0
}

Write-HTLog "تعداد فایل: $($files.Count)" "INFO" $Paths
$ok = 0; $fail = 0

foreach ($file in $files) {
    Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray
    if (Invoke-HTProcessFile -FilePath $file.FullName -Paths $Paths -Config $Config -OpenExcel:$OpenExcel) {
        $ok++
    } else {
        $fail++
    }
}

Write-Host ""
Write-HTLog "پایان — موفق: $ok | ناموفق: $fail" "OK" $Paths
Write-Host "📂 $($Paths.OutputDir)" -ForegroundColor Cyan

if ($Config.OpenFolder) {
    try { Start-Process explorer.exe $Paths.OutputDir } catch { }
}
