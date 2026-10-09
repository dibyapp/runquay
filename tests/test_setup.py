import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import install_setup as setup
from supervisor import Supervisor


class SetupTests(unittest.TestCase):
    def test_package_recipes_use_fixed_ids_and_os_permission_boundaries(self):
        def which(name): return '/fixed/'+name if name in ('winget','brew','apt-get','sudo') else ''
        self.assertIn('Git.Git',setup.git_recipe('win32',which))
        self.assertNotIn('--accept-package-agreements',setup.git_recipe('win32',which))
        self.assertEqual(setup.git_recipe('darwin',which),['/fixed/brew','install','git'])
        with patch('install_setup.os.geteuid',return_value=1000,create=True):
            self.assertIn('-n',setup.git_recipe('linux',which))
            self.assertNotIn('-n',setup.git_recipe('linux',which,interactive=True))
        self.assertEqual(setup.git_recipe('unknown',which),[])

    def test_release_selection_rejects_unsupported_cpus_and_names(self):
        digest='a'*64
        listing=f'{digest}  node-v22.17.0-win-x64.zip\n{digest}  node-v22.17.0-linux-arm64.tar.gz'
        self.assertEqual(setup.node_release('win32','AMD64',listing),('node-v22.17.0-win-x64.zip',digest))
        self.assertEqual(setup.node_release('linux','aarch64',listing)[0],'node-v22.17.0-linux-arm64.tar.gz')
        for system,machine in [('linux','unknown'),('unknown','x64'),('darwin','arm64')]:
            with self.assertRaises(ValueError): setup.node_release(system,machine,listing)

    def test_archive_paths_links_and_expansion_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); destination=root/'out'; destination.mkdir()
            for name in ('node/../../escape','node/../escape','node/C:/escape','node\\..\\..\\escape'):
                archive=root/'bad.zip'
                with zipfile.ZipFile(archive,'w') as contents: contents.writestr(name,b'bad')
                with self.assertRaises(ValueError): setup.extract_node(archive,destination)
            archive=root/'good.tar.gz'
            with tarfile.open(archive,'w:gz') as contents:
                entry=tarfile.TarInfo('node/bin/node'); entry.size=2; entry.mode=0o755
                contents.addfile(entry,io.BytesIO(b'ok'))
                entry=tarfile.TarInfo('node/bin/npm');entry.type=tarfile.SYMTYPE;entry.linkname='../../outside'
                contents.addfile(entry)
            setup.extract_node(archive,destination)
            self.assertEqual((destination/'bin/node').read_bytes(),b'ok')
            self.assertFalse((destination/'bin/npm').exists())
            archive=root/'hardlink.tar.gz'
            with tarfile.open(archive,'w:gz') as contents:
                entry=tarfile.TarInfo('node/link');entry.type=tarfile.LNKTYPE;entry.linkname='/outside';contents.addfile(entry)
            with self.assertRaises(ValueError): setup.extract_node(archive,destination)

    def test_checksum_failure_never_installs_download(self):
        with tempfile.TemporaryDirectory() as temporary, patch('install_setup.tools_home',return_value=Path(temporary)), patch('install_setup.node_ready',return_value=False), patch('install_setup.platform.machine',return_value='x86_64'), patch('install_setup.sys.platform','linux'):
            def download(url,path,maximum):
                path.write_bytes((('a'*64)+'  node-v22.17.0-linux-x64.tar.gz').encode() if url.endswith('.txt') else b'wrong archive')
            with patch('install_setup.download',side_effect=download):
                with self.assertRaises(ValueError): setup.install_node(lambda message:None)
            self.assertFalse((Path(temporary)/'node-runtime').exists())

    def test_npm_uses_user_prefix_fixed_registry_and_rejects_arbitrary_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'node-runtime/lib/node_modules/npm/bin/npm-cli.js';script.parent.mkdir(parents=True);script.write_text('fixture')
            with patch('install_setup.tools_home',return_value=root), patch('install_setup.node_binary',return_value='/fixed/node'), patch('install_setup.node_ready',return_value=True):
                args=setup.npm_command('@google/gemini-cli')
                self.assertEqual(args[:2],['/fixed/node',str(script)])
                self.assertIn(str(root),args);self.assertIn('https://registry.npmjs.org',args)
                with self.assertRaises(ValueError): setup.npm_command('untrusted-package')

    def test_setup_guards_and_failed_installs_remain_retryable(self):
        with tempfile.TemporaryDirectory() as temporary:
            sup=Supervisor(Path(temporary),'fixture-codex')
            try:
                ready={'os':'Fixture OS','provider':'codex','ready':True,'automatic':False,'missing':[]}
                with patch.object(sup.setup,'plan',return_value=ready), patch('supervisor.find_codex',return_value='fixture-codex'):
                    sup.store.set('running',True)
                    with self.assertRaises(ValueError): sup.setup.start('codex',background=False)
                    sup.store.set('running',False);sup.login_in_progress=True
                    with self.assertRaises(ValueError): sup.setup.start('codex',background=False)
                    sup.login_in_progress=False
                    sup.setup.start('codex',background=False)
                    self.assertEqual(sup.setup.status['state'],'complete')
                    sup.setup.lock.acquire()
                    with self.assertRaises(ValueError): sup.setup.start('codex',background=False)
                    sup.setup.lock.release()
                missing={**ready,'ready':False,'automatic':True,'missing':['node']}
                with patch.object(sup.setup,'plan',return_value=missing),patch('install_setup.install_node',side_effect=OSError('fixture-private-detail')):
                    sup.setup.start('codex',background=False)
                    self.assertEqual(sup.setup.status['state'],'error')
                    self.assertNotIn('fixture-private-detail',sup.setup.status['message'])
                    self.assertTrue(sup.setup.lock.acquire(blocking=False));sup.setup.lock.release()
                with self.assertRaises(ValueError): sup.setup.plan('arbitrary')
            finally: sup.children.close()

    def test_installed_native_codex_does_not_need_node_or_reinstallation(self):
        with tempfile.TemporaryDirectory() as temporary:
            sup=Supervisor(Path(temporary),'fixture-codex')
            try:
                with patch.object(sup.setup,'inspect',return_value={'os':'Windows','git':True,'node':False,'git_auto':False,'node_auto':False}):
                    plan=sup.setup.plan('codex')
                    self.assertTrue(plan['ready']);self.assertEqual(plan['missing'],[])
                    plan=sup.setup.plan('antigravity')
                    self.assertFalse(plan['automatic'])
            finally: sup.children.close()
