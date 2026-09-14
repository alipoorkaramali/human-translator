# ============================================================
# setup.ps1 - نصب اولیه اجرای آفلاین روی ویندوز (یک‌بار)
# ============================================================
# استفاده:
#   .\scripts\setup.ps1
#   .\scripts\setup.ps1 -Rebuild
# ============================================================

param(
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"

$ScriptDir   = $PSScriptRoot
$ProjectRoot = Split-Path $ScriptDir -Parent
Set-Location $ProjectRoot

function Write-Step($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   ✅ $msg" -ForegroundColor Green }
function Write-Bad($msg)  { Write-Host "   ❌ $msg" -ForegroundColor Red }
function Write-Tip($msg)  { Write-Host "   💡 $msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Text Processor - Setup (Windows Offline)           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 ریشه پروژه: $ProjectRoot" -ForegroundColor DarkGray
Write-Host ""

# --- 1) Docker ---
Write-Step "🔍 بررسی Docker..."
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker not found" }
    Write-Ok "$dockerVersion"
} catch {
    Write-Bad "Docker نصب نیست یا در PATH نیست."
    Write-Tip "Docker Desktop را نصب و باز کن: https://www.docker.com/products/docker-desktop/"
    exit 1
}

try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "daemon down" }
    Write-Ok "Docker daemon در حال اجراست"
} catch {
    Write-Bad "Docker Desktop اجرا نشده."
    Write-Tip "از Start Menu برنامه Docker Desktop را باز کن و صبر کن تا سبز شود."
    exit 1
}

# --- 2) Book1.xlsx ---
Write-Host ""
Write-Step "🔍 بررسی Book1.xlsx..."
$BookFile = Join-Path $ProjectRoot "Book1.xlsx"
if (-not (Test-Path $BookFile)) {
    Write-Bad "Book1.xlsx پیدا نشد: $BookFile"
    exit 1
}
Write-Ok "Book1.xlsx موجود است"

# --- 3) nltk_data ---
Write-Host ""
Write-Step "🔍 بررسی nltk_data..."
$NltkData = Join-Path $ProjectRoot "nltk_data"
$required = @(
    "tokenizers\punkt",
    "corpora\wordnet",
    "corpora\cmudict"
)

function Test-NltkReady {
    if (-not (Test-Path $NltkData)) { return $false }
    foreach ($pkg in $required) {
        $p = Join-Path $NltkData $pkg
        $zip = "$p.zip"
        if (-not (Test-Path $p) -and -not (Test-Path $zip)) { return $false }
    }
    return $true
}

if (-not (Test-NltkReady)) {
    Write-Tip "nltk_data کامل نیست — تلاش برای دانلود با scripts\download_nltk.py"
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if ($py) {
        $env:NLTK_DATA = $NltkData
        & $py.Source (Join-Path $ScriptDir "download_nltk.py")
        if ($LASTEXITCODE -ne 0) {
            Write-Bad "دانلود NLTK ناموفق بود."
            exit 1
        }
    } else {
        Write-Bad "پوشه nltk_data آماده نیست و Python برای دانلود پیدا نشد."
        Write-Tip "یا Python نصب کن و دوباره setup را بزن، یا nltk_data را دستی در ریشه پروژه بگذار."
        exit 1
    }
}

if (-not (Test-NltkReady)) {
    Write-Bad "بعد از دانلود هنوز nltk_data ناقص است."
    exit 1
}
Write-Ok "پکیج‌های NLTK موجود هستند"

# --- 4) Dockerfile.offline ---
Write-Host ""
Write-Step "🔍 بررسی Dockerfile.offline..."
$DockerfileOffline = Join-Path $ProjectRoot "docker\Dockerfile.offline"
if (-not (Test-Path $DockerfileOffline)) {
    Write-Bad "docker\Dockerfile.offline پیدا نشد."
    exit 1
}
Write-Ok "Dockerfile.offline موجود است"

# --- 5) پوشه‌ها ---
Write-Host ""
Write-Step "🔍 پوشه‌های data..."
foreach ($dir in @("data\input", "data\output")) {
    $full = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
        Write-Ok "ساخته شد: $dir"
    } else {
        Write-Ok "موجود: $dir"
    }
}

# --- 6) ایمیج ---
Write-Host ""
Write-Step "🔍 ایمیج Docker..."
$ImageName = "text-processor"
$imageId = docker images -q $ImageName 2>$null

if ($imageId -and -not $Rebuild) {
    Write-Ok "ایمیج '$ImageName' از قبل هست"
    Write-Tip "برای ساخت مجدد: .\scripts\setup.ps1 -Rebuild"
} else {
    if ($Rebuild -and $imageId) {
        Write-Tip "حذف ایمیج قبلی برای Rebuild..."
        docker rmi $ImageName 2>$null | Out-Null
    }
    Write-Host "   🐳 ساخت ایمیج آفلاین (اولین بار چند دقیقه طول می‌کشد)..." -ForegroundColor Yellow
    docker build -f docker/Dockerfile.offline -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Bad "خطا در docker build"
        exit 1
    }
    Write-Ok "ایمیج '$ImageName' ساخته شد"
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Setup کامل شد                                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "مراحل بعدی:" -ForegroundColor Cyan
Write-Host "  • دوبار کلیک روی watch.bat   → رصد خودکار data\input" -ForegroundColor White
Write-Host "  • دوبار کلیک روی process.bat → پردازش یک‌بار همه فایل‌ها" -ForegroundColor White
Write-Host ""
