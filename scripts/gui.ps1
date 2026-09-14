# ============================================================
# gui.ps1 - Human Translator (WinForms) + integrated auto-watch
# ============================================================
$ErrorActionPreference = "Stop"
function Write-GuiCrashLog([string]$Message) {
  try {
    $root = Split-Path $PSScriptRoot -Parent
    $dir = Join-Path $root "data\output"
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Add-Content (Join-Path $dir "gui-error.log") ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message) -Encoding UTF8
  } catch {}
}
try {
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
  [System.Windows.Forms.Application]::EnableVisualStyles()
  . "$PSScriptRoot\common.ps1"
  $Paths = Get-HTPaths; $Config = Get-HTConfig $Paths
  Ensure-HTDirs $Paths; Set-Location $Paths.ProjectRoot

  $bg=[Drawing.Color]::FromArgb(24,26,32); $panelBg=[Drawing.Color]::FromArgb(36,40,48)
  $accent=[Drawing.Color]::FromArgb(88,166,255); $ok=[Drawing.Color]::FromArgb(63,185,80)
  $warn=[Drawing.Color]::FromArgb(210,153,34); $bad=[Drawing.Color]::FromArgb(248,81,73)
  $text=[Drawing.Color]::FromArgb(230,237,243); $muted=[Drawing.Color]::FromArgb(139,148,158)
  $btnBg=[Drawing.Color]::FromArgb(48,54,64)

  function New-Btn($T,$X,$Y,$W,$H,$Back,$Fore) {
    $b=New-Object Windows.Forms.Button; $b.Text=$T; $b.Location=New-Object Drawing.Point($X,$Y)
    $b.Size=New-Object Drawing.Size($W,$H); $b.FlatStyle='Flat'; $b.FlatAppearance.BorderSize=0
    $b.BackColor=$Back; $b.ForeColor=$Fore; $b.Font=New-Object Drawing.Font('Segoe UI',10,[Drawing.FontStyle]::Bold)
    $b.Cursor='Hand'; return $b
  }
  function Log($m,$lvl='INFO') {
    $p=switch($lvl){'OK'{'[OK]'}'ERROR'{'[ERR]'}'WARN'{'[!]'}default{'[...]'}}
    $statusBox.AppendText(("[{0}] {1} {2}`r`n" -f (Get-Date -Format 'HH:mm:ss'), $p, $m))
    $statusBox.SelectionStart=$statusBox.Text.Length; $statusBox.ScrollToCaret()
    [Windows.Forms.Application]::DoEvents()
    try { Write-HTLog $m $lvl $Paths } catch {}
  }
  function Update-Bar {
    $d=$false;$i=$false
    try{$d=Test-HTDocker $Paths}catch{}; try{$i=Test-HTImage $Paths}catch{}
    $b=Test-Path $Paths.BookFile
    $lblStatus.Text = "$(if($d){'Docker OK'}else{'Docker missing'}) | $(if($i){'Image OK'}else{'Image missing'}) | $(if($b){'Book1 OK'}else{'Book1 missing'})"
    $lblStatus.ForeColor = if($d -and $i -and $b){$ok}elseif($d){$warn}else{$bad}
  }
  $script:busy=$false; $script:watchProc=$false
  $script:pending=@{}; $script:lastDone=@{}; $script:sync=New-Object object
  $script:fsW=$null; $script:tmr=$null

  function Enq([string]$p) {
    if(-not $p){return}; $n=[IO.Path]::GetFileName($p)
    if($n -like '~*' -or $n -like '.*' -or $n -like '_smoke*' -or $n -notlike '*.txt'){return}
    [Threading.Monitor]::Enter($script:sync)
    try{$script:pending[$p]=[DateTime]::UtcNow.Ticks}finally{[Threading.Monitor]::Exit($script:sync)}
  }
  function Stop-Watch {
    if($script:tmr){$script:tmr.Stop(); $script:tmr.Dispose(); $script:tmr=$null}
    if($script:fsW){$script:fsW.EnableRaisingEvents=$false; $script:fsW.Dispose(); $script:fsW=$null}
    Log 'Auto-watch OFF' 'WARN'
  }
  function Start-Watch {
    if($script:fsW){return}
    if(-not (Test-Path $Paths.InputDir)){New-Item -ItemType Directory -Path $Paths.InputDir -Force|Out-Null}
    Get-ChildItem $Paths.InputDir -Filter '*.txt' -ea 0|%{ if($_.Name -notlike '~*' -and $_.Name -notlike '_smoke*'){ $script:lastDone[$_.FullName]=$_.LastWriteTimeUtc }}
    $w=New-Object IO.FileSystemWatcher; $w.Path=$Paths.InputDir; $w.Filter='*.txt'; $w.IncludeSubdirectories=$false
    $w.NotifyFilter=[IO.NotifyFilters]::LastWrite -bor [IO.NotifyFilters]::FileName -bor [IO.NotifyFilters]::Size
    $w.SynchronizingObject=$form
    $w.Add_Changed({Enq $EventArgs.FullPath}); $w.Add_Created({Enq $EventArgs.FullPath}); $w.Add_Renamed({Enq $EventArgs.FullPath})
    $w.EnableRaisingEvents=$true; $script:fsW=$w
    $t=New-Object Windows.Forms.Timer; $t.Interval=300
    $t.Add_Tick({
      if($script:watchProc -or $script:busy -or -not $chkWatch.Checked){return}
      $db=900; try{$db=[int]$Config.DebounceMs}catch{}; if($db -lt 300){$db=300}
      $now=[DateTime]::UtcNow.Ticks; $ready=@()
      [Threading.Monitor]::Enter($script:sync)
      try{ foreach($k in @($script:pending.Keys)){ if((($now-$script:pending[$k])/10000.0) -ge $db){ $ready+=$k; $script:pending.Remove($k) } } }
      finally{[Threading.Monitor]::Exit($script:sync)}
      Get-ChildItem $Paths.InputDir -Filter '*.txt' -ea 0|%{
        if($_.Name -like '~*' -or $_.Name -like '.*' -or $_.Name -like '_smoke*'){return}
        $f=$_.FullName; $lw=$_.LastWriteTimeUtc
        if(-not $script:lastDone.ContainsKey($f) -or $script:lastDone[$f] -ne $lw){ if($f -notin $ready){ $ready+=$f } }
      }
      foreach($fp in $ready){
        $it=Get-Item -LiteralPath $fp -ea 0; if(-not $it -or $it.Length -eq 0){continue}
        $lw=$it.LastWriteTimeUtc
        if($script:lastDone.ContainsKey($fp) -and $script:lastDone[$fp] -eq $lw){continue}
        $script:watchProc=$true
        try {
          Log "Auto: $($it.Name)"
          $ok=Invoke-HTProcessFile -FilePath $fp -Paths $Paths -Config $Config -OpenExcel:($chkExcel.Checked)
          if($ok){ $script:lastDone[$fp]=$lw; Log "Done: $($it.Name)" 'OK'; Update-Bar }
          else { Log "Failed: $($it.Name)" 'ERROR' }
        } catch { Log "Watch error: $($_.Exception.Message)" 'ERROR' }
        finally { $script:watchProc=$false }
      }
    })
    $script:tmr=$t; $t.Start(); Log 'Auto-watch ON — save .txt in Input' 'OK'
  }

  $form=New-Object Windows.Forms.Form
  $form.Text='Human Translator'; $form.Size=New-Object Drawing.Size(560,640)
  $form.StartPosition='CenterScreen'; $form.BackColor=$bg; $form.ForeColor=$text
  $form.FormBorderStyle='FixedSingle'; $form.MaximizeBox=$false; $form.Font=New-Object Drawing.Font('Segoe UI',9)

  $lblTitle=New-Object Windows.Forms.Label; $lblTitle.Text='Human Translator'
  $lblTitle.Font=New-Object Drawing.Font('Segoe UI',18,[Drawing.FontStyle]::Bold)
  $lblTitle.ForeColor=$accent; $lblTitle.Location=New-Object Drawing.Point(24,16); $lblTitle.AutoSize=$true
  $form.Controls.Add($lblTitle)

  $lblSub=New-Object Windows.Forms.Label; $lblSub.Text='Quantifier Tagger · Offline Windows'
  $lblSub.ForeColor=$muted; $lblSub.Location=New-Object Drawing.Point(26,50); $lblSub.AutoSize=$true
  $form.Controls.Add($lblSub)

  $panel=New-Object Windows.Forms.Panel; $panel.Location=New-Object Drawing.Point(24,80)
  $panel.Size=New-Object Drawing.Size(500,160); $panel.BackColor=$panelBg; $form.Controls.Add($panel)

  $btnSetup=New-Btn 'Setup (once)' 20 20 220 40 $accent ([Drawing.Color]::FromArgb(10,20,40))
  $btnRebuild=New-Btn 'Rebuild Image' 260 20 220 40 $btnBg $text
  $btnProcess=New-Btn 'Process Once' 20 75 460 40 $btnBg $text
  $btnInput=New-Btn 'Input' 20 125 145 32 $btnBg $muted
  $btnOutput=New-Btn 'Output' 177 125 145 32 $btnBg $muted
  $btnLog=New-Btn 'Log' 334 125 146 32 $btnBg $muted
  $panel.Controls.AddRange(@($btnSetup,$btnRebuild,$btnProcess,$btnInput,$btnOutput,$btnLog))

  $chkWatch=New-Object Windows.Forms.CheckBox
  $chkWatch.Text='Auto-watch Input (process on Save) — ON by default'
  $chkWatch.ForeColor=$ok; $chkWatch.Location=New-Object Drawing.Point(28,250); $chkWatch.AutoSize=$true; $chkWatch.Checked=$true
  $form.Controls.Add($chkWatch)

  $chkExcel=New-Object Windows.Forms.CheckBox
  $chkExcel.Text='Open Excel automatically after each process'
  $chkExcel.ForeColor=$muted; $chkExcel.Location=New-Object Drawing.Point(28,274); $chkExcel.AutoSize=$true
  $chkExcel.Checked=[bool]$Config.OpenExcel; $form.Controls.Add($chkExcel)

  $statusBox=New-Object Windows.Forms.TextBox
  $statusBox.Multiline=$true; $statusBox.ScrollBars='Vertical'; $statusBox.ReadOnly=$true
  $statusBox.BackColor=[Drawing.Color]::FromArgb(18,20,26); $statusBox.ForeColor=$text
  $statusBox.Font=New-Object Drawing.Font('Consolas',9)
  $statusBox.Location=New-Object Drawing.Point(24,310); $statusBox.Size=New-Object Drawing.Size(500,250)
  $statusBox.BorderStyle='FixedSingle'; $form.Controls.Add($statusBox)

  $lblStatus=New-Object Windows.Forms.Label; $lblStatus.Text='...'; $lblStatus.ForeColor=$muted
  $lblStatus.Location=New-Object Drawing.Point(24,570); $lblStatus.AutoSize=$true; $form.Controls.Add($lblStatus)

  function Run-Job($msg, $work) {
    if($script:busy){ Log 'Busy - wait' 'WARN'; return }
    $script:busy=$true
    try { & $work } catch { Log $_.Exception.Message 'ERROR' }
    finally { $script:busy=$false; Update-Bar }
  }

  $btnSetup.Add_Click({ Run-Job 'Setup' { 
    $a=@('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $Paths.ScriptDir 'setup.ps1'))
    Log 'Setup started...'; $p=Start-Process powershell.exe -ArgumentList $a -Wait -PassThru -WorkingDirectory $Paths.ProjectRoot
    if($p.ExitCode -eq 0){Log 'Setup OK' 'OK'} else {Log "Setup failed $($p.ExitCode)" 'ERROR'}
  }})
  $btnRebuild.Add_Click({ Run-Job 'Rebuild' {
    $a=@('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $Paths.ScriptDir 'setup.ps1'),'-Rebuild')
    Log 'Rebuild started...'; $p=Start-Process powershell.exe -ArgumentList $a -Wait -PassThru -WorkingDirectory $Paths.ProjectRoot
    if($p.ExitCode -eq 0){Log 'Rebuild OK' 'OK'} else {Log "Rebuild failed" 'ERROR'}
  }})
  $btnProcess.Add_Click({ Run-Job 'Process' {
    $files=@(Get-ChildItem $Paths.InputDir -Filter '*.txt' -ea 0 | ?{ $_.Name -notlike '~*' -and $_.Name -notlike '_smoke*' -and $_.Length -gt 0 })
    if($files.Count -eq 0){ Log 'No .txt in Input' 'WARN'; return }
    $n=0;$f=0
    foreach($file in $files){
      Log "Process: $($file.Name)"
      if(Invoke-HTProcessFile -FilePath $file.FullName -Paths $Paths -Config $Config -OpenExcel:($chkExcel.Checked)){ $n++ } else { $f++ }
    }
    Log "Done OK=$n Fail=$f" 'OK'
  }})
  $btnInput.Add_Click({ if(-not (Test-Path $Paths.InputDir)){New-Item -ItemType Directory $Paths.InputDir -Force|Out-Null}; Start-Process explorer.exe $Paths.InputDir })
  $btnOutput.Add_Click({ if(-not (Test-Path $Paths.OutputDir)){New-Item -ItemType Directory $Paths.OutputDir -Force|Out-Null}; Start-Process explorer.exe $Paths.OutputDir })
  $btnLog.Add_Click({ if(Test-Path $Paths.LogFile){Start-Process notepad.exe $Paths.LogFile} else {Log 'No log yet' 'WARN'} })

  $chkWatch.Add_CheckedChanged({
    if($chkWatch.Checked){ $chkWatch.ForeColor=$ok; Start-Watch } else { $chkWatch.ForeColor=$muted; Stop-Watch }
  })

  $form.Add_Shown({
    Update-Bar
    if($chkWatch.Checked){ Start-Watch }
    Log 'Ready — Auto-watch ON. Save .txt in Input to process.' 'OK'
    Log 'Tick Open Excel to auto-open results after each process.'
  })
  $form.Add_FormClosed({ try{Stop-Watch}catch{} })
  $ico=Join-Path $Paths.ProjectRoot 'assets\app.ico'
  if(Test-Path $ico){ try{$form.Icon=New-Object Drawing.Icon($ico)}catch{} }
  [void]$form.ShowDialog()
} catch {
  Write-GuiCrashLog $_.Exception.Message
  try { [Windows.Forms.MessageBox]::Show("GUI failed:`n$($_.Exception.Message)`nSee data\output\gui-error.log")|Out-Null } catch {}
  exit 1
}
