from pathlib import Path
p=Path(__file__).with_name('probe_v665_sleep_ui.py');s=p.read_text(encoding='utf8')
s=s.replace("page.locator('#djSleepScheduleDetails').is_hidden()", "page.eval_on_selector('#djSleepScheduleDetails','e=>e.hidden')")
s=s.replace("page.locator('#djSleepScheduleDetails').is_visible()", "not page.eval_on_selector('#djSleepScheduleDetails','e=>e.hidden')")
s=s.replace("page.locator('#djSunriseZipDetails').is_visible()", "not page.eval_on_selector('#djSunriseZipDetails','e=>e.hidden')")
s=s.replace("page.locator('#djSunriseZipDetails').is_hidden()", "page.eval_on_selector('#djSunriseZipDetails','e=>e.hidden')")
q=p.with_name('probe_v665_sleep_ui_v2.py');assert not q.exists();q.write_text(s,encoding='utf8')
