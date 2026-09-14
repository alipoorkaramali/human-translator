# ============================================================
# watch.ps1 - Auto-process .txt files saved in data/input
#   .\scripts\watch.ps1
#   .\scripts\watch.ps1 -OpenExcel
#   .\scripts\watch.ps1 -ProcessExisting
# ============================================================
param(
    [switch]$OpenExcel,
    [switch]$ProcessExisting
)

$ErrorActionPreference = "Continue"

$common = Join-Path $PSScriptRoot "common.ps1"
if (-not (Test-Path -LiteralPath $common)) {
    Write-Host "ERROR: common.ps1 not found at $common" -ForegroundColor Red
    Read-Host "Press Enter"; exit 1
}
. $common

if (-not (Get-Command Write-HTLog -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: common.ps1 did not load Write-HTLog" -ForegroundColor Red
    Read-Host "Press Enter"; exit 1
}

$Paths  = Get-HTPaths
$Config = Get-HTConfig $Paths

# Always use absolute, legal paths for FileSystemWatcher
$projectRoot = [System.IO.Path]::GetFullPath($Paths.ProjectRoot)
$inputDir    = [System.IO.Path]::GetFullPath((Join-Path $projectRoot "data\input"))
$outputDir   = [System.IO.Path]::GetFullPath((Join-Path $projectRoot "data\output"))

$Paths = [pscustomobject]@{
    ScriptDir   = $Paths.ScriptDir
    ProjectRoot = $projectRoot
    InputDir    = $inputDir
    OutputDir   = $outputDir
    BookFile    = [System.IO.Path]::GetFullPath($Paths.BookFile)
    SrcDir      = [System.IO.Path]::GetFullPath($Paths.SrcDir)
    NltkData    = $Paths.NltkData
    LogFile     = [System.IO.Path]::GetFullPath($Paths.LogFile)
    LockDir     = [System.IO.Path]::GetFullPath($Paths.LockDir)
    Dockerfile  = $Paths.Dockerfile
    ImageName   = $Paths.ImageName
}

Set-Location -LiteralPath $Paths.ProjectRoot
Ensure-HTDirs $Paths

if (-not (Test-Path -LiteralPath $Paths.InputDir)) {
    New-Item -ItemType Directory -Path $Paths.InputDir -Force | Out-Null
}

if (-not (Test-HTImage $Paths)) {
    Write-HTLog "Docker image missing. Run setup.bat first." "ERROR" $Paths
    Read-Host "Press Enter"; exit 1
}
if (-not (Test-Path -LiteralPath $Paths.BookFile)) {
    Write-HTLog "Book1.xlsx not found" "ERROR" $Paths
    Read-Host "Press Enter"; exit 1
}

$doOpenExcel = $OpenExcel -or [bool]$Config.OpenExcel
$doExisting  = $ProcessExisting -or [bool]$Config.ProcessExistingOnStart
$debounceMs  = [int]($Config.DebounceMs)
if ($debounceMs -lt 300) { $debounceMs = 300 }
$pollMs = [int]($Config.PollMs)
if ($pollMs -lt 400) { $pollMs = 400 }

Clear-Host
Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Magenta
Write-Host "   AUTO-PROCESS  -  Watch Mode" -ForegroundColor Magenta
Write-Host "  ======================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Folder:  $($Paths.InputDir)" -ForegroundColor Cyan
Write-Host "  Output:  $($Paths.OutputDir)" -ForegroundColor Cyan
Write-Host "  Action:  Save any .txt in Input -> process automatically" -ForegroundColor Green
Write-Host "  Stop:    Ctrl+C" -ForegroundColor Yellow
if ($doOpenExcel) { Write-Host "  Excel:   opens after each file" -ForegroundColor Yellow }
Write-Host ""

$script:fileStates = @{}
$script:lastProcessed = @{}

function Should-SkipName([string]$Name) {
    if (-not $Name) { return $true }
    if ($Name -like "~*") { return $true }
    if ($Name -like ".*") { return $true }
    if ($Name -like "_smoke*") { return $true }
    if ($Name -notlike "*.txt") { return $true }
    return $false
}

function Try-ProcessFile([string]$FullPath) {
    if (-not $FullPath) { return }
    if (-not (Test-Path -LiteralPath $FullPath)) { return }
    $item = Get-Item -LiteralPath $FullPath -ErrorAction SilentlyContinue
    if (-not $item) { return }
    if (Should-SkipName $item.Name) { return }
    if ($item.Length -eq 0) {
        Write-HTLog "Empty file ignored: $($item.Name)" "WARN" $Paths
        return
    }

    $lw = $item.LastWriteTimeUtc
    if ($script:lastProcessed.ContainsKey($FullPath) -and $script:lastProcessed[$FullPath] -eq $lw) {
        return
    }

    # Debounce: wait until file is stable
    Start-Sleep -Milliseconds $debounceMs
    $item2 = Get-Item -LiteralPath $FullPath -ErrorAction SilentlyContinue
    if (-not $item2) { return }
    if ($item2.LastWriteTimeUtc -ne $lw) {
        # still being written; next poll will pick it up
        return
    }

    Write-HTLog "Detected change: $($item2.Name)" "INFO" $Paths
    $ok = Invoke-HTProcessFile -FilePath $FullPath -Paths $Paths -Config $Config -OpenExcel:$doOpenExcel
    if ($ok) {
        $script:lastProcessed[$FullPath] = $item2.LastWriteTimeUtc
    }
}

# Seed known files
Get-ChildItem -LiteralPath $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    if (Should-SkipName $_.Name) { return }
    $script:fileStates[$_.FullName] = $_.LastWriteTimeUtc
    if ($doExisting) {
        Try-ProcessFile $_.FullName
    } else {
        $script:lastProcessed[$_.FullName] = $_.LastWriteTimeUtc
    }
}

# Optional FileSystemWatcher (best-effort). Polling is always the reliable backup.
$watcher = $null
try {
    if ([string]::IsNullOrWhiteSpace($Paths.InputDir)) {
        throw "InputDir is empty"
    }
    if (-not [System.IO.Directory]::Exists($Paths.InputDir)) {
        [System.IO.Directory]::CreateDirectory($Paths.InputDir) | Out-Null
    }
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $Paths.InputDir
    $watcher.Filter = "*.txt"
    $watcher.IncludeSubdirectories = $false
    $watcher.NotifyFilter = [IO.NotifyFilters]::LastWrite -bor [IO.NotifyFilters]::FileName -bor [IO.NotifyFilters]::Size
    $watcher.EnableRaisingEvents = $true
    Write-HTLog "FileSystemWatcher ON for $($Paths.InputDir)" "OK" $Paths
} catch {
    $watcher = $null
    Write-HTLog "FileSystemWatcher unavailable ($($_.Exception.Message)) - using poll only" "WARN" $Paths
}

Write-HTLog "Watch started. Save a .txt in Input to process." "OK" $Paths

try {
    while ($true) {
        Start-Sleep -Milliseconds $pollMs

        $current = @(Get-ChildItem -LiteralPath $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue)
        foreach ($file in $current) {
            if (Should-SkipName $file.Name) { continue }
            $full = $file.FullName
            $lw = $file.LastWriteTimeUtc

            if (-not $script:fileStates.ContainsKey($full)) {
                $script:fileStates[$full] = $lw
                Try-ProcessFile $full
                continue
            }
            if ($script:fileStates[$full] -ne $lw) {
                $script:fileStates[$full] = $lw
                Try-ProcessFile $full
            }
        }
    }
} finally {
    if ($watcher) {
        try {
            $watcher.EnableRaisingEvents = $false
            $watcher.Dispose()
        } catch { }
    }
    Write-HTLog "Watch stopped" "INFO" $Paths
}
