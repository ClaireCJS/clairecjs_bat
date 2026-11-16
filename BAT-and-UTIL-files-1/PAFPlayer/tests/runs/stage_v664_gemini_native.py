from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=(root/'src/PAFPlayer_dj.py').read_text(encoding='utf8')
anchor='def dialogue(history, opts):\n'
helper='''def _gemini_dialogue(key, prompt, data, speakers):
    """Use the native Gemini API, including support for AQ authorization keys."""
    url='https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent'
    body={'systemInstruction':{'parts':[{'text':prompt}]},
          'contents':[{'role':'user','parts':[{'text':data}]}],
          'generationConfig':{'responseMimeType':'application/json'}}
    value=post_json(url,body,{'x-goog-api-key':key},timeout=60)
    candidates=value.get('candidates',[])
    if not candidates:raise ValueError('Gemini returned no candidate')
    parts=candidates[0].get('content',{}).get('parts',[])
    text=''.join(part.get('text','') for part in parts if not part.get('thought'))
    return parse_dialogue(text,speakers)


'''
assert src.count(anchor)==1;src=src.replace(anchor,helper+anchor,1)
old="candidates.append(('gemini','GEMINI_API_KEY','https://generativelanguage.googleapis.com/v1beta/openai/chat/completions','gemini-2.5-flash-lite'))"
new="candidates.append(('gemini','GEMINI_API_KEY','','gemini-3.5-flash-lite'))"
assert src.count(old)==1;src=src.replace(old,new,1)
old="            result=_chat_dialogue(url,key,model,prompt,data,opts['speakers'])"
new="            result=(_gemini_dialogue(key,prompt,data,opts['speakers']) if provider=='gemini' else _chat_dialogue(url,key,model,prompt,data,opts['speakers']))"
assert src.count(old)==1;src=src.replace(old,new,1)
compile(src,'candidate','exec');p=root/'tests/runs/PAFPlayer_dj_v664_candidate.py';assert not p.exists();p.write_text(src,encoding='utf8');print(p)
