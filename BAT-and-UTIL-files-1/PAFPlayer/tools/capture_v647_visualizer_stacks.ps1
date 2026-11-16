param([ValidateRange(5,60)][int]$Seconds = 30)
$ErrorActionPreference = 'Stop'
$project = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$profiler = Join-Path $project 'tests\runs\v647-profiler-20261109\py-spy.exe'
$expected = '0890578CA20BF839D7F890BBCDB508A21CB9F1B71F99BF32BE371C5E492A0B48'
if ((Get-FileHash -LiteralPath $profiler -Algorithm SHA256).Hash -ne $expected) {
    throw 'Profiler hash mismatch; capture cancelled.'
}
$hello = Invoke-RestMethod 'http://127.0.0.1:666/api/remote-tray/hello?timeline=0' -TimeoutSec 5
if ($hello.official -ne $true -or $hello.program -ine 'PAFPlayer') {
    throw 'The local endpoint is not the verified official PAFPlayer.'
}
$diagnostics = Invoke-RestMethod 'http://127.0.0.1:666/api/runtime-diagnostics' -TimeoutSec 5
$playerPid = [int]$diagnostics.pid
if ($playerPid -le 0) { throw 'No valid player process ID.' }
$null = Get-Process -Id $playerPid
$reports = Join-Path $project 'tests\reports'
$stem = 'v647-interactive-stacks-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$output = Join-Path $reports ($stem + '.json')
$collision = 0
while (Test-Path -LiteralPath $output) {
    $collision++
    $output = Join-Path $reports ($stem + ' (' + $collision + ').json')
}
Write-Host "Sampling $($hello.version), PID $playerPid, for $Seconds seconds. Keep the problem displays running."
# Reads stacks without injecting code, pausing the process, or collecting locals.
# No player POST, settings write, security change, or process termination.
& $profiler record --pid $playerPid --nonblocking --threads --idle --rate 50 --duration $Seconds --format speedscope --output $output
if ($LASTEXITCODE -ne 0) {
    throw 'Stack capture failed. No security settings were changed; report the error to Codex.'
}
if (-not (Test-Path -LiteralPath $output)) { throw 'Profiler produced no report.' }
Write-Host "Saved $output"
