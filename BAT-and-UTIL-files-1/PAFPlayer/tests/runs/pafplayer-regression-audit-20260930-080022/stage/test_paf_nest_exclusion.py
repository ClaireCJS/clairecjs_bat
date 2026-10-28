import unittest
import play_audio_file as p


class NestExclusionTests(unittest.TestCase):
    def test_nest_including_nonbreaking_space_and_audio_is_excluded(self):
        payload = {'media': [{'app': 'chrome.exe', 'state': 'Playing',
                             'title': 'Live video from your Nest\u00a0Camera'}],
                   'audio': [{'name': 'chrome', 'state': 1, 'peak': .5}]}
        self.assertEqual((), p.resolve_external_media_snapshot(payload, 0)['active'])

    def test_other_chrome_media_still_interrupts(self):
        payload = {'media': [
            {'app': 'chrome.exe', 'state': 'Playing', 'title': 'Live video from your Nest Camera'},
            {'app': 'chrome.exe', 'state': 'Playing', 'title': 'Music video'},
        ]}
        result = p.resolve_external_media_snapshot(payload, 0)
        self.assertEqual(('chrome',), result['active'])
        self.assertIn('Music video', result['reasons']['chrome'][0])

    def test_unknown_title_is_not_exempted(self):
        self.assertEqual(('chrome',), p.resolve_external_media_snapshot(
            {'media': [{'app': 'chrome.exe', 'state': 'Playing'}]}, 0)['active'])
