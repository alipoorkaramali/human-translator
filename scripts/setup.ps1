# ============================================================
# setup.ps1 - نصب اولیه (ویندوز / آفلاین)
#   .\scripts\setup.ps1
#   .\scripts\setup.ps1 -Rebuild
#   .\scripts\setup.ps1 -SkipSmoke
# ============================================================
param(
    [switch]$Rebuild,
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

$Paths  = Get-HTPaths
$Config = Get-HTConfig $Paths
Set-Location $Paths.ProjectRoot
Ensure-HTDirs $Paths

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Text Processor - Setup (Windows Offline)           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "📁 $($Paths.ProjectRoot)" -ForegroundColor DarkGray
Write-Host ""

Write-HTLog "بررسی Docker..." "INFO" $Paths
if (-not (Test-HTDocker $Paths)) {
    Write-HTLog "Docker Desktop نصب/اجرا نیست." "ERROR" $Paths
    Write-Host "   https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}
Write-HTLog "Docker آماده است" "OK" $Paths

if (-not (Test-Path $Paths.BookFile)) {
    Write-HTLog "Book1.xlsx پیدا نشد: $($Paths.BookFile)" "ERROR" $Paths
    exit 1
}
Write-HTLog "Book1.xlsx OK" "OK" $Paths

$required = @("tokenizers\punkt", "corpora\wordnet", "corpora\cmudict")
function Test-NltkReady {
    if (-not (Test-Path $Paths.NltkData)) { return $false }
    foreach ($pkg in $required) {
        $p = Join-Path $Paths.NltkData $pkg
        if (-not (Test-Path $p) -and -not (Test-Path "$p.zip")) { return $false }
    }
    return $true
}

if (-not (Test-NltkReady)) {
    Write-HTLog "nltk_data ناقص — تلاش برای دانلود..." "WARN" $Paths
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if ($py) {
        $env:NLTK_DATA = $Paths.NltkData
        & $py.Source (Join-Path $Paths.ScriptDir "download_nltk.py")
        if ($LASTEXITCODE -ne 0) { Write-HTLog "دانلود NLTK ناموفق" "ERROR" $Paths; exit 1 }
    } else {
        Write-HTLog "Python برای دانلود NLTK پیدا نشد. nltk_data را دستی بگذار." "ERROR" $Paths
        exit 1
    }
}
if (-not (Test-NltkReady)) { Write-HTLog "nltk_data هنوز ناقص است" "ERROR" $Paths; exit 1 }
Write-HTLog "nltk_data OK" "OK" $Paths

if (-not (Test-Path $Paths.Dockerfile)) {
    Write-HTLog "Dockerfile.offline پیدا نشد" "ERROR" $Paths
    exit 1
}

$hasImage = Test-HTImage $Paths
if ($hasImage -and -not $Rebuild) {
    Write-HTLog "ایمیج '$($Paths.ImageName)' موجود است (Rebuild با -Rebuild)" "OK" $Paths
} else {
    if ($Rebuild -and $hasImage) {
        Write-HTLog "حذف ایمیج قبلی..." "INFO" $Paths
        docker rmi $Paths.ImageName 2>$null | Out-Null
    }
    Write-HTLog "ساخت ایمیج آفلاین (چند دقیقه)..." "INFO" $Paths
    docker build -f docker/Dockerfile.offline -t $Paths.ImageName .
    if ($LASTEXITCODE -ne 0) { Write-HTLog "docker build شکست خورد" "ERROR" $Paths; exit 1 }
    Write-HTLog "ایمیج ساخته شد" "OK" $Paths
}

if ($Config.SmokeTest -and -not $SkipSmoke) {
    Write-HTLog "Smoke test روی ایمیج..." "INFO" $Paths
    if (Invoke-HTSmokeTest $Paths) {
        Write-HTLog "Smoke test موفق" "OK" $Paths
    } else {
        Write-HTLog "Smoke test ناموفق — با -Rebuild دوباره بساز" "ERROR" $Paths
        exit 1
    }
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Setup کامل شد                                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "  watch.bat   → رصد خودکار" -ForegroundColor White
Write-Host "  process.bat → پردازش یک‌بار" -ForegroundColor White
Write-Host "  لاگ: data\output\processor.log" -ForegroundColor DarkGray
Write-Host ""
