# MonkeyMote Winamp evidence

Inspected the locally installed, Authenticode-valid Martin Tofall Winamp
plug-in 2.5.0.0 at `C:\Program Files (x86)\winamp\Plugins\gen_monkeymote.dll`.
Original SHA-256:
`204e5fd0852ebe21565851b067c761d02f94b6a3bfacc719bf58d06502a4a09f`.
Identical copies were found in the Winamp 5.9.2 and 5.666 installation folders.
The vendor download page lists a newer 2.5.3; this research does not claim to
have inspected that version. No published wire specification was found in the
targeted searches. AIMPRemoteControl's JSON-RPC protocol is a different product.

A separate UPX-unpacked research copy was produced without modifying the
installed DLL. It is local research material, not a runtime dependency or a
redistribution artifact. `dumpbin /disasm:nobytes` produced the retained protocol
and network disassemblies. Addresses below are virtual addresses, image base
0x10000000, in this particular unpacked 2.5.0 image.

| Evidence | Function/address | Result |
|---|---|---|
| TCP framing parser | 100477F0 | Three little-endian uint32: magic 71D9873B, message, payload length |
| Server connection greeting | 10047C80 | Message 1; 11 bytes: uint16 0302, password-present byte, 8-byte nonce |
| Authentication | 10042DB0 | Message 2: 16 digest bytes, optionally 2 capability bytes; MD5(password bytes + nonce); message 3 one-byte accepted |
| Keepalive | 10044690, dispatcher 10046EA0 | Server message 23; client 23 acknowledgement, client 46 heartbeat request |
| Commands | 10045900; delegate 1002CDC0 | Message 7, command byte + uint32 argument; 1 Play, 2 Pause, 8 Next, 9 Previous |
| Volume | 100459C1, delegate 1002CF80 | Command 6; legacy 8-bit low byte or 16-bit high word |
| Track | 100431D0, record builder 1003DE10 | Message 5, index/duration, technical fields, 16-byte hash, flags, four byte lengths, NUL-terminated UTF-8 title/artist/album/genre |
| Playback state | 100430F0; delegate 1002CC90 | Message 6, 10 bytes: position ms, state 1 playing/2 paused/3 stopped, shuffle, repeat, 8-bit and 16-bit volume |
| Basic current playlist | 10043E80 | Message 9, count then uint32 index + NUL-terminated label |
| Current playlist lookup | request table 10045890 | Message 4 request 10, playlist ID FFFFFFFF, optional detail mode |
| Named playlist, classic | 10043C80 | Message 31, count, playlist ID, indexed labels |
| Named playlist, detailed | 10043670 | Message 50, count/ID/name length/flags/name; 32-byte per-entry header and four 16-bit string lengths |
| Current index | 10043420 | Message 11, uint32 index |
| Playlist invalidation | 10044070 | Message 12 empty for the current playlist; message 35 for a named playlist |
| Artwork | request 3 at 10044CA6 | Message 8: uint32 byte count, 16-byte track hash, image bytes |
| Lyrics | request 11 at 1004536D, emitter 10045469 | Message 36: uint32 UTF-8 byte count, 16-byte track hash, NUL-terminated UTF-8 text; absent is a 20-byte zero payload |
| Lyrics reader | 10029CE0 / 10028670 / 100320D0 | Reads MP4 lyric atom / ID3 USLT and corresponding FLAC/Ogg text; confirms response 36 is lyrics |
| Arbitrary current-playlist track details | 10044C30 | Request 1 forwards its uint32 index into the metadata provider and emits message 5 |
| No artwork | request 3 at 10044CA6 | Message 13, empty payload |
| Playback settings | request 19 at 10045789; 10044AF0 | Message 51, 8 bytes |
| Extended capabilities | 10044820 | Message 28, 64-bit feature mask; adapter advertises zero extended features |
| Select then play | 1002EB90 | Command 10 selects index; command 1 starts playback |

The first real iPad probe authenticated using an 18-byte message, then requested
settings (19), sent a 16-byte artwork hash acknowledgement (message 22), requested
the detailed current playlist (request 10), artwork (3), and current index (5).
It reconnected about every 10 seconds until server heartbeat messages were added.
The second probe remained connected, acknowledged heartbeats, and the user
confirmed both playlist entries and the sample Now Playing display.

Trace files contain message numbers, sizes and interpreted numeric requests;
they omit challenge/digest bytes, passwords, full metadata and filenames. Thus
they are observed protocol traces, not full packet captures. Unit-test golden
bytes are independently constructed from the disassembly; they must not be
described as captured packets. Real iPad evidence now also covers actual V565/V566 player controls,
playlist order/selection, current artwork, and repeated-command handling.
V566 future-track Details and Lyrics were reported broken; the user confirmed
both now work with V567. Golden fixture tests are not a substitute for this device check.

Unimplemented: compression wrappers (17/45), full library/search/saved-playlist
protocol, noncurrent artwork, ratings, equalizer and discovery TXT records. Large
responses currently use the ordinary uncompressed frame. Verify large playlists
with real clients before extending the 5,000-entry first-version limit. The
installed code references `_monkeymote._tcp`, but discovery is intentionally not
implemented before end-to-end manual control has been verified.


V568 drill-down completion: actual V567 diagnostics observed message 18 (20-byte
payload) after Details/artist navigation, which had received no response.
Winamp dispatcher 1004703C calls 10045AE0: DWORD request ID, three presence bytes,
then present UTF-8 NUL-terminated filter strings. 10044110 emits opcode 19 with
DWORD request ID, DWORD count, BYTE result type, then rows. Modern empty track
list type 7 is selected at 10044403; the library provider also converts empty
album lists to empty track lists (1002F495 onward). V568 returns only that empty
result, with the original ID, and does not invent a full library index.
Fixtures are constructed from that code, not captured mobile packets; actual
empty-result rendering on the iPad remains to be checked.
