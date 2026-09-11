"""Repeat the small full lifecycle with both backends; not a timing comparison.
Run: python3 -B experiments/repeat_lifecycle.py --tag <fresh-name>
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from freetoken import is_alive
RUNNER = ROOT / 'scripts/freetoken.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    if not args.tag.replace('-', '').isalnum():
        parser.error('Use letters, digits and hyphens')
    records = ROOT / 'experiments/runs' / args.tag
    records.mkdir(parents=True, exist_ok=False)

    def backend_run(backend):
        rows = []
        for repeat in (1, 2):
            for mode in ('normal', 'cancel', 'timeout'):
                name = f'{backend}-{repeat}-{mode}'
                work = ROOT / 'experiments/workspaces' / f'{args.tag}-{name}'
                fixture = 'tags-v1' if mode == 'normal' else 'cancel-v1'
                shutil.copytree(ROOT / 'experiments/fixtures' / fixture, work)
                (work / 'USER_NOTE').write_text('baseline\n')
                for command in (['git', 'init'], ['git', 'add', '.'],
                                ['git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                                 'commit', '-m', 'test: freeze repeat baseline']):
                    subprocess.run(command, cwd=work, capture_output=True, check=True)
                (work / 'USER_NOTE').write_text('preserve dirty work\n')
                task = ROOT / 'experiments/raw' / f'{args.tag}-{name}'
                def call(command, prompt=None, budget=120):
                    argv = [sys.executable, '-B', str(RUNNER), command, '--task-dir', str(task)]
                    if prompt:
                        path = records / f'{name}-{command}.md'
                        path.write_text(prompt)
                        argv += ['--prompt-file', str(path), '--budget', str(budget)]
                    if command == 'start':
                        argv += ['--cwd', str(work), '--backend', backend]
                        for allowed in (['tags.py'] if mode == 'normal' else ['started', 'finished']):
                            argv += ['--allow', allowed]
                        if backend == 'codebuddy':
                            argv += ['--model', 'deepseek-v4.1-flash', '--executable',
                                     '/Users/dev/.local/share/codebuddy/versions/2.149.0/codebuddy']
                    return argv
                def state():
                    return json.loads((task / 'state.json').read_text())
                def archive(label):
                    data = state()
                    (records / f'{name}-{label}.json').write_text(json.dumps(data, indent=2) + '\n')
                    usage = Path(data['attempt_dir']) / 'usage.json'
                    if usage.exists(): shutil.copy2(usage, records / f'{name}-{label}-usage.json')
                    return data
                start_prompt = ('只修改 tags.py 的 normalize_tags：按英文逗号拆分、去空白、忽略空项、按首次出现顺序去重，大小写敏感。运行 python3 -B acceptance.py。'
                                if mode == 'normal' else
                                '只执行一次前台命令 python3 -B slow_operation.py start。等待控制端取消；不要重复调用或修改脚本。')
                with (records / f'{name}-start.log').open('w') as log:
                    process = subprocess.Popen(call('start', start_prompt, 35 if mode == 'timeout' else 120), stdout=log, stderr=log)
                    if mode != 'normal':
                        deadline = time.monotonic() + 65
                        while not (work / 'started').exists():
                            assert process.poll() is None and time.monotonic() < deadline, name
                            time.sleep(.1)
                        checkpoint = (work / 'started').read_bytes()
                        marker = json.loads(checkpoint)
                        if mode == 'cancel':
                            subprocess.run(call('cancel'), capture_output=True, check=True)
                    assert process.wait(timeout=150) == (0 if mode == 'normal' else 2), name
                before = archive('first')
                assert before['status'] == {'normal': 'awaiting_review', 'cancel': 'cancelled', 'timeout': 'timed_out'}[mode], before
                assert not before['out_of_scope'] and not before['cleanup_required'], before
                if mode == 'normal':
                    first = subprocess.run([sys.executable, '-B', 'acceptance.py'], cwd=work, capture_output=True, text=True)
                    assert first.returncode == 0, first.stdout
                    (records / f'{name}-first-check.md').write_text(first.stdout)
                    feedback = '继续原会话：新增支持中文逗号，保留全部原行为；只修改 tags.py。运行原验收并验证 normalize_tags(" a，b,a ") == ["a", "b"]。'
                else:
                    assert not any(is_alive(p) for p in before['known_processes'])
                    time.sleep(max(0, marker['started_at'] + 47 - time.time()))
                    assert not (work / 'finished').exists() and (work / 'started').read_bytes() == checkpoint
                    feedback = '继续原会话：检查 started 已存在，只调用 python3 -B slow_operation.py finish 完成剩余部分。不得重新 start，不修改脚本。'
                with (records / f'{name}-resume.log').open('w') as log:
                    resumed = subprocess.run(call('resume', feedback), stdout=log, stderr=log, timeout=150)
                assert resumed.returncode == 0, name
                after = archive('resumed')
                assert before['session_id'] == after['session_id'] and after['attempt'] == 2
                assert not after['out_of_scope'] and (work / 'USER_NOTE').read_text() == 'preserve dirty work\n'
                if mode == 'normal':
                    check = subprocess.run([sys.executable, '-B', '-c', 'from acceptance import CASES; from tags import normalize_tags; assert all(normalize_tags(text)==expected for text,expected in CASES); assert normalize_tags(" a，b,a ")==["a","b"]; print("4 original and 1 incremental checks passed")'], cwd=work, text=True, capture_output=True)
                    assert check.returncode == 0, check.stdout + check.stderr
                    evidence_text = check.stdout
                else:
                    assert (work / 'started').read_bytes() == checkpoint
                    assert (work / 'finished').read_text() == 'completed\n'
                    stamp = (work / 'finished').stat().st_mtime_ns
                    subprocess.run([sys.executable, '-B', 'slow_operation.py', 'finish'], cwd=work, check=True, capture_output=True)
                    assert (work / 'finished').stat().st_mtime_ns == stamp
                    evidence_text = 'Observed processes stopped; no late finish after checkpoint +47s; same-session finish preserved checkpoint; second finish did not rewrite marker.\n'
                evidence = records / f'{name}-acceptance.md'
                evidence.write_text(evidence_text + 'USER_NOTE unchanged; no out-of-scope changes; session ID preserved.\n')
                subprocess.run(call('review') + ['--decision', 'accepted', '--evidence-file', str(evidence)], capture_output=True, check=True)
                row = {'name': name, 'passed': True, 'session_id': after['session_id'],
                       'first_s': before['elapsed_s'], 'resume_s': after['elapsed_s'], 'task_dir': str(task)}
                rows.append(row)
                print(json.dumps(row), flush=True)
        return rows

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(backend_run, backend) for backend in ('codebuddy', 'dsh')]
        rows = [row for future in futures for row in future.result()]
    (records / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')

if __name__ == '__main__':
    main()
