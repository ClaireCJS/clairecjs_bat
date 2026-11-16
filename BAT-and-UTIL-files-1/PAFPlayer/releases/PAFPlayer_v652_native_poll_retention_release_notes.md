# PAFPlayer V652 — native polling memory retention and cleanup stalls

Released November 11, 2026. SHA-256: `ae9aaea9f3cc9a95ce9d0e99e7597d49867a2fc702cefc865e922b44417422db`.

The remaining tiny visualizer hangs were investigated beyond rendering itself.
Two roughly 270–290 ms diagnostic delays in a V650 live trace coincided with
generation-2 garbage collection. Those are HTTP sampling delays, not measured
frame durations. The same live process subsequently reported about 6.25 GB of
private memory after 5.4 hours, compared with about 1.42 GB early in the session.
These observations motivated isolated allocation checks, not a claim that all
growth or every hitch had one cause.

## Root cause and fix

Repeated external-audio polling recreated GUID/PROPERTYKEY classes and native
function signatures. Python ctypes retains pointer and callback signature types
in process-wide caches, so these definitions and their object graphs survived
ordinary garbage collection. Steam process enumeration and diagnostic memory
polling had the same structure-type retention problem. Casting owning COM
pointer wrappers also created disposable self-reference cycles on each call.

V652 reuses those native definitions and private DLL bindings. COM apartments,
interfaces, handles, process records, and memory values still belong to each
individual poll and are acquired/read/released as before. It casts the numeric
COM address while retaining the owning argument during the call. Steam reuses
one path buffer per enumeration. Cursor visibility and idle-input polling reuse
their small structure definitions instead of creating collectible class graphs.

No garbage collector policy, audio processing, frame target, rendering precision,
terminal encoding, configuration ID, or polling cadence changed. The playback
owner and artwork-popup implementations are AST-identical to the V651 snapshot.
The native monitor continues to read external playback; it sends no playback or
volume commands. V651's idle-art controls and session-error display are preserved.

## Measurements and validation

The benchmark used the then-current V651 source, then the fixed candidate and
current V653 source after another chat advanced the working file. The changed
native functions are retained in that newer source.

| Isolated workload | V651 | V652 |
| --- | ---: | ---: |
| New retained pointer/function types, 20 audio polls | 340 | 0 |
| Cyclic garbage, 20 audio polls | 4,877 objects | 17 objects |
| New retained pointer types, 100 diagnostics | 100 | 0 |
| New retained pointer types, 20 Steam polls | 20 | 0 |
| Cyclic garbage, 100 cursor visibility calls | 1,100 objects | 0 |

The accelerated soak performed 500 real read-only audio polls, 100 diagnostic
reads and 20 Steam enumerations in isolated processes with normal automatic GC.
Both versions returned 500 known audio samples. After cleanup, V651 retained
129,197 additional tracked objects and 14,049,280 additional private bytes.
V652 retained two additional tracked objects; private bytes decreased by 503,808.
This verifies the targeted retention fix, not a full-player multi-hour soak or
a guaranteed FPS improvement. Warm artwork-render cost remained about 1.8 ms
in the synthetic fixture; rendering itself was not modified in this release.

- [V651 allocation probe](../tests/reports/pipeline-gc-V651-20261111-062028.json)
- [Fixed candidate allocation probe](../tests/reports/pipeline-gc-V651-20261111-062303.json)
- [Current V653 allocation probe](../tests/reports/pipeline-gc-V653-20261111-063118.json)
- [V651 soak](../tests/reports/native-soak-V651-20261111-062528.json)
- [V652 soak](../tests/reports/native-soak-V652-20261111-062525.json)
- [Original live sampling](../tests/reports/v648-thread-stacks-20261111-005959.json)

All nine new regression tests pass. The 107-test native/Steam/media/retention
selection has 105 passes and the same two old media-coordinator failures as the
98-test V651 baseline. The 188-test render/karaoke/transport selection has 176
passes, 11 old failures and one old source-contract error, matching V651 exactly.
Python compilation, 27 bundled-source comparisons and eight generated JavaScript
syntax checks pass. This is not an all-green full-suite claim.

The previous combined GUI harness aborted on both versions with Tk's wrong-thread
cleanup diagnostic. The new test runner collects destroyed Tk fixture cycles on
their main owner thread before starting the next test. That test-only cleanup
allowed both 188-test comparisons to finish; production GC behavior is unchanged.
An initial missing Steam source fixture in the new runner was corrected; the
original failed reports remain retained.

- [V652 focused/relevant checks](../tests/reports/native-checks-V652-20261111-062531.json)
- [V651 matching baseline](../tests/reports/native-checks-V651-20261111-062824.json)
- [V652 broad selection](../tests/reports/pipeline-regressions-V652-20261111-063118.json)
- [V651 broad baseline](../tests/reports/pipeline-regressions-V651-20261111-062821.json)

## Restart and live verification

Restart the player to load the fixes and release the old process's retained
types. The active PAFPlayer.py has advanced independently to V653 and contains
these changes; this immutable V652 copy preserves the exact tested performance
change. Keep console karaoke, artwork popup and floating lyrics running. Check
lyric-gap resizes and normal playback for remaining hitches; observe memory
over several hours using occasional `/api/runtime-diagnostics` reads.
`tests/probe_v648_thread_stacks.py` can collect a bounded local stack/GC trace.
Do not infer frame latency from HTTP request latency alone.

Live visual smoothness and multi-hour whole-player memory stability after restart
remain unverified. The formerly running V650 process was not stopped or altered.
Other non-hot dynamic native types remain outside this focused change; this does
not claim every possible allocation or leak in the application is removed.

## Files and safety

Replaced files received verified sibling backups, archived in their designated
folders. Prior release artifacts were preserved. No files were permanently
deleted. Root audit results and every operation-owned artifact are recorded in
[the affected-path manifest](../tests/reports/v652-change-manifest.json).
`play_audio_file.py` was not changed. No literal C:\BAT paths changed.
