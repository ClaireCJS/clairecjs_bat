"""Local OCR, glyph masks, classical repair and measured text compositing."""
from __future__ import annotations
from dataclasses import dataclass, field, replace
import csv
import io
import json
import math
import os
from pathlib import Path
import subprocess
import uuid
import re

from .errors import DependencyUnavailable, IntegrityError, RenderBlocked, ImageDeferred
from .fs import capacity, hide, sha256, identity
from .rules import transform


def libraries():
    try:
        import numpy as np
        import cv2
        from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, PngImagePlugin
        return np, cv2, Image, ImageDraw, ImageFont, ImageOps, ImageFilter, PngImagePlugin
    except ImportError as error:
        raise DependencyUnavailable("Required bundled Pillow/NumPy/OpenCV packages are unavailable. Run environment repair.") from error


@dataclass
class Word:
    text: str
    box: tuple
    confidence: float
    start: int = 0
    end: int = 0


@dataclass
class Region:
    before: str
    after: str
    box: tuple
    confidence: float
    words: list
    trace: list
    settings: dict = field(default_factory=dict)
    skipped: bool = False
    line_index: int | None = None
    ocr_span: tuple | None = None


def decode(path):
    _, _, Image, _, _, ImageOps, _, _ = libraries()
    with Image.open(path) as handle:
        handle.verify()
    with Image.open(path) as handle:
        if getattr(handle, "n_frames", 1) != 1:
            raise ImageDeferred("Animated/multiframe image deferred; no frames were discarded.")
        if handle.format not in ("PNG", "JPEG"):
            raise ImageDeferred("This format is not validated for editing; deferred without modifying it.")
        metadata = {"format": handle.format, "info": dict(handle.info), "exif": handle.getexif(), "size": handle.size}
        image = ImageOps.exif_transpose(handle).convert("RGBA")
    return image, metadata


def marker(path):
    _, _, Image, _, _, _, _, _ = libraries()
    with Image.open(path) as image:
        text = image.info.get("ICGF")
        if not text:
            description = str(image.getexif().get(270, ""))
            if "\nICGF:" in description:
                text = description.rsplit("\nICGF:", 1)[1]
        if text:
            try:
                value = json.loads(text)
                if not isinstance(value,dict) or value.get("application")!="icgf" or value.get("schema")!=1:
                    raise IntegrityError("Unrecognized reserved ICGF metadata; inspect before editing.")
                if value.get("application") == "icgf" and value.get("schema") == 1:
                    uuid.UUID(value["transaction"])
                    return value
            except (ValueError, KeyError, TypeError):
                raise IntegrityError("Malformed ICGF image marker; inspect before editing.")
    return None


def ocr(image, executable, tessdata, eco=False, full=False, psm=11):
    np, _, Image, _, _, _, _, _ = libraries()
    factor = min(1.0, (1200 if eco else 1800) / max(image.size)) if not full else 1.0
    prepared = image
    if factor < 1:
        prepared = prepared.resize((max(1, round(image.width * factor)), max(1, round(image.height * factor))), Image.Resampling.LANCZOS)
    if "A" in prepared.getbands():
        rgba=np.array(prepared.convert("RGBA"))
        if float(np.mean(rgba[:,:,3]<32))>.25:
            visible=rgba[:,:,:3][rgba[:,:,3]>32]
            luminance=float(np.median(visible)) if visible.size else 0
            background=(0,0,0,255) if luminance>160 else (255,255,255,255)
            canvas=Image.new("RGBA",prepared.size,background)
            canvas.alpha_composite(prepared.convert("RGBA"))
            prepared=canvas
    prepared=prepared.convert("RGB")
    buffer = io.BytesIO()
    prepared.save(buffer, format="PNG")
    command = [str(executable), "stdin", "stdout", "--tessdata-dir", str(tessdata), "-l", "eng", "--psm", str(psm), "-c", "tessedit_create_tsv=1"]
    result = subprocess.run(command, input=buffer.getvalue(), capture_output=True, timeout=120,
                            env=dict(os.environ, OMP_THREAD_LIMIT="1", OMP_NUM_THREADS="1"))
    if result.returncode:
        raise DependencyUnavailable("Tesseract failed: " + result.stderr.decode("utf-8", "replace")[:500])
    lines = {}
    for row in csv.DictReader(io.StringIO(result.stdout.decode("utf-8-sig")), delimiter="\t",quoting=csv.QUOTE_NONE):
        if row.get("level") != "5" or not row.get("text", "").strip():
            continue
        x, y, w, h = (round(int(row[k]) / factor) for k in ("left", "top", "width", "height"))
        key = tuple(row[k] for k in ("page_num", "block_num", "par_num", "line_num"))
        lines.setdefault(key, []).append(Word(row["text"], (x, y, x+w, y+h), float(row["conf"])))
    answer = []
    for words in lines.values():
        offset = 0
        for word in words:
            word.start, word.end = offset, offset + len(word.text)
            offset = word.end + 1
        answer.append({"text": " ".join(w.text for w in words), "words": words})
    return answer


def regions(lines, rules, ignores=()):
    answer, protected = [], [w.box for line in lines for w in line["words"]]
    for line_index,line in enumerate(lines):
        result = transform(line["text"], rules, ignores)
        groups = []
        for edit in result["edits"]:
            selected = [w for w in line["words"] if w.start < edit["end"] and edit["start"] < w.end]
            if not selected:
                continue
            a, b = selected[0].start, selected[-1].end
            if groups and a <= groups[-1][1]:
                groups[-1] = (groups[-1][0], max(b, groups[-1][1]))
            else:
                groups.append((a, b))
        for a, b in groups:
            words = [w for w in line["words"] if a <= w.start and w.end <= b]
            source = line["text"][a:b]
            replacement = source
            selected_edits=[e for e in result["edits"] if a <= e["start"] and e["end"] <= b]
            for edit in reversed(selected_edits):
                replacement=replacement[:edit["start"]-a]+edit["after"]+replacement[edit["end"]-a:]
            if source == replacement:
                continue
            box = (min(w.box[0] for w in words), min(w.box[1] for w in words),
                   max(w.box[2] for w in words), max(w.box[3] for w in words))
            trace=[t for t in result["trace"] if t["original_span"][0] < b and a < t["original_span"][1]]
            answer.append(Region(source, replacement, box, min(w.confidence for w in words), words, trace,
                                 line_index=line_index,ocr_span=(a,b)))
    return answer, protected


def full_captions(lines,regions):
    """Retain every OCR line; apply reviewed region wording at original spans."""
    detected=[];proposed=[]
    for index,line in enumerate(lines):
        before=after=line["text"]
        changes=[region for region in regions if region.line_index==index and region.ocr_span is not None]
        for region in sorted(changes,key=lambda region:region.ocr_span[0],reverse=True):
            start,end=region.ocr_span
            before=before[:start]+region.before+before[end:]
            after=after[:start]+(region.before if region.skipped else region.after)+after[end:]
        detected.append(before);proposed.append(after)
    return {"detected":"\n".join(detected) or "(No text recognized)",
            "proposed":"\n".join(proposed) or "(No text recognized)"}


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def scene_faces(image):
    """Use only the small face cascade already shipped with OpenCV, if present."""
    np,cv,_,_,_,_,_,_=libraries()
    cascade=Path(cv.__file__).parent/"data/haarcascade_frontalface_default.xml"
    if not cascade.is_file(): return []
    classifier=cv.CascadeClassifier(str(cascade))
    if classifier.empty(): return []
    scale=min(1,800/max(image.size))
    gray=cv.cvtColor(np.array(image.convert("RGB")),cv.COLOR_RGB2GRAY)
    if scale<1: gray=cv.resize(gray,(max(1,round(image.width*scale)),max(1,round(image.height*scale))))
    boxes=classifier.detectMultiScale(gray,scaleFactor=1.15,minNeighbors=5,minSize=(24,24))
    return [(round(x/scale),round(y/scale),round((x+w)/scale),round((y+h)/scale)) for x,y,w,h in boxes]


def review_crop(path,crop,kind,artifacts,callback,region_index):
    path=Path(path)
    if path.exists(): raise IntegrityError("Review artifact path is occupied; preserve it.")
    entry={"path":str(path),"hash":None,"identity":None,"kind":kind,"region":region_index}
    artifacts.append(entry)
    if callback: callback(artifacts)
    with path.open("xb") as output:
        entry["identity"]=identity(path)[:2]
        if callback: callback(artifacts)
        crop.save(output,format="PNG");output.flush();os.fsync(output.fileno())
    hide(path);entry["hash"]=sha256(path)
    if callback: callback(artifacts)
    return path


def fonts():
    base = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    names = ["arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf", "calibri.ttf", "calibrib.ttf", "calibrii.ttf", "segoeui.ttf", "seguisb.ttf", "impact.ttf", "tahoma.ttf", "consola.ttf"]
    return [base / name for name in names if (base / name).is_file()]


def styled(text, font, foreground, outline=0, outline_color=(0, 0, 0, 255), tracking=0, shadow=(0, 0), blur=0, angle=0, shadow_color=(0,0,0,180)):
    _, _, Image, Draw, _, _, Filter, _ = libraries()
    measure = Draw.Draw(Image.new("RGBA", (1, 1)))
    bbox = measure.textbbox((0, 0), text, font=font, stroke_width=outline)
    width = max(1, math.ceil(measure.textlength(text, font=font) + max(0, len(text)-1)*tracking + 2*outline))
    margin = max(3, outline + math.ceil(blur*3) + max(abs(shadow[0]), abs(shadow[1])) + 2)
    layer = Image.new("RGBA", (width+2*margin, max(1, bbox[3]-bbox[1])+2*margin), (0, 0, 0, 0))
    glyphs = Image.new("RGBA", layer.size)
    painter = Draw.Draw(glyphs)
    position = margin - bbox[0]
    if tracking:
        for char in text:
            painter.text((position, margin-bbox[1]), char, font=font, fill=foreground, stroke_width=outline, stroke_fill=outline_color)
            position += measure.textlength(char, font=font) + tracking
    else:
        painter.text((position, margin-bbox[1]), text, font=font, fill=foreground, stroke_width=outline, stroke_fill=outline_color)
    if shadow != (0, 0) or blur:
        shadow_layer = Image.new("RGBA", layer.size)
        shadow_layer.paste(shadow_color, (0, 0, *layer.size), glyphs.getchannel("A"))
        if blur:
            shadow_layer = shadow_layer.filter(Filter.GaussianBlur(blur))
        layer.alpha_composite(shadow_layer, shadow)
    layer.alpha_composite(glyphs)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    actual = layer.getbbox()
    return layer.crop(actual) if actual else Image.new("RGBA", (1, 1))


def estimate(image, region):
    np, cv, Image, _, Font, _, _, _ = libraries()
    box = region.box
    crop = np.array(image.crop(box).convert("RGB"))
    rgba=np.array(image.crop(box).convert("RGBA"))
    if crop.size == 0:
        raise RenderBlocked("Empty OCR box; correct its bounds before rendering.")
    padding=max(4,round((box[3]-box[1])*.25))
    context_rgba=np.array(image.crop((max(0,box[0]-padding),max(0,box[1]-padding),min(image.width,box[2]+padding),min(image.height,box[3]+padding))).convert("RGBA"))
    context=context_rgba[:,:,:3]
    edge = np.concatenate((context[0], context[-1], context[:, 0], context[:, -1]))
    background = np.median(edge, axis=0)
    background_alpha=int(np.median(np.concatenate((context_rgba[0,:,3],context_rgba[-1,:,3],context_rgba[:,0,3],context_rgba[:,-1,3]))))
    distance = np.linalg.norm(crop.astype(float)-background, axis=2)*(rgba[:,:,3]/255)+np.abs(rgba[:,:,3].astype(float)-background_alpha)
    selected=distance>=max(25,float(np.percentile(distance,65)))
    foreground = np.median(crop[selected],axis=0) if selected.any() else 255-background
    mask = (distance > 28).astype("uint8")*255
    best = None
    candidates=[]
    for filename in ([Path(region.settings["font"])] if region.settings.get("font") else fonts()):
          font = Font.truetype(str(filename), max(6, round((box[3]-box[1])*1.3)))
          glyph = styled(region.before, font, (255,255,255,255)).getchannel("A").resize((crop.shape[1], crop.shape[0]))
          predicted = np.array(glyph) > 80
          target = mask > 0
          score = float(np.logical_and(predicted,target).sum() / max(1,np.logical_or(predicted,target).sum()))
          candidates.append({"font":str(filename),"score":score})
          if best is None or score > best[0]:
              best = (score, filename, font)
    if best is None:
          raise RenderBlocked("No plausible installed font is available; choose a local font path or defer.")
    foreground_alpha=int(np.median(rgba[:,:,3][mask>0])) if np.any(mask>0) else 255
    return {"foreground": tuple(int(x) for x in foreground)+(foreground_alpha,), "background": tuple(int(x) for x in background),"background_alpha":background_alpha,
              "texture": float(edge.std(axis=0).mean()), "font": str(best[1]), "size": best[2].size,
              "font_score": best[0], "font_candidates":sorted(candidates,key=lambda c:-c["score"])[:3], "source_mask": mask}


def render_region(image, region, protected, *, repair_only=False):
    np, cv, Image, Draw, Font, _, _, _ = libraries()
    style = estimate(image, region)
    cfg = region.settings
    x1,y1,x2,y2 = cfg.get("box", region.box)
    sides=cfg.get("mask_sides",{})
    pad = max(4, round((y2-y1)*0.15),max(sides.values(),default=0))
    crop_box = (max(0,x1-pad), max(0,y1-pad), min(image.width,x2+pad), min(image.height,y2+pad))
    original = image.crop(crop_box)
    rgb = np.array(original.convert("RGB"))
    alpha=np.array(original.getchannel("A"))
    distance = np.linalg.norm(rgb.astype(float)-np.array(style["background"]), axis=2)*(alpha/255)+np.abs(alpha.astype(float)-style["background_alpha"])
    raw = (distance > 25).astype("uint8")*255
    restriction = np.zeros(raw.shape, dtype="uint8")
    local = (x1-crop_box[0], y1-crop_box[1], x2-crop_box[0], y2-crop_box[1])
    restriction[max(0,local[1]-sides.get("up",0)):min(raw.shape[0],local[3]+sides.get("down",0)), max(0,local[0]-sides.get("left",0)):min(raw.shape[1],local[2]+sides.get("right",0))] = 255
    if style["texture"] >= 12 or cfg.get("effects") is False:
          source_font = Font.truetype(style["font"], style["size"])
          glyph = styled(region.before, source_font, (255,255,255,255)).getchannel("A").resize((max(1,x2-x1),max(1,y2-y1)))
          restriction[:] = 0
          restriction[local[1]:local[3], local[0]:local[2]] = np.array(glyph)
          restriction = cv.dilate(restriction, np.ones((3,3),"uint8"))
    mask = cv.bitwise_and(raw, restriction)
    dilation = int(cfg.get("mask", 1))
    if dilation > 0:
          mask = cv.dilate(mask,np.ones((2*dilation+1,2*dilation+1),"uint8"))
    elif dilation < 0:
          mask = cv.erode(mask,np.ones((1-2*dilation,1-2*dilation),"uint8"))
    neighbors = [p for p in protected if p not in [w.box for w in region.words]]+list(cfg.get("protected",[]))
    for neighbor in neighbors:
          a,b,c,d = neighbor
          mask[max(0,b-crop_box[1]):max(0,min(mask.shape[0],d-crop_box[1])),
               max(0,a-crop_box[0]):max(0,min(mask.shape[1],c-crop_box[0]))] = 0
    if cfg.get('_fit_lane'):
        a,b,c,d=cfg['_fit_lane']
        mask[:max(0,b-crop_box[1]),:]=0;mask[max(0,d-crop_box[1]):,:]=0
        mask[:,:max(0,a-crop_box[0])]=0;mask[:,max(0,c-crop_box[0]):]=0
    method = cfg.get("repair", "fill" if style["texture"] < 6 else "telea")
    repaired = rgb.copy()
    repaired_alpha=np.array(original.getchannel("A"))
    if method == "fill":
          repaired[mask > 0] = style["background"]
          repaired_alpha[mask>0]=style["background_alpha"]
    elif method == "gradient":
          for row in range(rgb.shape[0]):
              gradient = np.linspace(rgb[row,0],rgb[row,-1],rgb.shape[1])
              repaired[row,mask[row]>0] = gradient[mask[row]>0]
              alpha_gradient=np.linspace(repaired_alpha[row,0],repaired_alpha[row,-1],rgb.shape[1])
              repaired_alpha[row,mask[row]>0]=alpha_gradient[mask[row]>0]
    elif method in ("telea", "navier"):
          candidate = cv.inpaint(rgb,mask,3,cv.INPAINT_TELEA if method == "telea" else cv.INPAINT_NS)
          repaired[mask>0] = candidate[mask>0]
          alpha_candidate=cv.inpaint(repaired_alpha,mask,3,cv.INPAINT_TELEA if method=="telea" else cv.INPAINT_NS)
          repaired_alpha[mask>0]=alpha_candidate[mask>0]
    elif method == "patch":
          # Search nearby, unprotected same-size patches and match the unmasked
          # context. Do not synthesize a flat rectangle over a photograph.
          candidates = []
          source_rgb = np.array(image.convert("RGB"))
          h,w = rgb.shape[:2]
          for dx,dy in [(0,-h),(0,h),(-w,0),(w,0),(-w,-h),(w,h)]:
              a,b = crop_box[0]+dx,crop_box[1]+dy
              candidate_box = (a,b,a+w,b+h)
              if a<0 or b<0 or a+w>image.width or b+h>image.height or any(overlaps(candidate_box,p) for p in protected):
                  continue
              candidate = source_rgb[b:b+h,a:a+w]
              context = mask == 0
              score = float(np.mean(np.abs(candidate[context].astype(float)-rgb[context]))) if context.any() else 1000
              candidates.append((score,candidate))
          if not candidates:
              raise RenderBlocked("No safe neighboring patch; choose another repair or defer.")
          selected = min(candidates,key=lambda item:item[0])[1]
          repaired[mask>0] = selected[mask>0]
          # Nearby alpha is reconstructed conservatively from the context.
          repaired_alpha[mask>0]=style["background_alpha"]
    else:
          raise IntegrityError("Unknown background-repair method.")
    repair_image = Image.fromarray(repaired).convert("RGBA")
    repair_image.putalpha(Image.fromarray(repaired_alpha))
    composite = image.copy()
    composite.paste(repair_image,crop_box[:2])
    if repair_only:
          # Repair availability is independent of whether the new text fits.
          if not mask.any():
              raise RenderBlocked("No reliable erasure mask; correct the OCR box or mask before choosing a repair.")
          gray=cv.cvtColor(repaired,cv.COLOR_RGB2GRAY).astype("float32")
          original_gray=cv.cvtColor(rgb,cv.COLOR_RGB2GRAY).astype("float32")
          border=(cv.dilate(mask,np.ones((3,3),"uint8"))>0)&~(cv.erode(mask,np.ones((3,3),"uint8"))>0)
          context=~(cv.dilate(mask,np.ones((5,5),"uint8"))>0)
          edges=np.abs(cv.Laplacian(gray,cv.CV_32F))
          reference=np.abs(cv.Laplacian(original_gray,cv.CV_32F))
          seam=float(np.percentile(edges[border],90)) if border.any() else 0
          expected=float(np.percentile(reference[context],90)) if context.any() else 0
          score=max(0,seam-expected)+(style["texture"]*2 if method=="fill" and style["texture"]>=6 else 0)
          preferred="fill" if style["texture"]<6 else "telea"
          score+=0 if method==preferred else .001
          return composite,{"repair":method,"repair_score":score,"background_only":True,
              "level":2 if style["texture"]<18 else 3,"seam_warning":seam,
              "style":{k:v for k,v in style.items() if k!="source_mask"},"affected":crop_box}, {
              "original":original,"repair":repair_image}
    foreground = tuple(cfg.get("foreground",style["foreground"]))
    if "opacity" in cfg: foreground=foreground[:3]+(round(255*cfg["opacity"]),)
    outline = int(cfg.get("outline",0))
    shadow = tuple(cfg.get("shadow",(0,0)))
    chosen = None
    size = max(6,round(style["size"]*float(cfg.get("scale",1))))
    mode=cfg.get('_fit_mode')
    # Exhaust rightward positions before trying leftward positions. Never move
    # across a neighboring word, even when there is free space beyond it.
    phases=('right','left') if mode=='move' else ('squeeze',) if mode=='squeeze' else ('normal',)
    candidates=(1,0.95,0.9,0.85,0.8)
    for phase in phases:
        for factor in candidates:
            font = Font.truetype(cfg.get("font",style["font"]),max(6,round(size*factor)))
            for tracking in (float(cfg.get("tracking",0)), -0.5, -1):
                layer = styled(region.after,font,foreground,outline,tuple(cfg.get("outline_color",(0,0,0,255))),tracking,
                               shadow,float(cfg.get("blur",0)),float(cfg.get("rotation",0)),tuple(cfg.get("shadow_color",(0,0,0,180))))
                base_x=x1+int(cfg.get("dx",0));y=y1+int(cfg.get("dy",0))
                scales=(1,.98,.95,.90,.85,.80) if phase=='squeeze' else (1,)
                for horizontal_scale in scales:
                    fitted=layer if horizontal_scale==1 else layer.resize((max(1,round(layer.width*horizontal_scale)),layer.height),Image.Resampling.LANCZOS)
                    lane=cfg.get('_fit_lane',(0,0,image.width,image.height))
                    left,right=lane[0],lane[2]-fitted.width
                    for a,b,c,d in neighbors:
                        if b<y+fitted.height and y<d:
                            if c<=x1:left=max(left,c)
                            if a>=x2:right=min(right,a-fitted.width)
                    if phase=='right':shifts=range(1,min(max(0,right-base_x),max(4,min(32,round((y2-y1)*.75))))+1)
                    elif phase=='left':shifts=range(-1,max(min(0,left-base_x),-max(4,min(32,round((y2-y1)*.75))))-1,-1)
                    elif phase=='squeeze':shifts=(0,) if fitted.width<=x2-x1 else ()
                    else:shifts=(0,-2,-4,-round((y2-y1)*0.25))
                    for shift in shifts:
                        x=base_x+shift
                        bounds=(x,y,x+fitted.width,y+fitted.height)
                        if x<left or x>right or y<lane[1] or bounds[3]>lane[3] or any(overlaps(bounds,p) for p in neighbors):continue
                        chosen=(fitted,(x,y),bounds,factor,tracking,horizontal_scale,phase)
                        break
                    if chosen:break
                if chosen:
                    break
            if chosen:
                break
        if chosen:break
    if not chosen:
        raise RenderBlocked("Replacement cannot fit safely within image/protected text. Adjust, choose other wording, or defer.")
    if cfg.get("label"):
        label_bounds=(min(crop_box[0],chosen[2][0]),min(crop_box[1],chosen[2][1]),max(crop_box[2],chosen[2][2]),max(crop_box[3],chosen[2][3]))
        if any(overlaps(label_bounds,p) for p in neighbors): raise RenderBlocked("Explicit caption label would cover protected text.")
        Draw.Draw(composite).rectangle(label_bounds,fill=tuple(cfg["label"]))
    composite.alpha_composite(chosen[0],chosen[1])
    overlay = original.copy()
    tint = Image.new("RGBA",original.size,(255,30,40,140))
    overlay.alpha_composite(Image.composite(tint,Image.new("RGBA",original.size),Image.fromarray(mask)))
    Draw.Draw(overlay).text((2,2),"MASK",fill="yellow")
    ring=cv.dilate(mask,np.ones((3,3),"uint8"))>0
    gray_repaired=cv.cvtColor(repaired,cv.COLOR_RGB2GRAY).astype("float32")
    gradient=np.abs(cv.Laplacian(gray_repaired,cv.CV_32F))
    seam=float(np.percentile(gradient[ring],90)) if ring.any() else 0
    context_edges=cv.Canny(rgb,80,180)>0
    background_edges=context_edges & ~(cv.dilate(mask,np.ones((7,7),"uint8"))>0)
    edge_warning=bool(background_edges.sum()>max(8,background_edges.size*.025))
    warnings=[]
    if seam>max(45,float(np.median(gradient))*4): warnings.append("Repair boundary may have a visible seam; compare repair candidates.")
    if edge_warning: warnings.append("Strong background edges near the text may belong to an important object.")
    level = 3 if style["texture"] >= 18 or cfg.get("rotation") else 2
    if style["texture"] < 6 and region.confidence >= 92 and style["font_score"] >= 0.72 and chosen[3] == 1 and not outline and shadow == (0,0):
        level = 1
    if region.confidence < 70 or not mask.any():
        level = 3
    # Never call expansion into textured/contrasting background Level 1.
    x,y,right,bottom=chosen[2]
    expansion=np.array(image.crop(chosen[2]).convert("RGB"))
    expansion_mask=np.ones(expansion.shape[:2],dtype=bool)
    expansion_mask[max(0,y1-y):max(0,min(bottom-y,y2-y)),max(0,x1-x):max(0,min(right-x,x2-x))]=False
    expansion_warning=bool(expansion_mask.any() and np.percentile(np.linalg.norm(expansion.astype(float)-np.array(style["background"]),axis=2)[expansion_mask],90)>35)
    if expansion_warning: warnings.append("Replacement expands into contrasting or textured background.")
    if expansion_warning or cfg.get("label") or edge_warning or seam>80: level=3
    if style["background_alpha"]<250 or style["foreground"][3]<250:
        level=max(2,level)
        warnings.append("Transparency changes contrast against the viewer background; inspect the intended appearance.")
    if mode:
        level=max(2,level)
        if mode=='squeeze':warnings.append('Nearby words were redrawn with horizontal compression; inspect their shape and spacing.')
        else:warnings.append('Replacement moved '+chosen[6]+' to fit; inspect its spacing and background.')
    affected = (min(crop_box[0],chosen[2][0]),min(crop_box[1],chosen[2][1]),max(crop_box[2],chosen[2][2]),max(crop_box[3],chosen[2][3]))
    return composite,{"level":level,"style":{k:v for k,v in style.items() if k!="source_mask"},
                      "repair":method,"seam_warning":seam,"fit_scale":chosen[3],"horizontal_scale":chosen[5],"fit_action":chosen[6],"affected":affected,"expansion_warning":expansion_warning,"warnings":warnings}, {
                      "original":original,"mask":overlay,"repair":repair_image,"corrected":composite.crop(affected)}


def caption_lane(image,region,lines):
    """Keep replacements in the original caption panel/column, never the photo."""
    from .ocr_quality import panels
    x1,y1,x2,y2=region.box
    candidates=[]
    for box in panels(image):
        a,b,c,d=box
        if all(a<=(w.box[0]+w.box[2])/2<=c and b<=(w.box[1]+w.box[3])/2<=d for w in region.words):
            candidates.append(box)
    if candidates:return min(candidates,key=lambda box:(box[2]-box[0])*(box[3]-box[1]))
    if region.line_index is not None and region.line_index<len(lines):
        words=lines[region.line_index]['words']
        if words:
            # Permit a small amount of room at either end of the detected line.
            # Longer wording must tighten its spacing instead of migrating out
            # into a different part of the picture.
            margin=max(4,min(16,round((y2-y1)*.4)))
            return (max(0,min(w.box[0] for w in words)-margin),0,
                    min(image.width,max(w.box[2] for w in words)+margin),image.height)
    return (0,0,image.width,image.height)


def render_fitting_region(image,region,protected,caption_lines,other_regions):
    """Safe placement fallback followed by at most two unchanged words per side.

    Context exists only in the rendering copy; substitution spans, captions,
    rule traces and the original image remain intact for review and undo.
    """
    region=replace(region,settings=dict(region.settings,_fit_lane=caption_lane(image,region,caption_lines)))
    if not region.settings.get('move_squeeze'):
        try:return render_region(image,region,protected)
        except RenderBlocked as error:
            if 'cannot fit safely' not in str(error):raise
    moved=replace(region,settings=dict(region.settings,_fit_mode='move'))
    try:return render_region(image,moved,protected)
    except RenderBlocked as error:
        if 'cannot fit safely' not in str(error):raise
        failure=error
    index=region.line_index;span=region.ocr_span
    if index is None or not span or index>=len(caption_lines):raise failure
    line=caption_lines[index];start,end=span
    if line['text'][start:end]!=region.before:raise failure
    words=line['words'];selected=[i for i,w in enumerate(words) if w.start<end and start<w.end]
    if not selected:raise failure
    occupied=[w.box for other in other_regions if not (other.line_index==region.line_index and other.ocr_span==region.ocr_span and other.box==region.box) for w in other.words]
    counts=(0,) if len(selected)==len(words) else (1,2)
    for count in counts:
        lo=max(0,min(selected)-count);hi=min(len(words),max(selected)+count+1)
        context=words[lo:hi]
        # Stop at another edited region, rather than redrawing/undoing its edit.
        if any(w.box in occupied for w in context):continue
        if count and len(context)==len(selected):continue
        a,b=context[0].start,context[-1].end
        before=line['text'][a:b]
        after=line['text'][a:start]+region.after+line['text'][end:b]
        box=(min(w.box[0] for w in context),min(w.box[1] for w in context),max(w.box[2] for w in context),max(w.box[3] for w in context))
        # A hand-adjusted box must not be silently replaced by OCR geometry.
        if region.settings.get('box'):raise failure
        candidate=replace(region,before=before,after=after,box=box,words=context,
                          settings=dict(region.settings,_fit_mode='squeeze'))
        try:
            result,diagnostic,crops=render_region(image,candidate,protected)
            diagnostic['fit_context']={'before':before,'after':after,'words_per_side':count}
            return result,diagnostic,crops
        except RenderBlocked as error:
            if 'cannot fit safely' not in str(error):raise
            failure=error
    raise failure


def save_image(image, metadata, path, transaction, original_hash, rules_hash, eco=False, on_created=None):
    _, _, Image, _, _, _, _, PNG = libraries()
    marker_data = json.dumps({"application":"icgf","schema":1,"transaction":transaction,
                              "original_sha256":original_hash,"rules_fingerprint":rules_hash},separators=(",",":"))
    exif = Image.Exif()
    exif.load(metadata["exif"].tobytes())
    exif[274] = 1
    exif[40962],exif[40963] = image.size
    if 34665 in exif:
        nested=dict(exif.get_ifd(34665))
        nested[40962],nested[40963]=image.size
        exif[34665]=nested
    options = {"icc_profile":metadata["info"].get("icc_profile"),"exif":exif.tobytes()}
    if metadata["info"].get("dpi"):
        options["dpi"]=metadata["info"]["dpi"]
    if metadata["format"] == "JPEG":
        exif[270] = str(exif.get(270,""))+"\nICGF:"+marker_data
        options.update(exif=exif.tobytes(),quality=95,subsampling=0)
        image = image.convert("RGB")
    else:
        png = PNG.PngInfo()
        for key,value in metadata["info"].items():
            if isinstance(value,str) and key != "ICGF":
                png.add_text(key,value)
        png.add_text("ICGF",marker_data)
        options.update(pnginfo=png,compress_level=3 if eco else 6)
    with Path(path).open("xb") as output:
        if on_created:
            on_created()
        image.save(output,format=metadata["format"],**options)
        output.flush()
        os.fsync(output.fileno())
    hide(path)
    with Image.open(path) as check:
        check.verify()
    with Image.open(path) as check:
        if check.size != image.size or getattr(check,"n_frames",1) != 1:
            raise IntegrityError("Staging output dimensions/frame count failed validation.")


def proposal(source, image, metadata, region_list, protected, root, ocr_executable, original_hash, rules_hash, eco=False, transaction=None, artifact_callback=None, caption_lines=None):
    _, _, Image, Draw, _, _, _, _ = libraries()
    transaction = transaction or str(uuid.uuid4())
    capacity(Path(source).parent,image.width*image.height*12)
    current = image.copy()
    diagnostics,artifacts = [],[]
    protected=list(protected)
    def plan(path,kind,region_index=None):
        entry={"path":str(path),"hash":None,"identity":None,"kind":kind}
        if region_index is not None: entry["region"]=region_index
        artifacts.append(entry)
        if artifact_callback: artifact_callback(artifacts)
        return entry
    def created(entry,path):
        entry["identity"]=identity(path)[:2]
        if artifact_callback: artifact_callback(artifacts)
    def finished(entry,path):
        entry["hash"]=sha256(path)
        if artifact_callback: artifact_callback(artifacts)
    prefix = ".icgf-"+transaction
    faces=scene_faces(image)
    for index,region in enumerate(region_list):
        if region.skipped:
            continue
        try:
            current,diagnostic,crops = render_fitting_region(current,region,protected,caption_lines or [],region_list)
        except RenderBlocked as error:
            return {"transaction":transaction,"stage":None,"artifacts":artifacts,"diagnostics":diagnostics,
                    "level":3,"verification":[],"trace":[],"blocked":{"region":index,"reason":str(error)}}
        protected.append(diagnostic["affected"])
        if any(overlaps(diagnostic["affected"],face) for face in faces):
            diagnostic["level"]=3
            diagnostic.setdefault("warnings",[]).append("A detected face overlaps this edit; preserve facial features and inspect the repair.")
        diagnostic.update(index=index,before=region.before,after=region.after)
        diagnostics.append(diagnostic)
        for kind,crop in crops.items():
            if kind=="mask":
                painter=Draw.Draw(crop);painter.rectangle((0,0,65,14),fill=(0,0,0,220));painter.text((2,1),"MASK "+str(index+1),fill="yellow")
            path = Path(source).parent/(prefix+f"-{index+1}-{kind}.png")
            if path.exists():
                raise IntegrityError("Candidate artifact already exists; preserve and use a new transaction.")
            entry=plan(path,kind,index)
            with path.open("xb") as output:
                created(entry,path)
                crop.save(output,format="PNG")
            hide(path)
            finished(entry,path)
    if not diagnostics:
        return None
    extension = ".jpg" if metadata["format"] == "JPEG" else ".png"
    stage = Path(source).parent/(prefix+"-proposal"+extension)
    entry=plan(stage,"proposal")
    save_image(current,metadata,stage,transaction,original_hash,rules_hash,eco,lambda:created(entry,stage))
    finished(entry,stage)
    verification = []
    for region,diagnostic in [(region_list[d["index"]],d) for d in diagnostics]:
        detected = ocr(current.crop(diagnostic["affected"]),ocr_executable,Path(root)/"environment/tessdata",eco,True,6)
        final_text = " ".join(line["text"] for line in detected)
        expected = region.after.casefold().split()
        passed = all(word.strip(".,!?;:") in final_text.casefold() for word in expected)
        source_absent=not bool(re.search(r"(?<!\w)"+re.escape(region.before)+r"(?!\w)",final_text,re.I))
        passed=passed and source_absent
        verification.append({"region":diagnostic["index"],"replacement_confirmed":passed,"source_absent":source_absent})
        if not passed:
            diagnostic["level"] = max(2,diagnostic["level"])
    return {"transaction":transaction,"stage":str(stage),"artifacts":artifacts,"diagnostics":diagnostics,
            "level":max(d["level"] for d in diagnostics),"verification":verification,
            "trace":[t for r in region_list if not r.skipped for t in r.trace]}
