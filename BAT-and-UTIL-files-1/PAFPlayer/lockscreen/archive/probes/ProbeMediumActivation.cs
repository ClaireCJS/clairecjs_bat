using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Security.Principal;

class ProbeMediumActivation {
 [StructLayout(LayoutKind.Sequential)] struct SIDATTR { public IntPtr Sid; public uint Attributes; }
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct STARTUPINFO {
  public int cb; public string reserved, desktop, title; public int x,y,xsize,ysize,xchars,ychars,fill,flags;
  public short show, reserved2; public IntPtr lpReserved2,input,output,error;
 }
 [StructLayout(LayoutKind.Sequential)] struct PROCESSINFO {public IntPtr process,thread; public uint pid,tid;}
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool CreateRestrictedToken(IntPtr token,uint flags,uint count,[In] SIDATTR[] disable,uint n,IntPtr privileges,uint nr,IntPtr restricted,out IntPtr result);
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool ConvertStringSidToSid(string str,out IntPtr sid);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool SetTokenInformation(IntPtr token,int type,ref SIDATTR info,int size);
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessAsUser(IntPtr token,string app,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref STARTUPINFO startup,out PROCESSINFO process);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr handle);
 [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr handle,uint millis);
 [DllImport("kernel32.dll")] static extern bool GetExitCodeProcess(IntPtr handle,out uint code);
 [ComImport,Guid("2e941141-7f97-4756-ba1d-9decde894a3d"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)] interface IActivation {
  [PreserveSig] int ActivateApplication([MarshalAs(UnmanagedType.LPWStr)] string app,[MarshalAs(UnmanagedType.LPWStr)] string args,uint flags,out uint pid);
 }
 static void Check(bool ok) { if(!ok) throw new Win32Exception(Marshal.GetLastWin32Error()); }
 [STAThread] static int Main(string[] args) {
  if(args.Length != 2) return 1;
  if(args[0]=="--child") {
   var manager=(IActivation)Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")));
   uint pid; int hr=manager.ActivateApplication("ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2!App", "", 0,out pid);
   using(var file=new StreamWriter(new FileStream(args[1],FileMode.CreateNew)))
    file.WriteLine("User="+WindowsIdentity.GetCurrent().Name+"; Admin="+new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator)+"; HRESULT=0x"+hr.ToString("X8")+"; PID="+pid);
   return hr;
  }
  IntPtr token=IntPtr.Zero, reduced=IntPtr.Zero, admin=IntPtr.Zero, medium=IntPtr.Zero;
  try {
   Check(OpenProcessToken(Process.GetCurrentProcess().Handle,0xF01FF,out token));
   Check(ConvertStringSidToSid("S-1-5-32-544",out admin));
   Check(CreateRestrictedToken(token,1,1,new[]{new SIDATTR{Sid=admin}},0,IntPtr.Zero,0,IntPtr.Zero,out reduced));
   Check(ConvertStringSidToSid("S-1-16-8192",out medium));
   var label=new SIDATTR{Sid=medium,Attributes=0x20};
   Check(SetTokenInformation(reduced,25,ref label,Marshal.SizeOf(label)+16));
   var startup=new STARTUPINFO{cb=Marshal.SizeOf(typeof(STARTUPINFO)),desktop="winsta0\\default",flags=1,show=0};
   PROCESSINFO child;
   string exe=Process.GetCurrentProcess().MainModule.FileName;
   Check(CreateProcessAsUser(reduced,exe,new StringBuilder("\""+exe+"\" --child \""+args[1]+"\""),IntPtr.Zero,IntPtr.Zero,false,0x08000000,IntPtr.Zero,Environment.CurrentDirectory,ref startup,out child));
   Console.WriteLine("Restricted probe PID="+child.pid);
   WaitForSingleObject(child.process,15000); uint exit; GetExitCodeProcess(child.process,out exit); Console.WriteLine("Probe exit=0x"+exit.ToString("X8")); CloseHandle(child.process); CloseHandle(child.thread);
  } finally { if(token!=IntPtr.Zero)CloseHandle(token);if(reduced!=IntPtr.Zero)CloseHandle(reduced);if(admin!=IntPtr.Zero)LocalFree(admin);if(medium!=IntPtr.Zero)LocalFree(medium); }
  return 0;
 }
}
