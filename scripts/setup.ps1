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

# Host nltk_data is optional now (image downloads its own during build).
# Still try to prepare it for developers who run without Docker.
if (-not (Test-Path $Paths.NltkData)) {
    Write-HTLog "Host nltk_data missing (OK for Docker build; optional for local Python)" "WARN" $Paths
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if ($py) {
        Write-HTLog "Trying optional NLTK download on host..." "INFO" $Paths
        $env:NLTK_DATA = $Paths.NltkData
        & $py.Source (Join-Path $Paths.ScriptDir "download_nltk.py")
        if ($LASTEXITCODE -eq 0) { Write-HTLog "Host nltk_data prepared" "OK" $Paths }
        else { Write-HTLog "Host NLTK download skipped/failed (Docker build will still work)" "WARN" $Paths }
    }
} else {
    Write-HTLog "Host nltk_data found" "OK" $Paths
}

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
        docker rmi -f $Paths.ImageName 2>$null | Out-Null
    }

    Write-HTLog "Building offline image (needs internet; may take several minutes)..." "INFO" $Paths
    Write-HTLog "Full build log -> $($Paths.LogFile)" "INFO" $Paths

    $buildLog = Join-Path $Paths.OutputDir "docker-build.log"
    $ErrorActionPreference = "Continue"
    docker build --progress=plain -f docker/Dockerfile.offline -t $Paths.ImageName . 2>&1 |
        ForEach-Object {
            $line = "$_"
            Write-Host $line
            try { Add-Content -Path $Paths.LogFile -Value $line -Encoding UTF8 } catch { }
            try { Add-Content -Path $buildLog -Value $line -Encoding UTF8 } catch { }
        }
    $buildExit = $LASTEXITCODE
    $ErrorActionPreference = "Stop"

    if ($buildExit -ne 0) {
        Write-HTLog "docker build FAILED (exit=$buildExit)" "ERROR" $Paths
        Write-HTLog "See: data\output\docker-build.log" "ERROR" $Paths
        Write-Host ""
        Write-Host "Common fixes:" -ForegroundColor Yellow
        Write-Host "  1) Docker Desktop must be Running (whale icon)" -ForegroundColor Yellow
        Write-Host "  2) Internet required during first build (pip + spaCy + NLTK)" -ForegroundColor Yellow
        Write-Host "  3) Book1.xlsx must exist in project root" -ForegroundColor Yellow
        Write-Host "  4) Open data\output\docker-build.log for the real error" -ForegroundColor Yellow
        exit 1
    }
    Write-HTLog "Image built OK" "OK" $Paths
}

if ($Config.SmokeTest -and -not $SkipSmoke) {
    Write-HTLog "Running smoke test..." "INFO" $Paths
    if (Invoke-HTSmokeTest $Paths) {
        Write-HTLog "Smoke test passed" "OK" $Paths
    } else {
        Write-HTLog "Smoke test failed - image built but process failed; check processor.log" "ERROR" $Paths
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
