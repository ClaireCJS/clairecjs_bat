"""V595 survey presentation, catalog, and explicit integration boundary."""
import io
from pathlib import Path
from unittest import mock

import PAFPlayer as app


class Tty:
    def isatty(self): return True


def run(questions, answers, defaults, current=None):
    output=[]
    values=iter(answers)
    current=current or {}
    with mock.patch.object(app,'_install_survey_sections',return_value=[('Sample',questions)]), \
         mock.patch.object(app,'_install_survey_defaults',return_value=defaults), \
         mock.patch.object(app,'load_player_settings',return_value=current), \
         mock.patch.object(app,'_install_survey_web_preferences',return_value={}), \
         mock.patch.object(app,'_install_survey_favorites',return_value=[]), \
         mock.patch.object(app,'_global_config_write_json',side_effect=AssertionError('write')), \
         mock.patch.object(app,'save_player_settings',side_effect=AssertionError('active write')):
        code=app.run_install_survey_dry_run(input_fn=lambda _:next(values),output_fn=output.append,stdin=Tty())
    return code,'\n'.join(output)


def test_catalog_omits_unwanted_questions_and_exposes_integrations():
    sections=app._install_survey_sections()
    keys={q['key'] for _,items in sections for q in items}
    assert not keys.intersection({'speed_index','volume','balance','visualizer_bars_enabled',
                                  'visualizer_background_artwork_enabled','tray_icon_enabled',
                                  'tray_full_info_tooltip','sixel_enabled','artwork_seam_strategy',
                                  'art_color_bar_blend_mode','art_color_bar_strength',
                                  'art_color_black_strength','console_alerts_enabled',
                                  'alert_non_default_speed','paf-web-background-config-v238.enabled'})
    assert {'lastfm','discord','monkeymote','remote_uploads','screensaver','lockscreen',
            'tray_icon_style'}.issubset(keys)
    assert any(title=='Console visualizer' and any(q['key']=='console_visualizer_volume_feedback_enabled' for q in items)
               for title,items in sections)


def test_dcc_defaults_override_registry_and_decensor_starts_on():
    with mock.patch.object(app,'effective_player_defaults',return_value={'OutputRate':48000,'DecensorConsoleKaraoke':0}), \
         mock.patch.object(app,'_global_config_read_json',return_value={'player_settings':{'OutputRate':192000}}):
        defaults=app._install_survey_defaults()
    assert defaults['OutputRate']==192000
    assert defaults['DecensorConsoleKaraoke']==1


def test_khz_answer_and_seconds_conversion():
    select={'key':'output_rate','setting':'OutputRate','kind':'select','options':[
        {'value':48000,'label':'48 kHz'},{'value':192000,'label':'192 kHz'}]}
    seconds={'key':'inter_track_timing_ms','setting':'InterTrackTimingAdjustmentMs',
             'kind':'seconds','min':-5000,'max':10000}
    assert app._install_survey_parse_answer('192',select,48000,[])==192000
    assert app._install_survey_parse_answer('-1.5',seconds,0,[])==-1500
    assert app._install_survey_parse_answer('1.5',seconds,0,[])==1500
    assert app._install_survey_describe(seconds,-1500)=='-1.5 seconds'


def test_bass_questions_are_combined_and_percent_accepts_sign():
    questions={q['key']:q for _,items in app._install_survey_sections() for q in items}
    bass=questions['bass_boost_percent']; locked=questions['locked_bass_reduction_percent']
    assert bass['enabled_setting']=='BassBoostEnabled'
    assert locked['enabled_setting']=='ReduceBassWhenLocked'
    assert app._install_survey_parse_answer('+25%',bass,0,[])==25
    assert app._install_survey_parse_answer('-30%',bass,0,[])==-30
    assert app._install_survey_parse_answer('50%',locked,0,[])==50


def test_no_favorite_is_offered_and_abort_can_skip_section():
    q={'key':'flag','setting':'Flag','kind':'toggle','label':'Flag','tooltip':'Toggle'}
    code,text=run([q],['c','a','s','d'],{'Flag':1},{'Flag':0})
    assert code==0 and 'Saved favorites' not in text
    assert 'Selected:' not in text and 'Proposed changes (0)' in text
    code,text=run([q],['c','a','w'],{'Flag':1},{'Flag':0})
    assert code==130 and 'Survey aborted' in text


def test_selection_green_and_enter_default_explained():
    q={'key':'flag','setting':'Flag','kind':'toggle','label':'Flag','tooltip':'Toggle'}
    code,text=run([q],['c','','d'],{'Flag':1},{'Flag':0})
    assert code==0 and '\x1b[1;92mSelected: On' in text


def test_integration_preview_needs_exact_override_for_real_install():
    q={'key':'screensaver','setting':'screensaver','kind':'integration',
       'label':'Screensaver','tooltip':'Art and lyrics','default':0}
    with mock.patch.object(app,'_install_survey_screensaver_status',return_value=(Path('PAFPlayer.scr'),False)), \
         mock.patch.object(app,'_install_survey_install_screensaver',return_value='Installed') as installer:
        code,text=run([q],['c','on','','','d'],{})
        assert code==0 and 'Preview:' in text
        installer.assert_not_called()
        code,text=run([q],['c','on','INSTALL SCREEN SAVER','','d'],{})
        assert code==0 and 'Installed' in text
        installer.assert_called_once()


def test_noninteractive_and_empty_input_are_safe():
    out=[]
    assert app.run_install_survey_dry_run(output_fn=out.append,stdin=io.StringIO())==2
    q={'key':'flag','setting':'Flag','kind':'toggle','label':'Flag'}
    code,text=run([q],[],{'Flag':1},{'Flag':0})
    assert code==130 and 'Survey aborted' in text
