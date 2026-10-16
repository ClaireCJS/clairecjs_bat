# PAFPlayer V428 — fast Ctrl+Break shutdown

- Ctrl+Break now uses a bounded artwork-window shutdown path: no synchronous signal-handler geometry wait, and at most 0.5 seconds waiting for Tk to acknowledge close.
- Normal interactive shutdown retains the prior safer geometry persistence and 10-second Tk close window.
- The trace identified normal album-art teardown as the delay source: the latest stop spent 4.7 seconds there, with a possible worst case of about 12 seconds before other cleanup.
