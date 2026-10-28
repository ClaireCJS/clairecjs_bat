# Diagnostic side-by-side identity. Does not replace the selected package.
$ErrorActionPreference = 'Stop'
$output = Join-Path $PSScriptRoot ('recovery-probe-' + (Get-Date -Format yyyyMMddHHmmss))
if (Test-Path -LiteralPath $output) { throw 'Output exists.' }
$stage = New-Item -ItemType Directory -Path (Join-Path $output 'package')
$runtime = New-Item -ItemType Directory -Path (Join-Path $output 'runtime')
$source = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'DesktopHost.cs') -Raw).Replace(
    'ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2', 'ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2').Replace(
    'Local\PAFPlayerLockScreenPublisher','Local\PAFPlayerLockScreenRecoveryPublisher').Replace(
    'PAFPlayer Lock Screen V510','PAFPlayer Lock Screen Recovery Test')
$source | Set-Content -LiteralPath (Join-Path $output 'DesktopHost.cs') -Encoding UTF8
$embedded = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'DesktopHost.manifest') -Raw).Replace(
    'packageName="ClaireCJS.PAFPlayer.LockScreen"', 'packageName="ClaireCJS.PAFPlayer.LockScreen.Recovery"').Replace('510.0.0.5','511.0.0.0')
$embedded | Set-Content -LiteralPath (Join-Path $output 'DesktopHost.manifest') -Encoding UTF8
$manifest = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'DesktopPackage.appxmanifest') -Raw).Replace(
    'Name="ClaireCJS.PAFPlayer.LockScreen"', 'Name="ClaireCJS.PAFPlayer.LockScreen.Recovery"').Replace('510.0.0.5','511.0.0.0').Replace(
    'DisplayName="PAFPlayer Lock Screen"', 'DisplayName="PAFPlayer Lock Screen Recovery"').Replace(
    '<DisplayName>PAFPlayer Lock Screen</DisplayName>', '<DisplayName>PAFPlayer Lock Screen Recovery</DisplayName>')
$manifest | Set-Content -LiteralPath (Join-Path $stage 'AppxManifest.xml') -Encoding UTF8
$framework = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319"
$sdk = "${env:ProgramFiles(x86)}\Windows Kits\10"
$refs = @('System.dll','System.Core.dll','System.Net.Http.dll','System.Drawing.dll','System.Windows.Forms.dll',
    "$framework\System.Runtime.dll", "$framework\System.Runtime.WindowsRuntime.dll", "$framework\System.Runtime.InteropServices.WindowsRuntime.dll",
    "$sdk\UnionMetadata\10.0.26100.0\Windows.winmd")
$compilerArgs = @('/nologo','/target:winexe','/platform:x64','/optimize+',('/win32manifest:' + (Join-Path $output 'DesktopHost.manifest')),('/out:' + (Join-Path $runtime 'PAFPlayerLockScreen.exe')))
foreach ($reference in $refs) { $compilerArgs += '/r:' + $reference }
& "$framework\csc.exe" @compilerArgs (Join-Path $output 'DesktopHost.cs') (Join-Path $PSScriptRoot 'StatusUpdater.cs')
if ($LASTEXITCODE) { throw 'Compilation failed.' }
New-Item -ItemType Directory -Path (Join-Path $stage 'Assets') | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot 'Assets\PAF*.png') | Copy-Item -Destination (Join-Path $stage 'Assets')
Copy-Item -LiteralPath (Join-Path $stage 'Assets') -Destination $runtime -Recurse
& "$sdk\bin\10.0.26100.0\x64\makeappx.exe" pack /nv /d $stage.FullName /p (Join-Path $output 'RecoveryIdentity.msix')
if ($LASTEXITCODE) { throw 'Packaging failed.' }
Write-Output $output
