using System;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Windows.ApplicationModel;
using Windows.Data.Json;
using Windows.Storage;
using Windows.UI.Notifications;

namespace PAFPlayerLockScreen
{
    internal static class DesktopHost
    {
        [STAThread]
        private static int Main(string[] args)
        {
            try
            {
                // Calling notification APIs without our real package identity is unsupported.
                if (Package.Current.Id.FamilyName != "ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2")
                    throw new InvalidOperationException("Launch the installed PAFPlayer Lock Screen app from Start.");
                if (args.Length == 2 && args[0] == "--verify")
                    return VerifyAsync(args[1]).GetAwaiter().GetResult();
                bool first;
                using (var instance = new Mutex(true, "Local\\PAFPlayerLockScreenPublisher", out first))
                {
                    if (!first) return 0;
                    Application.EnableVisualStyles();
                    Application.Run(new StatusWindow());
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
                MessageBox.Show(error.Message, "PAFPlayer Lock Screen", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }

        private static async Task<int> VerifyAsync(string path)
        {
            var config = Settings.Load();
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
        private static string PathName { get { return Path.Combine(ApplicationData.Current.LocalFolder.Path, "publisher-settings.json"); } }
        internal static Settings Load()
        {
            var result = new Settings();
            if (File.Exists(PathName))
            {
                var json = JsonObject.Parse(File.ReadAllText(PathName));
                result.Server = json.GetNamedString(StatusUpdater.ServerKey, result.Server);
                result.Enabled = json.GetNamedBoolean("PAFPlayerLockScreenEnabled", true);
            }
            else
            {
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
            File.WriteAllText(PathName, json.Stringify());
        }
    }

    internal sealed class StatusWindow : Form
    {
        private readonly Settings settings = Settings.Load();
        private readonly TextBox server = new TextBox { Dock = DockStyle.Top };
        private readonly CheckBox enabled = new CheckBox { Text = "Publish lock-screen status", AutoSize = true };
        private readonly Label statusText = new Label { AutoSize = true, MaximumSize = new Size(620, 0) };
        private readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = 5000 };
        private readonly NotifyIcon tray = new NotifyIcon { Icon = SystemIcons.Information, Text = "PAFPlayer Lock Screen", Visible = true };
        private bool refreshing, exiting;
        internal StatusWindow()
        {
            Text = "PAFPlayer Lock Screen Recovery Test";
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
            panel.Controls.Add(new Label { Text = "Choose this app for detailed and/or quick status in Windows Lock screen Settings.\nClosing this window keeps updates running. Exit from the tray stops publishing.", AutoSize = true });
            panel.Controls.Add(close); Controls.Add(panel);
            save.Click += async (s, e) => {
                Uri endpoint;
                if (!StatusUpdater.TryServerUrl(server.Text, out endpoint)) { statusText.Text = "Use an HTTP host and port without a path."; return; }
                try {
                    var next = new Settings { Server = endpoint.GetLeftPart(UriPartial.Authority), Enabled = enabled.Checked };
                    next.Save();
                    settings.Server = next.Server; settings.Enabled = next.Enabled;
                    if (!settings.Enabled) { StatusUpdater.Clear(); statusText.Text = "Publishing disabled."; }
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
                try { StatusUpdater.Clear(); } catch { /* Existing notifications expire after 90 seconds. */ }
                tray.Dispose(); timer.Dispose();
            };
            timer.Tick += async (s, e) => await RefreshAsync();
            Shown += async (s, e) => { await RefreshAsync(); timer.Start(); };
        }
        private async Task RefreshAsync()
        {
            if (refreshing) return;
            refreshing = true;
            try
            {
                if (!settings.Enabled) { StatusUpdater.Clear(); statusText.Text = "Publishing disabled."; return; }
                string requestedServer = settings.Server;
                var status = await StatusUpdater.FetchAsync(requestedServer);
                if (exiting || !settings.Enabled || settings.Server != requestedServer) return;
                StatusUpdater.Publish(status);
                statusText.Text = status.Summary + "\n" + (status.Verified ? "Tile and " + status.Badge + " badge submitted to Windows." : status.Error);
            }
            catch (Exception error) { if (!IsDisposed) statusText.Text = "Windows publication failed: " + error.Message; }
            finally { refreshing = false; }
        }
    }
}

