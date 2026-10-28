param(
    [string]$Package = (Join-Path $PSScriptRoot 'dist\PAFPlayerLockScreen_v505_x64_r2.msix'),
    [string]$Certificate = (Join-Path $PSScriptRoot 'dist\PAFPlayerLockScreen_v505.cer')
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Package -PathType Leaf)) { throw "Package missing: $Package" }
if (-not (Test-Path -LiteralPath $Certificate -PathType Leaf)) { throw "Public certificate missing: $Certificate" }
$public = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($Certificate)
$trusted = @(
    Get-ChildItem Cert:\CurrentUser\TrustedPeople -ErrorAction SilentlyContinue
    Get-ChildItem Cert:\CurrentUser\Root -ErrorAction SilentlyContinue
) | Where-Object Thumbprint -eq $public.Thumbprint
if (-not $trusted) {
    throw 'The PAFPlayer self-signed certificate is not trusted by this Windows user. Registration was not attempted.'
}
Add-AppxPackage -Path $Package
$installed = Get-AppxPackage -Name 'ClaireCJS.PAFPlayer.LockScreen'
if (-not $installed) { throw 'Windows did not report the PAFPlayer Lock Screen package as registered.' }
$installed | Select-Object Name,Version,PackageFullName
