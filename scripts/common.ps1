# ============================================================
# common.ps1 - Shared helpers for Windows offline scripts
# ASCII-only messages (safe for Windows PowerShell 5.1)
# ============================================================

$script:HT_ImageName = "text-processor"
$script:HT_DockerExe = $null

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
        SrcDir      = Join-Path $root "src"
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

function Resolve-HTDockerExe {
    if ($script:HT_DockerExe -and (Test-Path $script:HT_DockerExe)) {
        return $script:HT_DockerExe
    }

    $cmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        $script:HT_DockerExe = $cmd.Source
        return $script:HT_DockerExe
    }

    $candidates = @(
        "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\resources\bin\docker.exe",
        "$env:LOCALAPPDATA\Programs\Docker\Docker\resources\bin\docker.exe"
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path $p)) {
            $script:HT_DockerExe = $p
            return $script:HT_DockerExe
        }
    }
    return $null
}

function Invoke-HTNativeDocker {
    # Run docker via cmd so stderr WARNINGs do not become terminating
    # PowerShell errors under $ErrorActionPreference = 'Stop'.
    param(
        [string]$Exe,
        [string[]]$Args
    )
    $argLine = ($Args | ForEach-Object {
        if ($_ -match '\s') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
    }) -join ' '

    $quotedExe = '"' + $Exe + '"'
    cmd.exe /c "$quotedExe $argLine" | Out-Null
    return $LASTEXITCODE
}

function Get-HTDockerStatus {
    # Returns: @{ Ok = $bool; Reason = $string; Exe = $string }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $exe = Resolve-HTDockerExe
        if (-not $exe) {
            return @{
                Ok = $false
                Reason = "docker.exe not found in PATH or default install folders. Install Docker Desktop."
                Exe = $null
            }
        }

        $verExit = Invoke-HTNativeDocker -Exe $exe -Args @('--version')
        if ($verExit -ne 0) {
            return @{
                Ok = $false
                Reason = "docker --version failed (exit=$verExit). Is Docker Desktop installed?"
                Exe = $exe
            }
        }

        $infoExit = Invoke-HTNativeDocker -Exe $exe -Args @('info')
        if ($infoExit -ne 0) {
            return @{
                Ok = $false
                Reason = "Docker Desktop engine is not running (docker info exit=$infoExit). Open Docker Desktop and wait until status is Running."
                Exe = $exe
            }
        }

        return @{ Ok = $true; Reason = "OK"; Exe = $exe }
    } finally {
        $ErrorActionPreference = $prevEap
    }
}

function Test-HTDocker {
    param($Paths)
    $st = Get-HTDockerStatus
    return [bool]$st.Ok
}

function Test-HTImage {
    param($Paths)
    $exe = Resolve-HTDockerExe
    if (-not $exe) { return $false }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $id = cmd.exe /c "`"$exe`" images -q $($Paths.ImageName)" 2>$null
        return [bool]($id -and "$id".Trim())
    } finally {
        $ErrorActionPreference = $prevEap
    }
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
        Write-HTLog "Skipped (already processing): $fileName" "WARN" $Paths
        return $false
    }

    Set-FileLock $Paths $fileName
    try {
        Write-HTLog "Processing: $fileName" "INFO" $Paths

        $tempExcel = Join-Path $Paths.OutputDir "output.xlsx"
        $tempTxt   = Join-Path $Paths.OutputDir "output.txt"
        if (Test-Path $tempExcel) { Remove-Item -Force $tempExcel -ErrorAction SilentlyContinue }
        if (Test-Path $tempTxt)   { Remove-Item -Force $tempTxt -ErrorAction SilentlyContinue }

        $dataRoot = Split-Path $Paths.InputDir -Parent
        $dockerDataPath = Get-DockerPath $dataRoot
        $dockerBookPath = Get-DockerPath $Paths.BookFile
        $dockerSrcPath  = Get-DockerPath $Paths.SrcDir
        $containerInput = "data/input/$fileName"

        $exe = Resolve-HTDockerExe
        if (-not $exe) {
            Write-HTLog "docker.exe not found" "ERROR" $Paths
            return $false
        }

        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $prevEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $dockerArgs = @(
            "run", "--rm",
            "-v", "${dockerDataPath}:/app/data",
            "-v", "${dockerBookPath}:/app/Book1.xlsx",
            "-v", "${dockerSrcPath}:/app/src",
            $Paths.ImageName,
            $containerInput
        )

        $output = & $exe @dockerArgs 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $prevEap
        $sw.Stop()

        foreach ($line in $output) {
            $s = "$line"
            if ($s -match "ERROR") { Write-HTLog $s "ERROR" $Paths }
            elseif ($s -match "WARNING") { Write-HTLog $s "WARN" $Paths }
            elseif ($s -match "INFO|OK") { Write-HTLog $s "INFO" $Paths }
        }

        if ($exitCode -eq 0) {
            $newExcel = Join-Path $Paths.OutputDir "output_${baseName}.xlsx"
            $newTxt   = Join-Path $Paths.OutputDir "output_${baseName}.txt"
            if (Test-Path $tempExcel) { Move-Item -Force $tempExcel $newExcel }
            if (Test-Path $tempTxt)   { Move-Item -Force $tempTxt $newTxt }

            $sec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
            Write-HTLog "OK (${sec}s) -> output_${baseName}.xlsx" "OK" $Paths

            $shouldOpen = $OpenExcel -or ($Config -and $Config.OpenExcel)
            if ($shouldOpen -and (Test-Path $newExcel)) {
                try { Start-Process $newExcel } catch { }
            }
            return $true
        } else {
            Write-HTLog "Failed: $fileName (exit=$exitCode)" "ERROR" $Paths
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
