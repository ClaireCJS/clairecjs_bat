$ErrorActionPreference = 'Stop'
$lockscreenRoot = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format yyyyMMddHHmmss
$folder = Join-Path $lockscreenRoot ('archive\staging\test-build-' + $stamp)
if (Test-Path -LiteralPath $folder) { throw 'Test build directory exists.' }
New-Item -ItemType Directory -Path $folder | Out-Null
$framework = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319"
$sdk = "${env:ProgramFiles(x86)}\Windows Kits\10"
$refs = @('System.dll','System.Core.dll','System.Net.Http.dll','System.Drawing.dll','System.Windows.Forms.dll',
    "$framework\System.Runtime.dll", "$framework\System.Runtime.WindowsRuntime.dll", "$framework\System.Runtime.InteropServices.WindowsRuntime.dll",
    "$sdk\UnionMetadata\10.0.26100.0\Windows.winmd")
$exe = Join-Path $folder 'StatusUpdaterTests.exe'
$compilerArgs = @('/nologo','/target:exe','/platform:x64','/main:PAFPlayerLockScreen.StatusUpdaterTests',('/out:' + $exe))
foreach ($ref in $refs) { $compilerArgs += '/r:' + $ref }
& "$framework\csc.exe" @compilerArgs (Join-Path $lockscreenRoot 'StatusUpdater.cs') (Join-Path $PSScriptRoot 'StatusUpdaterTests.cs') (Join-Path $lockscreenRoot 'ManagedPublisher.cs') (Join-Path $lockscreenRoot 'DesktopHost.cs') (Join-Path $lockscreenRoot 'DesktopBackground.cs')
if ($LASTEXITCODE) { throw 'Test compilation failed.' }
$report = Join-Path (Split-Path $lockscreenRoot) ('tests\reports\v530-status-updater-' + $stamp + '.txt')
if (Test-Path -LiteralPath $report) { throw 'Report exists.' }
& $exe | Tee-Object -FilePath $report
if ($LASTEXITCODE) { throw "Tests failed; see $report" }
