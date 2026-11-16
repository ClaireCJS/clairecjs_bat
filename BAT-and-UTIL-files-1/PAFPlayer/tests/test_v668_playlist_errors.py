import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v668_error_delivery',root/'src/PAFPlayer_error_delivery.py')
delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
spec=importlib.util.spec_from_file_location('v668_player',root/'PAFPlayer.py')
player=importlib.util.module_from_spec(spec);sys.modules[spec.name]=player;spec.loader.exec_module(player)

class Tests(unittest.TestCase):
    def test_consecutive_missing_entries_are_recorded_without_alerts(self):
        folder=Path(tempfile.mkdtemp(prefix='paf-missing-test-'));first=folder/'missing-one.mp3';second=folder/'missing-two.mp3';good=folder/'song.mp3';good.write_bytes(b'music')
        missing=[];alerts=delivery.ErrorAlerts()
        with mock.patch.object(delivery.threading,'Thread') as thread, mock.patch.object(delivery,'_popup') as popup, mock.patch.object(delivery,'_sound') as sound:
            successor=delivery.next_playable_entry([first,second,good],first,on_missing=missing.append)
            delivery.record_missing_playlist_entries(alerts,[first]+missing,successor is not None)
        self.assertEqual(good,successor);self.assertEqual([second],missing)
        self.assertEqual([str(second),str(first)],[row['path'] for row in alerts.snapshot()])
        self.assertTrue(all(row['continuing'] for row in alerts.snapshot()))
        thread.assert_not_called();popup.assert_not_called();sound.assert_not_called()

    def test_no_playable_successor_reports_final_outcome_and_deduplicates(self):
        folder=Path(tempfile.mkdtemp(prefix='paf-all-missing-'));first=folder/'one.mp3';second=folder/'two.mp3';found=[];alerts=delivery.ErrorAlerts()
        successor=delivery.next_playable_entry([first,second],first,on_missing=found.append)
        delivery.record_missing_playlist_entries(alerts,[first]+found,False)
        delivery.record_missing_playlist_entries(alerts,[first]+found,False)
        self.assertIsNone(successor);self.assertEqual(2,len(alerts.snapshot()))
        self.assertTrue(all(not row['continuing'] for row in alerts.snapshot()))

    def test_missing_branch_excludes_console_and_alert_delivery(self):
        source=(root/'PAFPlayer.py').read_text(encoding='utf8')
        body=source[source.index('            problem = file_problem(current_audio)'):source.index('            # V309: no distinct-file launch guard.')]
        self.assertIn('record_missing_playlist_entries(',body)
        self.assertIn("if problem != 'missing' or playlist_path is None:",body)
        self.assertLess(body.index("if problem != 'missing' or playlist_path is None:"),body.index('web_server.publish_notice('))

if __name__=='__main__':unittest.main()
