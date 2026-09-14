# ============================================================
# gui.ps1 - Text Processor dashboard (WinForms)
# Live progress in status panel (no silent freeze)
# ============================================================

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

. "$PSScriptRoot\common.ps1"
$Paths  = Get-HTPaths
$Config = Get-HTConfig $Paths
Ensure-HTDirs $Paths
Set-Location $Paths.ProjectRoot

$bg       = [System.Drawing.Color]::FromArgb(24, 26, 32)
$panelBg  = [System.Drawing.Color]::FromArgb(36, 40, 48)
$accent   = [System.Drawing.Color]::FromArgb(88, 166, 255)
$accent2  = [System.Drawing.Color]::FromArgb(63, 185, 80)
$warn     = [System.Drawing.Color]::FromArgb(210, 153, 34)
$danger   = [System.Drawing.Color]::FromArgb(248, 81, 73)
$text     = [System.Drawing.Color]::FromArgb(230, 237, 243)
$muted    = [System.Drawing.Color]::FromArgb(139, 148, 158)
$btnBg    = [System.Drawing.Color]::FromArgb(48, 54, 64)

function New-HTButton {
    param(
        [string]$Text,
        [int]$X, [int]$Y, [int]$W = 200, [int]$H = 44,
        [System.Drawing.Color]$Back = $btnBg,
        [System.Drawing.Color]$Fore = $text
    )
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $Text
    $b.Location = New-Object System.Drawing.Point($X, $Y)
    $b.Size = New-Object System.Drawing.Size($W, $H)
    $b.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $b.FlatAppearance.BorderSize = 0
    $b.BackColor = $Back
    $b.ForeColor = $Fore
    $b.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $b.Cursor = [System.Windows.Forms.Cursors]::Hand
    $b.FlatAppearance.MouseOverBackColor = [System.Drawing.Color]::FromArgb(
        [Math]::Min(255, $Back.R + 20),
        [Math]::Min(255, $Back.G + 20),
        [Math]::Min(255, $Back.B + 20)
    )
    return $b
}

function Append-Status {
    param([string]$Msg, [string]$Level = "INFO")
    $ts = Get-Date -Format "HH:mm:ss"
    $prefix = switch ($Level) {
        "OK"    { "[OK]" }
        "ERROR" { "[ERR]" }
        "WARN"  { "[!]" }
        default { "[...]" }
    }
    $line = "[$ts] $prefix $Msg"
    $statusBox.AppendText("$line`r`n")
    $statusBox.SelectionStart = $statusBox.Text.Length
    $statusBox.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
    try { Write-HTLog $Msg $Level $Paths } catch { }
}

function Update-StatusBar {
    $dockerOk = Test-HTDocker $Paths
    $imageOk  = Test-HTImage $Paths
    $bookOk   = Test-Path $Paths.BookFile

    $parts = @()
    if ($dockerOk) { $parts += "Docker OK" } else { $parts += "Docker missing" }
    if ($imageOk)  { $parts += "Image OK" } else { $parts += "Image missing" }
    if ($bookOk)   { $parts += "Book1 OK" } else { $parts += "Book1 missing" }
    $lblStatus.Text = ($parts -join "  |  ")
    if ($dockerOk -and $imageOk -and $bookOk) {
        $lblStatus.ForeColor = $accent2
    } elseif ($dockerOk) {
        $lblStatus.ForeColor = $warn
    } else {
        $lblStatus.ForeColor = $danger
    }
}

function Set-Busy([bool]$On, [string]$Msg = "") {
    $script:busy = $On
    $lblBusy.Text = $Msg
    $lblBusy.Visible = $On
    foreach ($c in @($btnSetup, $btnWatch, $btnProcess, $btnRebuild)) {
        $c.Enabled = -not $On
    }
    [System.Windows.Forms.Application]::DoEvents()
}

function Start-HTJob {
    param([scriptblock]$Work, [string]$BusyMsg)
    if ($script:busy) {
        Append-Status "A job is already running - wait." "WARN"
        return
    }
    Set-Busy $true $BusyMsg
    try {
        & $Work
    } catch {
        Append-Status "Error: $($_.Exception.Message)" "ERROR"
    } finally {
        Set-Busy $false
        Update-StatusBar
    }
}

function Wait-HTProcessLive {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$Activity,
        [string]$LogPath = $null
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $lastLogLen = 0
    if ($LogPath -and (Test-Path $LogPath)) {
        $lastLogLen = (Get-Item $LogPath).Length
    }

    while (-not $Process.HasExited) {
        $sec = [int]$sw.Elapsed.TotalSeconds
        $lblBusy.Text = "$Activity  (${sec}s elapsed - not frozen, please wait)"
        [System.Windows.Forms.Application]::DoEvents()

        # Stream new log lines into the status panel
        if ($LogPath -and (Test-Path $LogPath)) {
            try {
                $fs = [System.IO.File]::Open($LogPath, 'Open', 'Read', 'ReadWrite')
                try {
                    if ($fs.Length -gt $lastLogLen) {
                        $fs.Seek($lastLogLen, 'Begin') | Out-Null
                        $sr = New-Object System.IO.StreamReader($fs)
                        $chunk = $sr.ReadToEnd()
                        $lastLogLen = $fs.Length
                        foreach ($ln in ($chunk -split "`r?`n")) {
                            if ($ln -and $ln.Trim()) {
                                $clean = $ln -replace '^\[\d{4}-\d{2}-\d{2} [^\]]+\]\s*\[[^\]]+\]\s*', ''
                                if ($clean.Length -gt 120) { $clean = $clean.Substring(0, 117) + '...' }
                                Append-Status $clean "INFO"
                            }
                        }
                    }
                } finally { $fs.Close() }
            } catch { }
        }

        Start-Sleep -Milliseconds 400
    }
    $Process.WaitForExit() | Out-Null
    return $Process.ExitCode
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "Human Translator"
$form.Size = New-Object System.Drawing.Size(560, 640)
$form.StartPosition = "CenterScreen"
$form.BackColor = $bg
$form.ForeColor = $text
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font("Segoe UI", 9)

$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "Human Translator"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$lblTitle.ForeColor = $accent
$lblTitle.Location = New-Object System.Drawing.Point(24, 18)
$lblTitle.AutoSize = $true
$form.Controls.Add($lblTitle)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Quantifier Tagger  ·  Offline Windows"
$lblSub.ForeColor = $muted
$lblSub.Location = New-Object System.Drawing.Point(26, 52)
$lblSub.AutoSize = $true
$form.Controls.Add($lblSub)

$panel = New-Object System.Windows.Forms.Panel
$panel.Location = New-Object System.Drawing.Point(24, 88)
$panel.Size = New-Object System.Drawing.Size(500, 210)
$panel.BackColor = $panelBg
$form.Controls.Add($panel)

$btnSetup = New-HTButton "Setup (once)" 20 20 220 44 $accent ([System.Drawing.Color]::FromArgb(10, 20, 40))
$btnRebuild = New-HTButton "Rebuild Image" 260 20 220 44 $btnBg $text
$btnWatch = New-HTButton "Watch Mode" 20 80 220 44 $accent2 ([System.Drawing.Color]::FromArgb(10, 30, 15))
$btnProcess = New-HTButton "Process Once" 260 80 220 44 $btnBg $text
$btnInput = New-HTButton "Input Folder" 20 140 145 40 $btnBg $muted
$btnOutput = New-HTButton "Output Folder" 177 140 145 40 $btnBg $muted
$btnLog = New-HTButton "Log" 334 140 146 40 $btnBg $muted

$panel.Controls.AddRange(@($btnSetup, $btnRebuild, $btnWatch, $btnProcess, $btnInput, $btnOutput, $btnLog))

$chkExcel = New-Object System.Windows.Forms.CheckBox
$chkExcel.Text = "Open Excel after processing"
$chkExcel.ForeColor = $muted
$chkExcel.Location = New-Object System.Drawing.Point(28, 308)
$chkExcel.AutoSize = $true
$chkExcel.Checked = [bool]$Config.OpenExcel
$form.Controls.Add($chkExcel)

$lblBusy = New-Object System.Windows.Forms.Label
$lblBusy.Text = ""
$lblBusy.ForeColor = $warn
$lblBusy.Location = New-Object System.Drawing.Point(28, 336)
$lblBusy.Size = New-Object System.Drawing.Size(500, 20)
$lblBusy.Visible = $false
$form.Controls.Add($lblBusy)

$lblLogTitle = New-Object System.Windows.Forms.Label
$lblLogTitle.Text = "Status (live)"
$lblLogTitle.ForeColor = $muted
$lblLogTitle.Location = New-Object System.Drawing.Point(28, 360)
$lblLogTitle.AutoSize = $true
$form.Controls.Add($lblLogTitle)

$statusBox = New-Object System.Windows.Forms.TextBox
$statusBox.Multiline = $true
$statusBox.ScrollBars = "Vertical"
$statusBox.ReadOnly = $true
$statusBox.BackColor = [System.Drawing.Color]::FromArgb(18, 20, 26)
$statusBox.ForeColor = $text
$statusBox.Font = New-Object System.Drawing.Font("Consolas", 9)
$statusBox.Location = New-Object System.Drawing.Point(24, 382)
$statusBox.Size = New-Object System.Drawing.Size(500, 160)
$statusBox.BorderStyle = "FixedSingle"
$form.Controls.Add($statusBox)

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "Checking..."
$lblStatus.ForeColor = $muted
$lblStatus.Location = New-Object System.Drawing.Point(24, 554)
$lblStatus.AutoSize = $true
$form.Controls.Add($lblStatus)

$script:busy = $false

# ---------- Process Once: run INLINE so every step shows in Status ----------
$btnProcess.Add_Click({
    Start-HTJob -BusyMsg "Preparing..." -Work {
        if (-not (Test-HTImage $Paths)) {
            Append-Status "Docker image missing. Run Setup first." "ERROR"
            return
        }
        if (-not (Test-Path $Paths.BookFile)) {
            Append-Status "Book1.xlsx not found" "ERROR"
            return
        }

        $files = @(Get-ChildItem -Path $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notlike "~*" -and $_.Name -notlike "_smoke*" -and $_.Length -gt 0 })

        if ($files.Count -eq 0) {
            Append-Status "No .txt files in data\input - put a file there first." "WARN"
            return
        }

        Append-Status "Found $($files.Count) file(s) to process" "INFO"
        $ok = 0; $fail = 0; $n = $files.Count; $i = 0

        foreach ($file in $files) {
            $i++
            $lblBusy.Text = "Processing $($file.Name)  ($i of $n) - Docker running, please wait..."
            Append-Status "[$i/$n] Start: $($file.Name)" "INFO"
            [System.Windows.Forms.Application]::DoEvents()

            $cfg = @{ OpenExcel = [bool]$chkExcel.Checked }
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $success = $false
            try {
                $success = Invoke-HTProcessFile -FilePath $file.FullName -Paths $Paths -Config $cfg -OpenExcel:$chkExcel.Checked
            } catch {
                Append-Status "Exception: $($_.Exception.Message)" "ERROR"
                $success = $false
            }
            $sw.Stop()
            $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)

            if ($success) {
                $ok++
                Append-Status "[$i/$n] Done: $($file.Name) (${sec}s) -> output_$([IO.Path]::GetFileNameWithoutExtension($file.Name)).xlsx" "OK"
            } else {
                $fail++
                Append-Status "[$i/$n] Failed: $($file.Name) (${sec}s)" "ERROR"
            }
            [System.Windows.Forms.Application]::DoEvents()
        }

        Append-Status "Finished — OK: $ok | Failed: $fail" "OK"
        if ($ok -gt 0) {
            Append-Status "Open Output Folder to see Excel files" "INFO"
        }
    }
})

# ---------- Setup / Rebuild: visible console + live elapsed + log tail ----------
function Start-SetupScript {
    param([switch]$Rebuild)
    $argList = [System.Collections.ArrayList]@("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Paths.ScriptDir "setup.ps1"))
    if ($Rebuild) { [void]$argList.Add("-Rebuild") }

    Append-Status $(if ($Rebuild) { "Rebuild started (internet + several minutes)..." } else { "Setup started..." }) "INFO"
    Append-Status "A console window shows full docker build log." "INFO"

    $p = Start-Process -FilePath "powershell.exe" -ArgumentList $argList -PassThru -WorkingDirectory $Paths.ProjectRoot
    $activity = $(if ($Rebuild) { "Rebuilding image" } else { "Running setup" })
    $code = Wait-HTProcessLive -Process $p -Activity $activity -LogPath $Paths.LogFile

    if ($code -eq 0) {
        Append-Status $(if ($Rebuild) { "Rebuild finished OK" } else { "Setup finished OK" }) "OK"
    } else {
        Append-Status "Setup/Rebuild failed (exit $code). Click Log for details." "ERROR"
        $buildLog = Join-Path $Paths.OutputDir "docker-build.log"
        if (Test-Path $buildLog) { Append-Status "See also: data\output\docker-build.log" "ERROR" }
    }
}

$btnSetup.Add_Click({
    Start-HTJob -BusyMsg "Setup running..." -Work { Start-SetupScript }
})

$btnRebuild.Add_Click({
    Start-HTJob -BusyMsg "Rebuild running..." -Work { Start-SetupScript -Rebuild }
})

$btnWatch.Add_Click({
    Append-Status "Watch Mode opened in a new window (Ctrl+C to stop)" "INFO"
    $wargs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Paths.ScriptDir "watch.ps1"))
    if ($chkExcel.Checked) { $wargs += "-OpenExcel" }
    Start-Process -FilePath "powershell.exe" -ArgumentList $wargs
})

$btnInput.Add_Click({
    if (-not (Test-Path $Paths.InputDir)) { New-Item -ItemType Directory -Path $Paths.InputDir -Force | Out-Null }
    Start-Process explorer.exe $Paths.InputDir
})
$btnOutput.Add_Click({
    if (-not (Test-Path $Paths.OutputDir)) { New-Item -ItemType Directory -Path $Paths.OutputDir -Force | Out-Null }
    Start-Process explorer.exe $Paths.OutputDir
})
$btnLog.Add_Click({
    $buildLog = Join-Path $Paths.OutputDir "docker-build.log"
    if (Test-Path $Paths.LogFile) { Start-Process notepad.exe $Paths.LogFile }
    elseif (Test-Path $buildLog) { Start-Process notepad.exe $buildLog }
    else { Append-Status "No log yet" "WARN" }
})

$form.Add_Shown({
    Update-StatusBar
    Append-Status "Ready - put .txt in Input, then click Process Once" "INFO"
    Append-Status "Status panel updates live while processing." "INFO"
})

$iconPath = Join-Path $Paths.ProjectRoot "assets\app.ico"
if (Test-Path $iconPath) {
    try { $form.Icon = New-Object System.Drawing.Icon($iconPath) } catch { }
}

[void]$form.ShowDialog()
