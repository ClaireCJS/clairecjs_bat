# PAFPlayer V708 — Responsive AI DJ configuration

Released November 13, 2026.

The AI DJ configuration is reorganized into three readable cards:

- **Schedule & cadence**
- **Conversation model**
- **Voices & speech**

The conversation-prompt editor now has an explicit one-column layout. The
preset selector, explanatory text, full-width prompt editor, and named-preset
save row no longer inherit the generic horizontal `.control-item` flex layout.

The card grid uses three columns on wide screens, two below 1100 px, and one
below 720 px. Inputs use zero-safe grid minimums and bounded widths; the AI DJ
section clips accidental outer overflow as a final guard.

Verification parses the generated HTML and uses installed Chrome in headless
mode to measure the DJ settings, prompt panel, and textarea at 1440, 720, and
420 px. None reports horizontal overflow.
