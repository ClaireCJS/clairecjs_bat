using System;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Windows.ApplicationModel;
using Windows.ApplicationModel.Background;
using Windows.Data.Json;
using Windows.Storage;
using Windows.UI.Notifications;

namespace PAFPlayerLockScreen
{
    internal static class DesktopHost
    {
        internal static EventWaitHandle StopPublisher;
        [STAThread]
        private static int Main(string[] args)
        {
            try
            {
                // Calling notification APIs without our real package identity is unsupported.
                if (Package.Current.Id.FamilyName != "ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2")
                    throw new InvalidOperationException("Launch the installed PAFPlayer Lock Screen app from Start.");
                if (args.Length > 0 && args[0] == "--background-task")
                    return DesktopBackgroundServer.Run();
                if (args.Length == 2 && args[0] == "--verify")
                    return VerifyAsync(args[1]).GetAwaiter().GetResult();
                bool managed = args.Length == 5 && args[0] == "--managed";
                if (args.Length != 0 && !managed) return 2;
                if (managed && !ManagedPublisher.ValidateAsync(args[1], args[2]).GetAwaiter().GetResult()) return 4;
                using (StopPublisher = new EventWaitHandle(false, EventResetMode.ManualReset,
                    "Local\\PAFPlayerLockScreenRecoveryStopPublisher"))
                using (var instance = new Mutex(false, "Local\\PAFPlayerLockScreenRecoveryPublisher"))
                {
                    bool acquired;
                    try { acquired = instance.WaitOne(0); }
                    catch (AbandonedMutexException) { acquired = true; }
                    if (!acquired && managed)
                    {
                        StopPublisher.Set();
                        try { acquired = instance.WaitOne(TimeSpan.FromSeconds(12)); }
                        catch (AbandonedMutexException) { acquired = true; }
                    }
                    if (!acquired) return managed ? 3 : 0;
                    try
                    {
                        StopPublisher.Reset();
                        if (managed) return ManagedPublisher.RunAsync(args[1], args[2], args[3], args[4]).GetAwaiter().GetResult();
                        Application.EnableVisualStyles();
                        Application.Run(new StatusWindow());
                    }
                    finally { instance.ReleaseMutex(); }
                }
                return 0;
            }
            catch (Exception error)
            {
                if (args.Length == 2 && args[0] == "--verify")
                {
                    var failure = new JsonObject();
                    failure["startupError"] = JsonValue.CreateStringValue(error.ToString());
                    using (var file = new StreamWriter(new FileStream(args[1], FileMode.CreateNew, FileAccess.Write)))
                        file.Write(failure.Stringify());
                    return 1;
                }
                if (args.Length > 0 && args[0] == "--managed") return 1;
                MessageBox.Show(error.Message, "PAFPlayer Lock Screen", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }

        private static async Task<int> VerifyAsync(string path)
        {
            var config = Settings.Load();
            await BackgroundRegistration.EnsureAsync(config.Enabled);
            var status = await StatusUpdater.FetchAsync(config.Server);
            bool published = false;
            string error = "";
            try { if (config.Enabled) { StatusUpdater.Publish(status); published = true; } else StatusUpdater.Clear(); }
            catch (Exception ex) { error = ex.ToString(); }
            var report = new JsonObject();
            report["time"] = JsonValue.CreateStringValue(DateTimeOffset.UtcNow.ToString("o"));
            report["package"] = JsonValue.CreateStringValue(Package.Current.Id.FullName);
            report["user"] = JsonValue.CreateStringValue(System.Security.Principal.WindowsIdentity.GetCurrent().Name);
            report["session"] = JsonValue.CreateNumberValue(System.Diagnostics.Process.GetCurrentProcess().SessionId);
            report["server"] = JsonValue.CreateStringValue(config.Server);
            report["officialVerified"] = JsonValue.CreateBooleanValue(status.Verified);
            report["identity"] = JsonValue.CreateStringValue(status.Identity);
            report["published"] = JsonValue.CreateBooleanValue(published);
            report["enabled"] = JsonValue.CreateBooleanValue(config.Enabled);
            report["badge"] = JsonValue.CreateStringValue(status.Badge);
            report["summary"] = JsonValue.CreateStringValue(status.Summary);
            report["lyric"] = JsonValue.CreateStringValue(status.Lyric);
            report["tileXml"] = JsonValue.CreateStringValue(StatusUpdater.TileXml(status).GetXml());
            report["badgeXml"] = JsonValue.CreateStringValue(StatusUpdater.BadgeXml(status).GetXml());
            report["tileNotificationSetting"] = JsonValue.CreateStringValue(TileUpdateManager.CreateTileUpdaterForApplication().Setting.ToString());
            try
            {
                report["backgroundAccess"] = JsonValue.CreateStringValue(BackgroundExecutionManager.GetAccessStatus().ToString());
                report["backgroundRegistered"] = JsonValue.CreateBooleanValue(BackgroundRegistration.IsRegistered);
                report["backgroundTaskIds"] = JsonValue.CreateStringValue(String.Join(",", BackgroundTaskRegistration.AllTasks.Where(t => t.Value.Name == BackgroundRegistration.TaskName).Select(t => t.Key.ToString())));
            }
            catch (Exception ex) { report["backgroundDiagnosticError"] = JsonValue.CreateStringValue(ex.ToString()); }
            report["backgroundRegistrationError"] = JsonValue.CreateStringValue(BackgroundRegistration.Error);
            report["error"] = JsonValue.CreateStringValue(error.Length == 0 ? status.Error : error);
            using (var file = new StreamWriter(new FileStream(path, FileMode.CreateNew, FileAccess.Write)))
                file.Write(report.Stringify());
            return published && status.Verified ? 0 : 2;
        }
    }

    internal sealed class Settings
    {
        internal string Server = "http://127.0.0.1:666";
        internal bool Enabled = true;
        internal bool Managed;
        private static string PathName { get { return Path.Combine(ApplicationData.Current.LocalFolder.Path, "publisher-settings.json"); } }
        internal static Settings Load()
        {
            var result = new Settings();
            if (File.Exists(PathName))
            {
                var json = JsonObject.Parse(File.ReadAllText(PathName));
                result.Server = json.GetNamedString(StatusUpdater.ServerKey, result.Server);
                result.Enabled = json.GetNamedBoolean("PAFPlayerLockScreenEnabled", true);
                result.Managed = json.GetNamedBoolean("PAFPlayerManagedPublisher", false);
            }
            else
            {
                // Preserve the V510 settings keys and values without changing its
                // package or files. Windows requires the new identity to be selected.
                string previous = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Packages", "ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2", "LocalState", "publisher-settings.json");
                if (File.Exists(previous))
                {
                    var json = JsonObject.Parse(File.ReadAllText(previous));
                    result.Server = json.GetNamedString(StatusUpdater.ServerKey, result.Server);
                    result.Enabled = json.GetNamedBoolean("PAFPlayerLockScreenEnabled", true);
                    return result;
                }
                var old = ApplicationData.Current.LocalSettings.Values[StatusUpdater.ServerKey] as string;
                Uri endpoint;
                if (StatusUpdater.TryServerUrl(old, out endpoint)) result.Server = endpoint.GetLeftPart(UriPartial.Authority);
            }
            return result;
        }
        internal void Save()
        {
            if (File.Exists(PathName))
            {
                string stem = PathName + ".bak." + DateTime.Now.ToString("yyyyMMddHHmm") + ".replaced-by-chatgpt";
                string backup = stem + ".bak";
                for (int n = 1; File.Exists(backup); n++) backup = stem + " (" + n + ").bak";
                File.Copy(PathName, backup, false);
                using (var sha = SHA256.Create())
                {
                    if (!sha.ComputeHash(File.ReadAllBytes(PathName)).SequenceEqual(sha.ComputeHash(File.ReadAllBytes(backup))))
                        throw new IOException("Settings backup verification failed.");
                }
            }
            var json = new JsonObject();
            json[StatusUpdater.ServerKey] = JsonValue.CreateStringValue(Server);
            json["PAFPlayerLockScreenEnabled"] = JsonValue.CreateBooleanValue(Enabled);
            json["PAFPlayerManagedPublisher"] = JsonValue.CreateBooleanValue(Managed);
            File.WriteAllText(PathName, json.Stringify());
        }
    }

    internal sealed class StatusWindow : Form
    {
        private readonly Settings settings = Settings.Load();
        private readonly TextBox server = new TextBox { Dock = DockStyle.Top };
        private readonly CheckBox enabled = new CheckBox { Text = "Publish lock-screen status", AutoSize = true };
        private readonly Label statusText = new Label { AutoSize = true, MaximumSize = new Size(620, 0) };
        private readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = StatusUpdater.PollMilliseconds };
        private readonly NotifyIcon tray = new NotifyIcon { Icon = SystemIcons.Information, Text = "PAFPlayer Lock Screen V530", Visible = true };
        private bool refreshing, exiting, disabledCleared;
        private readonly PublicationSession publication = new PublicationSession();
        internal StatusWindow()
        {
            Text = "PAFPlayer Lock Screen V530";
            ClientSize = new Size(660, 300);
            var panel = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown,
                WrapContents = false, Padding = new Padding(20), AutoScroll = true };
            server.Width = 600;
            server.Text = settings.Server;
            enabled.Checked = settings.Enabled;
            var save = new Button { Text = "Save and refresh", AutoSize = true };
            var close = new Button { Text = "Hide to tray", AutoSize = true };
            panel.Controls.Add(new Label { Text = "Official PAFPlayer server (read only)", AutoSize = true });
            panel.Controls.Add(server); panel.Controls.Add(enabled); panel.Controls.Add(save);
            panel.Controls.Add(statusText);
            panel.Controls.Add(new Label { Text = "In Windows Lock screen Settings, select PAFPlayer Lock Screen V530\nfor BOTH detailed and quick status. Check the version in each picker.\nClosing this window keeps updates running. Exit from the tray stops publishing.", AutoSize = true });
            panel.Controls.Add(close); Controls.Add(panel);
            save.Click += async (s, e) => {
                Uri endpoint;
                if (!StatusUpdater.TryServerUrl(server.Text, out endpoint)) { statusText.Text = "Use an HTTP host and port without a path."; return; }
                try {
                    var next = new Settings { Server = endpoint.GetLeftPart(UriPartial.Authority), Enabled = enabled.Checked };
                    next.Save();
                    settings.Server = next.Server; settings.Enabled = next.Enabled;
                    await BackgroundRegistration.EnsureAsync(settings.Enabled);
                    if (!settings.Enabled) { StatusUpdater.Clear(); publication.Reset(); disabledCleared = true; statusText.Text = "Publishing disabled."; }
                    await RefreshAsync();
                } catch (Exception ex) { statusText.Text = ex.Message; }
            };
            close.Click += (s, e) => Hide();
            tray.DoubleClick += (s, e) => { Show(); WindowState = FormWindowState.Normal; Activate(); };
            var menu = new ContextMenuStrip();
            menu.Items.Add("Show settings", null, (s, e) => { Show(); Activate(); });
            menu.Items.Add("Exit and clear status", null, (s, e) => { exiting = true; Close(); });
            tray.ContextMenuStrip = menu;
            FormClosing += (s, e) => {
                if (!exiting && e.CloseReason == CloseReason.UserClosing) { e.Cancel = true; Hide(); return; }
                timer.Stop();
                try { BackgroundRegistration.Unregister(); } catch { /* Preserve normal shutdown if Windows rejects removal. */ }
                try { StatusUpdater.Clear(); } catch { /* Existing notifications expire after 90 seconds. */ }
                tray.Dispose(); timer.Dispose();
            };
            timer.Tick += async (s, e) => {
                if (DesktopHost.StopPublisher.WaitOne(0)) { exiting = true; Close(); return; }
                await RefreshAsync();
            };
            Shown += async (s, e) => { await BackgroundRegistration.EnsureAsync(settings.Enabled); await RefreshAsync(); timer.Start(); };
        }
        private async Task RefreshAsync()
        {
            if (refreshing) return;
            refreshing = true;
            try
            {
                if (!settings.Enabled)
                {
                    if (!disabledCleared) { StatusUpdater.Clear(); publication.Reset(); disabledCleared = true; }
                    statusText.Text = "Publishing disabled."; return;
                }
                disabledCleared = false;
                string requestedServer = settings.Server;
                var status = await StatusUpdater.FetchAsync(requestedServer);
                if (exiting || !settings.Enabled || settings.Server != requestedServer) return;
                publication.Update(status);
                timer.Interval = status.Verified ? StatusUpdater.PollMilliseconds : 3000;
                statusText.Text = status.Summary + "\n" + (status.Verified ? "Tile and " + status.Badge + " badge submitted to Windows." : status.Error);
                statusText.Text += "\n" + (BackgroundRegistration.Error.Length == 0 ? "Windows background registration ready." : "Background registration failed: " + BackgroundRegistration.Error);
            }
            catch (Exception error) { if (!IsDisposed) statusText.Text = "Windows publication failed: " + error.Message; }
            finally { refreshing = false; }
        }
    }
}
