$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format yyyyMMddHHmmss
$report = Join-Path (Split-Path $PSScriptRoot) ('tests\reports\v515-lock-processes-' + $stamp + '.jsonl')
$stream = [IO.StreamWriter]::new([IO.File]::Open($report, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write))
$deadline = (Get-Date).AddMinutes(4)
$previous = ''
try {
    while ((Get-Date) -lt $deadline) {
        $state = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -in @('LockApp','LogonUI','PAFPlayerLockScreen')} | Sort-Object Id | Select-Object ProcessName,Id,SessionId)
        $key = $state | ConvertTo-Json -Compress
        if ($key -ne $previous) {
            $stream.WriteLine((@{time=(Get-Date).ToString('o');processes=$state} | ConvertTo-Json -Depth 4 -Compress))
            $stream.Flush()
            $previous = $key
        }
        Start-Sleep -Seconds 1
    }
} finally { $stream.Dispose() }
Write-Output $report
