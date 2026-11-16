"""V634 web confirmation and startup warning regressions."""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import unittest

import PAFPlayer as player


class SixelSafetyTests(unittest.TestCase):
    def test_startup_warning_only_when_sixel_is_active(self):
        output = io.StringIO()
        self.assertFalse(player.warn_if_sixel_enabled(False, stream=output))
        self.assertEqual("", output.getvalue())
        self.assertTrue(player.warn_if_sixel_enabled(True, stream=output))
        self.assertIn("SIXEL visualizer is enabled", output.getvalue())
        self.assertIn("--no-sixel-visualizer", output.getvalue())

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to execute web JavaScript")
    def test_sixel_web_toggle_requires_two_confirmations(self):
        html = player._paf_web_html()
        match = re.search(
            r"function confirmSixelEnable\(.*?(?=\nfunction setControlApplicability)",
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        harness = r"""
const assert = require('assert');
const vm = require('vm');
const fs = require('fs');
const code = fs.readFileSync(0, 'utf8');
function run(answers, desired) {
  const actions = [], prompts = [];
  const context = {
    action: value => actions.push(value),
    confirm: message => { prompts.push(message); return answers.shift(); },
    document: { createElement: tag => ({
      tagName: tag, dataset: {}, children: [],
      append(...children) { this.children.push(...children); }
    }) }
  };
  const makeToggle = vm.runInNewContext(code + '\nmakeToggle', context);
  const input = makeToggle({key:'sixel_enabled', label:'SIXEL visualizer', action:'toggle-sixel'}).children[0];
  input.checked = desired;
  input.onchange();
  return {checked:input.checked, actions, prompts};
}
let result = run([false], true);
assert.strictEqual(result.checked, false);
assert.strictEqual(result.prompts.length, 1);
assert.deepStrictEqual(result.actions, []);
result = run([true, false], true);
assert.strictEqual(result.checked, false);
assert.strictEqual(result.prompts.length, 2);
assert.deepStrictEqual(result.actions, []);
result = run([true, true], true);
assert.strictEqual(result.checked, true);
assert.strictEqual(result.prompts.length, 2);
assert.deepStrictEqual(result.actions, ['toggle-sixel']);
result = run([], false);
assert.strictEqual(result.checked, false);
assert.strictEqual(result.prompts.length, 0);
assert.deepStrictEqual(result.actions, ['toggle-sixel']);
"""
        result = subprocess.run(
            [shutil.which("node"), "-e", harness],
            input=match.group(), text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
