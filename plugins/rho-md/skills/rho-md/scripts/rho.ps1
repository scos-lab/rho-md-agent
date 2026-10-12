# Rho MD client without node (Windows). Same arguments and exit codes as rho.mjs:
#   powershell -NoProfile -ExecutionPolicy Bypass -File rho.ps1 [--client NAME] <command-id> ['<json args>'] | --status | --launch
# Exit: 0 done / 1 failed or declined / 2 not running / 3 not allowed / 4 usage.
$ErrorActionPreference = 'Stop'
$Id = 'md.rho.app'
$client = ''
$rest = @()
for ($i = 0; $i -lt $args.Count; $i++) {
  if ($args[$i] -eq '--client') { $client = [string]$args[$i + 1]; $i++ } else { $rest += [string]$args[$i] }
}
if (-not $client) {
  if ($env:CLAUDECODE -eq '1') { $client = 'claude-code' }
  elseif (Get-ChildItem Env: | Where-Object { $_.Name -like 'CODEX_*' }) { $client = 'codex' }
  else { $client = 'ai-tool' }
}
$client = ($client.ToLower() -replace '[^a-z0-9]+', '-').Trim('-')
$label = switch ($client) { 'codex' { 'Codex' } 'claude-code' { 'Claude Code' } default { $client } }

function Find-Discovery {
  $dirs = @()
  if ($env:RHO_MD_DATA_DIR) { $dirs += $env:RHO_MD_DATA_DIR }
  $local = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME 'AppData\Local' }
  $dirs += (Join-Path $local $Id)
  # Microsoft Store copies keep the app's LocalAppData under the package's LocalCache.
  $pk = Join-Path $local 'Packages'
  if (Test-Path $pk) { Get-ChildItem $pk -Directory | ForEach-Object { $dirs += (Join-Path $_.FullName "LocalCache\Local\$Id") } }
  $files = $dirs | ForEach-Object { Join-Path $_ 'agent-connect.json' } | Where-Object { Test-Path $_ } | Get-Item | Sort-Object LastWriteTime -Descending
  if (-not $files) { return $null }
  try { return Get-Content -Raw $files[0].FullName | ConvertFrom-Json } catch { return $null }
}

function Not-Running {
  [Console]::Error.WriteLine("Rho MD is not running, or 'Allow AI tools to use Rho MD' is off in its Settings > AI tools.")
  [Console]::Error.WriteLine("Start it with: powershell -File `"$PSCommandPath`" --launch. If Rho MD is not installed, it has to be installed first (the skill gives the link).")
  exit 2
}

function Open-Session($info, [string]$line) {
  $tcp = New-Object System.Net.Sockets.TcpClient
  $tcp.Connect('127.0.0.1', [int]$info.port)
  $stream = $tcp.GetStream()
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  $w = New-Object System.IO.StreamWriter($stream, $utf8); $w.NewLine = "`n"; $w.AutoFlush = $true
  $r = New-Object System.IO.StreamReader($stream, $utf8)
  $hello = @{ token = $info.token; client = $client; label = $label } | ConvertTo-Json -Compress
  $w.WriteLine("hello $hello")
  $first = $r.ReadLine()
  $second = $null
  if ($first -and $first.StartsWith('ok') -and $line) { $w.WriteLine($line); $second = $r.ReadLine() }
  $tcp.Close()
  return @($first, $second)
}

if ($rest.Count -gt 0 -and $rest[0] -eq '--launch') {
  $before = Find-Discovery
  Start-Process 'rho://'
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    $now = Find-Discovery
    if ($now -and (-not $before -or $now.token -ne $before.token)) { Write-Output 'ok Rho MD is ready'; exit 0 }
    if ($now -and $before -and $i -ge 6) {
      try { $s = Open-Session $now $null; if ($s[0]) { Write-Output 'ok Rho MD is running'; exit 0 } } catch {}
    }
  }
  [Console]::Error.WriteLine('Rho MD did not start within 20 seconds. If Rho MD is not installed, it has to be installed first (the skill gives the link).')
  exit 2
}

if ($rest.Count -eq 0) { [Console]::Error.WriteLine("usage: rho.ps1 [--client NAME] <command-id> ['<json args>'] | --status | --launch"); exit 4 }
$status = $rest[0] -eq '--status'
$line = $null
if (-not $status) { $line = ($rest -join ' ').Trim() }

$info = Find-Discovery
if (-not $info) { Not-Running }
try { $res = Open-Session $info $line } catch { Not-Running }
$hello = [string]$res[0]
if (-not $hello.StartsWith('ok')) {
  if ($hello.StartsWith('denied')) { Write-Output $hello; exit 3 }
  Not-Running
}
if ($status) { Write-Output $hello; exit 0 }
$reply = [string]$res[1]
if (-not $reply) { [Console]::Error.WriteLine('Rho MD closed the connection before answering'); exit 1 }
Write-Output $reply
if ($reply.StartsWith('executed')) { exit 0 } else { exit 1 }
