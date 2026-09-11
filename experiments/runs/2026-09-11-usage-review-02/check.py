"""Real backend check: controlled incomplete hand-in -> review -> revise; one-shot; cleanup."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
RECORD = Path(__file__).resolve().parent
RUNNER = ROOT / 'scripts/freetoken.py'


def check_backend(backend):
    work = ROOT / 'experiments/workspaces' / f'usage-review-02-{backend}'
    shutil.copytree(ROOT / 'experiments/fixtures/tags-v1', work)
    for argv in (['git','init'], ['git','add','.'], ['git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','commit','-m','test: review workflow baseline']):
        subprocess.run(argv,cwd=work,check=True,capture_output=True)
    (work/'USER_NOTE').write_text('Preserve existing untracked user work.\n')
    task = ROOT / 'experiments/raw' / f'usage-review-02-{backend}'
    def run(command, folder=task, extra=(), expected=0):
        argv=[sys.executable,'-B',str(RUNNER),command,'--task-dir',str(folder),*map(str,extra)]
        result=subprocess.run(argv,text=True,capture_output=True,timeout=150)
        with (RECORD/f'{backend}-controller.log').open('a') as log:log.write(result.stdout+result.stderr)
        assert result.returncode==expected,(command,result.returncode,result.stdout,result.stderr)
        return result
    def start(folder, prompt, oneshot=False):
        path=RECORD/f'{backend}-{folder.name}-prompt.md';path.write_text(prompt)
        extra=['--cwd',work,'--backend',backend,'--prompt-file',path,'--budget','120','--allow','tags.py']
        if backend=='codebuddy':extra+=['--model','deepseek-v4.1-flash','--executable','/Users/dev/.local/share/codebuddy/versions/2.149.0/codebuddy']
        if oneshot:extra+=['--one-shot']
        run('start',folder,extra)
    start(task,'这是审核返工机制的受控测试。最终验收要求支持英文和中文逗号、去空白、忽略空项、按首次顺序去重，大小写敏感。本轮故意模拟不完整交卷：只实现英文逗号支持，不实现中文逗号；只修改 tags.py，运行 acceptance.py，报告本轮缺口，下一轮由审核意见驱动修复。')
    first=json.loads((task/'state.json').read_text());sid=first['session_id']
    probe=subprocess.run([sys.executable,'-B','-c','from tags import normalize_tags; assert normalize_tags(" a，b,a ")==["a","b"]'],cwd=work,capture_output=True,text=True)
    assert probe.returncode!=0,'Controlled defect was not present'
    feedback=RECORD/f'{backend}-feedback.md';feedback.write_text('独立验收失败：normalize_tags(" a，b,a ") 应返回 ["a","b"]，当前未拆中文逗号。请补齐原需求，只修改 tags.py；保留英文逗号、大小写敏感、去空白、去空项、按首次出现去重。运行原验收及该失败样例，报告实际结果。\n'+probe.stderr)
    run('revise',extra=['--evidence-file',feedback,'--budget','120'])
    revised=json.loads((task/'state.json').read_text());assert revised['session_id']==sid and revised['attempt']==2
    passed=subprocess.run([sys.executable,'-B','-c','from acceptance import CASES; from tags import normalize_tags; assert all(normalize_tags(t)==e for t,e in CASES); assert normalize_tags(" a，b,a ")==["a","b"]; print("All 5 cases passed")'],cwd=work,text=True,capture_output=True)
    assert passed.returncode==0,passed.stderr
    evidence=RECORD/f'{backend}-acceptance.md';evidence.write_text(passed.stdout+'Same session, attempt 2, review saved and automatically dispatched.\n')
    run('review',extra=['--decision','accepted','--evidence-file',evidence])
    oneshot=ROOT/'experiments/raw'/f'usage-review-02-{backend}-oneshot'
    start(oneshot,'只读取 tags.py，回答当前支持哪些分隔符。不得修改文件。',True)
    shot=json.loads((oneshot/'state.json').read_text());assert shot['changes']==[]
    report=(Path(shot['attempt_dir'])/'report.md').read_text();assert ',' in report and '，' in report
    (RECORD/f'{backend}-oneshot-report.md').write_text(report)
    shot_evidence=RECORD/f'{backend}-oneshot-acceptance.md';shot_evidence.write_text('Report names both supported commas; source behavior independently passed 5 cases; no files changed.\n')
    run('review',oneshot,['--decision','accepted','--evidence-file',shot_evidence])
    run('resume',oneshot,['--prompt-file',feedback],2)
    for folder in (task,oneshot):
        run('cleanup',folder,['--purge-raw'])
        run('cleanup',folder,['--purge-raw'])
        final=json.loads((folder/'state.json').read_text());assert final['session_closed'] and final['status']=='accepted'
        assert not list((folder/'attempts').glob('*/raw')) and (Path(final['attempt_dir'])/'report.md').exists()
        run('resume',folder,['--prompt-file',feedback],2)
        (RECORD/f'{backend}-{folder.name}-state.json').write_text(json.dumps(final,indent=2)+'\n')
    assert (work/'USER_NOTE').read_text()=='Preserve existing untracked user work.\n'
    print(backend,'review/revise, one-shot and local cleanup passed',flush=True)

with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(check_backend,b) for b in ('codebuddy','dsh')]
    for future in futures:future.result()
