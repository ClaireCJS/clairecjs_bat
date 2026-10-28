param([switch]$Activate, [string]$Arguments = '')
$ErrorActionPreference = 'Stop'
$env:PSModulePath = "$env:WINDIR\System32\WindowsPowerShell\v1.0\Modules"
$package = Get-AppxPackage -Name 'ClaireCJS.PAFPlayer.LockScreen'
$result = [ordered]@{
    time = (Get-Date).ToString('o')
    user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    session = (Get-Process -Id $PID).SessionId
    enableLUA = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System').EnableLUA
    package = $package.PackageFullName
    status = [string]$package.Status
}
if ($Activate) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[ComImport, Guid("2e941141-7f97-4756-ba1d-9decde894a3d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IActivationManager {
 [PreserveSig] int ActivateApplication([MarshalAs(UnmanagedType.LPWStr)] string app,
 [MarshalAs(UnmanagedType.LPWStr)] string args, uint options, out uint pid);
}
public static class ActivationProbe {
 public static string Run(string app, string args) {
  var manager = (IActivationManager)Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")));
  uint pid; int hr = manager.ActivateApplication(app, args, 0, out pid);
  return string.Format("HRESULT=0x{0:X8}; PID={1}", hr, pid);
 }
}
'@
    $result.activation = [ActivationProbe]::Run($package.PackageFamilyName + '!App', $Arguments)
}
$result | ConvertTo-Json
