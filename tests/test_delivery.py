import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import autowork
from delivery import result_details
from platform_support import open_folder


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = {"name": "Example", "path": str(self.root)}

    def tearDown(self):
        self.temp.cleanup()

    def test_start_here_wins_and_html_is_only_reported_not_run(self):
        (self.root / 'START_HERE.md').write_text('1. Open index.html.', encoding='utf-8')
        (self.root / 'README.md').write_text('Developer notes', encoding='utf-8')
        (self.root / 'index.html').write_text('<script>doNotExecute()</script>', encoding='utf-8')
        (self.root / '.env').write_text('private', encoding='utf-8')
        (self.root / 'credentials.json').write_text('{}', encoding='utf-8')
        result = result_details(self.project)
        self.assertEqual(result['source'], 'START_HERE.md')
        self.assertTrue(result['has_webpage'])
        self.assertEqual(result['instructions'], '1. Open index.html.')
        self.assertNotIn('.env', result['files'])
        self.assertNotIn('credentials.json', result['files'])

    def test_fallback_and_missing_instructions(self):
        self.assertEqual(result_details(self.project)['instructions'], '')
        (self.root / 'README.txt').write_text('<img src=x onerror=alert(1)>', encoding='utf-8')
        self.assertEqual(result_details(self.project)['instructions'], '<img src=x onerror=alert(1)>')

    def test_instruction_size_is_bounded(self):
        (self.root / 'START_HERE.md').write_text('a' * 30000, encoding='utf-8')
        self.assertLess(len(result_details(self.project)['instructions']), 16100)

    def test_symlink_handoff_cannot_read_a_file_outside_project(self):
        outside = self.root / 'outside'
        outside.mkdir()
        target = outside / 'private.txt'
        target.write_text('private content', encoding='utf-8')
        project = self.root / 'project'
        project.mkdir()
        try:
            (project / 'START_HERE.md').symlink_to(target)
        except OSError:
            self.skipTest('Symlink creation is unavailable in this OS session')
        self.assertEqual(result_details({'name':'Example','path':str(project)})['instructions'], '')

    def test_folder_opening_uses_a_known_directory_and_no_shell(self):
        with patch('platform_support.os.startfile', create=True) as start:
            open_folder(self.root, 'win32')
            start.assert_called_once_with(str(self.root.resolve()))
        for system, command in [('darwin','open'), ('linux','xdg-open')]:
            with patch('platform_support.subprocess.Popen') as start:
                open_folder(self.root, system)
                self.assertEqual(start.call_args.args[0], [command,str(self.root.resolve())])
                self.assertNotIn('shell', start.call_args.kwargs)
        with self.assertRaises(ValueError):
            open_folder(self.root / 'missing')

    def test_startup_prerequisites_have_actionable_explanations(self):
        with patch('autowork.sys.version_info', (3,10)), patch('autowork.shutil.which', return_value=None):
            problems = autowork.startup_problems()
            self.assertEqual(len(problems), 2)
            self.assertIn('Python 3.11', problems[0])
            self.assertIn('Install Git', problems[1])
        with patch('autowork.sys.version_info', (3,11)), patch('autowork.shutil.which', return_value='git'):
            self.assertEqual(autowork.startup_problems(), [])
