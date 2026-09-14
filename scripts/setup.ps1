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
$dockerStatus = Get-HTDockerStatus
if (-not $dockerStatus.Ok) {
    Write-HTLog $dockerStatus.Reason "ERROR" $Paths
    Write-Host ""
    Write-Host "Fix Docker first, then run Setup/Rebuild again:" -ForegroundColor Yellow
    Write-Host "  1) Install Docker Desktop if needed:" -ForegroundColor Yellow
    Write-Host "     https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    Write-Host "  2) Start Docker Desktop from the Start menu" -ForegroundColor Yellow
    Write-Host "  3) Wait until the whale icon says 'Docker Desktop is running'" -ForegroundColor Yellow
    Write-Host "  4) Open a NEW PowerShell and run:  docker info" -ForegroundColor Yellow
    Write-Host "     If that works, close and reopen start.bat" -ForegroundColor Yellow
    Write-Host ""
    if ($dockerStatus.Exe) {
        Write-HTLog "docker.exe found at: $($dockerStatus.Exe)" "INFO" $Paths
    }
    exit 1
}
Write-HTLog "Docker is ready ($($dockerStatus.Exe))" "OK" $Paths

if (-not (Test-Path $Paths.BookFile)) {
    Write-HTLog "Book1.xlsx not found: $($Paths.BookFile)" "ERROR" $Paths
    exit 1
}
Write-HTLog "Book1.xlsx OK" "OK" $Paths

if (-not (Test-Path $Paths.NltkData)) {
    Write-HTLog "Host nltk_data missing (OK - Docker image downloads its own)" "WARN" $Paths
} else {
    Write-HTLog "Host nltk_data found" "OK" $Paths
}

if (-not (Test-Path $Paths.Dockerfile)) {
    Write-HTLog "Dockerfile.offline not found" "ERROR" $Paths
    exit 1
}

$dockerExe = Resolve-HTDockerExe
$hasImage = Test-HTImage $Paths
if ($hasImage -and -not $Rebuild) {
    Write-HTLog "Image '$($Paths.ImageName)' already exists (use -Rebuild to rebuild)" "OK" $Paths
} else {
    if ($Rebuild -and $hasImage) {
        Write-HTLog "Removing old image..." "INFO" $Paths
        & $dockerExe rmi -f $Paths.ImageName 2>$null | Out-Null
    }

    Write-HTLog "Building offline image (needs internet; several minutes)..." "INFO" $Paths
    Write-HTLog "Full build log -> data\output\docker-build.log" "INFO" $Paths

    $buildLog = Join-Path $Paths.OutputDir "docker-build.log"
    try { Remove-Item -Force $buildLog -ErrorAction SilentlyContinue } catch { }

    $ErrorActionPreference = "Continue"
    & $dockerExe build --progress=plain -f docker/Dockerfile.offline -t $Paths.ImageName . 2>&1 |
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
        Write-Host "  1) Docker Desktop must be Running" -ForegroundColor Yellow
        Write-Host "  2) Internet required for first build (pip + spaCy + NLTK)" -ForegroundColor Yellow
        Write-Host "  3) Book1.xlsx must exist in project root" -ForegroundColor Yellow
        exit 1
    }
    Write-HTLog "Image built OK" "OK" $Paths
}

if ($Config.SmokeTest -and -not $SkipSmoke) {
    Write-HTLog "Running smoke test..." "INFO" $Paths
    if (Invoke-HTSmokeTest $Paths) {
        Write-HTLog "Smoke test passed" "OK" $Paths
    } else {
        Write-HTLog "Smoke test failed - check processor.log" "ERROR" $Paths
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
