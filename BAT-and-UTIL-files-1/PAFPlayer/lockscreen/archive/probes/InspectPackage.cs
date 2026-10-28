using System;
using System.Threading.Tasks;
using Windows.Management.Deployment;
class InspectPackage {
 static int Main(string[] args) {
  try {
   var manager = new PackageManager();
   foreach (var package in manager.FindPackagesForUser("")) {
    if (!package.Id.Name.Contains("PAFPlayer")) continue;
    Console.WriteLine(package.Id.FullName);
    var apps = package.GetAppListEntriesAsync().AsTask().GetAwaiter().GetResult();
    Console.WriteLine("App count: " + apps.Count);
    foreach(var app in apps) {
     Console.WriteLine("AUMID: " + app.AppUserModelId);
     if (args.Length > 0 && args[0] == "--launch") Console.WriteLine("LaunchAsync: " + app.LaunchAsync().AsTask().GetAwaiter().GetResult());
    }
   }
   return 0;
  } catch(Exception e) { Console.WriteLine(e); return 1; }
 }
}
