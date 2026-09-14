# ============================================================
# gui.ps1 - Human Translator dashboard (WinForms + auto-watch)
# Pure ASCII. Requires: powershell -STA
# ============================================================
$ErrorActionPreference = "Stop"

function Write-GuiCrashLog([string]$Message) {
  try {
    $root = Split-Path $PSScriptRoot -Parent
    $dir = Join-Path $root "data\output"
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $log = Join-Path $dir "gui-error.log"
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $log -Value $line -Encoding UTF8
  } catch {}
}

try {
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
  [System.Windows.Forms.Application]::EnableVisualStyles()

  . (Join-Path $PSScriptRoot "common.ps1")
  if (-not (Get-Command Write-HTLog -ErrorAction SilentlyContinue)) {
    throw "common.ps1 failed to load Write-HTLog"
  }

  $Paths = Get-HTPaths
  $Config = Get-HTConfig $Paths
  $Paths = [pscustomobject]@{
    ScriptDir   = $Paths.ScriptDir
    ProjectRoot = [IO.Path]::GetFullPath($Paths.ProjectRoot)
    InputDir    = [IO.Path]::GetFullPath((Join-Path $Paths.ProjectRoot "data\input"))
    OutputDir   = [IO.Path]::GetFullPath((Join-Path $Paths.ProjectRoot "data\output"))
    BookFile    = [IO.Path]::GetFullPath($Paths.BookFile)
    SrcDir      = [IO.Path]::GetFullPath($Paths.SrcDir)
    NltkData    = $Paths.NltkData
    LogFile     = [IO.Path]::GetFullPath($Paths.LogFile)
    LockDir     = [IO.Path]::GetFullPath($Paths.LockDir)
    Dockerfile  = $Paths.Dockerfile
    ImageName   = $Paths.ImageName
  }
  Ensure-HTDirs $Paths
  Set-Location -LiteralPath $Paths.ProjectRoot

  $bg      = [Drawing.Color]::FromArgb(24, 26, 32)
  $panelBg = [Drawing.Color]::FromArgb(36, 40, 48)
  $accent  = [Drawing.Color]::FromArgb(88, 166, 255)
  $okC     = [Drawing.Color]::FromArgb(63, 185, 80)
  $warn    = [Drawing.Color]::FromArgb(210, 153, 34)
  $bad     = [Drawing.Color]::FromArgb(248, 81, 73)
  $text    = [Drawing.Color]::FromArgb(230, 237, 243)
  $muted   = [Drawing.Color]::FromArgb(139, 148, 158)
  $btnBg   = [Drawing.Color]::FromArgb(48, 54, 64)

  function New-Btn($T, $X, $Y, $W, $H, $Back, $Fore) {
    $b = New-Object Windows.Forms.Button
    $b.Text = $T
    $b.Location = New-Object Drawing.Point($X, $Y)
    $b.Size = New-Object Drawing.Size($W, $H)
    $b.FlatStyle = "Flat"
    $b.FlatAppearance.BorderSize = 0
    $b.BackColor = $Back
    $b.ForeColor = $Fore
    $b.Font = New-Object Drawing.Font("Segoe UI", 10, [Drawing.FontStyle]::Bold)
    $b.Cursor = "Hand"
    return $b
  }

  function Log($m, $lvl = "INFO") {
    $p = switch ($lvl) { "OK" { "[OK]" } "ERROR" { "[ERR]" } "WARN" { "[!]" } default { "[...]" } }
    $line = "[{0}] {1} {2}" -f (Get-Date -Format "HH:mm:ss"), $p, $m
    if ($statusBox -and -not $statusBox.IsDisposed) {
      try {
        $statusBox.AppendText($line + "`r`n")
        $statusBox.SelectionStart = $statusBox.Text.Length
        $statusBox.ScrollToCaret()
      } catch {}
    }
    [Windows.Forms.Application]::DoEvents()
    try {
      if ($Paths.LogFile) {
        $dir = Split-Path $Paths.LogFile -Parent
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Add-Content -Path $Paths.LogFile -Value ("[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $lvl, $m) -Encoding UTF8
      }
    } catch {}
  }

  $global:HT_GuiLog = { param($Message, $Level) try { Log $Message $Level } catch {} }

  function Update-Bar {
    $d = $false; $i = $false
    try { $d = Test-HTDocker $Paths } catch {}
    try { $i = Test-HTImage $Paths } catch {}
    $b = Test-Path -LiteralPath $Paths.BookFile
    $lblStatus.Text = ("{0} | {1} | {2}" -f $(if ($d) { "Docker OK" } else { "Docker missing" }), $(if ($i) { "Image OK" } else { "Image missing" }), $(if ($b) { "Book1 OK" } else { "Book1 missing" }))
    $lblStatus.ForeColor = if ($d -and $i -and $b) { $okC } elseif ($d) { $warn } else { $bad }
  }

  function Set-Busy([bool]$On, [string]$Msg = "") {
    $script:busy = $On
    $lblBusy.Text = $Msg
    $lblBusy.Visible = $On
    foreach ($c in @($btnSetup, $btnRebuild, $btnProcess)) { $c.Enabled = (-not $On) }
    if (-not $On) {
      $progressBar.Visible = $false
      $lblPercent.Visible = $false
      $progressBar.Style = "Continuous"
      $progressBar.Value = 0
    }
    [Windows.Forms.Application]::DoEvents()
  }

  function Set-Progress([int]$Value, [int]$Maximum = 100, [string]$Caption = "") {
    if ($Maximum -lt 1) { $Maximum = 1 }
    if ($Value -lt 0) { $Value = 0 }
    if ($Value -gt $Maximum) { $Value = $Maximum }
    $progressBar.Style = "Continuous"
    $progressBar.Maximum = $Maximum
    $progressBar.Value = $Value
    $lblPercent.Text = ("{0}%" -f [int](100.0 * $Value / $Maximum))
    if ($Caption) { $lblBusy.Text = $Caption; $lblBusy.Visible = $true }
    $progressBar.Visible = $true
    $lblPercent.Visible = $true
    [Windows.Forms.Application]::DoEvents()
  }

  function Set-ProgressMarquee([string]$Caption = "Working...") {
    $progressBar.Style = "Marquee"
    $progressBar.MarqueeAnimationSpeed = 30
    $progressBar.Visible = $true
    $lblPercent.Text = "..."
    $lblPercent.Visible = $true
    $lblBusy.Text = $Caption
    $lblBusy.Visible = $true
    [Windows.Forms.Application]::DoEvents()
  }

  function Run-Job([string]$Name, [scriptblock]$Work) {
    if ($script:busy) { Log "Already busy - wait." "WARN"; return }
    Set-Busy $true $Name
    try { & $Work } catch { Log ("Error: " + $_.Exception.Message) "ERROR" }
    finally { Set-Busy $false; Update-Bar }
  }

  $script:busy = $false
  $script:watchProc = $false
  $script:pending = @{}
  $script:lastDone = @{}
  $script:sync = New-Object object
  $script:fsW = $null
  $script:tmr = $null

  function Enq([string]$p) {
    if (-not $p) { return }
    $n = [IO.Path]::GetFileName($p)
    if ($n -like "~*" -or $n -like ".*" -or $n -like "_smoke*" -or $n -notlike "*.txt") { return }
    [Threading.Monitor]::Enter($script:sync)
    try { $script:pending[$p] = [DateTime]::UtcNow.Ticks }
    finally { [Threading.Monitor]::Exit($script:sync) }
  }

  function Stop-Watch {
    if ($script:tmr) { try { $script:tmr.Stop(); $script:tmr.Dispose() } catch {}; $script:tmr = $null }
    if ($script:fsW) { try { $script:fsW.EnableRaisingEvents = $false; $script:fsW.Dispose() } catch {}; $script:fsW = $null }
    Log "Auto-watch OFF" "WARN"
  }

  function Start-Watch {
    if ($script:tmr) { return }
    if (-not (Test-Path -LiteralPath $Paths.InputDir)) {
      New-Item -ItemType Directory -Path $Paths.InputDir -Force | Out-Null
    }
    Get-ChildItem -LiteralPath $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
      if ($_.Name -notlike "~*" -and $_.Name -notlike "_smoke*") {
        $script:lastDone[$_.FullName] = $_.LastWriteTimeUtc
      }
    }

    try {
      $w = New-Object IO.FileSystemWatcher
      $w.Path = $Paths.InputDir
      $w.Filter = "*.txt"
      $w.IncludeSubdirectories = $false
      $w.NotifyFilter = [IO.NotifyFilters]::LastWrite -bor [IO.NotifyFilters]::FileName -bor [IO.NotifyFilters]::Size
      $w.SynchronizingObject = $form
      $w.Add_Changed({ Enq $EventArgs.FullPath })
      $w.Add_Created({ Enq $EventArgs.FullPath })
      $w.Add_Renamed({ Enq $EventArgs.FullPath })
      $w.EnableRaisingEvents = $true
      $script:fsW = $w
    } catch {
      $script:fsW = $null
      Log ("FileSystemWatcher off: " + $_.Exception.Message + " (poll only)") "WARN"
    }

    $t = New-Object Windows.Forms.Timer
    $t.Interval = 400
    $t.Add_Tick({
      if ($script:watchProc -or $script:busy -or -not $chkWatch.Checked) { return }
      $db = 900
      try { $db = [int]$Config.DebounceMs } catch {}
      if ($db -lt 300) { $db = 300 }
      $now = [DateTime]::UtcNow.Ticks
      $ready = @()
      [Threading.Monitor]::Enter($script:sync)
      try {
        foreach ($k in @($script:pending.Keys)) {
          if ((($now - $script:pending[$k]) / 10000.0) -ge $db) {
            $ready += $k
            $script:pending.Remove($k)
          }
        }
      } finally { [Threading.Monitor]::Exit($script:sync) }

      Get-ChildItem -LiteralPath $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Name -like "~*" -or $_.Name -like ".*" -or $_.Name -like "_smoke*") { return }
        $f = $_.FullName
        $lw = $_.LastWriteTimeUtc
        if (-not $script:lastDone.ContainsKey($f) -or $script:lastDone[$f] -ne $lw) {
          if ($f -notin $ready) { $ready += $f }
        }
      }

      foreach ($fp in $ready) {
        $it = Get-Item -LiteralPath $fp -ErrorAction SilentlyContinue
        if (-not $it -or $it.Length -eq 0) { continue }
        $lw = $it.LastWriteTimeUtc
        if ($script:lastDone.ContainsKey($fp) -and $script:lastDone[$fp] -eq $lw) { continue }
        $script:watchProc = $true
        try {
          Log ("Input updated: " + $it.Name)
          $ok = Invoke-HTProcessFile -FilePath $fp -Paths $Paths -Config $Config -OpenExcel:($chkExcel.Checked)
          if ($ok) {
            $script:lastDone[$fp] = $lw
            Log ("Finished: " + $it.Name + " - Excel ready in Output") "OK"
            Update-Bar
          } else {
            Log ("Failed: " + $it.Name) "ERROR"
          }
        } catch {
          Log ("Watch error: " + $_.Exception.Message) "ERROR"
        } finally {
          $script:watchProc = $false
        }
      }
    })
    $script:tmr = $t
    $t.Start()
    Log "Auto-watch ON - save .txt in Input" "OK"
  }

  $form = New-Object Windows.Forms.Form
  $form.Text = "Human Translator"
  $form.Size = New-Object Drawing.Size(560, 680)
  $form.StartPosition = "CenterScreen"
  $form.BackColor = $bg
  $form.ForeColor = $text
  $form.FormBorderStyle = "FixedSingle"
  $form.MaximizeBox = $false
  $form.Font = New-Object Drawing.Font("Segoe UI", 9)

  $lblTitle = New-Object Windows.Forms.Label
  $lblTitle.Text = "Human Translator"
  $lblTitle.Font = New-Object Drawing.Font("Segoe UI", 18, [Drawing.FontStyle]::Bold)
  $lblTitle.ForeColor = $accent
  $lblTitle.Location = New-Object Drawing.Point(24, 16)
  $lblTitle.AutoSize = $true
  $form.Controls.Add($lblTitle)

  $lblSub = New-Object Windows.Forms.Label
  $lblSub.Text = "Quantifier Tagger - Offline Windows"
  $lblSub.ForeColor = $muted
  $lblSub.Location = New-Object Drawing.Point(26, 50)
  $lblSub.AutoSize = $true
  $form.Controls.Add($lblSub)

  $panel = New-Object Windows.Forms.Panel
  $panel.Location = New-Object Drawing.Point(24, 80)
  $panel.Size = New-Object Drawing.Size(500, 160)
  $panel.BackColor = $panelBg
  $form.Controls.Add($panel)

  $btnSetup = New-Btn "Setup (once)" 20 20 220 40 $accent ([Drawing.Color]::FromArgb(10, 20, 40))
  $btnRebuild = New-Btn "Rebuild Image" 260 20 220 40 $btnBg $text
  $btnProcess = New-Btn "Process Once" 20 75 460 40 $btnBg $text
  $btnInput = New-Btn "Input" 20 125 145 32 $btnBg $muted
  $btnOutput = New-Btn "Output" 177 125 145 32 $btnBg $muted
  $btnLog = New-Btn "Log" 334 125 146 32 $btnBg $muted
  $panel.Controls.AddRange(@($btnSetup, $btnRebuild, $btnProcess, $btnInput, $btnOutput, $btnLog))

  $chkWatch = New-Object Windows.Forms.CheckBox
  $chkWatch.Text = "Auto-watch Input (process on Save) - ON by default"
  $chkWatch.ForeColor = $okC
  $chkWatch.Location = New-Object Drawing.Point(28, 250)
  $chkWatch.AutoSize = $true
  $chkWatch.Checked = $true
  $form.Controls.Add($chkWatch)

  $chkExcel = New-Object Windows.Forms.CheckBox
  $chkExcel.Text = "Open Excel automatically after each process"
  $chkExcel.ForeColor = $muted
  $chkExcel.Location = New-Object Drawing.Point(28, 274)
  $chkExcel.AutoSize = $true
  $chkExcel.Checked = [bool]$Config.OpenExcel
  $form.Controls.Add($chkExcel)

  $lblBusy = New-Object Windows.Forms.Label
  $lblBusy.Text = ""
  $lblBusy.ForeColor = $warn
  $lblBusy.Location = New-Object Drawing.Point(28, 300)
  $lblBusy.Size = New-Object Drawing.Size(450, 18)
  $lblBusy.Visible = $false
  $form.Controls.Add($lblBusy)

  $progressBar = New-Object Windows.Forms.ProgressBar
  $progressBar.Location = New-Object Drawing.Point(24, 322)
  $progressBar.Size = New-Object Drawing.Size(460, 22)
  $progressBar.Minimum = 0
  $progressBar.Maximum = 100
  $progressBar.Value = 0
  $progressBar.Visible = $false
  $form.Controls.Add($progressBar)

  $lblPercent = New-Object Windows.Forms.Label
  $lblPercent.Text = ""
  $lblPercent.ForeColor = $okC
  $lblPercent.Font = New-Object Drawing.Font("Segoe UI", 9, [Drawing.FontStyle]::Bold)
  $lblPercent.Location = New-Object Drawing.Point(490, 324)
  $lblPercent.Size = New-Object Drawing.Size(40, 20)
  $lblPercent.Visible = $false
  $form.Controls.Add($lblPercent)

  $statusBox = New-Object Windows.Forms.TextBox
  $statusBox.Multiline = $true
  $statusBox.ScrollBars = "Vertical"
  $statusBox.ReadOnly = $true
  $statusBox.BackColor = [Drawing.Color]::FromArgb(18, 20, 26)
  $statusBox.ForeColor = $text
  $statusBox.Font = New-Object Drawing.Font("Consolas", 9)
  $statusBox.Location = New-Object Drawing.Point(24, 352)
  $statusBox.Size = New-Object Drawing.Size(500, 200)
  $statusBox.BorderStyle = "FixedSingle"
  $form.Controls.Add($statusBox)

  $lblStatus = New-Object Windows.Forms.Label
  $lblStatus.Text = "Checking..."
  $lblStatus.ForeColor = $muted
  $lblStatus.Location = New-Object Drawing.Point(24, 564)
  $lblStatus.AutoSize = $true
  $form.Controls.Add($lblStatus)

  function Invoke-HiddenPowerShell {
    param([string[]]$ArgumentList, [string]$Activity)
    Set-ProgressMarquee $Activity
    $p = Start-Process -FilePath "powershell.exe" -ArgumentList $ArgumentList -PassThru -WorkingDirectory $Paths.ProjectRoot
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while (-not $p.HasExited) {
      $lblBusy.Text = ("{0} ({1}s)" -f $Activity, [int]$sw.Elapsed.TotalSeconds)
      [Windows.Forms.Application]::DoEvents()
      Start-Sleep -Milliseconds 400
    }
    $p.WaitForExit() | Out-Null
    Set-Progress 100 100 "Done"
    return $p.ExitCode
  }

  $btnSetup.Add_Click({
    Run-Job "Setup" {
      $setupPath = Join-Path $Paths.ScriptDir "setup.ps1"
      $a = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $setupPath)
      $code = Invoke-HiddenPowerShell -ArgumentList $a -Activity "Setup"
      if ($code -eq 0) { Log "Setup finished successfully" "OK"; Update-Bar }
      else { Log ("Setup failed (exit " + $code + "). Click Log.") "ERROR" }
    }
  })

  $btnRebuild.Add_Click({
    Run-Job "Rebuild" {
      $setupPath = Join-Path $Paths.ScriptDir "setup.ps1"
      $a = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $setupPath, "-Rebuild")
      $code = Invoke-HiddenPowerShell -ArgumentList $a -Activity "Rebuild"
      if ($code -eq 0) { Log "Rebuild finished successfully" "OK"; Update-Bar }
      else { Log ("Rebuild failed (exit " + $code + ").") "ERROR" }
    }
  })

  $btnProcess.Add_Click({
    Run-Job "Process" {
      $files = @(Get-ChildItem -LiteralPath $Paths.InputDir -Filter "*.txt" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "~*" -and $_.Name -notlike "_smoke*" -and $_.Length -gt 0 })
      if ($files.Count -eq 0) { Log "No .txt in Input" "WARN"; return }
      $n = 0; $f = 0; $total = $files.Count; $i = 0
      Set-Progress 0 $total "Starting..."
      foreach ($file in $files) {
        $i++
        Set-Progress ($i - 1) $total ("Processing " + $file.Name + " (" + $i + " of " + $total + ")")
        Log ("Input: " + $file.Name)
        if (Invoke-HTProcessFile -FilePath $file.FullName -Paths $Paths -Config $Config -OpenExcel:($chkExcel.Checked)) { $n++ }
        else { $f++ }
        Set-Progress $i $total ("Done " + $file.Name)
      }
      Log ("Batch done - OK=" + $n + " Failed=" + $f) "OK"
    }
  })

  $btnInput.Add_Click({
    if (-not (Test-Path -LiteralPath $Paths.InputDir)) { New-Item -ItemType Directory -Path $Paths.InputDir -Force | Out-Null }
    Start-Process explorer.exe $Paths.InputDir
  })
  $btnOutput.Add_Click({
    if (-not (Test-Path -LiteralPath $Paths.OutputDir)) { New-Item -ItemType Directory -Path $Paths.OutputDir -Force | Out-Null }
    Start-Process explorer.exe $Paths.OutputDir
  })
  $btnLog.Add_Click({
    if (Test-Path -LiteralPath $Paths.LogFile) { Start-Process notepad.exe $Paths.LogFile }
    else { Log "No log yet" "WARN" }
  })

  $chkWatch.Add_CheckedChanged({
    if ($chkWatch.Checked) { $chkWatch.ForeColor = $okC; Start-Watch }
    else { $chkWatch.ForeColor = $muted; Stop-Watch }
  })

  $form.Add_Shown({
    try { Update-Bar } catch {}
    if ($chkWatch.Checked) { try { Start-Watch } catch { Log ("Watch start failed: " + $_.Exception.Message) "WARN" } }
    Log "Ready - save .txt in Input to process." "OK"
  })
  $form.Add_FormClosed({ try { Stop-Watch } catch {}; $global:HT_GuiLog = $null })

  $ico = Join-Path $Paths.ProjectRoot "assets\app.ico"
  if (Test-Path -LiteralPath $ico) {
    try { $form.Icon = New-Object Drawing.Icon($ico) } catch {}
  }

  [void]$form.ShowDialog()
}
catch {
  Write-GuiCrashLog $_.Exception.Message
  Write-GuiCrashLog $_.ScriptStackTrace
  try {
    [Windows.Forms.MessageBox]::Show(
      ("GUI failed:`n`n" + $_.Exception.Message + "`n`nSee data\output\gui-error.log"),
      "Human Translator"
    ) | Out-Null
  } catch {
    Write-Host ("GUI failed: " + $_.Exception.Message)
    Read-Host "Press Enter"
  }
  exit 1
}
