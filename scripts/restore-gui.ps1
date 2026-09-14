$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$sb = New-Object System.Text.StringBuilder
for ($i = 0; $i -le 30; $i++) {
  $f = Join-Path $root ("assets\gui.part{0}.b64" -f $i)
  if (Test-Path $f) { [void]$sb.Append(((Get-Content -LiteralPath $f -Raw) -replace '\s','')) }
}
if ($sb.Length -lt 1000) { throw "GUI parts missing" }
$out = Join-Path $PSScriptRoot "gui.ps1"
[System.IO.File]::WriteAllBytes($out, [Convert]::FromBase64String($sb.ToString()))
