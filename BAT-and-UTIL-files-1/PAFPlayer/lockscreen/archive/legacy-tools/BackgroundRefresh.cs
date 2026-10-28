using Windows.ApplicationModel.Background;

namespace PAFPlayerLockScreen.BackgroundTasks
{
    public sealed class RefreshTask : IBackgroundTask
    {
        public async void Run(IBackgroundTaskInstance taskInstance)
        {
            var deferral = taskInstance.GetDeferral();
            try { await PAFPlayerLockScreen.StatusUpdater.RefreshAsync(); }
            finally { deferral.Complete(); }
        }
    }
}
