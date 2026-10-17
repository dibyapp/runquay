"""Optional Chromium acceptance checks. Requires Node and Playwright, no AI login.

Run: python tests/browser_smoke.py
All profiles, project histories and work outputs are fictional and temporary.
No vendor CLI, installer, purchase, reset or external model call is executed.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    node=shutil.which('node')
    if not node:
        raise SystemExit('Install Node.js and Playwright to run browser checks.')
    with tempfile.TemporaryDirectory(prefix='runquay-browser-') as temporary:
        directory=Path(temporary)
        env={**os.environ,'RUNQUAY_BROWSER_ARTIFACTS':str(directory)}
        log=(directory/'fixture.log').open('w',encoding='utf-8')
        process=subprocess.Popen([sys.executable,str(ROOT/'tests/browser_fixture.py'),str(directory)],cwd=ROOT,stdout=log,stderr=log)
        try:
            deadline=time.monotonic()+45
            control=directory/'browser-control.json'
            while not control.exists():
                if process.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError('Disposable browser fixture did not become ready')
                time.sleep(.1)
            for script in ('browser_field.cjs','browser_controls.cjs','browser_tasks.cjs'):
                subprocess.run([node,str(ROOT/'tests'/script)],cwd=ROOT,env=env,check=True,timeout=240)
            print('Chromium acceptance checks passed; no real AI calls or private histories used.')
        finally:
            if control.exists():
                Path(json.loads(control.read_text(encoding='utf-8'))['stop']).touch()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=10)
            log.close()


if __name__=='__main__':
    main()
