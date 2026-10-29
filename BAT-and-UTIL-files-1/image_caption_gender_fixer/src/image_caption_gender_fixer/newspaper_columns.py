r"""ICGF COPY/ADAPTATION of Claire's print_with_columns / newspaper renderer.

Origin: C:\BAT\print_with_columns.py; newspaper.bat calls print-with-columns.bat.
Copied 2026-10-28 from SHA-256
f0cfcec8cec11d921a1f28ec4615f3f53e9a9401ce35d6b5cdf909cad8a37aaf.
The column slicing, column width and padded row assembly routines below are
adapted from distribute_lines_into_columns (line 473), calculate_column_widths
(515) and render_columns (591). CLI globals/debug/stripe highlighting are
removed. ICGF supplies bounded wrapping, safe OCR text, adaptive column counts,
and synchronized old/new column pairs. No rich/colorama/global package import
or newspaper subprocess is needed. Keep this attribution with these copies.
"""
import math
import re
import shutil
import unicodedata
from difflib import SequenceMatcher

ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
DIVIDER='  │  '

def safe_text(text):
    return ''.join(c if c in '\n\t' or not(ord(c)<32 or 127<=ord(c)<=159) else '\\x'+format(ord(c),'02x') for c in str(text)).expandtabs(4)

def display_width(text):
    import regex
    result=0
    for cluster in regex.findall(r'\X',ANSI.sub('',text)):
        if '\u200d' in cluster or '\u20e3' in cluster:result+=2;continue
        result+=sum(0 if unicodedata.combining(c) or unicodedata.category(c) in ('Mn','Me','Cf') else 2 if unicodedata.east_asian_width(c) in 'FW' else 1 for c in cluster)
    return result

def wrap_line(text,width):
    import regex
    width=max(2,width)
    clusters=regex.findall(r'\X',text)
    costs=[display_width(c) for c in clusters]
    if not clusters:return ['']
    result=[];start=0
    while start<len(clusters):
        end=start;used=0;space=None
        while end<len(clusters) and used+costs[end]<=width:
            if clusters[end]==' ':space=end
            used+=costs[end];end+=1
        if end==start:end+=1
        if end<len(clusters) and space is not None and space>start+(end-start)//2:end=space
        result.append(''.join(clusters[start:end]));start=end
        while start<len(clusters) and clusters[start]==' ':start+=1
    return result

# COPY/ADAPTATION: print_with_columns.distribute_lines_into_columns.
def distribute_lines_into_columns(lines,columns,rows_per_col):
    columns_data=[[] for _ in range(columns)]
    for col in range(columns):
        start_index=col*rows_per_col
        end_index=start_index+rows_per_col
        columns_data[col]=lines[start_index:end_index]
    return columns_data

# COPY/ADAPTATION: print_with_columns.calculate_column_widths.
def calculate_column_widths(columns_data):
    return [max((display_width(line) for line in column),default=0) for column in columns_data]

# COPY/ADAPTATION: print_with_columns.render_columns; no stripe side channel.
def render_columns(columns_data,column_widths,divider=DIVIDER):
    rows_per_col=max((len(col) for col in columns_data),default=0)
    rendered_rows=[]
    for row in range(rows_per_col):
        row_parts=[]
        for current_column_index,current_column in enumerate(columns_data):
            part=current_column[row] if row<len(current_column) else ''
            num_spaces_to_add=column_widths[current_column_index]-display_width(part)
            row_parts.append(part+' '*max(0,num_spaces_to_add))
        rendered_rows.append(divider.join(row_parts).rstrip(' '))
    return rendered_rows

def dimensions(width,height):
    size=shutil.get_terminal_size((120,40))
    return max(8,int(width or size.columns-1)),max(4,int(height or size.lines-10))

def newspaper(text,width=None,height=None):
    """Read down each column, then continue at the top of the next column."""
    width,height=dimensions(width,height);lines=safe_text(text).split('\n')
    best=None
    for columns in range(1,min(8,len(lines),max(1,(width+5)//21))+1):
        cell=max(2,(width-5*(columns-1))//columns)
        wrapped=[row for line in lines for row in wrap_line(line,cell)]
        data=distribute_lines_into_columns(wrapped,columns,math.ceil(len(wrapped)/columns))
        rendered=render_columns(data,calculate_column_widths(data))
        if best is None or len(rendered)<len(best):best=rendered
        if len(rendered)<=height:return rendered
    return best or ['']

def compare_columns(detected,proposed,width=None,height=None,enabled=None):
    from .presentation import color,GREEN,YELLOW
    width,height=dimensions(width,height)
    detected=safe_text(detected);proposed=safe_text(proposed)
    if width<64:
        output=[]
        for title,text,fg in [('📖 Detected caption',detected,GREEN),('✨ Proposed caption',proposed,YELLOW)]:
            output.extend(color(row,fg,enabled) for row in wrap_line(title,width));output.extend(color(row,fg,enabled) for row in newspaper(text,width,height))
        return '\n'.join(output)
    left=detected.splitlines();right=proposed.splitlines();pairs=[]
    for _,a,b,c,d in SequenceMatcher(None,left,right,autojunk=False).get_opcodes():
        pairs.extend((left[a+i] if a+i<b else '',right[c+i] if c+i<d else '') for i in range(max(b-a,d-c)))
    best=None
    # Each newspaper segment is a synchronized detected/proposed pair. Keeping
    # pairs together makes unchanged and edited sentences easy to compare.
    for segments in range(1,min(4,max(1,(width+3)//56))+1):
        cell=(width-5*(2*segments-1))//(segments*2)
        rows=[]
        for old,new in pairs:
            olds=wrap_line(old,cell);news=wrap_line(new,cell)
            for i in range(max(len(olds),len(news))):rows.append((olds[i] if i<len(olds) else '',news[i] if i<len(news) else ''))
        per_segment=max(1,math.ceil(len(rows)/segments));columns=[]
        for part in range(segments):
            group=rows[part*per_segment:(part+1)*per_segment]
            columns.append([color('📖 Detected caption',GREEN,enabled),*[color(a,GREEN,enabled) for a,b in group]])
            columns.append([color('✨ Proposed caption',YELLOW,enabled),*[color(b,YELLOW,enabled) for a,b in group]])
        # Copy's renderer pads by display width, including ANSI and wide glyphs.
        rendered=render_columns(columns,[cell]*len(columns),DIVIDER)
        if best is None or len(rendered)<len(best):best=rendered
        if len(rendered)<=height:return '\n'.join(rendered)
    return '\n'.join(best or [])
