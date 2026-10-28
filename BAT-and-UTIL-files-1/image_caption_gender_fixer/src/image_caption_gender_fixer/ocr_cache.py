"""Folder-local, hidden, append-only OCR results; never processing history."""
import hashlib
import json
import math
import os
from pathlib import Path

from .errors import IntegrityError
from .fs import canonical, folder_lock, hide, identity, now, reparse, sha256

HEADER={"application":"icgf","schema":1,"kind":"ocr-cache"}
ALGORITHM=2


def signature(root,executable,eco):
    """Invalidate when OCR code policy, engine, model or quality changes."""
    return {"algorithm":ALGORITHM,"engine":sha256(executable),
            "english":sha256(Path(root)/"environment/tessdata/eng.traineddata"),
            "eco":bool(eco),"quality_policy":"panel-gray-upscale-v2","psm":11,"full_retry_below_confidence":80}


def key_for(digest,settings,size):
    return hashlib.sha256(canonical({"image":digest,"settings":settings,"size":list(size)}).encode('utf-8')).hexdigest()


def unpack_lines(value,size):
    """Validate cached text, spans and geometry before reconstructing Words."""
    from .imaging import Word
    if not isinstance(value,list): raise ValueError('OCR lines are not a list')
    result=[]
    for line in value:
        if not isinstance(line,dict) or not isinstance(line.get('text'),str) or not isinstance(line.get('words'),list):
            raise ValueError('Invalid OCR line')
        words=[];offset=0
        for item in line['words']:
            text=item['text'];box=item['box'];confidence=item['confidence']
            if not isinstance(text,str) or not text or not isinstance(box,(list,tuple)) or len(box)!=4:
                raise ValueError('Invalid OCR word')
            if not all(type(n) is int for n in box) or not (0<=box[0]<box[2]<=size[0]+2 and 0<=box[1]<box[3]<=size[1]+2):
                raise ValueError('OCR geometry outside image')
            if type(confidence) not in (int,float) or not math.isfinite(confidence) or not -1<=confidence<=100:
                raise ValueError('Invalid OCR confidence')
            if item['start']!=offset or item['end']!=offset+len(text) or line['text'][item['start']:item['end']]!=text:
                raise ValueError('Invalid OCR text span')
            words.append(Word(text,tuple(box),float(confidence),item['start'],item['end']))
            offset=item['end']+1
        if line['text']!=' '.join(word.text for word in words): raise ValueError('OCR words disagree with caption')
        result.append({'text':line['text'],'words':words})
    return result


def pack_lines(lines,size):
    from dataclasses import asdict
    value=[{'text':line['text'],'words':[asdict(word) for word in line['words']]} for line in lines]
    unpack_lines(value,size)
    return value


class OCRCache:
    filename='.ocr'

    def __init__(self,folder):
        self.path=Path(folder)/self.filename
        self.entries={};self.warning=None;self._identity=None;self.blocked=False;self.incomplete=False

    def refresh(self,force=False):
        # Never follow a linked cache or overwrite an unrelated .ocr file.
        if not os.path.lexists(self.path):
            self.entries={};self.warning=None;self._identity=None;self.blocked=False;self.incomplete=False;return
        if reparse(self.path): raise IntegrityError('The .ocr cache is a reparse point; refused.')
        current=identity(self.path)
        if not force and current==self._identity: return
        self._identity=current;self.entries={};self.warning=None;self.blocked=False;self.incomplete=False
        try:
            with self.path.open('rb') as stream:
                if stream.readline()!=(canonical(HEADER)+'\n').encode('utf-8'):
                    raise ValueError('unrecognized .ocr header')
                for raw in stream:
                    try:
                        if not raw.endswith(b'\n'):
                            self.incomplete=True;raise ValueError('incomplete final OCR record')
                        record=json.loads(raw.decode('utf-8'))
                        if not isinstance(record,dict): raise ValueError('OCR record is not an object')
                        checksum=record.pop('checksum')
                        if hashlib.sha256(canonical(record).encode('utf-8')).hexdigest()!=checksum:
                            raise ValueError('OCR record checksum mismatch')
                        key=key_for(record['image_hash'],record['settings'],record['size'])
                        if record['key']!=key: raise ValueError('OCR record key mismatch')
                        unpack_lines(record['lines'],record['size'])
                        self.entries[key]=record
                    except (ValueError,TypeError,KeyError,IndexError,UnicodeDecodeError) as error:
                        self.warning='Invalid/incomplete saved OCR record ignored; existing bytes retained: '+str(error)
        except (ValueError,TypeError,KeyError,UnicodeDecodeError) as error:
            self.warning='Saved OCR is damaged/unrecognized; .ocr retained: '+str(error)
            self.entries={};self.blocked=True

    def get(self,digest,settings,size):
        self.refresh()
        record=self.entries.get(key_for(digest,settings,size))
        if record is None: return None
        try: return unpack_lines(record['lines'],size)
        except (ValueError,TypeError,KeyError,IndexError) as error:
            self.warning='Saved OCR entry is invalid; .ocr retained: '+str(error)
            return None

    def put(self,source,digest,settings,size,lines):
        packed=pack_lines(lines,size)
        key=key_for(digest,settings,size)
        with folder_lock(self.path.parent):
            # Recheck identity under the lock; parse again only if another
            # writer changed the file, rather than once per image in a batch.
            self.refresh()
            if self.blocked: raise IntegrityError(self.warning)
            if key in self.entries:
                unpack_lines(self.entries[key]['lines'],size)
                hide(self.path);return
            record={'key':key,'image_hash':digest,'settings':settings,'size':list(size),
                    'filename':Path(source).name,'created':now(),'lines':packed}
            record['checksum']=hashlib.sha256(canonical(record).encode('utf-8')).hexdigest()
            # Append rather than replace: old entries and interrupted evidence
            # are preserved, with no per-image copies of the whole cache.
            exists=self.path.exists()
            payload=('\n' if self.incomplete else '')+('' if exists else canonical(HEADER)+'\n')+canonical(record)+'\n'
            with self.path.open('ab' if exists else 'xb') as stream:
                stream.write(payload.encode('utf-8'));stream.flush();os.fsync(stream.fileno())
            hide(self.path)
            record.pop('checksum');self.entries[key]=record;self._identity=identity(self.path);self.incomplete=False


def recognize(image,executable,tessdata,eco):
    from .ocr_quality import recognize as improved
    return improved(image,executable,tessdata,eco)
