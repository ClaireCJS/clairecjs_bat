"""Deterministic, offline song review: timed lyrics, artwork and audio spectrum."""
from PAFPlayer_workflows import *


def render_song(runtime,audio, *, output=None, open_browser=True, prompt=True, prefix=None):
    from PIL import Image,ImageDraw,ImageFont,ImageOps
    import webbrowser
    app=runtime.app; audio=Path(audio).resolve()
    if not supported_file(audio,app.AUDIO_EXTENSIONS): raise ValueError('Choose an existing supported audio file')
    lyrics=app.load_lyrics(audio)
    if not lyrics: raise ValueError('No timed lyric lines found for this track')
    if not app._lyrics_are_timed(lyrics): raise ValueError('The render book requires timestamped lyrics')
    destination=unique(Path(output).resolve() if output else runtime.root/'render-reviews'/audio.stem)
    destination.mkdir(parents=True,exist_ok=False)
    fontfile=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts'/'arial.ttf'
    font=ImageFont.truetype(str(fontfile),32) if fontfile.exists() else ImageFont.load_default()
    small=ImageFont.truetype(str(fontfile),18) if fontfile.exists() else font
    cover=None
    # Read existing sidecars/embedded art only; do not materialize covers or write tags.
    for stem in (audio.stem,'cover','folder','front'):
        for ext in ('.jpg','.png','.jpeg','.webp'):
            candidate=audio.with_name(stem+ext)
            if candidate.is_file():
                with contextlib.suppress(Exception): cover=Image.open(candidate).convert('RGB')
                if cover is not None: break
        if cover is not None: break
    if cover is None:
        blob=app._extract_tagged_embedded_cover_art(audio)
        if blob:
            with contextlib.suppress(Exception): cover=Image.open(io.BytesIO(blob)).convert('RGB')
    duration=app.probe_duration_seconds(audio)
    timeline=app.build_audio_spectrum_timeline(audio,64,duration_limit=duration)
    cards=[]; images=[]
    for index,(start,end,text) in enumerate(lyrics,1):
        if not str(text).strip(): continue
        stamp=max(0.,float(start))
        image=Image.new('RGB',(1200,800),'#07121e'); draw=ImageDraw.Draw(image)
        if cover is not None:
            art=ImageOps.contain(cover,(700,520)); image.paste(art,((1200-art.width)//2,35))
        levels=app.spectrum_frame_at(timeline,stamp)
        for x,level in enumerate(levels):
            height=round(min(app.SPECTRUM_ANALYSIS_HEIGHT,level)/max(1,app.SPECTRUM_ANALYSIS_HEIGHT)*130)
            draw.rectangle((24+x*18,590-height,36+x*18,590),fill=app.rainbow_rgb(x/max(1,len(levels))))
        words=str(text).split(); lines=[]; line=''
        for word in words:
            trial=(line+' '+word).strip()
            if draw.textlength(trial,font=font)>1140 and line: lines.append(line); line=word
            else: line=trial
        if line: lines.append(line)
        # Grow downward for long lyrics rather than truncate them.
        needed=max(800,650+len(lines)*42+45)
        if needed!=800:
            expanded=Image.new('RGB',(1200,needed),'#07121e'); expanded.paste(image,(0,0)); image=expanded; draw=ImageDraw.Draw(image)
        for row,line in enumerate(lines): draw.text((600,625+row*42),line,font=font,fill='white',anchor='mt')
        context=f'{audio.name} | line {index} | {stamp:.3f}s'+(f'–{float(end):.3f}s' if end is not None else '')
        draw.text((24,image.height-32),context,font=small,fill='#8ec5e8')
        path=destination/f'line-{index:04d}.png'; image.save(path,format='PNG'); images.append(path)
        buffer=io.BytesIO(); image.save(buffer,format='PNG')
        cards.append('<figure><img alt="'+html.escape(context,quote=True)+'" src="data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()+'"><figcaption>'+html.escape(context)+'</figcaption></figure>')
    book='<!doctype html><meta charset="utf-8"><title>'+html.escape(audio.stem)+' — PAFPlayer render book</title><style>body{background:#101722;color:#eef;font:16px system-ui;max-width:1200px;margin:auto}figure{margin:2rem 0;break-inside:avoid}img{width:100%;height:auto}figcaption{padding:.5rem}@media print{figure{page-break-after:always}}</style><h1>'+html.escape(audio.stem)+'</h1><p>Offline review at each lyric start; deterministic artwork and audio-spectrum frames. No live playback state is changed.</p>'+''.join(cards)
    bookpath=destination/'index.html'; bookpath.write_text(book,encoding='utf-8')
    if open_browser: webbrowser.open(bookpath.as_uri())
    keep=True
    if prompt:
        keep=input(f'Save {len(images)} rendered images and review book? [y/N] ').strip().casefold() in ('y','yes')
        if keep: prefix=input('Numbered image filename prefix [lyric]: ').strip() or 'lyric'
    if keep:
        prefix=prefix or 'lyric'
        if not re.fullmatch(r'[\w .()-]{1,80}',prefix): raise ValueError(f'Unsafe prefix; original review files retained in {destination}')
        for index,path in enumerate(images,1):
            target=unique(destination/f'{prefix}-{index:04d}.png')
            if target!=path: path.rename(target)
        runtime.log('render-book.saved',track=audio,output=destination,lines=len(images))
        return {'directory':str(destination),'book':str(bookpath),'images':len(images),'saved':True}
    recycle(destination)
    runtime.log('render-book.declined',lines=len(images),cleanup='recycled')
    return {'saved':False,'images':len(images),'cleanup':'recycled'}
