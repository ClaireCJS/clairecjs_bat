# JSON and process contract

`--json` writes **one JSON object** to stdout. Human diagnostics use stderr.
There are no interactive prompts, ANSI sequences, progress animations, or Chafa
previews in JSON mode. Output includes state, applicable session/transaction IDs,
and per-image results where processing has begun. Selection-required errors
include available old-session summaries or the current review IDs. OCR/source
substitution text is not included in normal processing JSON.

| Code | Meaning |
| ---: | --- |
| 0 | Requested work succeeded |
| 10 | Processing completed with skipped/deferred or remaining work |
| 11 | Nothing to process or undo |
| 20 | User cancellation/input closure/interrupt |
| 21 | Explicit user selection or image review required |
| 30 | Required dependency/compatible interpreter unavailable, or installation declined |
| 40 | History/schema/integrity failure |
| 41 | Unsafe filesystem condition |
| 50 | Partial/recoverable processing failure or unexpected internal failure |
| 64 | Invalid arguments |

Per-image states include `committed`, `skipped`, `deferred`, `canceled`, and
`failed`. Only a committed output plus a durable authoritative history event
counts as successful conversion. A proposal or session entry is not a conversion.
An interrupted/error response can include already completed per-image results;
inspect session/history state before retrying a whole batch.

`--yes` never approves image review, installation/repair, session selection,
ambiguous recovery, a permanent preference change, modified-archive recycling,
or unsafe filesystem behavior. Review bypass requires one of the two explicit
confidence flags and a fully eligible level-1 proposal.

Read-only commands and dry runs create no image-folder files, session changes,
logs, cache updates, environment repairs, recovery renames, or recycling.
`explain FILE` may analyze OCR and provisional fit in memory; it never generates
previews or claims that an unsaved, unverified output has final level-1 approval.
Rule `show`/`explain` intentionally reveal the requested local rule text; normal
processing results and operation logs do not dump it.

Program, rules, markers, history, sessions, transactions, preferences, and bundle
have independent schema identifiers exposed by `--version --json`. Current data
schemas are 1; this does not require them to change together in future releases.
Stored event timestamps are timezone-aware UTC; backup names use local
`YYYYMMDDHHMM` with collision numbering before the final extension.
