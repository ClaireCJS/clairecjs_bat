using System;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Windows.ApplicationModel.Background;

namespace PAFPlayerLockScreen
{
    internal static class BackgroundRegistration
    {
        internal const string TaskName = "PAFPlayerLockScreenRefresh";
        internal static string Error = "";

        internal static bool IsRegistered
        {
            get { return BackgroundTaskRegistration.AllTasks.Any(t => t.Value.Name == TaskName); }
        }

        internal static void Unregister()
        {
            foreach (var task in BackgroundTaskRegistration.AllTasks.Where(t => t.Value.Name == TaskName).ToArray())
                task.Value.Unregister(true);
        }

        internal static async Task EnsureAsync(bool enabled)
        {
            Error = "";
            try
            {
                if (!enabled) { Unregister(); return; }
                var access = await BackgroundExecutionManager.RequestAccessAsync();
                if (!Allowed(access))
                    throw new InvalidOperationException("Windows background access: " + access);
                if (IsRegistered) return;
                var builder = new BackgroundTaskBuilder { Name = TaskName };
                builder.SetTaskEntryPointClsid(typeof(DesktopRefreshTask).GUID);
                builder.SetTrigger(new TimeTrigger(15, false));
                builder.Register();
            }
            catch (Exception ex) { Error = ex.ToString(); }
        }

        internal static bool Allowed(BackgroundAccessStatus status)
        {
            return status != BackgroundAccessStatus.Unspecified && status != BackgroundAccessStatus.Denied &&
                status != BackgroundAccessStatus.DeniedByUser && status != BackgroundAccessStatus.DeniedBySystemPolicy;
        }
    }

    // Windows 10 (19041+) COM background entry point. It uses exactly the same
    // verified GET-only status reader as the desktop publisher, without a UI.
    [ComVisible(true)]
    [ClassInterface(ClassInterfaceType.None)]
    [Guid("12BF3FEC-09DF-41BB-BB38-9881E610AA91")]
    [ComSourceInterfaces(typeof(IBackgroundTask))]
    public sealed class DesktopRefreshTask : IBackgroundTask
    {
        private volatile bool canceled;
        public void Run(IBackgroundTaskInstance taskInstance)
        {
            var deferral = taskInstance.GetDeferral();
            taskInstance.Canceled += OnCanceled;
            try
            {
                var settings = Settings.Load();
                if (settings.Enabled && !settings.Managed && !canceled)
                {
                    var status = StatusUpdater.FetchAsync(settings.Server).GetAwaiter().GetResult();
                    var current = Settings.Load();
                    // Never resurrect a notification after a settings change,
                    // cancellation or removal of our registration during the GET.
                    if (!canceled && current.Enabled && !current.Managed && current.Server == settings.Server && BackgroundRegistration.IsRegistered)
                        StatusUpdater.Publish(status);
                }
            }
            catch { /* Notifications expire; background failure must not affect playback. */ }
            finally
            {
                taskInstance.Canceled -= OnCanceled;
                deferral.Complete();
                DesktopBackgroundServer.Completed.Set();
            }
        }
        private void OnCanceled(IBackgroundTaskInstance sender, BackgroundTaskCancellationReason reason) { canceled = true; }
    }

    internal static class DesktopBackgroundServer
    {
        internal static readonly ManualResetEvent Completed = new ManualResetEvent(false);
        internal static int Run()
        {
            int result = 0;
            var thread = new Thread(() => {
                int cookie = 0;
                var service = new RegistrationServices();
                try
                {
                    cookie = service.RegisterTypeForComClients(typeof(DesktopRefreshTask),
                        RegistrationClassContext.LocalServer, RegistrationConnectionType.SingleUse);
                    if (!Completed.WaitOne(TimeSpan.FromSeconds(60))) result = 2;
                }
                catch { result = 1; }
                finally { if (cookie != 0) service.UnregisterTypeForComClients(cookie); }
            });
            thread.SetApartmentState(ApartmentState.MTA);
            thread.Start();
            thread.Join();
            return result;
        }
    }
}
