# PAFPlayer V572 — Last.fm web configuration tab

The web configuration now shows **Last.fm** as its own tab beside **Metadata / Maintenance**. It holds **View my Last.fm profile** and **Force Last.fm scrobble**, so these actions no longer appear with playlist and metadata maintenance.

The profile button continues to use the existing saved username and profile API. If no username has been saved, the player computer can enter one. Remote browsers may view the profile but cannot change the username. Scrobbling still needs credentials configured on the player computer and still follows the existing playback eligibility and action queue.

Verification: focused V572 tab and action-group tests, existing web-configuration and Last.fm tests, and Python compilation. No Last.fm protocol, credential storage, or playback timing change is intended.
