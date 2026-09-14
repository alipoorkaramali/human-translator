# ============================================================
# run-once.ps1 - پردازش یک‌بار همه فایل‌های data/input
# ============================================================

$ErrorActionPreference = "Stop"

$ScriptDir   = $PSScriptRoot
$ProjectRoot = Split-Path $ScriptDir -Parent
Set-Location $ProjectRoot

$InputDir  = Join-Path $ProjectRoot "data\input"
$OutputDir = Join-Path $ProjectRoot "data\output"
$ImageName = "text-processor"
$BookFile  = Join-Path $ProjectRoot "Book1.xlsx"

function Get-DockerPath([string]$Path) { return ($Path -replace '\\', '/') }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Text Processor - One Shot                          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if (-not (docker images -q $ImageName 2>$null)) {
    Write-Host "❌ ایمیج داکر نیست. اول setup.bat را اجرا کن." -ForegroundColor Red
    Read-Host "Enter"
    exit 1
}
if (-not (Test-Path $BookFile)) {
    Write-Host "❌ Book1.xlsx پیدا نشد." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $InputDir))  { New-Item -ItemType Directory -Path $InputDir -Force | Out-Null }
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

$files = @(Get-ChildItem -Path $InputDir -Filter "*.txt" -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -notlike "~*" -and $_.Length -gt 0 })

if ($files.Count -eq 0) {
    Write-Host "⚠️ هیچ فایل .txt معتبری در data\input نیست." -ForegroundColor Yellow
    Read-Host "Enter"
    exit 0
}

Write-Host "📂 تعداد فایل: $($files.Count)" -ForegroundColor Cyan
Write-Host ""

$dockerDataPath = Get-DockerPath (Join-Path $ProjectRoot "data")
$dockerBookPath = Get-DockerPath $BookFile

foreach ($file in $files) {
    $fileName = $file.Name
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)

    Write-Host "─────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "📄 $fileName" -ForegroundColor Cyan

    $tempExcel = Join-Path $OutputDir "output.xlsx"
    $tempTxt   = Join-Path $OutputDir "output.txt"
    if (Test-Path $tempExcel) { Remove-Item -Force $tempExcel -ErrorAction SilentlyContinue }
    if (Test-Path $tempTxt)   { Remove-Item -Force $tempTxt -ErrorAction SilentlyContinue }

    $dockerArgs = @(
        "run", "--rm",
        "-v", "${dockerDataPath}:/app/data",
        "-v", "${dockerBookPath}:/app/Book1.xlsx",
        $ImageName,
        "data/input/$fileName"
    )
    & docker @dockerArgs 2>&1 | ForEach-Object {
        if ("$_" -match "INFO|ERROR|✅|❌") { Write-Host "   $_" -ForegroundColor Gray }
    }

    if ($LASTEXITCODE -eq 0) {
        $newExcel = Join-Path $OutputDir "output_${baseName}.xlsx"
        $newTxt   = Join-Path $OutputDir "output_${baseName}.txt"
        if (Test-Path $tempExcel) { Move-Item -Force $tempExcel $newExcel }
        if (Test-Path $tempTxt)   { Move-Item -Force $tempTxt   $newTxt }
        Write-Host "   ✅ output_${baseName}.xlsx" -ForegroundColor Green
    } else {
        Write-Host "   ❌ خطا" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "✅ پایان. خروجی‌ها: $OutputDir" -ForegroundColor Green
try { Start-Process explorer.exe $OutputDir } catch { }
