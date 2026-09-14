# ============================================================
# setup.ps1 - First-time / rebuild setup (Windows offline)
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
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Text Processor - Setup (Windows Offline)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Root: $($Paths.ProjectRoot)" -ForegroundColor DarkGray
Write-Host ""

Write-HTLog "Checking Docker..." "INFO" $Paths
if (-not (Test-HTDocker $Paths)) {
    Write-HTLog "Docker Desktop is not installed or not running." "ERROR" $Paths
    Write-Host "   https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}
Write-HTLog "Docker is ready" "OK" $Paths

if (-not (Test-Path $Paths.BookFile)) {
    Write-HTLog "Book1.xlsx not found: $($Paths.BookFile)" "ERROR" $Paths
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
    Write-HTLog "nltk_data incomplete - trying download..." "WARN" $Paths
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if ($py) {
        $env:NLTK_DATA = $Paths.NltkData
        & $py.Source (Join-Path $Paths.ScriptDir "download_nltk.py")
        if ($LASTEXITCODE -ne 0) { Write-HTLog "NLTK download failed" "ERROR" $Paths; exit 1 }
    } else {
        Write-HTLog "Python not found for NLTK download. Place nltk_data manually." "ERROR" $Paths
        exit 1
    }
}
if (-not (Test-NltkReady)) { Write-HTLog "nltk_data still incomplete" "ERROR" $Paths; exit 1 }
Write-HTLog "nltk_data OK" "OK" $Paths

if (-not (Test-Path $Paths.Dockerfile)) {
    Write-HTLog "Dockerfile.offline not found" "ERROR" $Paths
    exit 1
}

$hasImage = Test-HTImage $Paths
if ($hasImage -and -not $Rebuild) {
    Write-HTLog "Image '$($Paths.ImageName)' already exists (use -Rebuild to rebuild)" "OK" $Paths
} else {
    if ($Rebuild -and $hasImage) {
        Write-HTLog "Removing old image..." "INFO" $Paths
        docker rmi $Paths.ImageName 2>$null | Out-Null
    }
    Write-HTLog "Building offline image (may take a few minutes)..." "INFO" $Paths
    docker build -f docker/Dockerfile.offline -t $Paths.ImageName .
    if ($LASTEXITCODE -ne 0) { Write-HTLog "docker build failed" "ERROR" $Paths; exit 1 }
    Write-HTLog "Image built" "OK" $Paths
}

if ($Config.SmokeTest -and -not $SkipSmoke) {
    Write-HTLog "Running smoke test..." "INFO" $Paths
    if (Invoke-HTSmokeTest $Paths) {
        Write-HTLog "Smoke test passed" "OK" $Paths
    } else {
        Write-HTLog "Smoke test failed - try setup.bat -Rebuild" "ERROR" $Paths
        exit 1
    }
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Setup complete" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  watch.bat   -> auto watch" -ForegroundColor White
Write-Host "  process.bat -> process once" -ForegroundColor White
Write-Host "  Log: data\output\processor.log" -ForegroundColor DarkGray
Write-Host ""
