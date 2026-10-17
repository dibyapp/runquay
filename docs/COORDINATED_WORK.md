# One request, a coordinated team

In **Create**, describe what you want. **Auto team** shows the tools that will work on it before you send. Runquay saves the plan, hands the same workspace to the builder, and requests a review before declaring the workflow finished. Open **View handoffs** on a task to see the reports and checks.

Choose a named tool under **Change AI** when you want a direct run instead. Existing tasks retain their selected tool and are not converted to coordinated work.

## How tools are selected

Auto team uses enabled connections with available executables. It prefers Codex, then Claude Code, then Gemini CLI for planning and building. The next available provider reviews the result; with only one supported provider, that tool performs a separate review. This is a deterministic preference, not a claim that a model is best for every task. Account sign-in and allowance are checked by the existing execution gates.

The displayed team is fixed into the request. If connections change before submission, the server rejects the changed team and asks you to review it. A missing or disabled connection pauses progress until it is restored; another provider is not silently substituted. Antigravity and custom adapters remain available for direct tasks but are excluded from Auto team because Runquay does not verify their read-only review contract.

## What happens after sending

1. **Plan:** inspect the project and propose implementation steps and acceptance checks.
2. **Build:** implement the goal and run appropriate checks. Intermediate milestones retain their checkpoint.
3. **Review:** inspect the actual files against the original goal, plan and reported evidence. A second provider gets the same project workspace and bounded prior handoffs, not unrelated chat histories or account credentials.
4. **Improve, if needed:** one repair cycle returns findings to the builder and then runs another review. If issues remain, the task needs your input. The existing milestone and time caps also apply.

Follow-up requests return a finished task to the builder. Pause and Stop apply to the whole task. No two stages write to its workspace simultaneously. Runquay stores the workflow locally and does not require you to copy reports between tools. Conversations and reports identify the provider that actually handled each run, even after the current task moves to another tool.

## Permissions, billing and limits

Planning and review use the supported adapters’ read-only or plan modes. A review is an inspection, not proof that every test was executed: reviewers must distinguish inspected evidence from checks they could run. Builds retain the normal workspace permissions. Runquay does not ask providers to spawn uncontrolled agents or launch another AI CLI themselves.

Every external-provider invocation still needs its own billing approval. Codex keeps its subscription quota and zero-paid-credit checks. Auto team does not buy credits, approve resets, publish, install software or change account settings. More stages mean more invocations and can use more of your provider allowance.

Handoffs are model-generated evidence and may be incomplete or wrong. Read the reports and try the result before relying on it. Auto team does not synchronize complete native conversations or control arbitrary vendor desktop interfaces.

The adapters use documented programmatic interfaces: [Codex non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode), [Claude Code programmatic execution](https://code.claude.com/docs/en/headless), and [Gemini CLI headless mode](https://geminicli.com/docs/cli/headless/). Tool logos identify the connected providers; Runquay remains an independent project.
