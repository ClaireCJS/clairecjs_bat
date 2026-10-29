# Multiple artwork instances and review hotkeys — 2026-10-29

Each ICGF process now registers its own artwork taskbar identity and notification
icon. Four running processes produce four independently discoverable artwork
windows, four distinct taskbar AppUserModelIDs and four tray entries. Tooltips
include the process ID and current image. Hidden windows retain their tray icons;
left-click restores that icon's artwork, and right-click offers Show this artwork,
Show all ICGF artwork, and Hide this artwork. Windows may put icons in tray overflow.

Ctrl+Alt+A in a waiting ICGF console restores that console's artwork and sends a
registered native reveal message to all other marked ICGF artwork windows on the
current desktop. The same shortcut works in artwork. Ctrl+A in the console keeps
its existing passive, own-window behavior. All participating instances must be
restarted to load the update. The new messages can only reveal artwork; they do
not approve, reject, rename or recycle images. No global hotkey or service is used.

Native shell notifications queue plain data; the normal Tk timer processes it on
the artwork thread. No Tk call, including after(), runs inside the native window
procedure. Icons are recreated after Explorer's TaskbarCreated notice and removed
when the artwork worker closes. Automatic image updates retain the activation
guard, while explicit show/restore commands request foreground activation.

Artwork keys are now A = Approve, G = Regenerate, R = Reject, I = Ignore and
N = New substitution. F2 opens a rename dialog prefilled with the source filename,
including when an unchanged caption has focus. Invalid names produce an error and
remain in review. Delete outside an editor opens a separate confirmation for the
current source image; default No retains it. Confirming uses the existing Recycle
Bin transaction path without a permanent-delete fallback. Delete and ordinary
letters inside text editors retain their editing behavior. Console keys keep
their displayed meanings. Concurrent Before/After artwork-click changes were
merged and preserved before deployment.

## Validation

- Complete installed suite: 406 passed; zero failures, errors or skips.
- Suite duration: 160.570 seconds.
- XML report: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\instances-20261029\installed-results-ea381c51195845c2af54b9ce4164f890.xml`.
- Four actual child processes were checked for distinct window handles, PIDs and
  Windows-reported AppUserModelIDs, APPWINDOW styles and real tray icon rectangles.
- Registered messages restored all four hidden windows; a native tray click restored
  only its owner, and the artwork Show all path restored its peers.
- Shell-icon recreation and cleanup were tested without restarting Explorer.
- The posted tray menu remains available for selection; Show all is callable and
  menu widgets are destroyed on their owning artwork thread during shutdown.
- A/G/R actions, prefilled F2 rename, invalid-name handling, Delete confirmation,
  declining deletion, and preserving text-editor Delete were tested.
- Existing tests exercise the real Recycle Bin using generated fixture images.
- Tests use a separate native message group to avoid revealing the user's windows.
- The shell tests require ordinary Windows shell access; sandboxed notification
  registration is restricted. The successful native and installed runs had that access.
- Deployed file hashes and replacement backups were verified with SHA-256.
- The project root still contains only the launcher and README as regular files.

Native API references: [taskbar behavior](https://learn.microsoft.com/en-us/windows/win32/shell/taskbar),
[notification icons](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shell_notifyiconw),
[registered messages](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerwindowmessagew).

## Every affected C:\BAT path

Replacement backups were verified before replacing content. The README sibling
backup was then moved to runtime/backups/implementation to keep the root minimal.
No item was permanently deleted. Deployment did not change user images or jobs.

- **Created**: `C:\BAT\image_caption_gender_fixer\docs\releases\multiple-artwork-instances-20261029.md`
- **Modified**: `C:\BAT\image_caption_gender_fixer\README.md`
- **Created; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291125.replaced-by-chatgpt.bak`**: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610291125.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291125.replaced-by-chatgpt.bak`
- **Created and subsequently modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\artwork_shell.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\artwork_shell.py.bak.202610291130.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610291125.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610291125.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_adaptive_artwork_layout.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_adaptive_artwork_layout.py.bak.202610291125.replaced-by-chatgpt.bak`
- **Created and subsequently modified**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_artwork_instances.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_artwork_instances.py.bak.202610291130.replaced-by-chatgpt.bak`
