# ============================================================
# watch.ps1 - Auto-process when .txt files are saved in data/input
#   .\scripts\watch.ps1
#   .\scripts\watch.ps1 -OpenExcel
#   .\scripts\watch.ps1 -ProcessExisting
# ============================================================
param(
    [switch]$OpenExcel,
    [switch]$ProcessExisting
)

$ErrorActionPreference = "Continue"
. "$PSScriptRoot\common.ps1"

$Paths  = Get-HTPaths
$Config = Get-HTConfig $Paths
Set-Location $Paths.ProjectRoot
Ensure-HTDirs $Paths

if (-not (Test-HTImage $Paths)) {
    Write-HTLog "Docker image missing. Run setup.bat first." "ERROR" $Paths
    Read-Host "Press Enter"; exit 1
}
if (-not (Test-Path $Paths.BookFile)) {
    Write-HTLog "Book1.xlsx not found" "ERROR" $Paths
    Read-Host "Press Enter"; exit 1
}

$doOpenExcel = $OpenExcel -or [bool]$Config.OpenExcel
$doExisting  = $ProcessExisting -or [bool]$Config.ProcessExistingOnStart
$debounceMs  = [int]($Config.DebounceMs)
if ($debounceMs -lt 300) { $debounceMs = 300 }

Clear-Host
Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Magenta
Write-Host "   AUTO-PROCESS  ·  Watch Mode" -ForegroundColor Magenta
Write-Host "  ======================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Folder:  $($Paths.InputDir)" -ForegroundColor Cyan
Write-Host "  Output:  $($Paths.OutputDir)" -ForegroundColor Cyan
Write-Host "  Action:  Save any .txt in Input → process automatically" -ForegroundColor Green
Write-Host "  Stop:    Ctrl+C" -ForegroundColor Yellow
if ($doOpenExcel) { Write-Host "  Excel:   opens after each file" -ForegroundColor Yellow }
Write-Host ""

$script:pending = @{}
$script:lastProcessed = @{}
$script:syncRoot = New-Object object

function Enqueue-File([string]$FullPath) {
    if (-not $FullPath) { return }
    $name = Split-Path $FullPath -Leaf
    if ($name -like "~*" -or $name -like ".*" -or $name -like "_smoke*") { return }
    if ($name -notlike "*.txt") { return }
    [System.Threading.Monitor]::Enter($script:syncRoot)
    try {
        $script:pending[$FullPath] = [DateTime]::UtcNow.Ticks
    } finally {
        [System.Threading.Monitor]::Exit($script:syncRoot)
    }
}

function Process-IfReady([string]$FullPath) {
    $item = Get-Item -LiteralPath $FullPath -ErrorAction SilentlyContinue
    if (-not $item) { return }
    if ($item.Length -eq 0) {
        Write-HTLog "Empty file ignored: $($item.Name)" "WARN" $Paths
        return
    }
    $lw = $item.LastWriteTimeUtc
    if ($script:lastProcessed.ContainsKey($FullPath) -and $script:lastProcessed[$FullPath] -eq $lw) {
        return
    }
    $ok = Invoke-HTProcessFile -FilePath $FullPath -Paths $Paths -Config $Config -OpenExcel:$doOpenExcel
    if ($ok) {
        $script:lastProcessed[$FullPath] = $lw
    }
}

Get-ChildItem -Path $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -like "~*" -or $_.Name -like "_smoke*") { return }
    if ($doExisting) {
        Enqueue-File $_.FullName
    } else {
        $script:lastProcessed[$_.FullName] = $_.LastWriteTimeUtc
    }
}

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $Paths.InputDir
$watcher.Filter = "*.txt"
$watcher.IncludeSubdirectories = $false
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor
                        [System.IO.NotifyFilters]::FileName -bor
                        [System.IO.NotifyFilters]::Size
$watcher.EnableRaisingEvents = $true

$handler = {
    param($sender, $e)
    Enqueue-File $e.FullPath
}
Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Created -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action {
    param($sender, $e)
    Enqueue-File $e.FullPath
} | Out-Null

Write-HTLog "Watching (FileSystemWatcher + poll backup). Save a .txt to process." "OK" $Paths

try {
    while ($true) {
        Start-Sleep -Milliseconds 250

        $now = [DateTime]::UtcNow.Ticks
        $ready = @()
        [System.Threading.Monitor]::Enter($script:syncRoot)
        try {
            $keys = @($script:pending.Keys)
            foreach ($k in $keys) {
                $ageMs = ($now - $script:pending[$k]) / 10000.0
                if ($ageMs -ge $debounceMs) {
                    $ready += $k
                    $script:pending.Remove($k)
                }
            }
        } finally {
            [System.Threading.Monitor]::Exit($script:syncRoot)
        }

        foreach ($fp in $ready) {
            Process-IfReady $fp
        }

        $pollMs = [int]$Config.PollMs
        if (-not $script:lastPoll) { $script:lastPoll = [DateTime]::UtcNow }
        if (([DateTime]::UtcNow - $script:lastPoll).TotalMilliseconds -ge $pollMs) {
            $script:lastPoll = [DateTime]::UtcNow
            Get-ChildItem -Path $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
                if ($_.Name -like "~*" -or $_.Name -like ".*" -or $_.Name -like "_smoke*") { return }
                $full = $_.FullName
                $lw = $_.LastWriteTimeUtc
                if (-not $script:lastProcessed.ContainsKey($full) -or $script:lastProcessed[$full] -ne $lw) {
                    Enqueue-File $full
                }
            }
        }
    }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Get-EventSubscriber | Where-Object { $_.SourceObject -eq $watcher } | Unregister-Event -Force -ErrorAction SilentlyContinue
    Write-HTLog "Watch stopped" "INFO" $Paths
}
