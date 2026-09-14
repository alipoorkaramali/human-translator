# ============================================================
# watch.ps1 - Watch data/input and process new/changed .txt files
#   .\scripts\watch.ps1
#   .\scripts\watch.ps1 -OpenExcel
# ============================================================
param([switch]$OpenExcel)

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

Clear-Host
Write-Host "======================================================" -ForegroundColor Magenta
Write-Host "  Text Processor - Watch Mode" -ForegroundColor Magenta
Write-Host "======================================================" -ForegroundColor Magenta
Write-Host "Input:  $($Paths.InputDir)" -ForegroundColor Cyan
Write-Host "Output: $($Paths.OutputDir)" -ForegroundColor Cyan
Write-Host "Log:    $($Paths.LogFile)" -ForegroundColor DarkGray
if ($OpenExcel -or $Config.OpenExcel) {
    Write-Host "OpenExcel: ON" -ForegroundColor Yellow
} else {
    Write-Host "OpenExcel: OFF (use watch.bat -OpenExcel)" -ForegroundColor DarkGray
}
Write-Host "Stop: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

$fileStates = @{}
Get-ChildItem -Path $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    $fileStates[$_.FullName] = $_.LastWriteTimeUtc
}

Write-HTLog "Watch started" "OK" $Paths

try {
    while ($true) {
        Start-Sleep -Milliseconds ([int]$Config.PollMs)
        $current = Get-ChildItem -Path $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue
        $toProcess = @()

        foreach ($file in $current) {
            if ($file.Name -like "~*" -or $file.Name -like ".*" -or $file.Name -like "_smoke*") { continue }
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
            Start-Sleep -Milliseconds ([int]$Config.DebounceMs)
            $item = Get-Item $fp -ErrorAction SilentlyContinue
            if (-not $item) { continue }
            if ($item.LastWriteTimeUtc -ne $fileStates[$fp]) {
                $fileStates[$fp] = $item.LastWriteTimeUtc
                continue
            }
            if ($item.Length -eq 0) {
                Write-HTLog "Empty file ignored: $($item.Name)" "WARN" $Paths
                continue
            }
            $null = Invoke-HTProcessFile -FilePath $fp -Paths $Paths -Config $Config -OpenExcel:$OpenExcel
        }
    }
} finally {
    Write-HTLog "Watch stopped" "INFO" $Paths
}
