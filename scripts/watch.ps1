# ============================================================
# watch.ps1 - رصد data/input و پردازش خودکار با Docker
# ============================================================

$ErrorActionPreference = "Continue"

$ScriptDir   = $PSScriptRoot
$ProjectRoot = Split-Path $ScriptDir -Parent
Set-Location $ProjectRoot

$InputDir  = Join-Path $ProjectRoot "data\input"
$OutputDir = Join-Path $ProjectRoot "data\output"
$ImageName = "text-processor"
$BookFile  = Join-Path $ProjectRoot "Book1.xlsx"

function Write-Info($m)    { Write-Host $m -ForegroundColor Cyan }
function Write-Success($m) { Write-Host $m -ForegroundColor Green }
function Write-Warn($m)    { Write-Host $m -ForegroundColor Yellow }
function Write-Err($m)     { Write-Host $m -ForegroundColor Red }

function Get-DockerPath([string]$Path) {
    return ($Path -replace '\\', '/')
}

$imageExists = docker images -q $ImageName 2>$null
if (-not $imageExists) {
    Write-Err "ایمیج '$ImageName' نیست. اول setup.bat را اجرا کن."
    Read-Host "Enter برای خروج"
    exit 1
}
if (-not (Test-Path $BookFile)) {
    Write-Err "Book1.xlsx پیدا نشد: $BookFile"
    Read-Host "Enter برای خروج"
    exit 1
}
foreach ($d in @($InputDir, $OutputDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

Clear-Host
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  Text Processor - Watch Mode                        ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Info "📂 ورودی:  $InputDir"
Write-Info "📂 خروجی:  $OutputDir"
Write-Info "📦 ایمیج:  $ImageName"
Write-Host ""
Write-Warn "فایل .txt را در data\input ذخیره کن تا خودکار پردازش شود."
Write-Warn "خروج: Ctrl+C"
Write-Host ""

function Process-File([string]$FilePath) {
    $fileName = Split-Path $FilePath -Leaf
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
    $timestamp = Get-Date -Format "HH:mm:ss"

    Write-Host ""
    Write-Host "─────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Info "[$timestamp] پردازش: $fileName"

    $tempExcel = Join-Path $OutputDir "output.xlsx"
    $tempTxt   = Join-Path $OutputDir "output.txt"
    if (Test-Path $tempExcel) { Remove-Item -Force $tempExcel -ErrorAction SilentlyContinue }
    if (Test-Path $tempTxt)   { Remove-Item -Force $tempTxt -ErrorAction SilentlyContinue }

    $dockerDataPath = Get-DockerPath (Join-Path $ProjectRoot "data")
    $dockerBookPath = Get-DockerPath $BookFile
    $containerInput = "data/input/$fileName"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $dockerArgs = @(
        "run", "--rm",
        "-v", "${dockerDataPath}:/app/data",
        "-v", "${dockerBookPath}:/app/Book1.xlsx",
        $ImageName,
        $containerInput
    )

    & docker @dockerArgs 2>&1 | ForEach-Object {
        $line = "$_"
        if ($line -match "INFO|ERROR|WARNING|✅|❌") {
            Write-Host "   $line" -ForegroundColor Gray
        }
    }
    $sw.Stop()

    if ($LASTEXITCODE -eq 0) {
        $newExcel = Join-Path $OutputDir "output_${baseName}.xlsx"
        $newTxt   = Join-Path $OutputDir "output_${baseName}.txt"
        if (Test-Path $tempExcel) { Move-Item -Force $tempExcel $newExcel }
        if (Test-Path $tempTxt)   { Move-Item -Force $tempTxt   $newTxt }

        $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        Write-Success "   ✅ تمام شد (${elapsed}s) → output_${baseName}.xlsx"
        if (Test-Path $newExcel) {
            try { Start-Process $newExcel } catch { }
        }
    } else {
        Write-Err "   ❌ خطا (exit=$LASTEXITCODE)"
    }
}

$fileStates = @{}
Get-ChildItem -Path $InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    $fileStates[$_.FullName] = $_.LastWriteTimeUtc
}

Write-Success "✅ در حال رصد..."
Write-Host ""

while ($true) {
    Start-Sleep -Milliseconds 800
    $current = Get-ChildItem -Path $InputDir -Filter "*.txt" -ErrorAction SilentlyContinue
    $toProcess = @()

    foreach ($file in $current) {
        if ($file.Name -like "~*" -or $file.Name -like ".*") { continue }
        $full = $file.FullName
        $lw = $file.LastWriteTimeUtc
        if (-not $fileStates.ContainsKey($full)) {
            $fileStates[$full] = $lw
            $toProcess += $full
            continue
        }
        if ($fileStates[$full] -ne $lw) {
            $fileStates[$full] = $lw
            $toProcess += $full
        }
    }

    foreach ($fp in $toProcess) {
        Start-Sleep -Milliseconds 700
        $item = Get-Item $fp -ErrorAction SilentlyContinue
        if (-not $item) { continue }
        if ($item.LastWriteTimeUtc -ne $fileStates[$fp]) {
            $fileStates[$fp] = $item.LastWriteTimeUtc
            continue
        }
        if ($item.Length -eq 0) {
            Write-Warn "   ⚠️ فایل خالی نادیده گرفته شد: $($item.Name)"
            continue
        }
        Process-File -FilePath $fp
    }
}
