using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using PAFPlayerScreenSaver;

public static class SaverTests {
    static int count;
    static void Check(bool condition, string name) { if (!condition) throw new Exception(name); count++; Console.WriteLine("PASS " + name); }
    static bool Throws(Action action) { try { action(); return false; } catch { return true; } }
    static byte[] Json(string title, string revision, bool enabled) {
        return Encoding.UTF8.GetBytes("{\"protocol\":1,\"session\":\"fixture\",\"enabled\":" + (enabled ? "true" : "false") + ",\"has_art\":true,\"brightness\":50,\"close_revision\":0,\"title\":\"" + title + "\",\"lyric\":\"A current timed lyric\",\"status\":\"Playing\",\"art_revision\":\"" + revision + "\"}");
    }
    sealed class Server : IDisposable {
        readonly TcpListener listener = new TcpListener(IPAddress.Loopback, 0); readonly Thread thread;
        public int Port, States, Arts, AuthenticatedPosts, Brightness = 50; public string LastPayload = ""; public bool RejectSettings; public string Mode = "normal"; public bool Enabled = true; volatile bool stop;
        public Server() { listener.Start(); Port = ((IPEndPoint)listener.LocalEndpoint).Port; thread = new Thread(Run) { IsBackground = true }; thread.Start(); }
        void Run() {
            while (!stop) {
                try {
                    using (TcpClient client = listener.AcceptTcpClient()) {
                        client.ReceiveTimeout = 1500; client.SendTimeout = 1500;
                        using (NetworkStream stream = client.GetStream()) {
                            StreamReader reader = new StreamReader(stream); string line = reader.ReadLine();
                            bool art = line != null && line.Contains("/art?");
                            int length = 0; string token = "", headerLine;
                            while (!string.IsNullOrEmpty(headerLine = reader.ReadLine())) {
                                if (headerLine.StartsWith("Content-Length:", StringComparison.OrdinalIgnoreCase)) length = int.Parse(headerLine.Substring(15).Trim());
                                if (headerLine.StartsWith("X-PAF-Workflow-Token:", StringComparison.OrdinalIgnoreCase)) token = headerLine.Substring(21).Trim();
                            }
                            string payload = "";
                            if (length > 0) { char[] chars = new char[length]; int total = 0, got;
                                while (total < length && (got = reader.Read(chars, total, length - total)) > 0) total += got;
                                payload = new string(chars, 0, total);
                            }
                            if (Mode == "timeout") { Thread.Sleep(1600); continue; }
                            byte[] body; string status = "200 OK";
                            if (art) {
                                Interlocked.Increment(ref Arts);
                                using (Bitmap image = new Bitmap(80, 80)) using (Graphics g = Graphics.FromImage(image)) using (MemoryStream bytes = new MemoryStream()) {
                                    g.Clear(Color.Red); image.Save(bytes, ImageFormat.Png); body = bytes.ToArray();
                                }
                            } else if (line.Contains("/api/workflows/status")) {
                                body = Encoding.UTF8.GetBytes("{\"local\":true,\"token\":\"fixture-token\"}");
                            } else {
                                if (line.StartsWith("POST ")) {
                                    if (token != "fixture-token" || RejectSettings) status = "403 Forbidden";
                                    else {
                                        Interlocked.Increment(ref AuthenticatedPosts); LastPayload = payload;
                                        var changes = new System.Web.Script.Serialization.JavaScriptSerializer().Deserialize<System.Collections.Generic.Dictionary<string, object>>(payload);
                                        if (changes.ContainsKey("enabled")) Enabled = (bool)changes["enabled"];
                                        if (changes.ContainsKey("brightness")) Brightness = (int)changes["brightness"];
                                    }
                                }
                                Interlocked.Increment(ref States); body = Json("Artist — Song " + States, "art-one", Enabled);
                                body = Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(body).Replace("\"brightness\":50", "\"brightness\":" + Brightness));
                            }
                            if (Mode == "bad-art" && art) body = new byte[] { 1, 2, 3 };
                            if (Mode == "bad-json") body = Encoding.UTF8.GetBytes("{}");
                            if (Mode == "redirect") status = "302 Found";
                            if (Mode == "oversize") body = new byte[5000];
                            byte[] header = Encoding.ASCII.GetBytes("HTTP/1.1 " + status + "\r\nContent-Length: " + body.Length + "\r\nConnection: close\r\nLocation: http://127.0.0.1:1/\r\n\r\n");
                            stream.Write(header, 0, header.Length); stream.Write(body, 0, body.Length);
                        }
                    }
                } catch { if (stop) return; }
            }
        }
        public void Dispose() { stop = true; listener.Stop(); thread.Join(2000); }
    }
    static Packet Await(Mailbox box, Func<Packet, bool> condition) {
        DateTime end = DateTime.UtcNow.AddSeconds(5);
        while (DateTime.UtcNow < end) {
            Packet p = box.Take();
            if (p != null) { if (condition(p)) return p; if (p.Artwork != null) p.Artwork.Dispose(); }
            Thread.Sleep(25);
        }
        throw new Exception("Timed out waiting for sidecar state");
    }
    static void Pump(Func<bool> condition) {
        DateTime until = DateTime.UtcNow.AddSeconds(7);
        do { Application.DoEvents(); if (condition()) return; Thread.Sleep(20); } while (DateTime.UtcNow < until);
        throw new Exception("UI operation timed out");
    }
    [DllImport("user32.dll")] static extern IntPtr GetParent(IntPtr handle);
    [STAThread] public static int Main(string[] args) {
        try {
            string output = args[0]; Directory.CreateDirectory(output);
            ConfigStore.OverridePath = Path.Combine(output, "PAFPlayer", "screensaver", "PAFPlayer.cfg");
            Check(ConfigStore.PathName.EndsWith(Path.Combine("PAFPlayer", "screensaver", "PAFPlayer.cfg")), "sidecar configuration uses requested path");
            ConfigStore.Save(false, 37, true);
            ScreenSaverConfig persisted = ConfigStore.Load();
            Check(!persisted.Enabled && persisted.Brightness == 37 && persisted.RequirePassword, "sidecar configuration saves brightness and password requirement");
            ConfigStore.Save(true, 50);
            Check(ConfigStore.Load().RequirePassword, "legacy two-field saves preserve the password setting");
            Check(Directory.GetFiles(Path.GetDirectoryName(ConfigStore.PathName), "PAFPlayer.cfg.bak.*.replaced-by-chatgpt*.bak").Length == 1, "sidecar replacement creates verified sibling backup");
            Check(SaverForm.ShouldLockOnExit("s", true, true, ConfigStore.Load()), "fullscreen dismissal requests sign-in when enabled");
            Check(!SaverForm.ShouldLockOnExit("p", true, true, ConfigStore.Load()) && !SaverForm.ShouldLockOnExit("s", false, true, ConfigStore.Load()), "preview and unseen saver never lock");
            ConfigStore.Save(true, 50, false);
            Check(!SaverForm.ShouldLockOnExit("s", true, true, ConfigStore.Load()), "unchecked password option does not lock");
            Check(Options.Parse(new string[0]).Mode == "c", "default configuration mode");
            Check(Options.Parse(new[] { "/S", "/port:8123" }).Port == 8123, "fullscreen and explicit port");
            Options launched = Options.Parse(new[] { "/s", "/close-revision:7" });
            Check(launched.HasInitialCloseRevision && launched.InitialCloseRevision == 7, "launch-time close revision is parsed");
            Check(Options.Parse(new[] { "/P:123456789" }).Parent.ToInt64() == 123456789, "colon preview handle");
            Check(Options.Parse(new[] { "/p", "123456789" }).Mode == "p", "separate preview handle");
            Check(Options.Parse(new[] { "/c:123" }).Mode == "c", "configuration handle");
            Check(Throws(() => Options.Parse(new[] { "/p" })) && Throws(() => Options.Parse(new[] { "/p:-1" })), "reject invalid preview handles");
            Check(Throws(() => Options.Parse(new[] { "/s", "/p:12" })) && Throws(() => Options.Parse(new[] { "/port:70000" })), "reject ambiguous mode and bad port");
            StartupInputGuard guard = new StartupInputGuard();
            Check(!guard.AcceptInput(100000), "no input dismissal before display");
            guard.Start(10000, new Point(5, 5));
            Check(!guard.AcceptInput(12999) && guard.AcceptInput(13000), "three-second grace begins at display, not construction");
            Check(!guard.Update(12999, new Point(700, 700), new[] { 65 }, new[] { 1 }), "startup keys, clicks and motion ignored");
            Check(!guard.Update(13000, new Point(1000, 1000), new int[0], new int[0]), "arming discards startup input");
            Check(!guard.Update(13010, new Point(1000, 1000), new[] { 65 }, new int[0]), "single key tap does not dismiss");
            Check(!guard.Update(13100, new Point(1000, 1000), new int[0], new int[0]), "key release does not dismiss");
            Check(guard.Update(13200, new Point(1000, 1000), new[] { 65 }, new int[0]), "two separate key hits dismiss");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            Check(!guard.Update(13010, Point.Empty, new[] { 65 }, new int[0]) && !guard.Update(14009, Point.Empty, new[] { 65 }, new int[0]), "held key and auto-repeat do not dismiss early");
            Check(guard.Update(14010, Point.Empty, new[] { 65 }, new int[0]), "one key held for a second dismisses");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            Check(!guard.Update(13010, Point.Empty, new[] { 16, 160 }, new int[0]), "generic and left Shift codes count as one key");
            Check(guard.Update(14010, Point.Empty, new[] { 16, 160 }, new int[0]), "modifier hold still dismisses after one second");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            Check(!guard.Update(13010, Point.Empty, new int[0], new[] { 1 }) && !guard.Update(14009, Point.Empty, new int[0], new[] { 1 }), "single mouse click does not dismiss early");
            Check(guard.Update(14010, Point.Empty, new int[0], new[] { 1 }), "mouse button held for a second dismisses");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            bool motionDismissed = false;
            for (int step = 1; step <= 10; step++) motionDismissed = guard.Update(13000 + step * 200, new Point(step * 4, 0), new int[0], new int[0]);
            Check(!motionDismissed && guard.Update(15200, new Point(44, 0), new int[0], new int[0]), "two seconds of sustained mouse motion dismisses");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            bool jitterDismissed = false;
            for (int step = 1; step <= 20; step++) jitterDismissed |= guard.Update(13000 + step * 150, new Point(step % 2, 0), new int[0], new int[0]);
            Check(!jitterDismissed, "back-and-forth pointer jitter never dismisses");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            bool slowMotionDismissed = false;
            for (int step = 1; step <= 25; step++) slowMotionDismissed |= guard.Update(13000 + step * 100, new Point(step, 0), new int[0], new int[0]);
            Check(slowMotionDismissed, "slow sustained pointer motion dismisses after two seconds");
            guard.Start(10000, Point.Empty); guard.Update(13000, Point.Empty, new int[0], new int[0]);
            Check(!guard.Update(13200, new Point(4, 0), new int[0], new int[0]) && !guard.Update(14000, new Point(4, 0), new int[0], new int[0]) && !guard.Update(14200, new Point(8, 0), new int[0], new int[0]), "motion pauses reset the two-second window");
            State state = State.Decode(Json("Björk — Jóga", "revision", true));
            Check(state.Title == "Björk — Jóga" && state.Lyric == "A current timed lyric", "Unicode title and timed lyric JSON");
            Check(Throws(() => State.Decode(Encoding.UTF8.GetBytes("{\"protocol\":99}"))), "reject incompatible protocol");
            Check(!new State().Online && new State().Title == "" && new State().Lyric == "", "offline clears presentation");

            using (Mailbox box = new Mailbox()) {
                Bitmap first = new Bitmap(2, 2); box.Publish(state, first);
                for (int i = 0; i < 100000; i++) box.Publish(state, null);
                Packet result = box.Take();
                Check(object.ReferenceEquals(first, result.Artwork) && box.Take() == null, "100000 updates retain one state and its pending image");
                result.Artwork.Dispose();
                Bitmap obsolete = new Bitmap(2, 2); box.Publish(state, obsolete); box.Publish(new State(), null);
                Check(Throws(() => { int width = obsolete.Width; }), "discarded images disposed on disconnect");
                box.Take();
                Bitmap stopped = new Bitmap(2, 2); box.Dispose(); box.Publish(state, stopped);
                Check(Throws(() => { int width = stopped.Width; }), "shutdown disposes late image results");
            }

            using (Bitmap original = new Bitmap(2048, 1024)) using (MemoryStream encoded = new MemoryStream()) {
                original.Save(encoded, ImageFormat.Png);
                using (Bitmap decoded = Poller.DecodeArtwork(encoded.ToArray())) Check(decoded.Width == 1024 && decoded.Height == 512, "art decode bounded to 1024 pixels");
            }
            Check(Throws(() => Poller.DecodeArtwork(new byte[] { 1, 2, 3 })), "bad artwork fails gracefully");
            Check(Throws(() => Poller.Fetch("http://example.com/", 100)), "never connects off loopback");
            using (Server server = new Server()) {
                server.Mode = "oversize"; Check(Throws(() => Poller.Fetch("http://127.0.0.1:" + server.Port + "/state", 1000)), "HTTP size cap");
                server.Mode = "redirect"; Check(Throws(() => Poller.Fetch("http://127.0.0.1:" + server.Port + "/state", 1000)), "redirect rejected");
                server.Mode = "timeout"; var watch = System.Diagnostics.Stopwatch.StartNew();
                Check(Throws(() => Poller.Fetch("http://127.0.0.1:" + server.Port + "/state", 1000)) && watch.ElapsedMilliseconds < 1400, "unresponsive server timeout");
            }
            using (Server server = new Server()) using (Mailbox box = new Mailbox()) using (Poller poll = new Poller(box, server.Port)) {
                Packet first = Await(box, p => p.State.Online && p.Artwork != null); first.Artwork.Dispose();
                int firstRead = server.States;
                Thread.Sleep(900);
                Packet latest = Await(box, p => p.State.Online);
                Check(server.States > firstRead && server.Arts == 1 && latest.Artwork == null, "live polling caches unchanged artwork");
                server.Enabled = false;
                Packet disabled = Await(box, p => p.State.Online && !p.State.Enabled);
                Check(!disabled.State.Enabled, "live disable observed");
                server.Dispose(); Packet offline = Await(box, p => !p.State.Online);
                Check(offline.State.Title == "" && offline.State.Lyric == "" && offline.Artwork == null, "disconnect clears old song and artwork");
            }
            using (Server server = new Server()) using (Mailbox box = new Mailbox()) {
                server.Mode = "bad-json";
                using (Poller poll = new Poller(box, server.Port)) Check(Await(box, p => !p.State.Online).State.Status.Contains("127.0.0.1:" + server.Port), "failed connection names endpoint while waiting and retrying");
            }

            using (Server server = new Server()) using (Mailbox box = new Mailbox()) {
                server.Mode = "bad-art";
                using (Poller poll = new Poller(box, server.Port)) {
                    Await(box, p => p.State.Online); Thread.Sleep(800);
                    Check(server.Arts == 1, "corrupt artwork is not downloaded repeatedly");
                }
            }
            // Exercise the real fullscreen handlers without showing/taking over the desktop.
            var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
            using (SaverForm form = new SaverForm(new Options { Mode = "s", Port = 1 })) {
                IntPtr window = form.Handle;
                var formInput = (StartupInputGuard)typeof(SaverForm).GetField("input", flags).GetValue(form);
                var formClock = (System.Diagnostics.Stopwatch)typeof(SaverForm).GetField("age", flags).GetValue(form);
                formInput.Start(formClock.ElapsedMilliseconds, Cursor.Position);
                typeof(SaverForm).GetMethod("OnKeyDown", flags).Invoke(form, new object[] { new KeyEventArgs(Keys.Space) });
                typeof(SaverForm).GetMethod("OnMouseDown", flags).Invoke(form, new object[] { new MouseEventArgs(MouseButtons.Left, 1, 0, 0, 0) });
                Check(!form.IsDisposed, "real fullscreen key/click do not dismiss");
                var inbox = (Mailbox)typeof(SaverForm).GetField("mailbox", flags).GetValue(form);
                inbox.Publish(new State { Online = true, Enabled = false, Session = "disabled-at-launch" }, null);
                typeof(SaverForm).GetMethod("Tick", flags).Invoke(form, new object[] { null, EventArgs.Empty });
                Check(!form.IsDisposed, "initially disabled player remains visible with instructions");
                formInput.Start(formClock.ElapsedMilliseconds - 3001, Cursor.Position);
                typeof(SaverForm).GetMethod("OnKeyDown", flags).Invoke(form, new object[] { new KeyEventArgs(Keys.Space) });
                Check(!form.IsDisposed, "real fullscreen single key never bypasses hold detector");
                typeof(SaverForm).GetMethod("ExitSaver", flags).Invoke(form, new object[0]);
                Check(form.IsDisposed, "normal fullscreen exit closes the form");
            }
            using (SaverForm form = new SaverForm(new Options { Mode = "s", Port = 1 })) {
                IntPtr window = form.Handle;
                var inbox = (Mailbox)typeof(SaverForm).GetField("mailbox", flags).GetValue(form);
                inbox.Publish(new State { Online = true, Enabled = true, Session = "live-disable" }, null);
                typeof(SaverForm).GetMethod("Tick", flags).Invoke(form, new object[] { null, EventArgs.Empty });
                inbox.Publish(new State { Online = true, Enabled = false, Session = "live-disable" }, null);
                typeof(SaverForm).GetMethod("Tick", flags).Invoke(form, new object[] { null, EventArgs.Empty });
                Check(form.IsDisposed, "explicit disable of active saver still closes it");
            }
            using (SaverForm form = new SaverForm(new Options { Mode = "s", Port = 1, HasInitialCloseRevision = true, InitialCloseRevision = 0 })) {
                IntPtr window = form.Handle;
                var inbox = (Mailbox)typeof(SaverForm).GetField("mailbox", flags).GetValue(form);
                inbox.Publish(new State { Online = true, Enabled = true, Session = "immediate-close", CloseRevision = 1 }, null);
                typeof(SaverForm).GetMethod("Tick", flags).Invoke(form, new object[] { null, EventArgs.Empty });
                Check(form.IsDisposed, "close requested before first status packet still exits normally");
            }
            using (Form parent = new Form()) using (SaverForm child = new SaverForm(new Options { Mode = "p", Parent = parent.Handle, Port = 1 })) {
                IntPtr handle = child.Handle;
                Check(GetParent(handle) == parent.Handle && (Native.GetWindowLong(handle, -16) & 0x40000000) != 0, "preview embeds as child before display");
                child.Close();
            }
            if (args.Length > 1) {
                using (Server server = new Server()) using (Form parent = new Form()) {
                    IntPtr host = parent.Handle;
                    var info = new System.Diagnostics.ProcessStartInfo(args[1], "/p " + host.ToInt64() + " /port:" + server.Port) { UseShellExecute = false, CreateNoWindow = true, WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden };
                    using (var preview = System.Diagnostics.Process.Start(info)) {
                        try {
                            Thread.Sleep(1000);
                            Check(!preview.HasExited && server.States > 0, "real .scr preview process starts and polls");
                            parent.Dispose();
                            Check(preview.WaitForExit(5000) && preview.ExitCode == 0, "real .scr exits when preview parent closes");
                        } finally { if (!preview.HasExited) preview.Kill(); }
                    }
                }
            }
            using (Server server = new Server()) {
                var changed = new System.Collections.Generic.Dictionary<string, object> { { "brightness", 27 }, { "enabled", false } };
                State saved = SettingsApi.Save(server.Port, changed);
                Check(!saved.Enabled && saved.Brightness == 27 && server.AuthenticatedPosts == 1, "native settings authenticate and save enable/brightness");
                Check(server.LastPayload.Contains("brightness") && server.LastPayload.Contains("enabled"), "only settings are submitted");
                server.RejectSettings = true;
                Check(Throws(() => SettingsApi.Save(server.Port, changed)), "save rejection is reported rather than claiming success");
            }
            Rectangle mainBounds = new Rectangle(0, 0, 1200, 900);
            Rectangle[] monitors = { new Rectangle(-800, 100, 800, 600), mainBounds, new Rectangle(1200, -500, 640, 480) };
            using (DisplayCover covers = new DisplayCover(monitors, mainBounds, false, null, null)) {
                Check(covers.Windows.Count == 2 && covers.Windows[0].Bounds == monitors[0] && covers.Windows[1].Bounds == monitors[2], "blackouts cover all secondary monitors including negative coordinates");
                foreach (CoverForm cover in covers.Windows) {
                    using (Bitmap screenshot = new Bitmap(cover.Width, cover.Height)) {
                        cover.DrawToBitmap(screenshot, new Rectangle(Point.Empty, cover.Size));
                        Check(screenshot.GetPixel(0, 0).ToArgb() == Color.Black.ToArgb() && screenshot.GetPixel(cover.Width - 1, cover.Height - 1).ToArgb() == Color.Black.ToArgb(), "secondary monitor is black edge to edge");
                    }
                }
                var firstCover = covers.Windows[0]; covers.Dispose();
                Check(firstCover.IsDisposed && covers.Windows.Count == 0, "closing saver releases every blackout");
            }
            using (HoldPreview hold = new HoldPreview()) {
                hold.Start(monitors, mainBounds, delegate(Graphics g, Size z) { g.Clear(Color.Teal); }, false);
                Check(hold.Active, "hold preview starts immediately");
                hold.Stop(); Check(!hold.Active, "hold preview release bypasses three-second saver grace");
                hold.Start(monitors, mainBounds, null, false); hold.Dispose(); Check(!hold.Active, "preview cleanup cannot leave covered monitors");
            }
            using (Server server = new Server()) using (SettingsForm settings = new SettingsForm(new Options { Port = server.Port })) {
                IntPtr window = settings.Handle;
                var enableBox = (CheckBox)typeof(SettingsForm).GetField("enabled", flags).GetValue(settings);
                var passwordBox = (CheckBox)typeof(SettingsForm).GetField("requirePassword", flags).GetValue(settings);
                var slider = (TrackBar)typeof(SettingsForm).GetField("brightness", flags).GetValue(settings);
                var held = (HoldPreview)typeof(SettingsForm).GetField("held", flags).GetValue(settings);
                var button = (Button)typeof(SettingsForm).GetField("preview", flags).GetValue(settings);
                Pump(() => (bool)typeof(SettingsForm).GetField("loaded", flags).GetValue(settings));
                Pump(() => server.States > 0 && ((State)typeof(SettingsForm).GetField("state", flags).GetValue(settings)).Online);
                Check(enableBox.Checked && slider.Value == 50 && !passwordBox.Checked, "settings window loads player values and local password choice");
                Check(settings.ClientSize.Width >= 700 && settings.ClientSize.Height >= 480, "settings window leaves room for every control");
                passwordBox.Checked = true;
                typeof(SettingsForm).GetMethod("Save", flags).Invoke(settings, new object[] { false });
                Pump(() => !(bool)typeof(SettingsForm).GetField("saving", flags).GetValue(settings) && ConfigStore.Load().RequirePassword);
                Check(server.AuthenticatedPosts == 0 && ConfigStore.Load().RequirePassword, "password-only Apply saves locally without sending an unrelated web setting");
                slider.Value = 63;
                held.Start(monitors, mainBounds, null, false);
                typeof(Control).GetMethod("OnMouseUp", flags).Invoke(button, new object[] { new MouseEventArgs(MouseButtons.Left, 1, 0, 0, 0) });
                Check(!held.Active && server.AuthenticatedPosts == 0, "button mouse release ends preview without saving draft");
                held.Start(monitors, mainBounds, null, false);
                typeof(Control).GetMethod("OnMouseCaptureChanged", flags).Invoke(button, new object[] { EventArgs.Empty });
                Check(!held.Active, "lost mouse capture ends preview");
                held.Start(monitors, mainBounds, null, false);
                typeof(Form).GetMethod("OnDeactivate", flags).Invoke(settings, new object[] { EventArgs.Empty });
                Check(!held.Active, "switching away from settings ends preview");
                typeof(SettingsForm).GetMethod("Save", flags).Invoke(settings, new object[] { false });
                Pump(() => server.AuthenticatedPosts == 1 && !(bool)typeof(SettingsForm).GetField("saving", flags).GetValue(settings));
                Check(server.Brightness == 63 && !server.LastPayload.Contains("enabled"), "Apply persists only edited fields through the real HTTP client");
                Check(ConfigStore.Load().Brightness == 63, "Apply persists artwork brightness to the sidecar configuration");
                settings.StartPosition = FormStartPosition.Manual; settings.Location = new Point(-30000, -30000);
                settings.ShowInTaskbar = false; settings.Show(); Application.DoEvents(); settings.PerformLayout();
                using (Bitmap screenshot = new Bitmap(settings.Width, settings.Height)) {
                    settings.DrawToBitmap(screenshot, new Rectangle(Point.Empty, settings.Size));
                    using (var file = new FileStream(Path.Combine(output, "screensaver-settings.png"), FileMode.CreateNew)) screenshot.Save(file, ImageFormat.Png);
                }
                ((System.Windows.Forms.Timer)typeof(SettingsForm).GetField("timer", flags).GetValue(settings)).Stop();
                button.Capture = true;
                Rectangle tiny = new Rectangle(-29000, -29000, 80, 60);
                typeof(SettingsForm).GetMethod("StartPreview", flags, null, new[] { typeof(Rectangle[]), typeof(Rectangle) }, null).Invoke(settings, new object[] { new[] { tiny, new Rectangle(-28900, -29000, 80, 60) }, tiny });
                Check(button.Capture && held.Active, "shown nonactivating preview preserves Preview button capture (active=" + held.Active + ", capture=" + button.Capture + ", status=" + ((Label)typeof(SettingsForm).GetField("status", flags).GetValue(settings)).Text + ")");
                typeof(Control).GetMethod("OnMouseUp", flags).Invoke(button, new object[] { new MouseEventArgs(MouseButtons.Left, 1, 0, 0, 0) });
                Check(!held.Active, "release closes shown preview windows immediately");
                slider.Value = 19; settings.Close();
                Check(server.Brightness == 63 && server.AuthenticatedPosts == 1, "closing settings discards unsaved changes");
            }
            using (Bitmap art = new Bitmap(300, 300)) using (Graphics ag = Graphics.FromImage(art))
            using (Bitmap full = new Bitmap(1200, 900)) using (Bitmap dark = new Bitmap(1200, 900)) {
                ag.Clear(Color.Teal);
                using (Font font = new Font("Segoe UI", 35)) ag.DrawString("PAF\nPLAYER", font, Brushes.White, 30, 85);
                state.HasArt = true; state.Status = "Playing"; state.Lyric = "The current lyric stays in time with the song";
                state.Brightness = 100; using (Graphics g = Graphics.FromImage(full)) Painter.Draw(g, full.Size, state, art, 0);
                state.Brightness = 0; using (Graphics g = Graphics.FromImage(dark)) Painter.Draw(g, dark.Size, state, art, 0);
                Check(full.GetPixel(400, 75).G > 0 && dark.GetPixel(400, 75).ToArgb() == Color.Black.ToArgb(), "brightness changes only artwork");
                bool equalText = true;
                for (int y = 550; y < 880; y += 3) for (int x = 50; x < 1150; x += 3) if (full.GetPixel(x, y) != dark.GetPixel(x, y)) equalText = false;
                Check(equalText, "brightness does not dim title or lyric");
                using (var file = new FileStream(Path.Combine(output, "screensaver-playing.png"), FileMode.CreateNew)) full.Save(file, ImageFormat.Png);
                state = new State(); using (Graphics g = Graphics.FromImage(dark)) Painter.Draw(g, dark.Size, state, null, 0);
                using (var file = new FileStream(Path.Combine(output, "screensaver-waiting.png"), FileMode.CreateNew)) dark.Save(file, ImageFormat.Png);
            }
            Console.WriteLine("COMPLETE: " + count + " checks passed"); return 0;
        } catch (Exception exc) { Console.Error.WriteLine(exc); return 1; }
    }
}
