import uuid
import pytest
from image_caption_gender_fixer import imaging
from image_caption_gender_fixer.errors import IntegrityError
from image_caption_gender_fixer.fs import sha256


def test_nested_exif_dimensions_follow_baked_orientation(tmp_path):
    _,_,Image,_,_,_,_,_=imaging.libraries()
    image=Image.new("RGB",(100,60),"orange")
    exif=Image.Exif();exif[274]=6;exif[34665]={40962:100,40963:60,36867:"2020:01:01 00:00:00"}
    source=tmp_path/"nested.jpg";image.save(source,exif=exif)
    decoded,metadata=imaging.decode(source)
    output=tmp_path/"saved.jpg"
    imaging.save_image(decoded,metadata,output,str(uuid.uuid4()),sha256(source),"rules")
    with Image.open(output) as saved:
        nested=saved.getexif().get_ifd(34665)
        assert (nested[40962],nested[40963])==(60,100)
        assert nested[36867]=="2020:01:01 00:00:00"


def test_foreign_reserved_marker_is_preserved_for_inspection(tmp_path):
    _,_,Image,_,_,_,_,PNG=imaging.libraries()
    info=PNG.PngInfo();info.add_text("ICGF",'{"application":"another-tool","schema":3}')
    source=tmp_path/"foreign.png";Image.new("RGB",(20,20),"white").save(source,pnginfo=info)
    original=source.read_bytes()
    with pytest.raises(IntegrityError,match="reserved ICGF"):
        imaging.marker(source)
    assert source.read_bytes()==original
