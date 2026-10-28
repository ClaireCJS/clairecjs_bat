using System;
using Windows.ApplicationModel.Background;
using Windows.Storage;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;

namespace PAFPlayerLockScreen
{
    public sealed partial class MainPage : Page
    {
        private DispatcherTimer timer;

        public MainPage()
        {
            InitializeComponent();
            ServerBox.Text = (string)ApplicationData.Current.LocalSettings.Values[StatusUpdater.ServerKey] ?? "";
            timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(5) };
            timer.Tick += async (sender, args) =>
            {
                timer.Stop();
                try { StatusText.Text = await StatusUpdater.RefreshAsync(); }
                finally { timer.Start(); }
            };
            Loaded += async (sender, args) =>
            {
                if (ServerBox.Text.Length > 0)
                {
                    try
                    {
                        await RegisterBackgroundRefreshAsync();
                        StatusText.Text = await StatusUpdater.RefreshAsync();
                        timer.Start();
                    }
                    catch (Exception error) { StatusText.Text = "Background refresh unavailable: " + error.Message; }
                }
            };
            Unloaded += (sender, args) => timer.Stop();
        }

        private async void ConnectButton_Click(object sender, RoutedEventArgs e)
        {
            Uri endpoint;
            if (!StatusUpdater.TryServerUrl(ServerBox.Text, out endpoint))
            {
                StatusText.Text = "Use a plain HTTP machine name and port, such as machineservername:666.";
                return;
            }
            ApplicationData.Current.LocalSettings.Values[StatusUpdater.ServerKey] = endpoint.GetLeftPart(UriPartial.Authority);
            try
            {
                await RegisterBackgroundRefreshAsync();
                StatusText.Text = await StatusUpdater.RefreshAsync();
                timer.Start();
            }
            catch (Exception error) { StatusText.Text = "Background refresh unavailable: " + error.Message; }
        }

        private static async System.Threading.Tasks.Task RegisterBackgroundRefreshAsync()
        {
            var access = await BackgroundExecutionManager.RequestAccessAsync();
            if (access == BackgroundAccessStatus.DeniedByUser ||
                access == BackgroundAccessStatus.DeniedBySystemPolicy)
                throw new InvalidOperationException("Windows denied the background task.");
            foreach (var task in BackgroundTaskRegistration.AllTasks)
                if (task.Value.Name == "PAFPlayerLockScreenRefresh") return;
            var builder = new BackgroundTaskBuilder
            {
                Name = "PAFPlayerLockScreenRefresh",
                TaskEntryPoint = "PAFPlayerLockScreen.BackgroundTasks.RefreshTask"
            };
            builder.SetTrigger(new TimeTrigger(15, false));
            builder.Register();
        }
    }
}
