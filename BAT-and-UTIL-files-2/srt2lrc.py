'''

Really, should be named convert_all_srt_to_lrc.py , but this is its original name and I kept it

Run it in srt file folder.
python 3.x

downloaded from: https://github.com/bojiang/srt2lrc/blob/master/srt2lrc.py

and fixed, because the original version failed very easily on SRT files that were the "wrong" encoding



'''
import glob
import re
import chardet                                                                                  #fix for real-world files that have varied encoding
import os


SRT_BLOCK_REGEX = re.compile(
        r'(\d+)[^\S\r\n]*[\r\n]+'
        r'(\d{2}:\d{2}:\d{2},\d{3,4})[^\S\r\n]*-->[^\S\r\n]*(\d{2}:\d{2}:\d{2},\d{3,4})[^\S\r\n]*[\r\n]+'
        r'([\s\S]*)')


def srt_block_to_irc(block):
    match = SRT_BLOCK_REGEX.search(block)
    if not match:
        return None
    num, time_start, time_end, content = match.groups()
    time_start = time_start[3:-1].replace(',', '.')
    time_end = time_end[3:-1].replace(',', '.')
    content_massaged = content.replace('\n', ' ')
    #eturn '[%s]%s\n[%s]\n' % (time_start, content_massaged, time_end)
    return {'start': time_start, 'end': time_end, 'content': content_massaged.strip()}


def filter_blocks_fail_01(blocks):
    filtered_blocks = []
    for i, block in enumerate(blocks):
        if not block:
            continue
        if block['content'] == "" and i + 1 < len(blocks):
            next_block = blocks[i + 1]
            if next_block and next_block['start'] == block['start']:
                continue  # Skip blank line with the same timestamp
            if time_difference(block['start'], next_block['start']) <= 1.5:
                continue  # Skip blank line within 1.5 seconds of the next line
        filtered_blocks.append(block)
    return filtered_blocks

def filter_blocks(blocks):
    filtered_blocks = []
    for i, block in enumerate(blocks):
        if not block:
            continue

        # Skip blocks with empty content if they have the same timestamp as the next one
        if block['content'] == "" and i + 1 < len(blocks) and blocks[i + 1]['start'] == block['start']:
            continue

        # Skip blocks with empty content if they are within 1.5 seconds of the next block
        if block['content'] == "" and i + 1 < len(blocks):
            next_block = blocks[i + 1]
            if time_difference(block['start'], next_block['start']) <= 1.5:
                continue

        # Skip blocks if they have the same timestamp as the previous one and the previous one has content
        if filtered_blocks and filtered_blocks[-1]['start'] == block['start'] and filtered_blocks[-1]['content']:
            continue

        filtered_blocks.append(block)
    return filtered_blocks


def time_difference(time1, time2):
    minutes1, seconds1 = map(float, time1.split(':'))
    minutes2, seconds2 = map(float, time2.split(':'))
    return abs((minutes2 * 60 + seconds2) - (minutes1 * 60 + seconds1))


def srt_file_to_irc(fname):
    with open(fname, 'rb') as raw_file:                                                         #fix for real-world files that have varied encoding
        result = chardet.detect(raw_file.read(1000))  # Detect encoding based on a sample       #fix for real-world files that have varied encoding
        encoding = result['encoding']                                                           #fix for real-world files that have varied encoding
    #ith open(fname, encoding='utf8'  ) as file_in:                                             #fix for real-world files that have varied encoding
    with open(fname, encoding=encoding) as file_in:                                             #fix for real-world files that have varied encoding
        str_in = file_in.read()
        blocks_in = str_in.replace('\r\n', '\n').split('\n\n')
        blocks_out = [srt_block_to_irc(block) for block in blocks_in]
        #if not all(blocks_out):
        #    err_info.append((fname, blocks_out.index(None), blocks_in[blocks_out.index(None)]))
        #blocks_out = filter(None, blocks_out)
        #str_out = ''.join(blocks_out)
        blocks_out = filter_blocks(blocks_out)
        #tr_out = ''.join('[{start}]{content}\n[{end}]\n'.format(**block) for block in blocks_out if block)
        str_out = ''.join('[{start}]{content}\n'         .format(**block) for block in blocks_out if block['content'])
        lrc_fname = fname.replace('srt', 'lrc')
        #with open(fname.replace('srt', 'lrc'), 'w', encoding='utf8') as file_out:
        #    file_out.write(str_out)
        if os.path.exists(lrc_fname):
            print(f"       * WARNING: LRC '{lrc_fname}' already exists!!!!!! Skipping to avoid overwriting!!!!!!\n")
            return  # Skip this file if LRC already exists
        with open(lrc_fname, 'w', encoding='utf8') as file_out:
            file_out.write(str_out)

if __name__ == '__main__':
    err_info = []
    print("\n* About to convert all SRT files in folder...\n");
    for file_name in glob.glob('*.srt'):
        print(f"    * Converting file: {file_name}");
        srt_file_to_irc(file_name)
    if err_info:
        print('  :/   success, but some exceptions are ignored:')
        for file_name, blocks_num, context in err_info:
            print('\tfile: %s,\tblock num: %s,\tcontext: %s' % (file_name, blocks_num, context))
    else:
        print('* All done!')