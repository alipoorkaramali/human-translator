# ============================================================
# common.ps1 - shared helpers for Windows offline scripts
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
    if ($global:HT_GuiLog -and $global:HT_GuiLog -is [scriptblock]) {
        try { & $global:HT_GuiLog $Message $Level } catch { }
    } else {
        switch ($Level) {
            "INFO"  { Write-Host $line -ForegroundColor Cyan }
            "WARN"  { Write-Host $line -ForegroundColor Yellow }
            "ERROR" { Write-Host $line -ForegroundColor Red }
            "OK"    { Write-Host $line -ForegroundColor Green }
        }
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
    $cmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    $candidates = @(
        "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\resources\bin\docker.exe",
        "$env:LOCALAPPDATA\Programs\Docker\Docker\resources\bin\docker.exe"
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    return $null
}

function Invoke-HTNativeDocker {
    param([string[]]$DockerArgs)
    $exe = Resolve-HTDockerExe
    if (-not $exe) { return @{ ExitCode = 127; Output = @("docker.exe not found") } }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $output = & $exe @DockerArgs 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    return @{ ExitCode = $code; Output = @($output) }
}

function Get-HTDockerStatus {
    param($Paths)
    $exe = Resolve-HTDockerExe
    if (-not $exe) {
        return @{ Ok = $false; Reason = "docker.exe not found. Install Docker Desktop." }
    }
    try {
        & $exe --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            return @{ Ok = $false; Reason = "docker --version failed. Is Docker Desktop installed?" }
        }
        & $exe info 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            return @{ Ok = $false; Reason = "Docker engine not running. Open Docker Desktop." }
        }
        return @{ Ok = $true; Reason = "OK" }
    } catch {
        return @{ Ok = $false; Reason = $_.Exception.Message }
    }
}

function Test-HTDocker {
    param($Paths)
    $st = Get-HTDockerStatus $Paths
    return [bool]$st.Ok
}

function Test-HTImage {
    param($Paths)
    $exe = Resolve-HTDockerExe
    if (-not $exe) { return $false }
    $id = & $exe images -q $Paths.ImageName 2>$null
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
        Write-HTLog "Skipped (already processing): $fileName" "WARN" $Paths
        return $false
    }

    Set-FileLock $Paths $fileName
    try {
        Write-HTLog "Input changed: $fileName — processing..." "INFO" $Paths

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
            $s = "$line".Trim()
            if (-not $s) { continue }
            if ($s -match "(?i)error|traceback|exception|failed") {
                if ($s -notmatch "(?i)deprecated|warning") {
                    Write-HTLog $s "ERROR" $Paths
                }
            }
        }

        if ($exitCode -eq 0) {
            $newExcel = Join-Path $Paths.OutputDir "output_${baseName}.xlsx"
            $newTxt   = Join-Path $Paths.OutputDir "output_${baseName}.txt"
            if (Test-Path $tempExcel) { Move-Item -Force $tempExcel $newExcel }
            if (Test-Path $tempTxt)   { Move-Item -Force $tempTxt $newTxt }

            $sec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
            Write-HTLog "Excel updated: output_${baseName}.xlsx (${sec}s)" "OK" $Paths
            if (Test-Path $newTxt) {
                Write-HTLog "Summary saved: output_${baseName}.txt" "INFO" $Paths
            }

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
