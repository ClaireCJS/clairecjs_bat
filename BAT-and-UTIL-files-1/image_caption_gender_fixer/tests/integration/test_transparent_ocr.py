import pytest
from pathlib import Path
from image_caption_gender_fixer import imaging,dependencies
from image_caption_gender_fixer.fs import sha256
from image_caption_gender_fixer.history import History
from test_images import app_for


@pytest.mark.parametrize("foreground",[(0,0,0,255),(255,255,255,255)])
def test_fully_transparent_png_ocr_edit_preserves_alpha_and_original(tmp_path,foreground):
    _,_,Image,Draw,Font,_,_,_=imaging.libraries()
    source=tmp_path/"transparent.png"
    image=Image.new("RGBA",(1000,300),(0,0,0,0))
    Draw.Draw(image).text((70,100),"good boi",font=Font.truetype(r"C:\Windows\Fonts\arial.ttf",72),fill=foreground)
    image.save(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(["a"]))
    result,code=app.process([str(source)])
    assert code==0 and result["results"][0]["state"]=="committed",result
    event=next(iter(History(tmp_path).transactions().values()))
    assert sha256(tmp_path/event["backup"])==original
    corrected=Path(result["results"][0]["corrected"])
    with Image.open(corrected) as output:
        assert output.mode=="RGBA" and output.getchannel("A").getextrema()==(0,255)
        lines=imaging.ocr(output,dependencies.native(app.root,"tesseract")["path"],app.root/"environment/tessdata",full=True)
    assert "good girl" in " ".join(line["text"].casefold() for line in lines)
