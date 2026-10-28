param([switch]$Apply)
# Targeted Windows-managed uninstall/reinstall. Requires explicit approval of
# the exception to the Recycle Bin rule for Windows-owned package files.
$ErrorActionPreference = 'Stop'
$env:PSModulePath = $env:WINDIR + '\System32\WindowsPowerShell\v1.0\Modules'
$name = 'ClaireCJS.PAFPlayer.LockScreen'
$family = 'ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2'
$build = Join-Path $PSScriptRoot 'build-v510-20261006222741'
$package = Join-Path $build 'PAFPlayerLockScreen_v510_x64.msix'
$runtime = Join-Path $build 'runtime'
$current = Get-AppxPackage -Name $name
if (!$current -or $current.PackageFamilyName -ne $family) { throw 'Expected installed package is missing.' }
if (!(Test-Path -LiteralPath $package)) { throw 'Recovery package is missing.' }
$signature = Get-AuthenticodeSignature -LiteralPath $package
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Thumbprint -ne '08AC642F1C17B503BC857189AE8C78E76B3358EC') { throw 'Recovery signature verification failed.' }
if (!$Apply) { Write-Output "Plan: preserve app data, then recreate only $($current.PackageFullName) using the same signed package and identity."; exit 0 }
$archive = Join-Path $PSScriptRoot ('registration-recovery-' + (Get-Date -Format yyyyMMddHHmmss))
if (Test-Path -LiteralPath $archive) { throw 'Recovery folder exists; rerun with a new timestamp.' }
New-Item -ItemType Directory -Path $archive | Out-Null
$data = Join-Path $env:LOCALAPPDATA ('Packages\' + $family)
if (Test-Path -LiteralPath $data) {
    Copy-Item -LiteralPath $data -Destination (Join-Path $archive 'app-data') -Recurse
    foreach ($file in Get-ChildItem -LiteralPath $data -Recurse -Force -File) {
        $relative = $file.FullName.Substring($data.Length + 1)
        $copy = Join-Path (Join-Path $archive 'app-data') $relative
        if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath $copy).Hash) { throw 'Recovery data verification failed.' }
    }
}
$current | Select-Object PackageFullName,PackageFamilyName,Status | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $archive 'previous-package.json')
Remove-AppxPackage -Package $current.PackageFullName -ErrorAction Stop
Add-AppxPackage -Path $package -ExternalLocation $runtime -ErrorAction Stop
Write-Output "Saved app data at $archive. Package registration recreated; activation still needs verification."
