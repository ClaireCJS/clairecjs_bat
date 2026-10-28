using System;
using System.Threading.Tasks;
using System.Threading;
using System.Diagnostics;

namespace PAFPlayerLockScreen
{
    internal static class ManagedPublisher
    {
        internal static bool Matches(PlayerStatus status, string identity)
        {
            return status.Verified && !String.IsNullOrWhiteSpace(identity) &&
                String.Equals(status.Identity, identity, StringComparison.Ordinal);
        }

        internal static async Task<bool> ValidateAsync(string server, string identity)
        {
            Uri endpoint;
            System.Net.IPAddress address;
            if (!StatusUpdater.TryServerUrl(server, out endpoint) ||
                !System.Net.IPAddress.TryParse(endpoint.Host, out address) ||
                !System.Net.IPAddress.IsLoopback(address) || String.IsNullOrWhiteSpace(identity)) return false;
            return Matches(await StatusUpdater.FetchAsync(server), identity);
        }

        internal static async Task<int> RunAsync(string server, string identity, string ownerId, string lease)
        {
            int pid;
            Guid leaseId;
            if (!Int32.TryParse(ownerId, out pid) || !Guid.TryParseExact(lease, "N", out leaseId)) return 2;
            using (var owner = Process.GetProcessById(pid))
            using (var stop = EventWaitHandle.OpenExisting("Local\\PAFPlayerManaged-" + lease))
            {
            if (owner.SessionId != Process.GetCurrentProcess().SessionId || owner.HasExited) return 2;
            // Validate the launching player's current identity before settings,
            // background registration or notification publication is changed.
            var initial = await StatusUpdater.FetchAsync(server);
            if (!Matches(initial, identity)) return 4;
            try
            {
                var settings = Settings.Load();
                if (settings.Server != server || !settings.Enabled || !settings.Managed)
                    new Settings { Server = server, Enabled = true, Managed = true }.Save();
                await BackgroundRegistration.EnsureAsync(true);
                var status = initial;
                var publication = new PublicationSession();
                while (!owner.HasExited && !stop.WaitOne(0) && !DesktopHost.StopPublisher.WaitOne(0))
                {
                    if (status.Verified && !Matches(status, identity)) return 4;
                    // A lost server clears track information. A different official
                    // session never inherits this process's publishing lease.
                    publication.Update(status);
                    await Task.Delay(status.Verified ? StatusUpdater.PollMilliseconds : 3000);
                    if (owner.HasExited || stop.WaitOne(0) || DesktopHost.StopPublisher.WaitOne(0)) break;
                    status = await StatusUpdater.FetchAsync(server);
                }
                return 0;
            }
            finally
            {
                try { BackgroundRegistration.Unregister(); } catch { }
                try { StatusUpdater.Clear(); } catch { /* 90-second expiry is the fallback. */ }
            }
            }
        }
    }
}
