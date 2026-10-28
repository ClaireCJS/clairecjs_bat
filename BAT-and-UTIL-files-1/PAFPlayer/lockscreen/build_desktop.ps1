param([string]$OutputDirectory, [string]$SigningThumbprint)
$ErrorActionPreference = 'Stop'
if (!$OutputDirectory) { $OutputDirectory = Join-Path $PSScriptRoot ('build-v530-' + (Get-Date -Format yyyyMMddHHmmss)) }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Build directory already exists; choose a new name.' }
$stage = New-Item -ItemType Directory -Path (Join-Path $OutputDirectory 'package')
$runtime = New-Item -ItemType Directory -Path (Join-Path $OutputDirectory 'runtime')
$framework = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319"
$sdk = "${env:ProgramFiles(x86)}\Windows Kits\10"
$references = @('System.dll','System.Core.dll','System.Net.Http.dll','System.Drawing.dll','System.Windows.Forms.dll',
    "$framework\System.Runtime.dll", "$framework\System.Runtime.WindowsRuntime.dll", "$framework\System.Runtime.InteropServices.WindowsRuntime.dll",
    "$sdk\UnionMetadata\10.0.26100.0\Windows.winmd")
$compilerArgs = @('/nologo','/target:winexe','/platform:x64','/optimize+',('/win32manifest:' + (Join-Path $PSScriptRoot 'DesktopHost.manifest')),('/out:' + (Join-Path $runtime 'PAFPlayerLockScreen.exe')))
foreach ($reference in $references) { $compilerArgs += '/r:' + $reference }
& "$framework\csc.exe" @compilerArgs (Join-Path $PSScriptRoot 'DesktopHost.cs') (Join-Path $PSScriptRoot 'DesktopBackground.cs') (Join-Path $PSScriptRoot 'ManagedPublisher.cs') (Join-Path $PSScriptRoot 'StatusUpdater.cs')
if ($LASTEXITCODE) { throw "C# compilation failed: $LASTEXITCODE" }
function Sign-NewBuildFile([string]$Path) {
    if (!$SigningThumbprint) { return }
    $stem = $Path + '.bak.' + (Get-Date -Format yyyyMMddHHmm) + '.replaced-by-chatgpt'
    $backup = $stem + '.bak'
    for ($n=1; Test-Path -LiteralPath $backup; $n++) { $backup = $stem + " ($n).bak" }
    [IO.File]::Copy($Path, $backup, $false)
    if ((Get-FileHash -LiteralPath $Path).Hash -ne (Get-FileHash -LiteralPath $backup).Hash) { throw 'Signing backup verification failed.' }
    & "$sdk\bin\10.0.26100.0\x64\signtool.exe" sign /fd SHA256 /sha1 $SigningThumbprint $Path
    if ($LASTEXITCODE) { throw 'Signing failed.' }
    & "$sdk\bin\10.0.26100.0\x64\signtool.exe" verify /pa $Path
    if ($LASTEXITCODE) { throw 'Signature verification failed.' }
}
Sign-NewBuildFile (Join-Path $runtime 'PAFPlayerLockScreen.exe')
Copy-Item -LiteralPath (Join-Path $runtime 'PAFPlayerLockScreen.exe') -Destination $stage
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'DesktopPackage.appxmanifest') -Destination (Join-Path $stage 'AppxManifest.xml')
New-Item -ItemType Directory -Path (Join-Path $stage 'Assets') | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot 'Assets\PAF*.png') | Copy-Item -Destination (Join-Path $stage 'Assets')
$package = Join-Path $OutputDirectory 'PAFPlayerLockScreen_v530_x64.msix'
# The executable and assets are owned by Windows in a complete MSIX package.
# Full semantic validation stays enabled; no external-location argument is used.
& "$sdk\bin\10.0.26100.0\x64\makeappx.exe" pack /d $stage.FullName /p $package
if ($LASTEXITCODE) { throw "Package validation failed: $LASTEXITCODE" }
Sign-NewBuildFile $package
Write-Output $package
