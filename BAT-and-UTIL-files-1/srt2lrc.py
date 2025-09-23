'''

srt2lrc batch converter


🍴🍴🍴 forked from: https://github.com/bojiang/srt2lrc/blob/master/srt2lrc.py ... which was bad for the following reasons:

    (1) did not take into account SRT end timestamps
            (a) which causes a line sung before a guitar solo to persist on screen for the whole guiar solo
            (b) which causes the last line sung on a song to persist until the end of the song
    (2) erroneously processed comments in SRT file (lines that start with “#”)
    (3) failed very easily on SRT files that were the “wrong” encoding
    (4) overwrote existing files even if you didn’t want them to
    (5) overwritten files were not backed up
    (6) lacked commenting in the code



'''



MIN_SECONDS_OF_SILENCE_BETWEEN_LINES_TO_NOT_INSERT_BLANK_LINE = 0.75                    # maximum amount of time, in seconds, that we can “linger” on a line that is done completing, without drawing a blank line before the next line is sung



import glob                     # to find each SRT file needing conversion
import re                       # to detect SRT data blocks with regular expressions
import chardet                  # fix for real-world files that have varied encoding
import os                       # to rename files when backing them up
import sys                      # to process command line options



# define regex for each block of data in the SRT file
SRT_BLOCK_REGEX = re.compile(
        r'(\d+)[^\S\r\n]*[\r\n]+'
        r'(\d{2}:\d{2}:\d{2},\d{3,4})[^\S\r\n]*-->[^\S\r\n]*(\d{2}:\d{2}:\d{2},\d{3,4})[^\S\r\n]*[\r\n]+'
        r'([\s\S]*)')



# converts one block of SRT data into LRC data
def srt_block_to_irc(block):
    match = SRT_BLOCK_REGEX.search(block)
    if not match:
        return None
    num, time_start, time_end, content = match.groups()
    time_start = time_start[3:-1].replace(',', '.')
    time_end   =   time_end[3:-1].replace(',', '.')

    #content_massaged = content.replace('\n', ' ')                                                                          # old way did not ignore commentedl ines
    content_massaged = ' '.join(line for line in content.splitlines() if not line.lstrip().startswith('#'))

    return {'start': time_start, 'end': time_end, 'content': content_massaged.strip()}



# skips blocks that we deem as meaningless
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


# computers time difference between 2 timestamps
def time_difference(time1, time2):
    minutes1, seconds1 = map(float, time1.split(':'))
    minutes2, seconds2 = map(float, time2.split(':'))
    return abs((minutes2 * 60 + seconds2) - (minutes1 * 60 + seconds1))




# converts a single SRT file to LRC
def srt_file_to_irc(fname, force=False):

    # First, we need to detect the encoding:                                                    # fix for real-world files that have varied encoding
    with open(fname, 'rb') as raw_file:                                                         # fix for real-world files that have varied encoding
        result = chardet.detect(raw_file.read(1000))  # Detect encoding based on a sample       # fix for real-world files that have varied encoding
        encoding = result['encoding'] or 'utf-8'                                                # fix for real-world files that have varied encoding
        if encoding.lower() == 'ascii' or encoding=="Windows-1252": encoding = 'utf-8'          # fix for real-world files that have varied encoding
        #DEBUG: print(f"using encoding {encoding}")                                             # fix for real-world files that have varied encoding

    # Then, we read the file with the proper encoding, which the original program didn’t do:    # fix for real-world files that have varied encoding
    #ith open(fname, encoding='utf8'  ) as file_in:                                             # fix for real-world files that have varied encoding
    with open(fname, encoding=encoding) as file_in:                                             # fix for real-world files that have varied encoding

        str_in     = file_in.read()                                                             # read the file in
        blocks_in  = str_in.replace('\r\n', '\n').split('\n\n')                                 # fix newlines
        blocks_out = [srt_block_to_irc(block) for block in blocks_in]                           # chunk up data into blocks
        blocks_out = filter_blocks(blocks_out)                                                  # filter out irreleevant blocks


        # OLD WAY, *NO* RECOGNITION OF THE END-TIMESAMP FROM OUR SRT FILE:
        #str_out = ''.join('[{start}]{content}\n'.format(**block) for block in blocks_out if block['content'])

        # NEW WAY, WITH RECOGNITION OF THE END-TIMESAMP FROM OUR SRT FILE:
        if 1 == 2:
            str_out = ''
            for i, block in enumerate(blocks_out):
                if not block or not block['content']: continue
                str_out += '[{start}]{content}\n'.format(**block)
                #if i + 1 < len(blocks_out):
                #    next_start = blocks_out[i + 1]['start']
                #    if block['end'] != next_start:                                                  # \__ only insert end-timestamp LRC-line if it’s not the
                #        str_out += '[{end}]\n'.format(**block)                                      # /   same as next start-timestamp of the next block
                is_last = (i + 1 == len(blocks_out))
                if is_last or block['end'] != blocks_out[i + 1]['start']:
                    str_out += '[{end}]\n'.format(**block)

        # NEW WAY, WITH RECOGNITION OF THE END-TIMESTAMP FROM OUR SRT FILE AND OUR USER-DEFINED THRESHOLD WITHIN WHICH TO NOT INVOKE THE END-TIMESTAMP-SIMULATION FUNCTOINALITY:
        str_out = ''
        for i, block in enumerate(blocks_out):
            if not block or not block['content']: continue
            str_out += '[{start}]{content}\n'.format(**block)
            is_last = (i + 1 == len(blocks_out))
            if is_last:
                str_out += '[{end}]\n'.format(**block)
            else:
                next_start = blocks_out[i + 1]['start']
                gap = time_difference(block['end'], next_start)
                if gap >= MIN_SECONDS_OF_SILENCE_BETWEEN_LINES_TO_NOT_INSERT_BLANK_LINE:
                    str_out += '[{end}]\n'.format(**block)


        # Write the converted LRC to disk (if applicable):                                                                          # *** Create the new LRC [if applicable]: ***
        lrc_fname = fname.replace('srt', 'lrc')                                                                                     # get new filename
        if os.path.exists(lrc_fname):                                                                                               # what if it exists?
            if not force:                                                                                                           # if we aren’t in force-overwrite mode
                print(f"       * WARNING: LRC '{lrc_fname}' already exists!!!!!! Skipping to avoid overwriting!!!!!!\n")            # then we simply warn them
                return                                                                                                              # and give up
            else:                                                                                                                   # but if we ARE in force-overwrite mode
                from datetime import datetime                                                                                       # \__ we will need to determine the
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")                                                                # /   current year/month/day/hour/second
                backup_name = f"{lrc_fname}.replaced-by-srt2lrc-reconversion-on-{timestamp}.bak"                                    # in order to create our backup filename
                os.rename(lrc_fname, backup_name)                                                                                   # which we will use to back the file up
                print(f"       * WARNING: LRC '{lrc_fname}' already existed — backed up as:\n         → {backup_name}\n")           # and warn the user accordingly

        with open(lrc_fname, 'w', encoding='utf8') as file_out:                                                                     # at this point we are definitely converting
            file_out.write('[Generated by Claire Sawyer’s WhisperAI-based]\n[transcription system.  Get cancer, Trumpers.]\n')      # insert a header
            file_out.write(str_out)                                                                                                 # and write the data out



if __name__ == '__main__':
    err_info = []
    force = 'force' in sys.argv
    go = 'go' in sys.argv

    if not (go or force):
        print("\n💫 Usage:\n  python srt2lrc.py go [force]\n\nOptions:\n  go     = convert all .SRT files in folder to .LRC\n  force  = overwrite existing .lrc files\n")
        sys.exit(1)

    print("\n* About to convert all SRT files in folder...\n");
    for file_name in glob.glob('*.srt'):
        print(f"    * Converting file: {file_name}");
        srt_file_to_irc(file_name, force)
    if err_info:
        print('  ☹   success, but some exceptions are ignored:')
        for file_name, blocks_num, context in err_info:
            print('\tfile: %s,\tblock num: %s,\tcontext: %s' % (file_name, blocks_num, context))
    else:
        print('* All done!')
