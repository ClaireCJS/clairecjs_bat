$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class PafDeviceEnumerator {}
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPafDevices { [PreserveSig] int EnumAudioEndpoints(int flow, uint mask, out IPafDeviceCollection devices); }
[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPafDeviceCollection { [PreserveSig] int GetCount(out uint count); [PreserveSig] int Item(uint index, out IPafDevice device); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPafDevice { [PreserveSig] int Activate(ref Guid iid, uint context, IntPtr parameters, [MarshalAs(UnmanagedType.IUnknown)] out object result); }
[ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPafManager {
    [PreserveSig] int GetAudioSessionControl(IntPtr guid, uint flags, out IntPtr session);
    [PreserveSig] int GetSimpleAudioVolume(IntPtr guid, uint flags, out IntPtr volume);
    [PreserveSig] int GetSessionEnumerator(out IPafSessions sessions);
}
[ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPafSessions { [PreserveSig] int GetCount(out int count); [PreserveSig] int GetSession(int index, [MarshalAs(UnmanagedType.IUnknown)] out object session); }
[ComImport, Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPafSession {
    [PreserveSig] int GetState(out int state);
    [PreserveSig] int GetDisplayName(out IntPtr value);
    [PreserveSig] int SetDisplayName(IntPtr value, IntPtr context);
    [PreserveSig] int GetIconPath(out IntPtr value);
    [PreserveSig] int SetIconPath(IntPtr value, IntPtr context);
    [PreserveSig] int GetGroupingParam(out Guid value);
    [PreserveSig] int SetGroupingParam(ref Guid value, IntPtr context);
    [PreserveSig] int RegisterAudioSessionNotification(IntPtr events);
    [PreserveSig] int UnregisterAudioSessionNotification(IntPtr events);
    [PreserveSig] int GetSessionIdentifier(out IntPtr value);
    [PreserveSig] int GetSessionInstanceIdentifier(out IntPtr value);
    [PreserveSig] int GetProcessId(out uint processId);
}
public class PafAudioSession { public string name; public uint processId; public int state; }
public static class PafMediaProbe {
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern IntPtr FindWindow(string cls, string title);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint msg, UIntPtr wparam, IntPtr lparam, uint flags, uint timeout, out UIntPtr result);
    static void Check(int result) { Marshal.ThrowExceptionForHR(result); }
    static void Release(object value) { if(value != null && Marshal.IsComObject(value)) Marshal.ReleaseComObject(value); }
    public static int WinampState() {
        IntPtr window = FindWindow("Winamp v1.x", null);
        if(window == IntPtr.Zero) return 0;
        UIntPtr result;
        if(SendMessageTimeout(window, 0x400, UIntPtr.Zero, new IntPtr(104), 2, 250, out result) == IntPtr.Zero) return -1;
        return (int)result.ToUInt64();
    }
    public static PafAudioSession[] AudioSessions() {
        var result = new List<PafAudioSession>();
        object enumerator = new PafDeviceEnumerator();
        IPafDeviceCollection devices = null;
        try {
            Check(((IPafDevices)enumerator).EnumAudioEndpoints(0, 1, out devices));
            uint count; Check(devices.GetCount(out count));
            for(uint d=0; d<count; d++) {
                IPafDevice device=null; object manager=null; IPafSessions sessions=null;
                try {
                    Check(devices.Item(d, out device));
                    Guid iid=new Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F");
                    Check(device.Activate(ref iid, 23, IntPtr.Zero, out manager));
                    Check(((IPafManager)manager).GetSessionEnumerator(out sessions));
                    int total; Check(sessions.GetCount(out total));
                    for(int i=0; i<total; i++) {
                        object raw=null;
                        try {
                            Check(sessions.GetSession(i, out raw));
                            IPafSession session=(IPafSession)raw;
                            int state; uint pid;
                            Check(session.GetState(out state)); Check(session.GetProcessId(out pid));
                            if(pid==0) continue;
                            try {
                                using(var process=Process.GetProcessById((int)pid)) {
                                    string name=process.ProcessName.ToLowerInvariant();
                                    if(name=="vlc" || name=="vlcplayer" || name=="chrome" || name=="msedge" || name=="firefox" || name=="brave" || name=="vivaldi" || name=="opera" || name=="librewolf" || name=="waterfox")
                                        result.Add(new PafAudioSession {name=name,processId=pid,state=state});
                                }
                            } catch(ArgumentException) {} // Process exited between enumeration and lookup.
                        } finally { Release(raw); }
                    }
                } finally { Release(sessions); Release(manager); Release(device); }
            }
        } finally { Release(devices); Release(enumerator); }
        return result.ToArray();
    }
}
'@
$manager = $null
$smtcError = ''
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $managerType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]
    $asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
    $task = $asTask.MakeGenericMethod($managerType).Invoke($null, @($managerType::RequestAsync()))
    if (-not $task.Wait(3000)) { throw 'Windows media session request timed out' }
    $manager = $task.Result
} catch { $smtcError = $_.Exception.GetBaseException().Message }
$ownerId = __PAF_OWNER_PID__
$owner = [Diagnostics.Process]::GetProcessById($ownerId)
while (-not $owner.HasExited) {
    $media = @(); $audio = @(); $errors = @(); $winamp = -1
    try { $audio = @([PafMediaProbe]::AudioSessions()) } catch { $errors += $_.Exception.Message }
    try { $winamp = [PafMediaProbe]::WinampState() } catch { $errors += $_.Exception.Message }
    if ($winamp -lt 0) { $errors += 'Winamp did not answer its playback-state query' }
    if ($null -ne $manager) {
        try {
            foreach ($session in $manager.GetSessions()) {
                $media += @{ app = $session.SourceAppUserModelId; state = $session.GetPlaybackInfo().PlaybackStatus.ToString() }
            }
        } catch { $errors += $_.Exception.Message }
    }
    @{ media = $media; audio = $audio; winamp = $winamp; known = ($errors.Count -eq 0); error = ($errors -join '; '); smtc_available = ($null -ne $manager); smtc_error = $smtcError } | ConvertTo-Json -Compress -Depth 5
    [Console]::Out.Flush()
    Start-Sleep -Milliseconds 250
    $owner.Refresh()
}
