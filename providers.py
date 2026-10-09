"""CLI adapter contracts. Secrets are owned by vendor CLIs, never the dashboard."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from install_setup import search_path, node_binary

TOOLS = {
    "codex": {"name": "Codex", "executable": "codex", "home_var": "CODEX_HOME", "home": ".codex", "advisor": True,
              "docs": "https://learn.chatgpt.com/docs/non-interactive-mode", "billing": "Verified subscription quota and zero paid credits"},
    "claude": {"name": "Claude Code", "executable": "claude", "home_var": "CLAUDE_CONFIG_DIR", "home": ".claude", "advisor": True,
               "docs": "https://code.claude.com/docs/en/cli-reference", "billing": "Quota unverified; one approval per invocation"},
    "gemini": {"name": "Gemini CLI", "executable": "gemini", "home_var": "GEMINI_CLI_HOME", "home": "", "advisor": True,
               "docs": "https://geminicli.com/docs/cli/headless/", "billing": "Quota unverified; one approval per invocation"},
    "antigravity": {"name": "Antigravity CLI", "executable": "agy", "home_var": "", "home": "", "advisor": False,
                    "docs": "https://antigravity.google/docs/cli/headless/", "billing": "Quota unverified; one approval per invocation"},
    "custom": {"name": "Custom CLI", "executable": "", "home_var": "", "home": "", "advisor": False,
               "docs": "", "billing": "Local adapter contract; one approval per invocation"},
}

SECRET_ENV = {"OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_BASE_URL", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
              "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_OAUTH_TOKEN",
              "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_GENAI_USE_VERTEXAI",
              "GOOGLE_GENAI_USE_GCA", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"}


def environment(provider, home):
    env = {k: v for k, v in os.environ.items() if k.upper() not in SECRET_ENV}
    env['PATH'] = search_path()
    # Avoid cross-tool account aliases inherited from the launching process.
    for key in ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "GEMINI_CLI_HOME"):
        env.pop(key, None)
    var = TOOLS[provider]["home_var"]
    if var:
        env[var] = str(home)
    if provider == "custom":
        env["AUTOWORK_PROFILE_HOME"] = str(home)
    return env


def resolve_executable(executable):
    found = shutil.which(executable, path=search_path())
    if found:
        return found
    path = Path(executable).expanduser()
    return str(path.resolve()) if path.is_file() else ""


def native_command(args):
    """Resolve npm .cmd shims to node + JS without cmd.exe interpolation."""
    if os.name != "nt" or Path(args[0]).suffix.lower() not in (".cmd", ".bat"):
        return args
    import re
    shim = Path(args[0])
    text = shim.read_text(encoding="utf-8", errors="replace")
    match = re.search(r'"%dp0%\\([^"\r\n]+\.(?:js|cjs|mjs))"', text, re.I)
    node = node_binary()
    if not match or not node:
        raise ValueError("This Windows CLI wrapper cannot be safely launched. Select the vendor's native executable.")
    script = shim.parent / match.group(1)
    if not script.is_file():
        raise ValueError("The CLI npm entry point is missing; reinstall the vendor CLI")
    return [node, str(script), *args[1:]]


def validate_custom(value):
    if not isinstance(value, list) or not value or len(value) > 40 or any(not isinstance(a, str) or not a or len(a) > 2000 for a in value):
        raise ValueError("Custom command must be a JSON array of 1–40 arguments; no shell command string")
    if any("{prompt}" in a for a in value):
        raise ValueError("Pass prompts through stdin, never command-line arguments")
    return value


def command(provider, executable, project, schema, final_path, model="", custom=None):
    advisor = project.get("kind") == "advisor"
    if advisor and not TOOLS[provider]["advisor"]:
        raise ValueError("This adapter has no enforced read-only advisor mode. Choose Codex, Claude Code, or Gemini CLI.")
    if provider == "codex":
        args = [executable, "exec", "--model", model, "--ignore-user-config", "--sandbox", "read-only" if advisor else "workspace-write", "--json",
                "-c", 'approval_policy="never"', "-c", 'forced_login_method="chatgpt"', "-c", 'model_provider="openai"',
                "--disable", "multi_agent", "--disable", "multi_agent_v2", "--disable", "apps", "--disable", "plugins",
                "--disable", "hooks", "--disable", "computer_use", "--disable", "browser_use", "--disable", "in_app_browser",
                "-c", "sandbox_workspace_write.network_access=true", "-c", "shell_environment_policy.ignore_default_excludes=false",
                "--cd", project["path"], "--output-schema", str(schema), "--output-last-message", str(final_path), "-"]
        if os.name == "nt":
            args[2:2] = ["-c", 'windows.sandbox="unelevated"']
        if not (Path(project["path"]) / ".git").exists():
            args.insert(2, "--skip-git-repo-check")
        return native_command(args)
    if provider == "claude":
        args = [executable, "-p", "--output-format", "json", "--json-schema", Path(schema).read_text(encoding="utf-8"),
                "--permission-mode", "plan" if advisor else "dontAsk", "--max-turns", "30",
                "--tools", "Read,Glob,Grep" if advisor else "Read,Glob,Grep,Edit,Write,Bash",
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--disable-slash-commands", "--no-session-persistence",
                "--setting-sources", "", "--safe-mode"]
        if not advisor:
            args += ["--allowedTools", "Read,Glob,Grep,Edit,Write,Bash(git status *),Bash(git diff *),Bash(python -m unittest *),Bash(npm test *),Bash(npm run build *),Bash(npm run lint *)"]
    elif provider == "gemini":
        # stdin supplies the entire prompt; no yolo/bypass permissions.
        args = [executable, "--output-format", "json", "--approval-mode", "plan" if advisor else "auto_edit", "--sandbox"]
    elif provider == "antigravity":
        args = [executable, "-p", "--output-format", "json", "--json-schema", str(schema), "--sandbox"]
    else:
        args = validate_custom(custom)
        args = [a.replace("{schema}", str(schema)).replace("{workspace}", project["path"]) for a in args]
        args[0] = executable
    if model and provider != "custom":
        args += ["--model", model]
    return native_command(args)


def parse_result(provider, stdout, final_path):
    if provider == "codex":
        return json.loads(Path(final_path).read_text(encoding="utf-8"))
    payload = json.loads(stdout)
    if provider == "claude":
        if payload.get("is_error"):
            raise ValueError("Claude reported an execution error")
        payload = payload.get("structured_output") or payload.get("result") or payload
    elif provider in ("gemini", "antigravity"):
        if payload.get("error") or payload.get("status") in ("ERROR", "CANCELED", "INTERRUPTED", "WAITING"):
            raise ValueError("Provider reported an execution error or permission blocker")
        payload = payload.get("response", payload)
    if isinstance(payload, str):
        value = payload.strip()
        if value.startswith("```json") and value.endswith("```"):
            value = value[7:-3].strip()
        payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("Provider did not return a structured checkpoint object")
    return payload
