# PAFPlayer Discord Social SDK helper

This Windows C++ helper uses the official Discord Social SDK. It is not built
or distributed with PAFPlayer because the SDK headers, import library, and DLL
must come from your application's Discord Developer Portal download.

1. Enable Social SDK for the PAFPlayer application in the Developer Portal.
   See [Discord integration](../docs/discord-integration.md) for the account
   and OAuth setup. Give Discord accurate application details.
2. Download the Windows C++ SDK and extract it. Find the directory containing
   `include/discordpp.h`, `lib/release/discord_partner_sdk.lib`, and
   `bin/release/discord_partner_sdk.dll`.
3. With Visual Studio C++ Build Tools and CMake installed, run from this folder:

   ```powershell
   cmake -S . -B build -A x64 -DDISCORD_SDK_ROOT="C:\path\to\discord_social_sdk"
   cmake --build build --config Release
   ```

   The build copies `PAFPlayerDiscordSocial.exe` and
   `discord_partner_sdk.dll` into this folder. Confirm both are present.
4. Restart PAFPlayer, choose **Automatic** or **Discord Social SDK only** in
   Web Config, save, then select **Connect Discord account**. Automatic uses
   Discord Desktop when available and this helper when Desktop is absent.
   Discord Desktop is not required for the SDK-only choice.

The helper communicates with PAFPlayer only through its private standard-input
and standard-output pipes. It performs OAuth and Rich Presence through the
official SDK and stores tokens in Windows Credential Manager. Its status lines
contain no credentials. It clears Rich Presence on normal shutdown. Keep the
SDK download and its license terms with the developer account; do not copy
SDK binaries into source releases without permission from Discord.

The first live build and OAuth/profile test require the official download.
