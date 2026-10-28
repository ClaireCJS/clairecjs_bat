using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Windows.Data.Json;
using Windows.Data.Xml.Dom;
using Windows.Storage;
using Windows.UI.Notifications;

namespace PAFPlayerLockScreen
{
    internal static class StatusUpdater
    {
        internal const string ServerKey = "PAFPlayerServerUrl";
        internal const int PollMilliseconds = 250;
        private static readonly HttpClient Client = CreateClient();

        private static HttpClient CreateClient()
        {
            return new HttpClient(new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false,
                UseCookies = false, UseDefaultCredentials = false }) {
                Timeout = TimeSpan.FromSeconds(3), MaxResponseContentBufferSize = 2 * 1024 * 1024 };
        }

        internal static bool TryServerUrl(string input, out Uri endpoint)
        {
            endpoint = null;
            string raw = (input ?? "").Trim();
            if (raw.Length == 0) return false;
            if (!raw.Contains("://")) raw = "http://" + raw;
            Uri candidate;
            if (!Uri.TryCreate(raw, UriKind.Absolute, out candidate) ||
                candidate.Scheme != "http" || string.IsNullOrWhiteSpace(candidate.Host) ||
                candidate.UserInfo.Length != 0 || candidate.AbsolutePath != "/" ||
                candidate.Query.Length != 0 || candidate.Fragment.Length != 0 ||
                candidate.Port < 1 || candidate.Port > 65535) return false;
            endpoint = candidate;
            return true;
        }

        internal static async Task<string> RefreshAsync()
        {
            string value = ApplicationData.Current.LocalSettings.Values[ServerKey] as string ?? "http://127.0.0.1:666";
            var status = await FetchAsync(value);
            Publish(status);
            return status.Summary;
        }

        internal static async Task<PlayerStatus> FetchAsync(string value)
        {
            Uri server;
            if (!TryServerUrl(value, out server))
                return PlayerStatus.Offline("Invalid server address");
            try
            {
                using (var response = await Client.GetAsync(new Uri(server, "/api/remote-tray/hello?lockscreen=1")))
                {
                    if (response.StatusCode != System.Net.HttpStatusCode.OK)
                        throw new InvalidOperationException("Server must return HTTP 200 without a redirect.");
                    return Parse(await response.Content.ReadAsStringAsync());
                }
            }
            catch (Exception error)
            {
                return PlayerStatus.Offline("Could not verify official player: " + error.Message);
            }
        }

        internal static PlayerStatus Parse(string json)
        {
            var root = JsonObject.Parse(json);
            if (!String.Equals(Read(root, "program"), "PAFPlayer", StringComparison.OrdinalIgnoreCase) ||
                !root.GetNamedBoolean("official", false) || Read(root, "identity").Length == 0)
                throw new InvalidOperationException("Target is not the official PAFPlayer instance.");
            var state = root.GetNamedObject("state");
            if (!String.Equals(Read(state, "program"), "PAFPlayer", StringComparison.OrdinalIgnoreCase) ||
                Read(root, "version").Length == 0 || Read(root, "version") != Read(state, "version"))
                throw new InvalidOperationException("Official instance state identity does not match.");
            // updated_at_epoch dates the last state change, not this live hello
            // response. Long songs and a paused/idle player can legitimately keep
            // it unchanged. Availability comes from the successful, verified GET.
            var metadata = state.GetNamedObject("metadata", new JsonObject());
            var track = state.GetNamedObject("track", new JsonObject());
            string title = Read(metadata, "Song");
            if (title.Length == 0) title = Read(metadata, "title");
            if (title.Length == 0) title = Read(track, "filename");
            if (title.Length == 0) title = "PAFPlayer idle";
            string artist = Read(metadata, "Artist");
            if (artist.Length == 0) artist = Read(metadata, "artist");
            string album = Read(metadata, "Album");
            if (album.Length == 0) album = Read(metadata, "album");
            string year = Read(metadata, "Year");
            if (year.Length == 0) year = Read(metadata, "year");
            if (year.Length == 0) year = Read(metadata, "Date");
            if (year.Length == 0) year = Read(metadata, "date");
            if (year.Length >= 4 && Char.IsDigit(year[0]) && Char.IsDigit(year[1]) &&
                Char.IsDigit(year[2]) && Char.IsDigit(year[3])) year = year.Substring(0, 4);
            bool stopped = state.GetNamedBoolean("transport_stopped", false);
            string playback = stopped ? "Waiting" : state.GetNamedBoolean("paused", false) ? "Paused" :
                              state.GetNamedBoolean("playing", false) ? "Playing" : "Waiting";
            return new PlayerStatus { Title = Clip(title), Artist = Clip(artist), Album = Clip(album), Year = Clip(year),
                Version = Clip(Read(root, "version")).ToLowerInvariant(),
                ShowVersion = state.GetNamedBoolean("lockscreen_show_version", false),
                Counter = stopped ? "" : PlaybackCounter(state),
                Lyric = stopped ? "" : Clip(Read(state, "lyric")), Playback = playback,
                PreviousLyric = stopped ? "" : Clip(Read(state, "lyric_previous")),
                HasLyricContext = state.ContainsKey("lyric_previous"),
                Badge = playback == "Playing" ? "playing" : playback == "Paused" ? "paused" : "available",
                Identity = Read(root, "identity"), Verified = true };
        }

        private static string Read(JsonObject value, string name)
        {
            IJsonValue item;
            if (!value.TryGetValue(name, out item) || item.ValueType != JsonValueType.String) return "";
            return item.GetString().Trim();
        }

        // Display actual server playback position, never the lyric's 250 ms lead.
        // No independent clock: pause, seeks and speed changes follow the player.
        private static double? Seconds(JsonObject state, string name)
        {
            IJsonValue item;
            if (!state.TryGetValue(name, out item) || item.ValueType != JsonValueType.Number) return null;
            double value = item.GetNumber();
            // Bound malformed values before converting to an integral duration.
            if (Double.IsNaN(value) || Double.IsInfinity(value) || value < 0 || value > Int32.MaxValue) return null;
            return value;
        }

        internal static string TimeText(double? seconds)
        {
            if (!seconds.HasValue) return "--:--";
            long whole = (long)Math.Floor(seconds.Value);
            return whole >= 3600 ? String.Format(System.Globalization.CultureInfo.InvariantCulture,
                "{0}:{1:00}:{2:00}", whole / 3600, (whole / 60) % 60, whole % 60) :
                String.Format(System.Globalization.CultureInfo.InvariantCulture, "{0}:{1:00}", whole / 60, whole % 60);
        }

        private static string PlaybackCounter(JsonObject state)
        {
            double? position = Seconds(state, "position_seconds"), duration = Seconds(state, "duration_seconds");
            if (duration == 0) duration = null; // Unknown/live duration, not a zero-length song.
            if (!position.HasValue && !duration.HasValue) return "";
            if (position.HasValue && duration.HasValue) position = Math.Min(position.Value, duration.Value);
            return TimeText(position) + "/" + TimeText(duration);
        }

        internal static string HeadingLine(PlayerStatus status)
        {
            string heading = status.Artist.Length == 0 ? status.Title : status.Artist + " – " + status.Title;
            if (heading.Length == 0) heading = "PAFPlayer";
            string counter = status.Counter.Length == 0 ? "" : " · " + status.Counter;
            return Clip("🎸 " + heading, 120 - counter.Length) + counter;
        }

        internal static string LyricLine(PlayerStatus status)
        {
            return status.Lyric.Length == 0 ? "🎤 ♪" : Clip("🎤 " + status.Lyric);
        }

        internal static string AlbumLine(PlayerStatus status)
        {
            string album = status.Album.Length == 0 ? "♪" : status.Album + (status.Year.Length == 0 ? "" : " (" + status.Year + ")");
            string suffix = status.ShowVersion && status.Version.Length != 0 ? " – PAFPlayer " + status.Version : "";
            return Clip("💿 " + album, 120 - suffix.Length) + suffix;
        }

        internal static XmlDocument TileXml(PlayerStatus status)
        {
            // Keep legacy text nodes and explicitly identify the three lock-screen
            // lines on the WIDE BINDING, as Toolkit 7.1.2's TileVisual serializer does.
            var tile = TileUpdateManager.GetTemplateContent(TileTemplateType.TileWide310x150Text01);
            var lines = tile.GetElementsByTagName("text");
            lines[0].InnerText = HeadingLine(status);
            // Nonempty rows keep lyric gaps from shrinking the requested layout.
            // The native lock screen still controls actual font/layout/animation.
            lines[1].InnerText = LyricLine(status);
            lines[2].InnerText = AlbumLine(status);
            var binding = (XmlElement)tile.GetElementsByTagName("binding")[0];
            for (int i = 0; i < 3; i++)
                binding.SetAttribute("hint-lockDetailedStatus" + (i + 1), lines[i].InnerText);
            return tile;
        }

        internal static XmlDocument BadgeXml(PlayerStatus status)
        {
            var badge = BadgeUpdateManager.GetTemplateContent(BadgeTemplateType.BadgeGlyph);
            ((XmlElement)badge.GetElementsByTagName("badge")[0]).SetAttribute("value", status.Badge);
            return badge;
        }

        internal static void Publish(PlayerStatus status)
        {
            PublishChanges(status, true, true);
        }

        internal static void PublishChanges(PlayerStatus status, bool tileChanged, bool badgeChanged)
        {
            if (!tileChanged && !badgeChanged) return;
            var expiration = DateTimeOffset.Now.AddSeconds(90);
            // V517's badge-only heartbeat made LockScreenData publish a no-text
            // change (trace reason=2) until the next tile arrived. Always submit
            // the pair in one burst, with detailed text last. No Clear between updates.
            BadgeUpdateManager.CreateBadgeUpdaterForApplication().Update(
                new BadgeNotification(BadgeXml(status)) { ExpirationTime = expiration });
            var notification = new TileNotification(TileXml(status)) { ExpirationTime = expiration, Tag = "PAFStatus" };
            TileUpdateManager.CreateTileUpdaterForApplication().Update(notification);
        }

        internal static void Clear()
        {
            TileUpdateManager.CreateTileUpdaterForApplication().Clear();
            BadgeUpdateManager.CreateBadgeUpdaterForApplication().Clear();
        }

        internal static string Clip(string value, int limit = 120)
        {
            // Metadata is untrusted text. Keep XML 1.0 characters and intact pairs.
            var clean = new StringBuilder();
            value = value ?? "";
            int bound = Math.Max(0, Math.Min(120, limit));
            for (int i = 0; i < value.Length && clean.Length < bound; i++)
            {
                char c = value[i];
                if (c == '\r' || c == '\n' || c == '\t') clean.Append(' ');
                else if (Char.IsHighSurrogate(c))
                {
                    if (i + 1 < value.Length && Char.IsLowSurrogate(value[i + 1]) && clean.Length < bound - 1)
                        clean.Append(c).Append(value[++i]);
                }
                else if (!Char.IsLowSurrogate(c) && c >= 0x20 && c != 0xfffe && c != 0xffff) clean.Append(c);
            }
            return clean.ToString().Trim();
        }
    }

    // Publish changed content immediately and renew at 30 seconds. Keep the
    // badge and detailed status together: Windows consumes them as one surface.
    internal sealed class PublicationSession
    {
        private readonly Action<PlayerStatus, bool, bool> submit;
        private readonly System.Diagnostics.Stopwatch clock = System.Diagnostics.Stopwatch.StartNew();
        private string tileKey, badgeKey, identity;
        private string lastTrack, lastLyric = "", priorLyric = "";
        private double tileAt, badgeAt;
        internal PublicationSession() : this(StatusUpdater.PublishChanges) { }
        internal PublicationSession(Action<PlayerStatus, bool, bool> sink) { submit = sink; }
        internal void Reset()
        {
            tileKey = badgeKey = identity = lastTrack = null;
            lastLyric = priorLyric = "";
        }
        internal bool Update(PlayerStatus status) { return Update(status, clock.Elapsed.TotalSeconds); }
        internal bool Update(PlayerStatus status, double now)
        {
            if (!status.HasLyricContext)
            {
                // V517 compatibility: retain the last observed line. V518 sends
                // the actual preceding cue, even when a short cue fell between polls.
                string track = status.Identity + "\n" + status.Artist + "\n" + status.Title;
                if (!status.Verified || lastTrack != track) { lastLyric = priorLyric = ""; }
                if (lastLyric != status.Lyric)
                {
                    priorLyric = status.Lyric.Length == 0 ? "" : lastLyric;
                    lastLyric = status.Lyric;
                }
                lastTrack = track;
                status = status.WithPreviousLyric(priorLyric);
            }
            string key = status.Title + "\n" + status.Artist + "\n" + status.Playback + "\n" +
                         StatusUpdater.HeadingLine(status) + "\n" + StatusUpdater.LyricLine(status) + "\n" + StatusUpdater.AlbumLine(status);
            bool tile = identity != status.Identity || tileKey != key || now - tileAt >= 30;
            bool badge = identity != status.Identity || badgeKey != status.Badge || now - badgeAt >= 30;
            if (!tile && !badge) return false;
            submit(status, true, true); // Both caches commit only after successful submission.
            tileKey = key; tileAt = now;
            badgeKey = status.Badge; badgeAt = now;
            identity = status.Identity;
            return true;
        }
    }

    internal sealed class PlayerStatus
    {
        internal string Title = "", Artist = "", Lyric = "", Playback = "", Badge = "", Identity = "", Error = "";
        internal bool Verified, HasLyricContext, ShowVersion;
        internal string PreviousLyric = "", Album = "", Year = "", Counter = "", Version = "";
        internal PlayerStatus WithPreviousLyric(string lyric)
        {
            var copy = (PlayerStatus)MemberwiseClone();
            copy.PreviousLyric = lyric;
            return copy;
        }
        internal string Summary { get { return Playback + ": " + Title + (Artist.Length == 0 ? "" : " — " + Artist); } }
        internal static PlayerStatus Offline(string error)
        {
            return new PlayerStatus { Title = "PAFPlayer offline", Playback = "Offline", Badge = "unavailable", Error = error };
        }
    }
}
