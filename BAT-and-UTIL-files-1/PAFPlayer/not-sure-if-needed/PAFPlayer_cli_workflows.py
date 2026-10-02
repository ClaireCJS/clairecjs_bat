"""Parse workflow switches before the established PAFPlayer playback parser."""
from PAFPlayer_workflows import *


def dispatch(runtime,arguments):
    parser=argparse.ArgumentParser(prog='PAFPlayer workflows',add_help=False)
    parser.add_argument('--queue-regex','--regex',dest='queue_regex')
    parser.add_argument('--filelist')
    parser.add_argument('--workflow-help',action='store_true')
    parser.add_argument('--monitor',action='append',default=[],metavar='PATH')
    parser.add_argument('--monitor-mode',choices=('index','playlist','library'),default='index')
    parser.add_argument('--monitor-playlist')
    parser.add_argument('--monitor-recursive',action='store_true')
    parser.add_argument('--monitor-dry-run',action='store_true')
    parser.add_argument('--repair-playlist')
    parser.add_argument('--repair-root',action='append',default=[])
    parser.add_argument('--repair-recursive',action='store_true')
    parser.add_argument('--repair-dry-run',action='store_true')
    parser.add_argument('--repair-batch',action='store_true')
    parser.add_argument('--repair-playlist-only',action='store_true')
    parser.add_argument('--render-song',metavar='AUDIO')
    parser.add_argument('--render-output')
    parser.add_argument('--render-prefix')
    parser.add_argument('--render-no-open',action='store_true')
    parser.add_argument('--render-save',action='store_true',help='Save without prompting; choose a prefix with --render-prefix')
    parser.add_argument('--gather-cuda-benchmarks',action='store_true')
    parser.add_argument('--cuda-benchmark-log')
    parser.add_argument('--analyze-cuda-benchmarks',nargs='?',const='',metavar='LOG')
    opts,remaining=parser.parse_known_args(arguments)
    if opts.workflow_help: parser.print_help(); return 0,remaining
    try:
        if opts.queue_regex is not None:
            from PAFPlayer_instance import resolve_request
            runtime.startup_request=resolve_request(runtime,[],regex=opts.queue_regex,filelist=opts.filelist)
            target=unique(runtime.root/'requests'/'regex.m3u8');target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('\n'.join(runtime.startup_request['paths'])+'\n',encoding='utf-8')
            remaining=['--playlist',str(target)]+remaining
        if opts.analyze_cuda_benchmarks is not None:
            from PAFPlayer_cuda_benchmarks import analyze
            path=opts.analyze_cuda_benchmarks or opts.cuda_benchmark_log or runtime.root/'cuda-benchmarks.jsonl'
            print(json.dumps(analyze(path),ensure_ascii=False,indent=2)); return 0,remaining
        if opts.render_song:
            from PAFPlayer_render_book import render_song
            print(json.dumps(render_song(runtime,opts.render_song,output=opts.render_output,open_browser=not opts.render_no_open,prompt=not opts.render_save,prefix=opts.render_prefix),ensure_ascii=False,indent=2))
            return 0,remaining
        if opts.repair_playlist:
            from PAFPlayer_web_workflows import repair_preview,apply_repair
            preview=repair_preview(runtime,{'playlist':opts.repair_playlist,'roots':opts.repair_root,'recursive':opts.repair_recursive})
            approved={}
            for item in preview['items']:
                print('\nMissing: '+item['missing'])
                for number,candidate in enumerate(item['candidates'],1):
                    print(f" {number}. [{candidate['confidence']}; {candidate['score']:.2f}] {candidate['path']}\n    "+'; '.join(candidate['evidence']))
                if opts.repair_dry_run: continue
                answer=input('Choose replacement number (Enter skips): ').strip()
                if not answer: continue
                number=int(answer)
                if number<1 or number>len(item['candidates']): raise ValueError('Candidate number out of range')
                approved[item['missing']]=item['candidates'][number-1]['path']
                if not opts.repair_batch:
                    print(json.dumps(apply_repair(runtime,{'id':preview['id'],'approved':{item['missing']:approved[item['missing']]},'dry_run':False,'playlist_only':True}),indent=2))
                    preview['hash']=digest(opts.repair_playlist)
            if opts.repair_batch and approved and not opts.repair_dry_run:
                print(json.dumps(approved,ensure_ascii=False,indent=2))
                if input('Apply these approved replacements together? [y/N] ').strip().casefold() in ('y','yes'):
                    print(json.dumps(apply_repair(runtime,{'id':preview['id'],'approved':approved,'dry_run':False,'playlist_only':True}),indent=2))
            # CLI repair operates on a playlist, never a separate running player's state.
            return 0,remaining
        if opts.gather_cuda_benchmarks:
            from PAFPlayer_cuda_benchmarks import Benchmark
            runtime.benchmark=Benchmark(Path(opts.cuda_benchmark_log) if opts.cuda_benchmark_log else runtime.root/'cuda-benchmarks.jsonl')
            print('Experimental CPU/CUDA comparison log: '+str(runtime.benchmark.path))
        if opts.monitor:
            if any(not Path(x).is_dir() for x in opts.monitor): raise ValueError('Monitor roots must be existing directories')
            if opts.monitor_mode=='playlist' and not opts.monitor_playlist: raise ValueError('Playlist mode requires --monitor-playlist')
            runtime.monitor=FolderMonitor(runtime,opts.monitor,opts.monitor_mode,opts.monitor_playlist,opts.monitor_recursive)
            if opts.monitor_dry_run:
                print(json.dumps(runtime.monitor.scan(dry_run=True),indent=2)); return 0,remaining
            runtime.monitor.start()
            if not remaining:
                print('Monitoring folders. Ctrl+C stops monitoring; source files are never removed.')
                try:
                    while not runtime.stop_event.wait(.5): pass
                except KeyboardInterrupt: runtime.close()
                return 0,remaining
    except (ValueError,OSError,EOFError) as exc:
        print('PAFPlayer workflow: '+str(exc)); return 2,remaining
    return None,remaining
