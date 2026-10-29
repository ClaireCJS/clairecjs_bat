"""Choose review chrome placement by the image size it leaves available."""
from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Layout:
    side: bool
    columns: int
    left: int
    right: int
    caption_height: int
    image_width: int
    image_height: int


def choose_layout(width, height, image_size, bank_widths, bank_counts, row_height,
                  caption_height=160, notice_height=60, dialog=False):
    width=max(1,int(width));height=max(1,int(height))
    aspect=image_size[0]/max(1,image_size[1])
    def fitted(w,h):
        h=max(1,min(h,w/aspect))
        return max(1,int(h*aspect)),max(1,int(h))
    columns=max(1,min(4 if dialog else 3,int(width/max(bank_widths)/(1 if dialog else 2))))
    controls=ceil(max(bank_counts)/columns)*row_height+8
    caption=min(caption_height,max(80,height//3))
    iw,ih=fitted(width,max(1,height-caption-controls-notice_height))
    best=Layout(False,columns,0,0,caption,iw,ih)
    for columns in (1,2,3):
        left=max(180,bank_widths[0]*columns+16)
        right=max(200,bank_widths[1]*columns+16)
        controls=ceil(max(bank_counts)/columns)*row_height+8
        if width-left-right<100 or height<controls+100+notice_height:continue
        iw,ih=fitted(width-left-right,height)
        if (iw*ih>best.image_width*best.image_height*1.01 or
            best.side and iw*ih>=best.image_width*best.image_height*.999 and columns>best.columns):
            best=Layout(True,columns,left,right,caption,iw,ih)
    return best
