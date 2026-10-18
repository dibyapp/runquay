"""Exercise durable cross-provider handoffs without making model calls."""
import json
import hashlib
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import orchestration
import providers
from supervisor import Supervisor, Store


class TeamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='runquay-team-')
        self.root = Path(self.temp.name)
        self.sup = Supervisor(self.root/'state', 'fixture-cli')
        self.sup.store.set('running', False)
        self.sup.profile_binary = lambda p: 'fixture-cli'
        for provider in ('codex', 'claude'):
            self.sup.store.execute('INSERT INTO profiles(id,name,home,provider) VALUES(?,?,?,?)',
                                   (provider, 'Example '+provider, str(self.root/provider), provider))

    def tearDown(self):
        self.sup.children.close()
        self.temp.cleanup()

    def request(self, **changes):
        return {'text': 'Create an offline checklist', 'provider': 'auto',
                'team_tools': ['codex', 'claude'], 'request_key': secrets.token_hex(16), **changes}

    def project(self, ident):
        return self.sup.store.one('SELECT * FROM projects WHERE id=?', (ident,))

    def execute(self, ident, status='complete'):
        project = self.project(ident)
        profile = self.sup.store.one('SELECT * FROM profiles WHERE provider=?', (project['provider'],))
        flow = orchestration.load(project)
        result = {'status': status, 'summary': 'Fixture evidence for '+flow['phase'], 'tests': 'Fixture only; no vendor calls',
                  'next_step': 'Fix an example issue' if status == 'continue' else '', 'question': ''}
        real_popen = subprocess.Popen
        class Rpc:
            def close(self): pass
            def call(self, method, params):
                return {'data': [{'isDefault': True, 'model': 'example-model'}]}
        def popen(command, **kwargs):
            if command[0] != 'fixture-cli':
                return real_popen(command, **kwargs)
            if profile['provider'] == 'codex':
                self.assertIn('read-only' if orchestration.readonly(flow) else 'workspace-write', command)
                output = command[command.index('--output-last-message')+1]
                script = 'import sys; from pathlib import Path; sys.stdin.read(); Path(sys.argv[1]).write_text(sys.argv[2],encoding="utf-8")'
                args = [sys.executable, '-c', script, output, json.dumps(result)]
            else:
                self.assertIn('plan', command)
                self.assertIn('Read,Glob,Grep', command)
                args = [sys.executable, '-c', 'import sys;sys.stdin.read();print(sys.argv[1])', json.dumps({'structured_output': result})]
            return real_popen(args, **kwargs)
        with patch('supervisor.subprocess.Popen', side_effect=popen):
            self.sup.run_step(project, profile, Rpc() if profile['provider'] == 'codex' else None)
        return self.project(ident)

    def test_build_is_not_done_before_review_and_handoffs_survive_reload(self):
        request = self.request()
        ident = self.sup.create_request(request)
        self.assertEqual(self.sup.create_request(request), ident)
        self.assertEqual(orchestration.load(self.execute(ident))['phase'], 'build')
        project = self.execute(ident)
        self.assertEqual((project['state'], project['provider']), ('queued', 'claude'))
        Store(self.root/'state')
        self.assertEqual(orchestration.load(self.project(ident))['phase'], 'review')
        profile = self.sup.store.one("SELECT * FROM profiles WHERE id='claude'")
        self.assertFalse(self.sup.select_external(project, profile))
        decision = self.sup.store.one("SELECT * FROM decisions WHERE kind='external_run'")
        self.assertEqual(json.loads(decision['payload'])['phase'], 'review')
        self.sup.decide_external(decision, True)
        self.assertTrue(self.sup.select_external(project, profile))
        self.assertEqual(self.execute(ident)['state'], 'complete')
        history = orchestration.load(self.project(ident))['history']
        self.assertEqual([h['phase'] for h in history], ['plan', 'build', 'review'])
        self.assertEqual([r['provider'] for r in self.sup.store.rows('SELECT * FROM runs ORDER BY started')], ['codex', 'codex', 'claude'])
        self.assertFalse(self.sup.store.setting('running'))

    def test_repair_loop_is_bounded_and_each_review_requires_fresh_approval(self):
        ident = self.sup.create_request(self.request())
        self.execute(ident); self.execute(ident)
        first = self.project(ident)
        profile = self.sup.store.one("SELECT * FROM profiles WHERE id='claude'")
        key = self.sup.external_key(first, profile)
        self.assertEqual(orchestration.load(self.execute(ident, 'continue'))['phase'], 'repair')
        self.assertEqual(orchestration.load(self.execute(ident))['phase'], 'review')
        self.assertNotEqual(self.sup.external_key(self.project(ident), profile), key)
        self.assertEqual(self.execute(ident, 'continue')['state'], 'attention')
        self.assertIsNone(self.sup.pending_project())

    def test_changed_team_and_unsupported_tools_fail_before_creating_files(self):
        for team in (None, ['claude'], ['codex', 'claude', 'gemini']):
            with self.assertRaises(ValueError): self.sup.create_request(self.request(team_tools=team))
        self.assertEqual(self.sup.store.rows('SELECT * FROM projects'), [])
        with self.assertRaises(ValueError): orchestration.team({'antigravity', 'custom'})
        self.assertEqual(orchestration.team({'gemini'})['reviewer'], 'gemini')

    def test_paused_and_stale_selection_never_launch_a_worker(self):
        ident = self.sup.create_request(self.request())
        stale = self.project(ident)
        self.sup.store.execute("UPDATE projects SET guidance='New guidance' WHERE id=?", (ident,))
        profile = self.sup.store.one("SELECT * FROM profiles WHERE id='codex'")
        with patch('supervisor.subprocess.Popen') as spawn:
            self.sup.run_step(stale, profile, None)
            self.sup.store.execute("UPDATE projects SET state='paused',run_requested=0 WHERE id=?", (ident,))
            self.sup.run_step(self.project(ident), profile, None)
            spawn.assert_not_called()

    def test_existing_direct_approval_identity_survives_upgrade(self):
        ident = self.sup.create_request(self.request(provider='claude'))
        p = self.project(ident)
        profile = self.sup.store.one("SELECT * FROM profiles WHERE id='claude'")
        old = [p['id'], p['goal'], p.get('guidance'), p.get('model'), p['steps'], p['failures'],
               profile['id'], profile.get('options'), profile['home']]
        self.assertEqual(self.sup.external_key(p, profile), hashlib.sha256(json.dumps(old).encode()).hexdigest())

    def test_review_adapters_restrict_tools_and_do_not_inherit_builder_model(self):
        for provider in orchestration.SUPPORTED:
            args = providers.command(provider, 'fixture-cli', {'kind':'review','path':str(self.root)},
                                     Path(__file__).resolve().parents[1]/'result-schema.json', self.root/'result')
            self.assertIn('read-only' if provider == 'codex' else 'plan', args)
            self.assertNotIn('bypassPermissions', args)
        ident = self.sup.create_request(self.request())
        self.sup.store.execute("UPDATE projects SET model='builder-only-model' WHERE id=?", (ident,))
        self.execute(ident); self.execute(ident)
        self.assertEqual(self.project(ident)['model'], '')

    def test_claude_limit_selects_next_profile_with_separate_approval(self):
        self.sup.store.execute('INSERT INTO profiles(id,name,home,provider) VALUES(?,?,?,?)',
                               ('claude-2', 'Example second', str(self.root/'claude-2'), 'claude'))
        ident = self.sup.create_request(self.request(provider='claude'))
        project = self.project(ident)
        first = self.sup.store.one("SELECT * FROM profiles WHERE id='claude'")
        real_popen = subprocess.Popen

        def limited_popen(command, **kwargs):
            if command[0] != 'fixture-cli':
                return real_popen(command, **kwargs)
            return real_popen([sys.executable, '-c',
                               'import sys,json;sys.stdin.read();print(json.dumps({"is_error":True,"result":"You have hit your usage limit"}))'],
                              **kwargs)

        self.assertFalse(self.sup.select_external(project, first))
        approval = self.sup.store.one("SELECT * FROM decisions WHERE profile_id='claude' AND kind='external_run'")
        self.sup.decide_external(approval, True)
        second = self.sup.store.one("SELECT * FROM profiles WHERE id='claude-2'")
        self.assertFalse(self.sup.select_external(project, second))
        old_second_approval = self.sup.store.one("SELECT * FROM decisions WHERE profile_id='claude-2' AND kind='external_run'")
        self.sup.decide_external(old_second_approval, True)
        with patch('supervisor.subprocess.Popen', side_effect=limited_popen):
            self.sup.step(project)
        self.assertEqual(self.project(ident)['state'], 'queued')
        self.assertGreater(self.sup.store.one("SELECT limit_until FROM profiles WHERE id='claude'")['limit_until'], 0)
        self.assertEqual(self.sup.store.one('SELECT state FROM runs WHERE project_id=?', (ident,))['state'], 'limited')
        self.assertEqual(self.sup.store.one('SELECT state FROM decisions WHERE id=?', (old_second_approval['id'],))['state'], 'expired')
        with patch.object(self.sup, 'run_step') as launch:
            self.sup.step(self.project(ident))
            launch.assert_not_called()
        next_approval = self.sup.store.one("SELECT * FROM decisions WHERE profile_id='claude-2' AND kind='external_run' AND state='pending'")
        self.assertEqual(next_approval['state'], 'pending')
        self.assertIn('switch_reason', json.loads(next_approval['payload']))
        self.sup.decide_external(next_approval, True)
        with patch.object(self.sup, 'run_step') as launch:
            self.sup.step(self.project(ident))
            self.assertEqual(launch.call_args.args[1]['id'], 'claude-2')
        self.assertFalse(self.sup.store.one("SELECT * FROM profiles WHERE id='claude-2'")['limit_until'])

    def test_only_explicit_claude_errors_trigger_rotation(self):
        self.assertTrue(providers.usage_limit_error('claude', '{"is_error":true,"result":"Rate limit reached"}'))
        self.assertTrue(providers.usage_limit_error('claude', '', ['API Error: 429 rate_limit_error']))
        self.assertFalse(providers.usage_limit_error('claude', '{"result":"Document rate limit handling"}'))
        self.assertFalse(providers.usage_limit_error('gemini', '{"is_error":true,"result":"Rate limit reached"}'))
        self.assertFalse(providers.usage_limit_error('claude', '{"is_error":true,"result":"Permission denied"}'))
