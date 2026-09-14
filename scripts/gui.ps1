# ============================================================
# gui.ps1 - داشبورد گرافیکی Text Processor (WinForms)
# بدون وابستگی خارجی — فقط .NET داخلی ویندوز
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

# ---------- پالت رنگ ----------
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
        "OK"    { "✓" }
        "ERROR" { "✗" }
        "WARN"  { "!" }
        default { "·" }
    }
    $line = "[$ts] $prefix $Msg"
    $statusBox.AppendText("$line`r`n")
    $statusBox.SelectionStart = $statusBox.Text.Length
    $statusBox.ScrollToCaret()
    try { Write-HTLog $Msg $Level $Paths } catch { }
}

function Update-StatusBar {
    $dockerOk = Test-HTDocker $Paths
    $imageOk  = Test-HTImage $Paths
    $bookOk   = Test-Path $Paths.BookFile

    $parts = @()
    if ($dockerOk) { $parts += "Docker ✓" } else { $parts += "Docker ✗" }
    if ($imageOk)  { $parts += "Image ✓" } else { $parts += "Image ✗" }
    if ($bookOk)   { $parts += "Book1 ✓" } else { $parts += "Book1 ✗" }
    $lblStatus.Text = ($parts -join "   ·   ")
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
        Append-Status "یک کار در حال اجراست — صبر کن." "WARN"
        return
    }
    Set-Busy $true $BusyMsg
    try {
        & $Work
    } catch {
        Append-Status "خطا: $($_.Exception.Message)" "ERROR"
    } finally {
        Set-Busy $false
        Update-StatusBar
    }
}

# ---------- فرم ----------
$form = New-Object System.Windows.Forms.Form
$form.Text = "Human Translator"
$form.Size = New-Object System.Drawing.Size(560, 620)
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

$btnSetup = New-HTButton "⚙   Setup (یک‌بار)" 20 20 220 44 $accent ([System.Drawing.Color]::FromArgb(10, 20, 40))
$btnRebuild = New-HTButton "↻   Rebuild Image" 260 20 220 44 $btnBg $text
$btnWatch = New-HTButton "▶   Watch Mode" 20 80 220 44 $accent2 ([System.Drawing.Color]::FromArgb(10, 30, 15))
$btnProcess = New-HTButton "⚡   Process Once" 260 80 220 44 $btnBg $text
$btnInput = New-HTButton "📂  Input Folder" 20 140 145 40 $btnBg $muted
$btnOutput = New-HTButton "📊  Output Folder" 177 140 145 40 $btnBg $muted
$btnLog = New-HTButton "📝  Log" 334 140 146 40 $btnBg $muted

$panel.Controls.AddRange(@($btnSetup, $btnRebuild, $btnWatch, $btnProcess, $btnInput, $btnOutput, $btnLog))

$chkExcel = New-Object System.Windows.Forms.CheckBox
$chkExcel.Text = "بعد از پردازش Excel را باز کن"
$chkExcel.ForeColor = $muted
$chkExcel.Location = New-Object System.Drawing.Point(28, 308)
$chkExcel.AutoSize = $true
$chkExcel.Checked = [bool]$Config.OpenExcel
$form.Controls.Add($chkExcel)

$lblBusy = New-Object System.Windows.Forms.Label
$lblBusy.Text = ""
$lblBusy.ForeColor = $warn
$lblBusy.Location = New-Object System.Drawing.Point(28, 336)
$lblBusy.AutoSize = $true
$lblBusy.Visible = $false
$form.Controls.Add($lblBusy)

$lblLogTitle = New-Object System.Windows.Forms.Label
$lblLogTitle.Text = "وضعیت"
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
$statusBox.Size = New-Object System.Drawing.Size(500, 150)
$statusBox.BorderStyle = "FixedSingle"
$form.Controls.Add($statusBox)

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "در حال بررسی..."
$lblStatus.ForeColor = $muted
$lblStatus.Location = New-Object System.Drawing.Point(24, 544)
$lblStatus.AutoSize = $true
$form.Controls.Add($lblStatus)

$script:busy = $false

$btnSetup.Add_Click({
    Start-HTJob -BusyMsg "Setup در حال اجرا..." -Work {
        $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Paths.ScriptDir "setup.ps1"))
        $p = Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Wait -PassThru -NoNewWindow
        if ($p.ExitCode -eq 0) { Append-Status "Setup تمام شد" "OK" }
        else { Append-Status "Setup با خطا تمام شد (کد $($p.ExitCode))" "ERROR" }
    }
})

$btnRebuild.Add_Click({
    Start-HTJob -BusyMsg "Rebuild ایمیج..." -Work {
        $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Paths.ScriptDir "setup.ps1"), "-Rebuild")
        $p = Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Wait -PassThru -NoNewWindow
        if ($p.ExitCode -eq 0) { Append-Status "Rebuild موفق" "OK" }
        else { Append-Status "Rebuild ناموفق" "ERROR" }
    }
})

$btnWatch.Add_Click({
    Append-Status "Watch Mode در پنجره جدا باز شد (Ctrl+C برای توقف)" "INFO"
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Paths.ScriptDir "watch.ps1"))
    if ($chkExcel.Checked) { $args += "-OpenExcel" }
    Start-Process -FilePath "powershell.exe" -ArgumentList $args
})

$btnProcess.Add_Click({
    Start-HTJob -BusyMsg "در حال پردازش فایل‌ها..." -Work {
        $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Paths.ScriptDir "run-once.ps1"))
        if ($chkExcel.Checked) { $args += "-OpenExcel" }
        $p = Start-Process -FilePath "powershell.exe" -ArgumentList $args -Wait -PassThru -NoNewWindow
        if ($p.ExitCode -eq 0) { Append-Status "Process Once تمام شد" "OK" }
        else { Append-Status "Process با خطا/هشدار تمام شد" "WARN" }
    }
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
    if (Test-Path $Paths.LogFile) { Start-Process notepad.exe $Paths.LogFile }
    else { Append-Status "هنوز لاگی نیست" "WARN" }
})

$form.Add_Shown({
    Update-StatusBar
    Append-Status "آماده — فایل .txt را در Input بگذار یا Process را بزن" "INFO"
})

$iconPath = Join-Path $Paths.ProjectRoot "assets\app.ico"
if (Test-Path $iconPath) {
    try { $form.Icon = New-Object System.Drawing.Icon($iconPath) } catch { }
}

[void]$form.ShowDialog()
