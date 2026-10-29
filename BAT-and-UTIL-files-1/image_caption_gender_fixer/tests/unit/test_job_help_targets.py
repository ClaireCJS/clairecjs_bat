import pytest
from test_old_sessions import old_jobs
from image_caption_gender_fixer.errors import SelectionRequired

@pytest.mark.parametrize('sequence',[['h','c'],['help','c'],['r','h','b','c'],['?','c']])
def test_bare_job_menu_exposes_help_and_leaves_jobs_untouched(tmp_path,capsys,sequence):
    app,source,first,second=old_jobs(tmp_path,answers=iter(sequence))
    prompts=[];original=app.ask_callback
    app.ask_callback=lambda message:(prompts.append(message),original(message))[1]
    before={s['id']:(app.sessions.directory/(s['id']+'.json')).read_bytes() for s in (first,second)}
    with pytest.raises(SelectionRequired):app.select_session([source])
    assert '[h]elp' in prompts[0]
    output=capsys.readouterr().err
    assert 'Explicit targets such as icgf .' in output and 'no session ID is needed' in output
    assert all((app.sessions.directory/(key+'.json')).read_bytes()==value for key,value in before.items())

def test_explicit_resume_overrides_direct_target_new_job_behavior(tmp_path):
    app,source,first,second=old_jobs(tmp_path,json_mode=True)
    app.args.resume=first['id']
    assert app.select_session([source],explicit_targets=True)['id']==first['id']
    assert len(app.sessions.list())==2
