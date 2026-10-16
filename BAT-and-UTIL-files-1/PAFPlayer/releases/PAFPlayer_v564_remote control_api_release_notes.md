# PAFPlayer V564 — authenticated remote-control API

V564 adds a narrow API for mobile remotes and homescreen pause widgets.

Added:

- `GET /api/remote/status`
- `POST /api/remote/pause`
- `POST /api/remote/resume`
- `POST /api/remote/toggle-pause`

The endpoints are intentionally open, with no secret or account setup. The
existing browser web controller and its local APIs are unchanged.

The API is intentionally transport-agnostic: use a trusted LAN/VPN or an
HTTPS reverse proxy when accessing it from another device. Because the API is
open, it should not be exposed directly to the public internet. PAFPlayer
itself does not provide TLS or authentication.
