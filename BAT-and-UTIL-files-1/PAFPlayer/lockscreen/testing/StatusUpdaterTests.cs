using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using Windows.Data.Json;

namespace PAFPlayerLockScreen
{
    internal static class StatusUpdaterTests
    {
        private static int passed, failed;
        private static string Fixture()
        {
            return "{\"program\":\"PAFplayer\",\"version\":\"V509\",\"official\":true,\"identity\":\"official-instance\",\"state\":{\"program\":\"PAFplayer\",\"version\":\"V509\",\"updated_at_epoch\":1700000000,\"playing\":true,\"paused\":false,\"metadata\":{\"Artist\":\"Artist & company\",\"Song\":\"Song <one>\"},\"lyric\":\"Line one\"}}";
        }
        private static PlayerStatus Parse(string json) { return StatusUpdater.Parse(json); }
        private static void Check(bool condition) { if (!condition) throw new Exception("Assertion failed"); }
        private static void Reject(string json) { try { Parse(json); } catch { return; } throw new Exception("Accepted invalid identity/state"); }
        private static void Test(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS " + name); }
            catch (Exception error) { failed++; Console.WriteLine("FAIL " + name + ": " + error); }
        }
        private static string Change(string field, IJsonValue value, bool state)
        {
            var root = JsonObject.Parse(Fixture());
            (state ? root.GetNamedObject("state") : root)[field] = value;
            return root.Stringify();
        }
        private static string TimedFixture(double position, double duration)
        {
            var root = JsonObject.Parse(Fixture()); var state = root.GetNamedObject("state");
            state["position_seconds"] = JsonValue.CreateNumberValue(position);
            state["duration_seconds"] = JsonValue.CreateNumberValue(duration);
            state.GetNamedObject("metadata")["Album"] = JsonValue.CreateStringValue("Album & <one>");
            state.GetNamedObject("metadata")["Year"] = JsonValue.CreateStringValue("1991");
            return root.Stringify();
        }
        private static async Task<PlayerStatus> FetchFixture(string response, Action<string> check)
        {
            var listener = new TcpListener(IPAddress.Loopback, 0);
            listener.Start();
            int port = ((IPEndPoint)listener.LocalEndpoint).Port;
            var serve = Task.Run(async () => {
                using (var peer = await listener.AcceptTcpClientAsync())
                using (var reader = new StreamReader(peer.GetStream()))
                {
                    string first = await reader.ReadLineAsync();
                    check(first);
                    while (!String.IsNullOrEmpty(await reader.ReadLineAsync())) { }
                    byte[] bytes = Encoding.UTF8.GetBytes(response);
                    await peer.GetStream().WriteAsync(bytes, 0, bytes.Length);
                }
            });
            try { var result = await StatusUpdater.FetchAsync("http://127.0.0.1:" + port); await serve; return result; }
            finally { listener.Stop(); }
        }
        private static string Http(string body)
        {
            return "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + Encoding.UTF8.GetByteCount(body) + "\r\nConnection: close\r\n\r\n" + body;
        }
        private static int Main()
        {
            Test("counter ends heading while lyric owns middle row and album uses third row", () => {
                var status=Parse(TimedFixture(61.9,120));
                var xml=StatusUpdater.TileXml(status); var lines=xml.GetElementsByTagName("text");
                Check(status.Counter=="1:01/2:00" && status.Album=="Album & <one>" && status.Year=="1991");
                Check(lines[0].InnerText=="🎸 Artist & company – Song <one> · 1:01/2:00" && lines[1].InnerText=="🎤 Line one" && lines[2].InnerText=="💿 Album & <one> (1991)");
                Check(xml.GetXml().Contains("Album &amp; &lt;one&gt;"));
                var binding=(Windows.Data.Xml.Dom.XmlElement)xml.GetElementsByTagName("binding")[0];
                Check(binding.GetAttribute("hint-lockDetailedStatus2")==lines[1].InnerText);
                Check(StatusUpdater.BadgeXml(status).GetXml().Contains("value=\"playing\""));
            });
            Test("lowercase album compatibility", () => Check(Parse(TimedFixture(0,120).Replace("Album\":", "album\":")).Album=="Album & <one>"));
            Test("date metadata supplies a four digit album year", () => {
                var root=JsonObject.Parse(TimedFixture(0,120));var metadata=root.GetNamedObject("state").GetNamedObject("metadata");
                metadata.Remove("Year");metadata["Date"]=JsonValue.CreateStringValue("1991-08-12");
                var status=Parse(root.Stringify());Check(status.Year=="1991" && StatusUpdater.AlbumLine(status)=="💿 Album & <one> (1991)");
            });
            Test("album alone remains visible for older status", () => {
                var status=Parse(Fixture()); status.Album="Record";
                Check(StatusUpdater.AlbumLine(status)=="💿 Record");
            });
            Test("counter alone does not invent an album", () => {
                var status=Parse(TimedFixture(61,120)); status.Album="";
                Check(StatusUpdater.HeadingLine(status)=="🎸 Artist & company – Song <one> · 1:01/2:00");
                Check(StatusUpdater.LyricLine(status)=="🎤 Line one");
            });
            Test("version is hidden by default and appended when selected", () => {
                var root=JsonObject.Parse(TimedFixture(61.9,120));
                var state=root.GetNamedObject("state");
                var hidden=Parse(root.Stringify());
                Check(hidden.Version=="v509" && !hidden.ShowVersion && StatusUpdater.AlbumLine(hidden)=="💿 Album & <one> (1991)");
                state["lockscreen_show_version"]=JsonValue.CreateBooleanValue(true);
                var shown=Parse(root.Stringify());
                Check(shown.ShowVersion && StatusUpdater.AlbumLine(shown)=="💿 Album & <one> (1991) – PAFPlayer v509");
            });
            Test("whole-second counter boundary and duplicate polls", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>{calls++;Check(t && b);});
                Check(session.Update(Parse(TimedFixture(60.01,120)),0));
                Check(!session.Update(Parse(TimedFixture(60.99,120)),.25));
                Check(session.Update(Parse(TimedFixture(61,120)),.5) && calls==2);
            });
            Test("timer does not delay a lyric within the same second", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>calls++);
                var first=Parse(TimedFixture(61.1,120)); session.Update(first,0);
                var next=Parse(TimedFixture(61.2,120)); next.Lyric="Next";
                Check(session.Update(next,.25) && calls==2);
            });
            Test("unchanged detail ignores hidden previous lyric", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>calls++);
                var status=Parse(TimedFixture(61,120)); status.HasLyricContext=true;
                status.PreviousLyric="One";session.Update(status,0);status.PreviousLyric="Two";
                Check(!session.Update(status,.25) && calls==1);
            });
            Test("changed album republishes the displayed row", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>calls++);
                var status=Parse(TimedFixture(61,120)); session.Update(status,0);status.Album="Other";
                Check(session.Update(status,.25) && calls==2);
            });
            Test("changed year republishes the displayed album row", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>calls++);
                var status=Parse(TimedFixture(61,120)); session.Update(status,0);status.Year="1992";
                Check(session.Update(status,.25) && calls==2);
            });
            Test("counter follows backwards seek immediately", () => {
                string last="";var session=new PublicationSession((s,t,b)=>last=s.Counter);
                session.Update(Parse(TimedFixture(61,120)),0);
                Check(session.Update(Parse(TimedFixture(4,120)),.25) && last=="0:04/2:00");
            });
            Test("paused counter does not extrapolate", () => {
                var root=JsonObject.Parse(TimedFixture(61.9,120));root.GetNamedObject("state")["paused"]=JsonValue.CreateBooleanValue(true);
                var status=Parse(root.Stringify());var session=new PublicationSession((s,t,b)=>Check(s.Counter=="1:01/2:00"));
                session.Update(status,0);Check(!session.Update(status,29));Check(session.Update(status,30));
                Check(status.Badge=="paused");
            });
            Test("stopped discards elapsed counter", () => {
                var root=JsonObject.Parse(TimedFixture(61,120));root.GetNamedObject("state")["transport_stopped"]=JsonValue.CreateBooleanValue(true);
                var status=Parse(root.Stringify());Check(status.Counter=="" && status.Lyric=="" && status.Album=="Album & <one>");
            });
            Test("offline has no stale album or counter", () => {
                PlayerStatus last=null;var session=new PublicationSession((s,t,b)=>last=s);
                session.Update(Parse(TimedFixture(61,120)),0);session.Update(PlayerStatus.Offline("gone"),1);
                Check(last.Album=="" && last.Counter=="" && StatusUpdater.AlbumLine(last)=="💿 ♪");
            });
            Test("hours and zero position format correctly", () => {
                Check(Parse(TimedFixture(3661,7200)).Counter=="1:01:01/2:00:00");
                Check(Parse(TimedFixture(0,120)).Counter=="0:00/2:00");
            });
            Test("position beyond duration clamps to song end", () => Check(Parse(TimedFixture(125,120)).Counter=="2:00/2:00"));
            Test("missing zero or invalid duration remains unknown", () => {
                foreach(double d in new[]{0.0,-1.0,1e30}) Check(Parse(TimedFixture(61,d)).Counter=="1:01/--:--");
                var root=JsonObject.Parse(TimedFixture(61,120));root.GetNamedObject("state").Remove("duration_seconds");
                Check(Parse(root.Stringify()).Counter=="1:01/--:--");
            });
            Test("invalid and missing position do not fabricate elapsed time", () => {
                Check(Parse(TimedFixture(-1,120)).Counter=="--:--/2:00");
                Check(Parse(TimedFixture(1e30,120)).Counter=="--:--/2:00");
                var root=JsonObject.Parse(TimedFixture(61,120));var state=root.GetNamedObject("state");
                state.Remove("position_seconds");Check(Parse(root.Stringify()).Counter=="--:--/2:00");
                state["position_seconds"]=JsonValue.CreateStringValue("61");state["duration_seconds"]=JsonValue.CreateNullValue();
                Check(Parse(root.Stringify()).Counter=="");
            });
            Test("long album cannot push counter beyond clip limit", () => {
                var status=Parse(TimedFixture(61,120));status.Album=new string('a',119)+"🎵";
                string line=StatusUpdater.AlbumLine(status);Check(line.StartsWith("💿 " + new string('a', 20)) && line.Length<=120 && !Char.IsHighSurrogate(line[line.Length-1]));
            });
            Test("long album retains the requested version suffix", () => {
                var status=Parse(TimedFixture(61,120));status.Album=new string('a',140)+"🎵";
                status.ShowVersion=true;status.Version="v611";
                string line=StatusUpdater.AlbumLine(status);
                Check(line.StartsWith("💿 ") && line.EndsWith(" – PAFPlayer v611") && line.Length<=120);
            });
            Test("long title retains the playback counter", () => {
                var status=Parse(TimedFixture(61,120));status.Title=new string('t',140)+"🎵";
                string line=StatusUpdater.HeadingLine(status);
                Check(line.StartsWith("🎸 ") && line.EndsWith(" · 1:01/2:00") && line.Length<=120);
            });
            Test("unchanged lyric does not resubmit notifications", () => {
                int calls = 0; var session = new PublicationSession((s,t,b) => { calls++; Check(t && b); });
                Check(session.Update(Parse(Fixture()), 0));
                for (int n=1; n<120; n++) Check(!session.Update(Parse(Fixture()), n*0.25));
                Check(calls == 1);
            });
            Test("next lyric submits text and badge together", () => {
                int calls = 0; bool tile = false, badge = false;
                var session = new PublicationSession((s,t,b) => { calls++; tile=t; badge=b; });
                session.Update(Parse(Fixture()), 0);
                session.Update(Parse(Change("lyric", JsonValue.CreateStringValue("Next line"), true)), 0.25);
                Check(calls == 2 && tile && badge);
            });
            Test("seek backwards republishes the earlier line", () => {
                int calls=0; string last="";
                var session=new PublicationSession((s,t,b)=>{calls++; last=s.Lyric;});
                session.Update(Parse(Fixture()),0);
                session.Update(Parse(Change("lyric",JsonValue.CreateStringValue("Later line"),true)),1);
                session.Update(Parse(Fixture()),1.25);
                Check(calls==3 && last=="Line one");
            });
            Test("instrumental gap clears the lyric", () => {
                string last="unset"; var session=new PublicationSession((s,t,b)=>last=s.Lyric);
                session.Update(Parse(Fixture()),0);
                session.Update(Parse(Change("lyric",JsonValue.CreateStringValue(""),true)),0.25);
                Check(last=="");
            });
            Test("pause changes badge and retains current line", () => {
                bool tile=false,badge=false; string lyric="";
                var session=new PublicationSession((s,t,b)=>{tile=t;badge=b;lyric=s.Lyric;});
                session.Update(Parse(Fixture()),0);
                var paused=Parse(Change("paused",JsonValue.CreateBooleanValue(true),true));
                Check(session.Update(paused,0.25) && tile && badge && lyric=="Line one");
                Check(!session.Update(paused,2));
            });
            Test("offline removes stale lyric and changes badge promptly", () => {
                bool tile=false,badge=false; PlayerStatus last=null;
                var session=new PublicationSession((s,t,b)=>{tile=t;badge=b;last=s;});
                session.Update(Parse(Fixture()),0);
                session.Update(PlayerStatus.Offline("gone"),0.25);
                Check(tile && badge && last.Lyric=="" && last.Badge=="unavailable");
            });
            Test("unchanged notifications renew before expiration", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>{calls++;Check(t && b);});
                session.Update(Parse(Fixture()),0);
                Check(session.Update(Parse(Fixture()),30) && calls==2);
            });
            Test("frequent lyric changes keep both Windows surfaces coherent", () => {
                int badges=0,tiles=0; var session=new PublicationSession((s,t,b)=>{if(t)tiles++;if(b)badges++;});
                for(int n=0;n<=120;n++) session.Update(Parse(Change("lyric",JsonValue.CreateStringValue("Line "+n),true)),n*0.25);
                Check(tiles==121 && badges==121);
            });
            Test("failed publication is retried", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>{if(++calls==1)throw new IOException("test");});
                try { session.Update(Parse(Fixture()),0); } catch(IOException) { }
                Check(session.Update(Parse(Fixture()),0.25) && calls==2);
            });
            Test("reenabling immediately republishes unchanged content", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>calls++);
                session.Update(Parse(Fixture()),0); session.Reset();
                Check(session.Update(Parse(Fixture()),0.25) && calls==2);
            });
            Test("lyric refresh moves both heartbeat deadlines together", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>{Check(t && b);calls++;});
                session.Update(Parse(Fixture()),0);
                var next=Parse(Change("lyric",JsonValue.CreateStringValue("Next line"),true));
                session.Update(next,1);
                Check(!session.Update(next,30)); // V517 sent a badge alone here and hid text.
                Check(session.Update(next,31) && calls==3);
            });
            Test("new server previous cue survives even if never polled as current", () => {
                var root=JsonObject.Parse(Fixture());
                root.GetNamedObject("state")["lyric_previous"]=JsonValue.CreateStringValue("Brief missed cue");
                var status=Parse(root.Stringify());
                var lines=StatusUpdater.TileXml(status).GetElementsByTagName("text");
                Check(status.HasLyricContext && lines[1].InnerText=="🎤 Line one" && lines[2].InnerText=="💿 ♪");
            });
            Test("old server retains previous observed lyric", () => {
                PlayerStatus last=null; var session=new PublicationSession((s,t,b)=>last=s);
                session.Update(Parse(Fixture()),0);
                session.Update(Parse(Change("lyric",JsonValue.CreateStringValue("Next line"),true)),1);
                Check(last.PreviousLyric=="Line one" && last.Lyric=="Next line");
            });
            Test("old server track change does not retain unrelated lyric", () => {
                PlayerStatus last=null; var session=new PublicationSession((s,t,b)=>last=s);
                session.Update(Parse(Fixture()),0);
                session.Update(Parse(Change("lyric",JsonValue.CreateStringValue("Next line"),true)),1);
                var next=Parse(Fixture());next.Title="Different track";session.Update(next,2);
                Check(last.PreviousLyric=="");
            });
            Test("hidden previous cue change does not republish current layout", () => {
                int calls=0; var session=new PublicationSession((s,t,b)=>calls++);
                var status=Parse(Fixture());status.HasLyricContext=true;status.PreviousLyric="One";
                session.Update(status,0);status.PreviousLyric="Two";
                Check(!session.Update(status,.25) && calls==1);
            });
            Test("blank lyric and offline payloads keep three nonempty rows", () => {
                foreach(var status in new[]{Parse(Change("lyric",JsonValue.CreateStringValue(""),true)),PlayerStatus.Offline("gone")})
                {
                    var doc=StatusUpdater.TileXml(status);
                    var binding=(Windows.Data.Xml.Dom.XmlElement)doc.GetElementsByTagName("binding")[0];
                    for(int i=1;i<=3;i++) Check(!String.IsNullOrWhiteSpace(binding.GetAttribute("hint-lockDetailedStatus"+i)));
                    Check(doc.GetElementsByTagName("text")[2].InnerText=="💿 ♪");
                }
            });
            Test("managed accepts only its launching session", () => Check(ManagedPublisher.Matches(Parse(Fixture()), "official-instance")));
            Test("managed rejects another official session", () => Check(!ManagedPublisher.Matches(Parse(Fixture()), "different-instance")));
            Test("managed rejects empty launch identity", () => Check(!ManagedPublisher.Matches(Parse(Fixture()), "")));
            Test("managed rejects unverified data", () => Check(!ManagedPublisher.Matches(PlayerStatus.Offline("offline"), "official-instance")));
            Test("official PAFplayer capitalization and canonical metadata", () => {
                var result = Parse(Fixture()); Check(result.Verified && result.Title == "Song <one>" && result.Artist == "Artist & company" && result.Identity == "official-instance");
            });
            Test("playing badge", () => Check(Parse(Fixture()).Badge == "playing"));
            Test("paused takes precedence over playing", () => Check(Parse(Change("paused", JsonValue.CreateBooleanValue(true), true)).Badge == "paused"));
            Test("stopped clears lyrics", () => { var s = Parse(Change("transport_stopped", JsonValue.CreateBooleanValue(true), true)); Check(s.Badge == "available" && s.Lyric == ""); });
            Test("waiting badge", () => Check(Parse(Change("playing", JsonValue.CreateBooleanValue(false), true)).Badge == "available"));
            Test("offline badge and no stale track", () => { var s = PlayerStatus.Offline("unreachable"); Check(s.Badge == "unavailable" && s.Lyric == "" && !s.Verified && s.Title == "PAFPlayer offline"); });
            Test("reject unofficial server", () => Reject(Change("official", JsonValue.CreateBooleanValue(false), false)));
            Test("reject string official flag", () => Reject(Change("official", JsonValue.CreateStringValue("true"), false)));
            Test("reject another program", () => Reject(Change("program", JsonValue.CreateStringValue("MusicPlayer"), false)));
            Test("reject missing instance identity", () => Reject(Change("identity", JsonValue.CreateStringValue(""), false)));
            Test("reject different state program", () => Reject(Change("program", JsonValue.CreateStringValue("Fake"), true)));
            Test("reject state version mismatch", () => Reject(Change("version", JsonValue.CreateStringValue("V508"), true)));
            Test("old state-change timestamp does not mark live official player offline", () => Check(Parse(Fixture()).Verified));
            Test("long paused state remains paused", () => Check(Parse(Change("paused", JsonValue.CreateBooleanValue(true), true)).Badge == "paused"));
            Test("server clock difference is not an identity failure", () => Check(Parse(Change("updated_at_epoch", JsonValue.CreateNumberValue(9999999999), true)).Verified));
            Test("reject malformed JSON", () => Reject("{"));
            Test("legacy metadata remains supported", () => Check(Parse(Fixture().Replace("Artist\"", "artist\"").Replace("Song\"", "title\"")).Title == "Song <one>"));
            Test("missing metadata uses idle title", () => Check(Parse(Change("metadata", new JsonObject(), true)).Title == "PAFPlayer idle"));
            Test("filename fallback", () => { var root = JsonObject.Parse(Fixture()); var s = root.GetNamedObject("state"); s["metadata"] = new JsonObject(); s["track"] = JsonObject.Parse("{\"filename\":\"file.flac\"}"); Check(Parse(root.Stringify()).Title == "file.flac"); });
            Test("tile contains actual lyric text and XML escaping", () => { var doc = StatusUpdater.TileXml(Parse(Fixture())); var lines = doc.GetElementsByTagName("text"); Check(lines[0].InnerText == "🎸 Artist & company – Song <one>" && lines[1].InnerText == "🎤 Line one" && lines[2].InnerText == "💿 ♪" && doc.GetXml().Contains("&lt;one&gt;")); });
            Test("lock-screen lines belong to wide binding and survive XML roundtrip", () => {
                var doc = new Windows.Data.Xml.Dom.XmlDocument();
                doc.LoadXml(StatusUpdater.TileXml(Parse(Fixture())).GetXml());
                var binding = (Windows.Data.Xml.Dom.XmlElement)doc.GetElementsByTagName("binding")[0];
                Check(binding.GetAttribute("template") == "TileWide310x150Text01");
                Check(binding.GetAttribute("hint-lockDetailedStatus1") == "🎸 Artist & company – Song <one>");
                Check(binding.GetAttribute("hint-lockDetailedStatus2") == "🎤 Line one");
                Check(binding.GetAttribute("hint-lockDetailedStatus3") == "💿 ♪");
                Check(((Windows.Data.Xml.Dom.XmlElement)doc.GetElementsByTagName("visual")[0]).GetAttribute("hint-lockDetailedStatus1") == "");
            });
            foreach (string glyph in new[] { "playing", "paused", "available", "unavailable" })
            { string current = glyph; Test("badge XML " + current, () => Check(StatusUpdater.BadgeXml(new PlayerStatus { Badge = current }).GetXml().Contains("value=\"" + current + "\""))); }
            Test("XML controls removed", () => Check(StatusUpdater.Clip("a\0b\u0001c\uffff\nline") == "abc line"));
            Test("valid Unicode retained", () => Check(StatusUpdater.Clip("café 🎵 中文") == "café 🎵 中文"));
            Test("unpaired surrogates removed", () => Check(StatusUpdater.Clip("a\ud800b\udc00c") == "abc"));
            Test("truncation preserves surrogate pair", () => Check(StatusUpdater.Clip(new string('a', 119) + "🎵").Length == 119));
            Test("maximum output length", () => Check(StatusUpdater.Clip(new string('a', 1000)).Length == 120));
            foreach (string input in new[] { "127.0.0.1:666", "http://localhost:666", "http://[::1]:666", "http://music-server:666/" })
            { string current = input; Test("valid server " + current, () => { Uri u; Check(StatusUpdater.TryServerUrl(current, out u)); }); }
            foreach (string input in new[] { "", "file:///tmp", "https://localhost:666", "http://user:secret@localhost", "http://localhost/path", "http://localhost?x=1", "http://localhost#fragment", "http://localhost:0", "http://localhost:65536" })
            { string current = input; Test("reject server " + current, () => { Uri u; Check(!StatusUpdater.TryServerUrl(current, out u)); }); }
            Test("read-only GET verifies official server", () => {
                var body = Fixture(); // Deliberately old state-change time from a fresh HTTP response.
                var result = FetchFixture(Http(body), line => Check(line == "GET /api/remote-tray/hello?lockscreen=1 HTTP/1.1")).GetAwaiter().GetResult(); Check(result.Verified);
            });
            Test("redirect rejected without contacting target", () => {
                var result = FetchFixture("HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1:1/commands\r\nContent-Length: 0\r\n\r\n", line => Check(line.StartsWith("GET /api/remote-tray/hello?lockscreen=1 "))).GetAwaiter().GetResult(); Check(!result.Verified && result.Error.Contains("HTTP 200"));
            });
            Test("invalid network response becomes offline", () => Check(!FetchFixture(Http("{bad-json"), line => Check(line.StartsWith("GET "))).GetAwaiter().GetResult().Verified));
            Test("connection refusal becomes offline", () => Check(StatusUpdater.FetchAsync("http://127.0.0.1:1").GetAwaiter().GetResult().Badge == "unavailable"));
            Console.WriteLine("RESULT: " + passed + " passed, " + failed + " failed");
            return failed == 0 ? 0 : 1;
        }
    }
}
