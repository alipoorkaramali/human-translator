# ============================================================
# common.ps1 - توابع مشترک اسکریپت‌های ویندوز
# ============================================================

$script:HT_ImageName = "text-processor"

function Get-HTPaths {
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.PSCommandPath }
    $root = Split-Path $scriptDir -Parent
    [pscustomobject]@{
        ScriptDir   = $scriptDir
        ProjectRoot = $root
        InputDir    = Join-Path $root "data\input"
        OutputDir   = Join-Path $root "data\output"
        BookFile    = Join-Path $root "Book1.xlsx"
        NltkData    = Join-Path $root "nltk_data"
        LogFile     = Join-Path $root "data\output\processor.log"
        LockDir     = Join-Path $root "data\output\.locks"
        Dockerfile  = Join-Path $root "docker\Dockerfile.offline"
        ImageName   = $script:HT_ImageName
    }
}

function Get-HTConfig {
    param($Paths)
    $cfg = @{
        OpenExcel     = $false
        OpenFolder    = $true
        DebounceMs    = 800
        PollMs        = 800
        LogToFile     = $true
        SmokeTest     = $true
    }
    $cfgFile = Join-Path $Paths.ProjectRoot "scripts\windows-config.psd1"
    if (Test-Path $cfgFile) {
        try {
            $user = Import-PowerShellDataFile $cfgFile
            foreach ($k in $user.Keys) { $cfg[$k] = $user[$k] }
        } catch { }
    }
    return $cfg
}

function Write-HTLog {
    param(
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR","OK")]
        [string]$Level = "INFO",
        $Paths
    )
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    switch ($Level) {
        "INFO"  { Write-Host $line -ForegroundColor Cyan }
        "WARN"  { Write-Host $line -ForegroundColor Yellow }
        "ERROR" { Write-Host $line -ForegroundColor Red }
        "OK"    { Write-Host $line -ForegroundColor Green }
    }
    if ($Paths -and $Paths.LogFile) {
        try {
            $dir = Split-Path $Paths.LogFile -Parent
            if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            Add-Content -Path $Paths.LogFile -Value $line -Encoding UTF8
        } catch { }
    }
}

function Get-DockerPath([string]$Path) {
    return ($Path -replace '\\', '/')
}

function Test-HTDocker {
    param($Paths)
    try {
        docker --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { return $false }
        docker info 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Test-HTImage {
    param($Paths)
    $id = docker images -q $Paths.ImageName 2>$null
    return [bool]$id
}

function Ensure-HTDirs {
    param($Paths)
    foreach ($d in @($Paths.InputDir, $Paths.OutputDir, $Paths.LockDir)) {
        if (-not (Test-Path $d)) {
            New-Item -ItemType Directory -Path $d -Force | Out-Null
        }
    }
}

function Get-FileLockPath {
    param($Paths, [string]$FileName)
    $safe = ($FileName -replace '[^\w\.\-]', '_')
    return Join-Path $Paths.LockDir "$safe.lock"
}

function Test-FileLocked {
    param($Paths, [string]$FileName)
    $lp = Get-FileLockPath $Paths $FileName
    if (-not (Test-Path $lp)) { return $false }
    $age = (Get-Date) - (Get-Item $lp).LastWriteTime
    if ($age.TotalMinutes -gt 10) {
        Remove-Item -Force $lp -ErrorAction SilentlyContinue
        return $false
    }
    return $true
}

function Set-FileLock {
    param($Paths, [string]$FileName)
    $lp = Get-FileLockPath $Paths $FileName
    Set-Content -Path $lp -Value (Get-Date -Format o) -Encoding UTF8
}

function Clear-FileLock {
    param($Paths, [string]$FileName)
    $lp = Get-FileLockPath $Paths $FileName
    Remove-Item -Force $lp -ErrorAction SilentlyContinue
}

function Invoke-HTProcessFile {
    param(
        [string]$FilePath,
        $Paths,
        $Config,
        [switch]$OpenExcel
    )

    $fileName = Split-Path $FilePath -Leaf
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)

    if (Test-FileLocked $Paths $fileName) {
        Write-HTLog "رد شد (در حال پردازش): $fileName" "WARN" $Paths
        return $false
    }

    Set-FileLock $Paths $fileName
    try {
        Write-HTLog "شروع پردازش: $fileName" "INFO" $Paths

        $tempExcel = Join-Path $Paths.OutputDir "output.xlsx"
        $tempTxt   = Join-Path $Paths.OutputDir "output.txt"
        if (Test-Path $tempExcel) { Remove-Item -Force $tempExcel -ErrorAction SilentlyContinue }
        if (Test-Path $tempTxt)   { Remove-Item -Force $tempTxt -ErrorAction SilentlyContinue }

        $dataRoot = Split-Path $Paths.InputDir -Parent
        $dockerDataPath = Get-DockerPath $dataRoot
        $dockerBookPath = Get-DockerPath $Paths.BookFile
        $containerInput = "data/input/$fileName"

        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $dockerArgs = @(
            "run", "--rm",
            "-v", "${dockerDataPath}:/app/data",
            "-v", "${dockerBookPath}:/app/Book1.xlsx",
            $Paths.ImageName,
            $containerInput
        )

        $output = & docker @dockerArgs 2>&1
        $exitCode = $LASTEXITCODE
        $sw.Stop()

        foreach ($line in $output) {
            $s = "$line"
            if ($s -match "ERROR") { Write-HTLog $s "ERROR" $Paths }
            elseif ($s -match "WARNING") { Write-HTLog $s "WARN" $Paths }
            elseif ($s -match "INFO|✅") { Write-HTLog $s "INFO" $Paths }
        }

        if ($exitCode -eq 0) {
            $newExcel = Join-Path $Paths.OutputDir "output_${baseName}.xlsx"
            $newTxt   = Join-Path $Paths.OutputDir "output_${baseName}.txt"
            if (Test-Path $tempExcel) { Move-Item -Force $tempExcel $newExcel }
            if (Test-Path $tempTxt)   { Move-Item -Force $tempTxt $newTxt }

            $sec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
            Write-HTLog "موفق (${sec}s) → output_${baseName}.xlsx" "OK" $Paths

            $shouldOpen = $OpenExcel -or ($Config -and $Config.OpenExcel)
            if ($shouldOpen -and (Test-Path $newExcel)) {
                try { Start-Process $newExcel } catch { }
            }
            return $true
        } else {
            Write-HTLog "شکست پردازش $fileName (exit=$exitCode)" "ERROR" $Paths
            return $false
        }
    } finally {
        Clear-FileLock $Paths $fileName
    }
}

function Invoke-HTSmokeTest {
    param($Paths)
    $sample = Join-Path $Paths.InputDir "_smoke_test.txt"
    try {
        Set-Content -Path $sample -Value "I have three books and a lot of water." -Encoding UTF8
        $ok = Invoke-HTProcessFile -FilePath $sample -Paths $Paths -Config @{ OpenExcel = $false }
        Remove-Item -Force $sample -ErrorAction SilentlyContinue
        Remove-Item -Force (Join-Path $Paths.OutputDir "output__smoke_test.xlsx") -ErrorAction SilentlyContinue
        Remove-Item -Force (Join-Path $Paths.OutputDir "output__smoke_test.txt") -ErrorAction SilentlyContinue
        return $ok
    } catch {
        Remove-Item -Force $sample -ErrorAction SilentlyContinue
        return $false
    }
}
