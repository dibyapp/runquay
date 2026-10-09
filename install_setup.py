"""OS-aware setup using fixed packages and a private, verified Node runtime."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import zipfile

from platform_support import child_options, command_display, data_home

PACKAGES = {'codex':'@openai/codex', 'claude':'@anthropic-ai/claude-code', 'gemini':'@google/gemini-cli'}
NAMES = {'git':'Git', 'node':'Node.js', 'codex':'Codex', 'claude':'Claude Code', 'gemini':'Gemini CLI'}
DOCS = {'git':'https://git-scm.com/downloads', 'node':'https://nodejs.org/en/download',
        'codex':'https://learn.chatgpt.com/docs/cli', 'claude':'https://code.claude.com/docs/en/setup',
        'gemini':'https://geminicli.com/docs/get-started/installation/'}


def tools_home():
    return data_home() / 'setup-tools'


def search_path():
    extra = [tools_home(), tools_home()/'bin', tools_home()/'node-runtime'/'bin',
             tools_home()/'node-runtime', Path.home()/'.local/bin']
    if os.name == 'nt':
        extra += [Path(os.environ.get('ProgramFiles','C:/Program Files'))/'nodejs',
                  Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Git/cmd',
                  Path(os.environ.get('APPDATA',Path.home()/'AppData/Roaming'))/'npm']
    else:
        extra += [Path('/opt/homebrew/bin'), Path('/usr/local/bin')]
    own_node=tools_home()/'node-runtime'
    prefix=[str(own_node),str(own_node/'bin')] if own_node.is_dir() else []
    return os.pathsep.join([*prefix,os.environ.get('PATH',''), *(str(p) for p in extra)])


def node_binary():
    own = tools_home()/'node-runtime'/('node.exe' if os.name=='nt' else 'bin/node')
    return str(own) if own.is_file() else shutil.which('node', path=search_path()) or ''


def node_ready():
    binary=node_binary()
    if not binary: return False
    try:
        result=subprocess.run([binary,'--version'],capture_output=True,text=True,timeout=5,**child_options())
        match=re.fullmatch(r'v(\d+)\.\d+\.\d+\s*',result.stdout)
        return result.returncode==0 and bool(match) and int(match[1])>=22
    except (OSError,subprocess.TimeoutExpired): return False


def git_ready():
    binary=shutil.which('git',path=search_path())
    if not binary: return False
    try:
        result=subprocess.run([binary,'--version'],capture_output=True,timeout=5,**child_options())
        return result.returncode==0
    except (OSError,subprocess.TimeoutExpired): return False


def git_recipe(system=None, which=None, interactive=False):
    system=system or sys.platform
    which=which or (lambda name: shutil.which(name,path=search_path()))
    if system=='win32' and which('winget'):
        return [which('winget'),'install','--id','Git.Git','--exact','--source','winget',
                '--no-upgrade', *([] if interactive else ['--disable-interactivity'])]
    if system=='darwin' and which('brew'): return [which('brew'),'install','git']
    if system=='linux':
        for manager, args in [('apt-get',['install','-y','git']),('dnf',['install','-y','git']),
                              ('pacman',['-S','--needed','--noconfirm','git']),('zypper',['--non-interactive','install','git'])]:
            if which(manager):
                if hasattr(os,'geteuid') and os.geteuid()==0: return [which(manager),*args]
                if which('sudo'): return [which('sudo'), *([] if interactive else ['-n']),which(manager),*args]
    return []


def node_release(system, machine, checksums):
    target={'win32':'win','darwin':'darwin','linux':'linux'}.get(system)
    arch={'amd64':'x64','x86_64':'x64','aarch64':'arm64','arm64':'arm64'}.get(machine.lower())
    if not target or not arch: raise ValueError('This OS or CPU needs manual Node.js installation.')
    suffix=f'-{target}-{arch}.'+('zip' if target=='win' else 'tar.gz')
    matches=[]
    for line in checksums.splitlines():
        match=re.fullmatch(r'([a-f0-9]{64})\s+(node-v22\.\d+\.\d+'+re.escape(suffix)+')',line)
        if match: matches.append((match[2],match[1]))
    if len(matches)!=1: raise ValueError('Official Node.js checksum listing did not match this computer.')
    return matches[0]


def download(url, destination, maximum):
    with urllib.request.urlopen(url,timeout=30) as response:
        final=urllib.parse.urlsplit(response.url)
        if final.scheme!='https' or final.hostname!='nodejs.org': raise ValueError('Unexpected download destination')
        size=0
        with destination.open('wb') as output:
            while chunk:=response.read(128*1024):
                size+=len(chunk)
                if size>maximum: raise ValueError('Node.js download exceeded its size limit')
                output.write(chunk)


def extract_node(archive, destination):
    """Copy regular files only; archive links and special files never execute."""
    total=0
    def target(name):
        parts=PurePosixPath(name).parts
        if '\\' in name or PurePosixPath(name).is_absolute() or any(p in ('..','.') or ':' in p for p in parts):
            raise ValueError('Unsafe Node.js archive path')
        if len(parts)<2: return None
        out=destination.joinpath(*parts[1:])
        if not out.resolve().is_relative_to(destination.resolve()): raise ValueError('Unsafe archive destination')
        return out
    def copy(name, size, source, mode):
        nonlocal total
        out=target(name)
        if out is None: return
        total+=size
        if total>600_000_000: raise ValueError('Expanded Node.js archive is too large')
        out.parent.mkdir(parents=True,exist_ok=True)
        with source, out.open('wb') as output: shutil.copyfileobj(source,output)
        if os.name!='nt': out.chmod(0o755 if mode&0o111 else 0o644)
    if archive.suffix=='.zip':
        with zipfile.ZipFile(archive) as contents:
            for entry in contents.infolist():
                if not entry.is_dir():
                    target(entry.orig_filename)
                    if (entry.external_attr>>16)&0o170000==0o120000: raise ValueError('Archive symlink rejected')
                    copy(entry.filename,entry.file_size,contents.open(entry),entry.external_attr>>16)
    else:
        with tarfile.open(archive,'r:gz') as contents:
            for entry in contents:
                if entry.isfile(): copy(entry.name,entry.size,contents.extractfile(entry),entry.mode)
                elif entry.issym(): target(entry.name)  # npm links are skipped; its JS entry point is used directly.
                elif not entry.isdir(): raise ValueError('Archive special file rejected')


def install_node(progress):
    if node_ready(): return
    home=tools_home(); home.mkdir(parents=True,exist_ok=True)
    target=home/'node-runtime'
    if target.exists(): raise ValueError('The private Node runtime needs repair. Use the official installation guide.')
    with tempfile.TemporaryDirectory(prefix='node-setup-',dir=home) as temporary:
        folder=Path(temporary)
        progress('Downloading the official Node.js checksum list…')
        sums=folder/'SHASUMS256.txt'
        download('https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt',sums,1_000_000)
        name,digest=node_release(sys.platform,platform.machine(),sums.read_text())
        archive=folder/name
        progress('Downloading Node.js for this computer…')
        download('https://nodejs.org/dist/latest-v22.x/'+name,archive,120_000_000)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest: raise ValueError('Node.js checksum failed. Nothing was installed.')
        progress('Verified download. Preparing the private runtime…')
        staged=folder/'runtime'; staged.mkdir()
        extract_node(archive,staged)
        binary=staged/('node.exe' if os.name=='nt' else 'bin/node')
        if not binary.is_file(): raise ValueError('Node.js executable is missing from the archive')
        staged.rename(target)
    if not node_ready(): raise ValueError('Node.js could not run. Use its official installation guide.')


def npm_command(package):
    if package not in PACKAGES.values(): raise ValueError('Unsupported setup package')
    node=node_binary()
    if not node or not node_ready(): raise ValueError('Install Node.js 22 or newer first')
    own=tools_home()/'node-runtime'
    candidates=[own/'node_modules/npm/bin/npm-cli.js',own/'lib/node_modules/npm/bin/npm-cli.js',
                Path(node).parent/'node_modules/npm/bin/npm-cli.js',Path(node).parent.parent/'lib/node_modules/npm/bin/npm-cli.js']
    script=next((p for p in candidates if p.is_file()),None)
    if not script:
        npm=shutil.which('npm',path=search_path())
        if not npm: raise ValueError('npm is missing. Use the Node.js installation guide.')
        from providers import native_command
        args=native_command([npm])
    else: args=[node,str(script)]
    return [*args,'install','--global','--prefix',str(tools_home()),'--registry','https://registry.npmjs.org',
            '--no-audit','--no-fund',package]


class SetupManager:
    def __init__(self, supervisor):
        self.sup=supervisor
        self.lock=threading.Lock()
        self.status={'state':'idle','message':''}
        self.checked=0; self.cached=None

    def inspect(self):
        if self.cached is not None and time.monotonic()-self.checked<15: return self.cached
        system=sys.platform
        label={'win32':'Windows','darwin':'macOS','linux':'Linux'}.get(system,system)
        if system=='linux' and hasattr(platform,'freedesktop_os_release'):
            try: label=platform.freedesktop_os_release().get('PRETTY_NAME','Linux')
            except OSError: pass
        self.cached={'os':label,'git':git_ready(), 'node':node_ready(),
                     'git_auto':bool(git_recipe()),'node_auto':system in ('win32','darwin','linux') and platform.machine().lower() in ('amd64','x86_64','aarch64','arm64')}
        self.checked=time.monotonic()
        return self.cached

    def plan(self, provider):
        if provider not in ('codex','claude','gemini','antigravity'): raise ValueError('Choose a supported AI tool')
        detected=self.inspect()
        tool=next(t for t in self.sup.tool_status() if t['id']==provider)
        missing=[]
        if not detected['git']: missing.append('git')
        if not tool['installed'] and provider in PACKAGES:
            if not detected['node']: missing.append('node')
            missing.append(provider)
        manual=not tool['installed'] and provider not in PACKAGES
        blocked=('git' in missing and not detected['git_auto']) or ('node' in missing and not detected['node_auto']) or manual
        return {'os':detected['os'],'provider':provider,'missing':missing,'names':[NAMES[x] for x in missing],
                'automatic':bool(missing) and not blocked,'ready':not missing and not manual,
                'docs':DOCS.get(provider,tool['docs']), 'status':dict(self.status)}

    def start(self, provider, interactive=False, background=True):
        plan=self.plan(provider)
        if not plan['ready'] and not plan['automatic']: raise ValueError('Use the official installation guide for this computer')
        with self.sup.active_lock:
            if self.sup.store.setting('running') or self.sup.active_proc is not None or self.sup.login_in_progress:
                raise ValueError('Pause work and finish sign-in before installing tools')
            if not self.lock.acquire(blocking=False): raise ValueError('Setup is already running')
        self.status={'state':'working','provider':provider,'message':'Checking this computer…'}
        def progress(message): self.status={'state':'working','provider':provider,'message':message}
        def perform():
            try:
                from providers import environment
                env=environment('custom',tools_home())
                env.update({'HOMEBREW_NO_ANALYTICS':'1','HOMEBREW_NO_AUTO_UPDATE':'1','HOMEBREW_NO_INSTALL_CLEANUP':'1'})
                for item in plan['missing']:
                    progress('Installing '+NAMES[item]+'…')
                    if item=='node': install_node(progress); continue
                    env['PATH']=search_path()
                    if item=='git': command=git_recipe(interactive=interactive)
                    else: command=npm_command(PACKAGES[item])
                    if not command: raise ValueError('A supported package manager is needed')
                    proc=subprocess.Popen(command,env=env,stdin=None if interactive else subprocess.DEVNULL,
                                          stdout=None if interactive else subprocess.DEVNULL,stderr=None if interactive else subprocess.DEVNULL,
                                          **child_options())
                    self.sup.children.add(proc)
                    try: code=proc.wait(timeout=900)
                    finally:
                        from supervisor import stop_tree
                        stop_tree(proc)
                    if code: raise ValueError('Installation needs attention. Open the terminal setup below to see errors or finish OS permission prompts.')
                    if item in PACKAGES:
                        from providers import resolve_executable, native_command
                        executable=resolve_executable({'codex':'codex','claude':'claude','gemini':'gemini'}[item])
                        if not executable: raise ValueError('The vendor executable was not installed')
                        check=subprocess.run(native_command([executable,'--version']),env=env,stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30,**child_options())
                        if check.returncode: raise ValueError('The installed tool could not start')
                os.environ['PATH']=search_path()
                from supervisor import find_codex
                self.sup.binary=find_codex()
                self.cached=None
                self.checked=0
                checked=self.plan(provider)
                if not checked['ready']: raise ValueError('A tool is still missing. Reopen Runquay or use the terminal setup.')
                self.status={'state':'complete','provider':provider,'message':'Tools are ready. Continue to connect your account.'}
            except Exception:
                self.status={'state':'error','provider':provider,'message':'Setup could not finish. Use the terminal setup for OS permissions, or follow the official installation guide.'}
            finally:
                self.cached=None; self.checked=0
                self.lock.release()
                self.sup.wake.set()
        if background: threading.Thread(target=perform,daemon=True).start()
        else: perform()

    def snapshot(self):
        plans={p:self.plan(p) for p in ('codex','claude','gemini','antigravity')}
        for provider, plan in plans.items():
            plan['terminal']=command_display([sys.executable,str(Path(__file__).parent/'runquay.py'),'setup','--provider',provider,'--install'])
        return {'detected':self.inspect(),'plans':plans,'status':dict(self.status)}


def cli(provider, install=False):
    from supervisor import Supervisor
    with tempfile.TemporaryDirectory(prefix='runquay-setup-state-') as temporary:
        sup=Supervisor(Path(temporary))
        try:
            plan=sup.setup.plan(provider)
            print(json.dumps(plan,indent=2))
            if install:
                sup.setup.start(provider,interactive=True,background=False)
                print(sup.setup.status['message'])
                if sup.setup.status['state']!='complete': raise SystemExit(2)
        finally: sup.children.close()
