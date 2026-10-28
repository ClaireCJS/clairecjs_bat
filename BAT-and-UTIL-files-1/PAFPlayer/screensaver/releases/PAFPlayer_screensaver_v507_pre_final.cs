// Standalone visual screensaver; no Python import and no audio ownership.
// 2026-09-29 startup-grace hotfix: three seconds from first display.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace PAFPlayerScreenSaver {
    // Sample physical input so auto-repeat and incidental pointer jitter cannot dismiss the saver.
    public sealed class StartupInputGuard {
        public const int GraceMilliseconds = 3000;
        public const int HoldMilliseconds = 1000, MotionMilliseconds = 2000, MultiKeyMilliseconds = 2000;
        const int MotionGapMilliseconds = 450;
        long shownAt, lastKeyHit = -1, motionStarted = -1, lastMotion = -1;
        bool shown, armed; Point previousMouse; int motionDistance;
        readonly HashSet<int> previousKeys = new HashSet<int>(), previousButtons = new HashSet<int>();
        readonly Dictionary<int, long> heldKeys = new Dictionary<int, long>(), heldButtons = new Dictionary<int, long>();
        public void Start(long now, Point mouse) {
            shownAt = now; shown = true; armed = false; previousMouse = mouse;
            lastKeyHit = motionStarted = lastMotion = -1; motionDistance = 0;
            previousKeys.Clear(); previousButtons.Clear(); heldKeys.Clear(); heldButtons.Clear();
        }
        public bool AcceptInput(long now) { return shown && now - shownAt >= GraceMilliseconds; }
        static void CopySet(HashSet<int> target, HashSet<int> source) {
            target.Clear(); foreach (int code in source) target.Add(code);
        }
        public bool Update(long now, Point mouse, IEnumerable<int> pressedKeys, IEnumerable<int> pressedButtons) {
            HashSet<int> keys = new HashSet<int>(pressedKeys), buttons = new HashSet<int>(pressedButtons);
            if (!AcceptInput(now) || !armed) {
                armed = AcceptInput(now); previousMouse = mouse;
                CopySet(previousKeys, keys); CopySet(previousButtons, buttons);
                heldKeys.Clear(); heldButtons.Clear(); motionStarted = lastMotion = -1; motionDistance = 0;
                return false;
            }
            foreach (int code in new List<int>(heldKeys.Keys)) if (!keys.Contains(code)) heldKeys.Remove(code);
            foreach (int code in keys) {
                if (!previousKeys.Contains(code)) {
                    if (lastKeyHit >= 0 && now - lastKeyHit <= MultiKeyMilliseconds) return true;
                    lastKeyHit = now; heldKeys[code] = now;
                } else if (heldKeys.ContainsKey(code) && now - heldKeys[code] >= HoldMilliseconds) return true;
            }
            foreach (int code in new List<int>(heldButtons.Keys)) if (!buttons.Contains(code)) heldButtons.Remove(code);
            foreach (int code in buttons) {
                if (!previousButtons.Contains(code)) heldButtons[code] = now;
                else if (heldButtons.ContainsKey(code) && now - heldButtons[code] >= HoldMilliseconds) return true;
            }
            long distance = Math.Abs((long)mouse.X - previousMouse.X) + Math.Abs((long)mouse.Y - previousMouse.Y);
            if (distance >= 2) {
                if (motionStarted < 0 || now - lastMotion > MotionGapMilliseconds) { motionStarted = now; motionDistance = 0; }
                motionDistance += (int)Math.Min(distance, 1000); lastMotion = now;
                if (now - motionStarted >= MotionMilliseconds && motionDistance >= 24) return true;
            } else if (lastMotion >= 0 && now - lastMotion > MotionGapMilliseconds) {
                motionStarted = lastMotion = -1; motionDistance = 0;
            }
            previousMouse = mouse; CopySet(previousKeys, keys); CopySet(previousButtons, buttons);
            return false;
        }
    }

    public sealed class Options {
        public string Mode = "c";
        public IntPtr Parent = IntPtr.Zero;
        public int Port = 666;
        public static Options Parse(string[] args) {
            Options value = new Options(); bool modeSeen = false;
            for (int i = 0; i < args.Length; i++) {
                string arg = args[i].ToLowerInvariant();
                if (arg.StartsWith("/port:")) {
                    int port;
                    if (!int.TryParse(arg.Substring(6), out port) || port < 1 || port > 65535) throw new ArgumentException("Invalid port");
                    value.Port = port; continue;
                }
                if (modeSeen || arg.Length < 2 || (arg[0] != '/' && arg[0] != '-')) throw new ArgumentException("Invalid screensaver argument");
                string mode = arg.Substring(1, 1);
                if (mode != "s" && mode != "p" && mode != "c") throw new ArgumentException("Expected /s, /p HWND, or /c");
                modeSeen = true; value.Mode = mode;
                string handle = "";
                if (arg.Length > 2) {
                    if (arg[2] != ':' || mode == "s") throw new ArgumentException("Invalid screensaver argument");
                    handle = arg.Substring(3);
                } else if (mode != "s" && i + 1 < args.Length && !args[i + 1].StartsWith("/")) handle = args[++i];
                if (handle.Length > 0) {
                    long number;
                    if (!long.TryParse(handle, out number) || number <= 0) throw new ArgumentException("Invalid preview handle");
                    value.Parent = new IntPtr(number);
                }
                if (mode == "p" && value.Parent == IntPtr.Zero) throw new ArgumentException("Preview requires a parent window");
            }
            return value;
        }
    }

    public sealed class State {
        public bool Enabled, Online, HasArt, RequirePassword;
        public int Brightness = 50, CloseRevision;
        public string Version = "", Title = "", Lyric = "", Status = "Waiting for PAFPlayer", ArtRevision = "", Session = "";
        public static State Decode(byte[] data) {
            JavaScriptSerializer serializer = new JavaScriptSerializer { MaxJsonLength = 32768, RecursionLimit = 8 };
            var map = serializer.Deserialize<Dictionary<string, object>>(System.Text.Encoding.UTF8.GetString(data));
            if (map == null || Number(map, "protocol", -1) != 1) throw new FormatException("Unsupported PAFPlayer sidecar protocol");
            return new State {
                Online = true, Version = Text(map, "player_version", 40), Enabled = Flag(map, "enabled"), HasArt = Flag(map, "has_art"),
                Brightness = Math.Max(0, Math.Min(100, Number(map, "brightness", 50))),
                CloseRevision = Number(map, "close_revision", 0), Session = Text(map, "session", 80),
                Title = Text(map, "title", 1100), Lyric = Text(map, "lyric", 2000),
                Status = Text(map, "status", 100), ArtRevision = Text(map, "art_revision", 160)
            };
        }
        static bool Flag(Dictionary<string, object> map, string key) { object v; return map.TryGetValue(key, out v) && v is bool && (bool)v; }
        static int Number(Dictionary<string, object> map, string key, int fallback) { object v; return map.TryGetValue(key, out v) && v is int ? (int)v : fallback; }
        static string Text(Dictionary<string, object> map, string key, int limit) { object v; string text = map.TryGetValue(key, out v) ? v as string : null; text = text ?? ""; return text.Substring(0, Math.Min(text.Length, limit)); }
        public string Signature { get { return string.Join("\n", new string[] { Online.ToString(), Enabled.ToString(), Title, Lyric, Status, ArtRevision, Brightness.ToString() }); } }
    }

    public sealed class ScreenSaverConfig {
        public bool Enabled = true;
        public int Brightness = 50;
        public bool RequirePassword;
    }

    public static class ConfigStore {
        // Tests may isolate persistence without changing the production path.
        public static string OverridePath;
        public static string PathName {
            get {
                if (!string.IsNullOrEmpty(OverridePath)) return OverridePath;
                string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
                DirectoryInfo folder = new DirectoryInfo(root);
                if (folder.Name.Equals("screensaver", StringComparison.OrdinalIgnoreCase) && folder.Parent != null && folder.Parent.Name.Equals("PAFPlayer", StringComparison.OrdinalIgnoreCase))
                    return Path.Combine(root, "PAFPlayer.cfg");
                return Path.Combine(root, "PAFPlayer", "screensaver", "PAFPlayer.cfg");
            }
        }
        public static ScreenSaverConfig Load() {
            ScreenSaverConfig result = new ScreenSaverConfig();
            try {
                if (!File.Exists(PathName)) return result;
                foreach (string raw in File.ReadAllLines(PathName)) {
                    string line = raw.Trim();
                    if (line.Length == 0 || line.StartsWith("#") || line.StartsWith(";")) continue;
                    int split = line.IndexOf('='); if (split < 1) continue;
                    string key = line.Substring(0, split).Trim().ToLowerInvariant();
                    string value = line.Substring(split + 1).Trim();
                    bool flag; int number;
                    if (key == "enabled" && bool.TryParse(value, out flag)) result.Enabled = flag;
                    if (key == "artwork_brightness" && int.TryParse(value, out number)) result.Brightness = Math.Max(0, Math.Min(100, number));
                    if (key == "require_password" && bool.TryParse(value, out flag)) result.RequirePassword = flag;
                }
            } catch (IOException) { } catch (UnauthorizedAccessException) { }
            return result;
        }
        static byte[] Digest(string path) {
            using (var hash = System.Security.Cryptography.SHA256.Create())
            using (FileStream input = File.OpenRead(path)) return hash.ComputeHash(input);
        }
        static bool Same(byte[] left, byte[] right) {
            if (left.Length != right.Length) return false;
            for (int i = 0; i < left.Length; i++) if (left[i] != right[i]) return false;
            return true;
        }
        static string CollisionSafe(string desired) {
            if (!File.Exists(desired) && !Directory.Exists(desired)) return desired;
            string directory = Path.GetDirectoryName(desired), extension = Path.GetExtension(desired);
            string stem = Path.GetFileNameWithoutExtension(desired);
            for (int number = 1; ; number++) {
                string candidate = Path.Combine(directory, stem + " (" + number + ")" + extension);
                if (!File.Exists(candidate) && !Directory.Exists(candidate)) return candidate;
            }
        }
        public static string Save(bool enabled, int brightness) { return Save(enabled, brightness, Load().RequirePassword); }
        public static string Save(bool enabled, int brightness, bool requirePassword) {
            brightness = Math.Max(0, Math.Min(100, brightness));
            string path = PathName, directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory)) Directory.CreateDirectory(directory);
            byte[] data = new System.Text.UTF8Encoding(false).GetBytes(
                "# PAFPlayer visual screensaver settings\r\n" +
                "enabled=" + enabled.ToString().ToLowerInvariant() + "\r\n" +
                "artwork_brightness=" + brightness + "\r\n" +
                "require_password=" + requirePassword.ToString().ToLowerInvariant() + "\r\n");
            if (File.Exists(path) && Same(File.ReadAllBytes(path), data)) return path;
            if (File.Exists(path)) {
                string desired = path + ".bak." + DateTime.Now.ToString("yyyyMMddHHmm") + ".replaced-by-chatgpt.bak";
                string backup = CollisionSafe(desired);
                File.Copy(path, backup, false);
                if (!Same(Digest(path), Digest(backup))) throw new IOException("Configuration backup verification failed.");
            }
            string temporary = CollisionSafe(path + ".tmp");
            File.WriteAllBytes(temporary, data);
            if (File.Exists(path)) File.Replace(temporary, path, null); else File.Move(temporary, path);
            if (!Same(Digest(path), System.Security.Cryptography.SHA256.Create().ComputeHash(data)))
                throw new IOException("Configuration write verification failed.");
            return path;
        }
        public static void Apply(State state) {
            ScreenSaverConfig config = Load();
            // Brightness is screensaver-owned. Preserve a live player's enable/
            // disable state so disabling an active saver still closes it.
            if (!state.Online) state.Enabled = config.Enabled;
            state.Brightness = config.Brightness;
            state.RequirePassword = config.RequirePassword;
        }
    }

    public sealed class Packet { public State State; public Bitmap Artwork; }

    // Latest state plus at most one decoded image. A slow GUI never queues frames.
    public sealed class Mailbox : IDisposable {
        readonly object gate = new object(); Packet latest; bool closed;
        public void Publish(State state, Bitmap art) {
            lock (gate) {
                if (closed) { if (art != null) art.Dispose(); return; }
                if (latest != null && latest.Artwork != null) {
                    if (art == null && state.HasArt && latest.State.ArtRevision == state.ArtRevision) art = latest.Artwork;
                    else latest.Artwork.Dispose();
                }
                latest = new Packet { State = state, Artwork = art };
            }
        }
        public Packet Take() { lock (gate) { Packet result = latest; latest = null; return result; } }
        public void Dispose() { lock (gate) { closed = true; if (latest != null && latest.Artwork != null) latest.Artwork.Dispose(); latest = null; } }
    }

    public sealed class Poller : IDisposable {
        readonly Mailbox mailbox; readonly string origin; readonly ManualResetEvent stop = new ManualResetEvent(false);
        readonly Thread worker; string fetched = ""; DateTime retryArt = DateTime.MinValue;
        public Poller(Mailbox box, int port) {
            mailbox = box; origin = "http://127.0.0.1:" + port;
            worker = new Thread(Run) { IsBackground = true, Name = "PAFPlayer screensaver reader", Priority = ThreadPriority.BelowNormal };
            worker.Start();
        }
        public static byte[] Fetch(string url, int limit) {
            Uri uri = new Uri(url);
            if (uri.Scheme != "http" || uri.Host != "127.0.0.1") throw new ArgumentException("Loopback only");
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(uri);
            request.Proxy = null; request.AllowAutoRedirect = false; request.Timeout = 700; request.ReadWriteTimeout = 700;
            request.KeepAlive = false;
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse()) {
                if (response.StatusCode != HttpStatusCode.OK || response.ContentLength > limit) throw new IOException("Invalid or oversized response");
                using (Stream input = response.GetResponseStream())
                using (MemoryStream output = new MemoryStream()) {
                    byte[] block = new byte[16384]; int count; Stopwatch deadline = Stopwatch.StartNew();
                    while ((count = input.Read(block, 0, Math.Min(block.Length, limit + 1 - (int)output.Length))) > 0) {
                        output.Write(block, 0, count);
                        if (output.Length > limit || deadline.ElapsedMilliseconds > 1200) throw new IOException("Response limit exceeded");
                    }
                    return output.ToArray();
                }
            }
        }
        public static Bitmap DecodeArtwork(byte[] data) {
            using (MemoryStream bytes = new MemoryStream(data))
            using (Image image = Image.FromStream(bytes, false, true)) {
                if ((long)image.Width * image.Height > 32000000) throw new IOException("Artwork dimensions exceed limit");
                float scale = Math.Min(1f, Math.Min(1024f / image.Width, 1024f / image.Height));
                Bitmap result = new Bitmap(Math.Max(1, (int)(image.Width * scale)), Math.Max(1, (int)(image.Height * scale)));
                try { using (Graphics g = Graphics.FromImage(result)) { g.Clear(Color.Black); g.InterpolationMode = InterpolationMode.HighQualityBicubic; g.DrawImage(image, 0, 0, result.Width, result.Height); } }
                catch { result.Dispose(); throw; }
                return result;
            }
        }
        void Run() {
            while (!stop.WaitOne(0)) {
                State state; Bitmap image = null;
                try {
                    state = State.Decode(Fetch(origin + "/api/screensaver/state", 32768));
                    ConfigStore.Apply(state);
                    if (!state.Enabled || !state.HasArt) fetched = "";
                    else if (state.ArtRevision != fetched && DateTime.UtcNow >= retryArt) {
                        try {
                            byte[] bytes = Fetch(origin + "/api/screensaver/art?revision=" + Uri.EscapeDataString(state.ArtRevision), 16 * 1024 * 1024);
                            fetched = state.ArtRevision; // Cache unsupported/corrupt covers until their revision changes.
                            try { image = DecodeArtwork(bytes); } catch { }
                        } catch { retryArt = DateTime.UtcNow.AddSeconds(2); }
                    }
                } catch (Exception error) {
                    string reason = error is FormatException ? "Incompatible player response" : "Connection unavailable";
                    WebException web = error as WebException;
                    if (web != null) {
                        HttpWebResponse response = web.Response as HttpWebResponse;
                        reason = response != null ? "HTTP " + (int)response.StatusCode + " (restart/update PAFPlayer if 404)" : web.Status.ToString();
                        if (response != null) response.Dispose();
                    }
                    state = new State { Status = reason + " at " + origin + " — retrying" }; ConfigStore.Apply(state);
                    fetched = ""; retryArt = DateTime.MinValue;
                }
                mailbox.Publish(state, image);
                if (stop.WaitOne(state.Online && state.Enabled ? 200 : 1000)) break;
            }
        }
        public void Dispose() { stop.Set(); if (worker.Join(2500)) stop.Dispose(); }
    }

    public static class Painter {
        public static void Draw(Graphics g, Size size, State state, Image image, int drift) {
            g.Clear(Color.Black); if (size.Width < 2 || size.Height < 2) return;
            float scale = Math.Min(size.Width / 1000f, size.Height / 800f);
            float dx = drift * Math.Min(3, scale * 3);
            bool content = state.Online && state.Enabled;
            float top = size.Height * .055f;
            float available = size.Height * .50f;
            if (content && image != null && state.HasArt) {
                float fit = Math.Min(size.Width * .82f / image.Width, available / image.Height);
                Rectangle rect = new Rectangle((int)((size.Width - image.Width * fit) / 2 + dx), (int)top, Math.Max(1, (int)(image.Width * fit)), Math.Max(1, (int)(image.Height * fit)));
                float light = state.Brightness / 100f;
                using (ImageAttributes attributes = new ImageAttributes()) {
                    ColorMatrix matrix = new ColorMatrix(); matrix.Matrix00 = matrix.Matrix11 = matrix.Matrix22 = light;
                    attributes.SetColorMatrix(matrix);
                    g.InterpolationMode = InterpolationMode.HighQualityBilinear;
                    g.DrawImage(image, rect, 0, 0, image.Width, image.Height, GraphicsUnit.Pixel, attributes);
                }
            }
            string title = content ? state.Title : state.Online ? "PAFPlayer detected — screensaver disabled" : "Waiting for PAFPlayer";
            if (title.Length == 0) title = "PAFPlayer";
            Text(g, title, new RectangleF(size.Width * .06f + dx, size.Height * .60f, size.Width * .88f, size.Height * .115f), Math.Max(9, 30 * scale), Color.Gainsboro);
            Text(g, content ? state.Lyric : state.Online ? "Enable Visual Screensaver in screensaver Settings." : "Start PAFPlayer to show your music here.", new RectangleF(size.Width * .06f + dx, size.Height * .735f, size.Width * .88f, size.Height * .20f), Math.Max(10, 40 * scale), Color.White);
            string status = state.Online && !state.Enabled ? "Enable Visual Screensaver in screensaver Settings. " + state.Version : state.Status;
            Text(g, status, new RectangleF(12, size.Height * .96f, size.Width - 24, size.Height * .04f), Math.Max(7, 12 * scale), Color.Gray);
        }
        static void Text(Graphics g, string text, RectangleF bounds, float size, Color color) {
            using (StringFormat format = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center, Trimming = StringTrimming.EllipsisWord })
            using (SolidBrush brush = new SolidBrush(color)) {
                float fit = size;
                while (fit > Math.Max(7, size * .55f)) {
                    using (Font font = new Font("Segoe UI", fit, FontStyle.Regular, GraphicsUnit.Pixel)) {
                        SizeF measure = g.MeasureString(text, font, (int)Math.Max(1, bounds.Width), format);
                        if (measure.Height <= bounds.Height) break;
                    }
                    fit -= 1;
                }
                using (Font font = new Font("Segoe UI", fit, FontStyle.Regular, GraphicsUnit.Pixel)) g.DrawString(text, font, brush, bounds, format);
            }
        }
    }


    public static class SettingsApi {
        public static State Save(int port, IDictionary<string, object> changes) {
            string origin = "http://127.0.0.1:" + port;
            var serializer = new JavaScriptSerializer { MaxJsonLength = 16 * 1024 * 1024, RecursionLimit = 64 };
            var auth = serializer.Deserialize<Dictionary<string, object>>(System.Text.Encoding.UTF8.GetString(Poller.Fetch(origin + "/api/workflows/status", 16 * 1024 * 1024)));
            object token, local;
            if (auth == null || !auth.TryGetValue("local", out local) || !(local is bool) || !(bool)local || !auth.TryGetValue("token", out token) || !(token is string) || ((string)token).Length == 0)
                throw new IOException("Could not authorize local settings. Retry after PAFPlayer starts.");
            byte[] body = System.Text.Encoding.UTF8.GetBytes(serializer.Serialize(changes));
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(origin + "/api/screensaver/settings");
            request.Proxy = null; request.AllowAutoRedirect = false; request.KeepAlive = false;
            request.Timeout = 3000; request.ReadWriteTimeout = 3000; request.Method = "POST";
            request.ServicePoint.Expect100Continue = false;
            request.ContentType = "application/json"; request.ContentLength = body.Length;
            request.Headers["X-PAF-Workflow-Token"] = (string)token;
            using (Stream output = request.GetRequestStream()) output.Write(body, 0, body.Length);
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse()) {
                if (response.StatusCode != HttpStatusCode.OK) throw new IOException("Settings were not saved.");
                using (Stream input = response.GetResponseStream()) using (MemoryStream output = new MemoryStream()) {
                    byte[] buffer = new byte[4096]; int read;
                    while ((read = input.Read(buffer, 0, buffer.Length)) > 0) {
                        if (output.Length + read > 32768) throw new IOException("Invalid settings response.");
                        output.Write(buffer, 0, read);
                    }
                    return State.Decode(output.ToArray());
                }
            }
        }
    }

    // Nonactivating windows preserve capture on the settings Preview button.
    public sealed class CoverForm : Form {
        readonly Action<Graphics, Size> paint;
        readonly Action dismiss;
        public CoverForm(Rectangle bounds, Action<Graphics, Size> draw, Action exit) {
            paint = draw; dismiss = exit;
            FormBorderStyle = FormBorderStyle.None; StartPosition = FormStartPosition.Manual;
            AutoScaleMode = AutoScaleMode.None; BackColor = Color.Black; ShowInTaskbar = false;
            DoubleBuffered = true; TopMost = true; Bounds = bounds;
        }
        protected override bool ShowWithoutActivation { get { return true; } }
        protected override CreateParams CreateParams {
            get { CreateParams p = base.CreateParams; p.ExStyle |= 0x08000000 | 0x80; return p; }
        }
        protected override void OnPaint(PaintEventArgs e) {
            e.Graphics.Clear(Color.Black); if (paint != null) paint(e.Graphics, ClientSize);
        }
        protected override void OnMouseDown(MouseEventArgs e) { if (dismiss != null) dismiss(); base.OnMouseDown(e); }
        protected override void OnKeyDown(KeyEventArgs e) { if (dismiss != null) dismiss(); base.OnKeyDown(e); }
    }

    public sealed class DisplayCover : IDisposable {
        readonly List<CoverForm> windows = new List<CoverForm>();
        public IList<CoverForm> Windows { get { return windows.AsReadOnly(); } }
        public DisplayCover(Rectangle[] monitors, Rectangle primary, bool includePrimary, Action<Graphics, Size> draw, Action dismiss) {
            try {
                foreach (Rectangle bounds in monitors) {
                    if (bounds == primary && !includePrimary) continue;
                    windows.Add(new CoverForm(bounds, bounds == primary ? draw : null, dismiss));
                }
            } catch { Dispose(); throw; }
        }
        public static Rectangle[] MonitorBounds() {
            Screen[] screens = Screen.AllScreens; Rectangle[] result = new Rectangle[screens.Length];
            for (int i = 0; i < screens.Length; i++) result[i] = screens[i].Bounds;
            return result;
        }
        public void Show() {
            foreach (CoverForm window in windows.ToArray()) {
                if (window.IsDisposed) continue;
                try { window.Show(); } catch (ObjectDisposedException) { if (!window.IsDisposed) throw; }
            }
        }
        public void Refresh() { foreach (CoverForm window in windows) window.Invalidate(); }
        public void Dispose() {
            // Hide all displays first; none should remain black during cleanup.
            foreach (CoverForm window in windows) window.Hide();
            foreach (CoverForm window in windows) window.Dispose();
            windows.Clear();
        }
    }

    public sealed class HoldPreview : IDisposable {
        DisplayCover cover;
        public bool Active { get { return cover != null; } }
        public void Start(Rectangle[] monitors, Rectangle primary, Action<Graphics, Size> draw, bool show) {
            Stop(); cover = new DisplayCover(monitors, primary, true, draw, Stop);
            try { if (show) cover.Show(); } catch { Stop(); throw; }
        }
        public void Refresh() { if (cover != null) cover.Refresh(); }
        public void Stop() { DisplayCover old = cover; cover = null; if (old != null) old.Dispose(); }
        public void Dispose() { Stop(); }
    }

    public sealed class SettingsForm : Form {
        readonly Options options;
        readonly Mailbox mailbox = new Mailbox(); readonly Poller poller;
        readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = 30 };
        readonly CheckBox enabled = new CheckBox { Text = "Enable visual screensaver", AutoSize = true, Name = "enabled" };
        readonly CheckBox requirePassword = new CheckBox { Text = "Require password after lock", AutoSize = true, Name = "requirePassword" };
        readonly TrackBar brightness = new TrackBar { Minimum = 0, Maximum = 100, Value = 50, TickFrequency = 10, Dock = DockStyle.Fill, Name = "brightness" };
        readonly Label percent = new Label { Text = "50%", AutoSize = true, Anchor = AnchorStyles.Left };
        readonly Label status = new Label { Text = "Connecting to PAFPlayer…", AutoSize = true, MaximumSize = new Size(680, 0) };
        readonly Button preview = new Button { Text = "Hold to preview", AutoSize = true, Name = "preview" };
        readonly Button apply = new Button { Text = "Apply", AutoSize = true, Enabled = false, Name = "apply" };
        readonly Button ok = new Button { Text = "OK", AutoSize = true, Enabled = false };
        readonly HoldPreview held = new HoldPreview();
        State state = new State(); Bitmap artwork, sample; string revision = "";
        bool loaded, updating, enabledDirty, brightnessDirty, passwordDirty, saving, released, startingPreview; string saveError = "";
        public SettingsForm(Options value) {
            options = value; Text = "PAFPlayer Screensaver Settings";
            Font = new Font("Segoe UI", 10); AutoScaleDimensions = new SizeF(96, 96); AutoScaleMode = AutoScaleMode.Dpi;
            FormBorderStyle = FormBorderStyle.Sizable; MaximizeBox = false; MinimizeBox = false;
            MinimumSize = new Size(640, 440);
            StartPosition = FormStartPosition.CenterScreen; ClientSize = new Size(760, 520);
            var layout = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, Padding = new Padding(18), ColumnCount = 2, RowCount = 8 };
            var body = new Panel { Dock = DockStyle.Fill, AutoScroll = true, Name = "settingsBody" };
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100)); layout.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            layout.Controls.Add(enabled, 0, 0); layout.SetColumnSpan(enabled, 2);
            layout.Controls.Add(requirePassword, 0, 1); layout.SetColumnSpan(requirePassword, 2);
            var passwordExplanation = new Label { Text = "When the fullscreen screensaver closes, lock Windows so you must sign in to return to the desktop.", AutoSize = true, MaximumSize = new Size(680, 0), Margin = new Padding(3, 3, 3, 10) };
            layout.Controls.Add(passwordExplanation, 0, 2); layout.SetColumnSpan(passwordExplanation, 2);
            var caption = new Label { Text = "Artwork brightness", AutoSize = true, Margin = new Padding(3, 14, 3, 0) };
            layout.Controls.Add(caption, 0, 3); layout.SetColumnSpan(caption, 2);
            layout.Controls.Add(brightness, 0, 4); layout.Controls.Add(percent, 1, 4);
            var explanation = new Label { Text = "Artwork and lyrics appear on the primary monitor.\nAll other monitors turn black. Release Preview to return.", AutoSize = true, Margin = new Padding(3, 6, 3, 10) };
            layout.Controls.Add(explanation, 0, 5); layout.SetColumnSpan(explanation, 2);
            layout.Controls.Add(preview, 0, 6); layout.SetColumnSpan(preview, 2);
            layout.Controls.Add(status, 0, 7); layout.SetColumnSpan(status, 2);
            var buttons = new FlowLayoutPanel { AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false, FlowDirection = FlowDirection.RightToLeft, Dock = DockStyle.Bottom, Padding = new Padding(12, 8, 12, 12), Name = "settingsFooter" };
            var cancel = new Button { Text = "Cancel", AutoSize = true, DialogResult = DialogResult.Cancel };
            buttons.Controls.Add(cancel); buttons.Controls.Add(ok); buttons.Controls.Add(apply);
            body.Controls.Add(layout);
            // Footer reserves its own client area; wrapped status text scrolls above it.
            Controls.Add(body); Controls.Add(buttons);
            CancelButton = cancel; AcceptButton = ok;
            enabled.CheckedChanged += delegate { if (!updating) { enabledDirty = true; saveError = ""; } UpdateButtons(); };
            requirePassword.CheckedChanged += delegate { if (!updating) { passwordDirty = true; saveError = ""; } UpdateButtons(); };
            brightness.ValueChanged += delegate { percent.Text = brightness.Value + "%"; if (!updating) { brightnessDirty = true; saveError = ""; } UpdateButtons(); };
            apply.Click += delegate { Save(false); }; ok.Click += delegate { Save(true); };
            preview.MouseDown += delegate(object sender, MouseEventArgs e) { if (e.Button == MouseButtons.Left) StartPreview(); };
            preview.MouseUp += delegate { StopPreview(); };
            preview.MouseCaptureChanged += delegate { if (!preview.Capture && !startingPreview) StopPreview(); };
            Deactivate += delegate { if (!startingPreview) StopPreview(); };
            ScreenSaverConfig local = ConfigStore.Load();
            updating = true; enabled.Checked = local.Enabled; brightness.Value = local.Brightness; requirePassword.Checked = local.RequirePassword; percent.Text = local.Brightness + "%"; updating = false;
            state.Enabled = local.Enabled; state.Brightness = local.Brightness; state.RequirePassword = local.RequirePassword; loaded = true;
            poller = new Poller(mailbox, options.Port); timer.Tick += Tick; timer.Start();
            status.Text = "Settings file: " + ConfigStore.PathName; UpdateButtons();
        }
        void UpdateButtons() {
            apply.Enabled = loaded && !saving && (enabledDirty || brightnessDirty || passwordDirty);
            ok.Enabled = loaded && !saving;
        }
        void Tick(object sender, EventArgs e) {
            // A lost mouse-up (release outside the button/window) must never trap a preview.
            if (held.Active && (Native.GetAsyncKeyState(1) & 0x8000) == 0) StopPreview();
            Packet packet = mailbox.Take();
            if (packet == null) return;
            state = packet.State;
            if (!state.Online || !state.Enabled || !state.HasArt || revision != state.ArtRevision || packet.Artwork != null) {
                if (artwork != null) artwork.Dispose(); artwork = packet.Artwork; packet.Artwork = null;
            }
            if (packet.Artwork != null) packet.Artwork.Dispose(); revision = state.ArtRevision;
            if (state.Online) {
                updating = true;
                if (!enabledDirty) enabled.Checked = state.Enabled;
                if (!brightnessDirty) brightness.Value = state.Brightness;
                if (!passwordDirty) requirePassword.Checked = state.RequirePassword;
                updating = false; loaded = true;
            }
            if (!saving) status.Text = saveError.Length > 0 ? saveError : (enabledDirty || brightnessDirty || passwordDirty) ? "Unsaved changes" : state.Online ? "Settings saved locally · connected to PAFPlayer " + state.Version : "Settings saved locally · PAFPlayer is not running";
            UpdateButtons(); held.Refresh();
        }
        void Save(bool closeAfter) {
            if (saving || !loaded) return;
            var changes = new Dictionary<string, object>();
            if (enabledDirty) changes["enabled"] = enabled.Checked;
            if (brightnessDirty) changes["brightness"] = brightness.Value;
            if (changes.Count == 0 && !passwordDirty) { if (closeAfter) Close(); return; }
            bool selectedEnabled = enabled.Checked, selectedPassword = requirePassword.Checked; int selectedBrightness = brightness.Value;
            saveError = ""; saving = true; enabled.Enabled = brightness.Enabled = requirePassword.Enabled = false; UpdateButtons(); status.Text = "Saving…";
            ThreadPool.QueueUserWorkItem(delegate {
                State saved = null; string error = null; bool localSaved = false;
                try {
                    ConfigStore.Save(selectedEnabled, selectedBrightness, selectedPassword); localSaved = true;
                    if (state.Online && changes.Count > 0) {
                        try { saved = SettingsApi.Save(options.Port, changes); }
                        catch (Exception ex) { error = "Saved locally; live PAFPlayer sync failed: " + ex.Message; }
                    }
                } catch (Exception ex) { error = "Could not save settings: " + ex.Message; }
                try {
                    if (!IsDisposed && IsHandleCreated) BeginInvoke((Action)delegate {
                        if (IsDisposed) return;
                        saving = false; enabled.Enabled = brightness.Enabled = requirePassword.Enabled = true;
                        if (localSaved) {
                            // Discard any pre-save poll result before clearing the dirty flags.
                            Packet pending = mailbox.Take(); if (pending != null && pending.Artwork != null) pending.Artwork.Dispose();
                            if (saved != null) state = saved;
                            state.Enabled = selectedEnabled; state.Brightness = selectedBrightness; state.RequirePassword = selectedPassword;
                            enabledDirty = brightnessDirty = passwordDirty = false; status.Text = error ?? "Settings saved to " + ConfigStore.PathName;
                            if (closeAfter) { Close(); return; }
                        } else { saveError = error; status.Text = error; }
                        UpdateButtons();
                    });
                } catch (InvalidOperationException) { }
            });
        }
        void StartPreview() { StartPreview(DisplayCover.MonitorBounds(), Screen.PrimaryScreen.Bounds); }
        void StartPreview(Rectangle[] monitors, Rectangle primary) {
            StopPreview(); startingPreview = true;
            try {
                held.Start(monitors, primary, DrawPreview, true);
                // WinForms may drop capture while showing new top-level windows.
                // Reacquire it only after all nonactivating overlays are shown.
                if (held.Active) preview.Capture = true;
            } catch { StopPreview(); status.Text = "Preview could not open. Try again."; }
            finally { startingPreview = false; }
        }
        void StopPreview() { held.Stop(); if (preview.Capture) preview.Capture = false; }
        void DrawPreview(Graphics graphics, Size size) {
            State display = new State { Online = true, Enabled = true, HasArt = true, Brightness = brightness.Value,
                Title = state.Enabled && state.Title.Length > 0 ? state.Title : "PAFPlayer screensaver preview",
                Lyric = state.Enabled && state.Title.Length > 0 ? state.Lyric : "Your artwork and lyrics appear here during playback.",
                Status = "Release the mouse button to return to settings" };
            if (sample == null) {
                sample = new Bitmap(300, 300);
                using (Graphics g = Graphics.FromImage(sample)) {
                    g.Clear(Color.Teal);
                    using (Font font = new Font("Segoe UI", 32)) g.DrawString("PAF\nPLAYER", font, Brushes.White, 30, 80);
                }
            }
            Painter.Draw(graphics, size, display, artwork ?? sample, 0);
        }
        protected override void Dispose(bool disposing) {
            if (disposing && !released) {
                released = true; StopPreview(); timer.Stop(); timer.Dispose(); poller.Dispose(); mailbox.Dispose();
                if (artwork != null) artwork.Dispose(); if (sample != null) sample.Dispose();
            }
            base.Dispose(disposing);
        }
    }

    public sealed class SaverForm : Form {
        readonly Options options; readonly Mailbox mailbox = new Mailbox(); readonly Poller poller;
        readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = 50 };
        State state = new State(); Bitmap artwork; string revision = "", session = ""; int closeRevision, drift;
        readonly StartupInputGuard input = new StartupInputGuard(); readonly Stopwatch age = Stopwatch.StartNew();
        bool cursorHidden, resourcesReleased, shown, dismissed; DisplayCover otherDisplays; string displayLayout = "";
        public SaverForm(Options value) {
            options = value; Text = "PAFPlayer Visual Screensaver"; BackColor = Color.Black;
            FormBorderStyle = FormBorderStyle.None; StartPosition = FormStartPosition.Manual; DoubleBuffered = true; ShowInTaskbar = false;
            Bounds = options.Mode == "p" ? new Rectangle(0, 0, 320, 240) : Screen.PrimaryScreen.Bounds;
            if (options.Mode == "p") TopLevel = false;
            TopMost = options.Mode == "s";
            poller = new Poller(mailbox, options.Port);
            timer.Tick += Tick; timer.Start();
        }
        protected override CreateParams CreateParams {
            get {
                CreateParams parameters = base.CreateParams;
                if (options != null && options.Mode == "p") {
                    parameters.Parent = options.Parent;
                    parameters.Style = (parameters.Style | 0x40000000) & ~unchecked((int)0x80000000);
                }
                return parameters;
            }
        }
        protected override void OnHandleCreated(EventArgs e) {
            base.OnHandleCreated(e);
            if (options.Mode == "p") {
                if (!Native.IsWindow(options.Parent)) { Close(); return; }
                Native.SetWindowLong(Handle, -16, (Native.GetWindowLong(Handle, -16) | 0x40000000) & ~unchecked((int)0x80000000));
                Native.SetParent(Handle, options.Parent);
            }
        }
        protected override void OnShown(EventArgs e) {
            base.OnShown(e);
            shown = true; input.Start(age.ElapsedMilliseconds, Cursor.Position);
            if (options.Mode == "s") { Cursor.Hide(); cursorHidden = true; CoverOtherDisplays(); }
        }
        void ExitSaver() { dismissed = true; Close(); }
        static List<int> PressedKeys() {
            var keys = new List<int>();
            for (int code = 8; code < 256; code++) if ((Native.GetAsyncKeyState(code) & 0x8000) != 0) keys.Add(code);
            return keys;
        }
        static List<int> PressedButtons() {
            var buttons = new List<int>();
            foreach (int code in new[] { 1, 2, 4, 5, 6 }) if ((Native.GetAsyncKeyState(code) & 0x8000) != 0) buttons.Add(code);
            return buttons;
        }
        void CoverOtherDisplays() {
            Rectangle[] monitors = DisplayCover.MonitorBounds();
            string current = Screen.PrimaryScreen.Bounds.ToString();
            foreach (Rectangle bounds in monitors) current += bounds.ToString();
            if (current == displayLayout) return;
            displayLayout = current;
            if (otherDisplays != null) otherDisplays.Dispose();
            Bounds = Screen.PrimaryScreen.Bounds;
            // Physical input is sampled centrally, including activity on a secondary monitor.
            otherDisplays = new DisplayCover(monitors, Bounds, false, null, null);
            otherDisplays.Show();
        }
        void Tick(object sender, EventArgs e) {
            if (Visible && options.Mode == "s") CoverOtherDisplays();
            if (options.Mode == "s" && input.Update(age.ElapsedMilliseconds, Cursor.Position, PressedKeys(), PressedButtons())) { ExitSaver(); return; }
            if (options.Mode == "p") {
                Native.Rect rect;
                if (!Native.IsWindow(options.Parent) || !Native.GetClientRect(options.Parent, out rect)) { Close(); return; }
                Size = new Size(Math.Max(1, Math.Min(8192, rect.Right)), Math.Max(1, Math.Min(8192, rect.Bottom)));
            }
            Packet packet = mailbox.Take();
            bool changed = false;
            if (packet != null) {
                State next = packet.State;
                if (next.Online) {
                    bool closing = session == next.Session && closeRevision != next.CloseRevision;
                    session = next.Session; closeRevision = next.CloseRevision;
                    bool disabledNow = state.Online && state.Enabled && !next.Enabled;
                    if (options.Mode == "s" && (disabledNow || closing)) { if (packet.Artwork != null) packet.Artwork.Dispose(); ExitSaver(); return; }
                }
                changed = state.Signature != next.Signature || packet.Artwork != null;
                if (!next.Online || !next.Enabled || !next.HasArt || revision != next.ArtRevision || packet.Artwork != null) {
                    if (artwork != null) artwork.Dispose(); artwork = packet.Artwork; packet.Artwork = null;
                }
                if (packet.Artwork != null) packet.Artwork.Dispose();
                revision = next.ArtRevision; state = next;
            }
            int shift = (int)(age.ElapsedMilliseconds / 20000 % 5) - 2;
            if (shift != drift) { drift = shift; changed = true; }
            if (changed) Invalidate();
        }
        protected override void OnPaint(PaintEventArgs e) { Painter.Draw(e.Graphics, ClientSize, state, artwork, drift); }
        protected override void OnKeyDown(KeyEventArgs e) { if (options.Mode == "s") e.SuppressKeyPress = true; base.OnKeyDown(e); }
        protected override void OnFormClosing(FormClosingEventArgs e) {
            if (options.Mode == "s" && shown && !dismissed && e.CloseReason == CloseReason.UserClosing) e.Cancel = true;
            base.OnFormClosing(e);
        }
        protected override void OnFormClosed(FormClosedEventArgs e) {
            base.OnFormClosed(e);
            if (ShouldLockOnExit(options.Mode, shown, dismissed, ConfigStore.Load())) Native.LockWorkStation();
        }
        public static bool ShouldLockOnExit(string mode, bool wasShown, bool wasDismissed, ScreenSaverConfig config) {
            return mode == "s" && wasShown && wasDismissed && config.RequirePassword;
        }
        protected override void Dispose(bool disposing) {
            if (disposing && !resourcesReleased) {
                resourcesReleased = true;
                if (otherDisplays != null) otherDisplays.Dispose();
                timer.Stop(); timer.Dispose(); if (poller != null) poller.Dispose(); mailbox.Dispose();
                if (artwork != null) artwork.Dispose(); if (cursorHidden) Cursor.Show();
            }
            base.Dispose(disposing);
        }
    }

    public static class Native {
        [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int key);
        [DllImport("user32.dll", SetLastError = true)] public static extern bool LockWorkStation();
        [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr context);
        [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
        public static void EnableDpiAwareness() {
            try { if (SetProcessDpiAwarenessContext(new IntPtr(-4))) return; } catch (EntryPointNotFoundException) { }
            try { SetProcessDPIAware(); } catch { }
        }
        [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left, Top, Right, Bottom; }
        [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr handle);
        [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr handle, out Rect rect);
        [DllImport("user32.dll")] public static extern IntPtr SetParent(IntPtr child, IntPtr parent);
        [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr handle, int index);
        [DllImport("user32.dll")] public static extern int SetWindowLong(IntPtr handle, int index, int value);
    }

    public static class Program {
        [STAThread] public static int Main(string[] args) {
            try {
                Options options = Options.Parse(args);
                Native.EnableDpiAwareness();
                Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
                if (options.Mode == "c") { Application.Run(new SettingsForm(options)); return 0; }
                try { Process.GetCurrentProcess().PriorityClass = ProcessPriorityClass.BelowNormal; } catch { }
                bool owns = false;
                using (Mutex single = new Mutex(false, "Local\\PAFPlayerVisualScreensaver-" + Process.GetCurrentProcess().SessionId + "-" + options.Port)) {
                    if (options.Mode == "s") {
                        try { owns = single.WaitOne(0); } catch (AbandonedMutexException) { owns = true; }
                        if (!owns) return 0;
                    }
                    try { Application.Run(new SaverForm(options)); }
                    finally { if (owns) single.ReleaseMutex(); }
                }
                return 0;
            } catch { return 1; } // A sidecar failure cannot terminate the player.
        }
    }
}
