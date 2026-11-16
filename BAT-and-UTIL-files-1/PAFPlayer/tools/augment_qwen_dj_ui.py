"""Add the Qwen3-TTS controls to the generated AI DJ page."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1] / "PAFPlayer.py"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one UI fragment, found {count}: {old[:90]}")
    return text.replace(old, new, 1)


def main() -> int:
    text = ROOT.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '<option value="piper">Local Piper only</option>',
        '<option value="piper">Local Piper only</option><option value="qwen3tts">Local Qwen3-TTS (natural voices)</option>',
    )
    text = replace_once(
        text,
        '<pre id="djPiperDetails" style="white-space:pre-wrap;overflow-wrap:anywhere">Checking installed Piper voices…</pre>',
        '<pre id="djPiperDetails" style="white-space:pre-wrap;overflow-wrap:anywhere">Checking installed Piper voices…</pre>'
        '<label>Qwen3-TTS model folder <input id="dj_qwen_tts_model_path" placeholder="T:\\models\\qwen-large-8oxzkzzr\\model"></label>'
        '<label>Qwen3-TTS Python executable <input id="dj_qwen_tts_python" placeholder="Blank = PAFPlayer Python"></label>'
        '<label>Qwen3-TTS speakers, comma-separated <input id="dj_qwen_tts_speakers" value="Ryan,Serena"></label>'
        '<label>Qwen3-TTS language <input id="dj_qwen_tts_language" value="English"></label>'
        '<label>Qwen3-TTS voice instruction <textarea id="dj_qwen_tts_instruct" rows="2">Natural, warm, conversational radio voice with clear diction and expressive prosody.</textarea></label>'
        '<pre id="djQwenDetails" style="white-space:pre-wrap;overflow-wrap:anywhere">Qwen3-TTS status appears when the local provider is selected.</pre>',
    )
    old_fields = "'speech_provider','speech_model','voices','accent','piper_executable','piper_voices','gemini_free_confirmed'"
    new_fields = "'speech_provider','speech_model','voices','accent','piper_executable','piper_voices','qwen_tts_model_path','qwen_tts_python','qwen_tts_speakers','qwen_tts_language','qwen_tts_instruct','gemini_free_confirmed'"
    if text.count(old_fields) != 2:
        raise RuntimeError("Expected the AI DJ field list twice")
    text = text.replace(old_fields, new_fields)
    text = replace_once(
        text,
        "d.piper_available?'Piper executable found':'Piper executable not detected',String(d.piper_voices_found||0)+' Piper voice model files found',d.openrouter_configured",
        "d.piper_available?'Piper executable found':'Piper executable not detected',String(d.piper_voices_found||0)+' Piper voice model files found',d.qwen_tts_ready?'Qwen3-TTS ready':d.qwen_tts_loading?'Qwen3-TTS loading':d.qwen_tts_error||'Qwen3-TTS not loaded',d.openrouter_configured",
    )
    text = replace_once(
        text,
        "$('status').textContent=[d.error,d.notice,d.sleeping?'Asleep: '+d.sleep_reason:'',d.stage,d.ready?'Commentary ready':'',",
        "const qwen=document.getElementById('djQwenDetails');if(qwen)qwen.textContent=d.qwen_tts_instructions+'\\n'+(d.qwen_tts_error||((d.qwen_tts_model_available?'Model folder found':'Model folder missing')+'; '+(d.qwen_tts_python_available?'Python runtime found':'Python runtime missing')));$('status').textContent=[d.error,d.notice,d.sleeping?'Asleep: '+d.sleep_reason:'',d.stage,d.ready?'Commentary ready':'',",
    )
    ROOT.write_text(text, encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
