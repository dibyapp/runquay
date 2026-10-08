# Runquay: market, naming and discovery research

Research date: **8 October 2026**. Decision: rename the public product from AutoWork to **Runquay**. Descriptor: **Open-source AI coding agent orchestrator**. Tagline: **Your agents. One local queue.**

## Method and limits

Reviewed public project READMEs, vendor issue reports, a research lab's published investigation, exact-name web searches, and official discovery guidance. Competitor capabilities below are their maintainers' descriptions, not hands-on comparative tests. Issues describe individual experiences at specific versions; they do not establish prevalence or current defects. Search results and repository topics reveal vocabulary and competition, not Google query counts. No paid keyword dataset, Search Console property, controlled user study, domain registration check, or trademark clearance was available. No traffic or star forecast is justified.

## What already exists

| Project | Position and public evidence | Implication for Runquay |
| --- | --- | --- |
| [Claude Squad](https://github.com/smtg-ai/claude-squad) | Terminal management for several coding agents; tmux sessions and Git worktrees. Roughly 8.6k stars shown during research. | Multi-tool session management already has substantial public attention. Our browser onboarding and native Windows process handling are different implementation choices. |
| [Happy](https://github.com/slopus/happy) | Desktop and mobile control for coding agents. Roughly 24.1k stars shown during research. | Remote access is an established use case. Runquay currently serves one local user and does not offer phone access. |
| [Cezar](https://github.com/open-mercato/cezar) | Multi-agent orchestration locally or on a server, worktree isolation and queued tasks. 530 stars shown during research. | Multi-provider queues and continuous operation are occupied territory. Avoid claiming to invent this category. |
| [Runstead](https://github.com/runstead/runstead) | Long-running work with checkpoints, evidence contracts and explicit governance levels. | Checkpointing and governance are also established. Simpler setup is a hypothesis to test, not a proven unique advantage. |
| [PatchRelay](https://github.com/krasnoperov/patchrelay/blob/main/docs/merge-queue.md) | Developer workflow tooling with a documented merge queue. | Another adjacent queue product; its name is unavailable for a distinctive identity. |

Star counts are rounded page snapshots, not active-user counts, adoption rates, or proof that a particular name caused success. Runquay has not benchmarked these tools against its own implementation.

**Conclusion:** the opportunity is a focused experience for a solo developer managing existing repositories on one computer: guided setup, one persistent queue, explicit decisions, bounded milestones and readable handoffs. This combination can be useful without being unprecedented. Whether users prefer it remains unvalidated.

## Where workflows fail

1. **Work becomes unobservable.** A [Claude Code issue](https://github.com/anthropics/claude-code/issues/52580) describes an optimizer continuing after compaction while its task handle and incremental results were unavailable. It was closed as not planned. Product response: surface milestone state and write durable checkpoint files; do not imply preservation of vendor conversation history.
2. **Quota timing disrupts planning.** A [Codex user report](https://github.com/openai/codex/issues/16423) describes scheduling deferred work around usage windows and being surprised by resets; it was closed as a duplicate. Product response: show observed quota and reset decisions. Polling cannot predict provider changes or guarantee an atomic spending cutoff.
3. **Wrapper and CLI versions drift.** [Claude Squad's FAQ](https://github.com/smtg-ai/claude-squad#faqs) documents a session-start timeout and recommends updating the underlying tool. Product response: keep detection, installed-version evidence, compatibility notes and useful blockers visible. Our adapters can drift too.
4. **Running successfully is different from being correct.** [Columbia DAPLab](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html) reports suppressed errors, incorrect business rules and codebase-awareness problems in its investigation of 15+ apps, tested as of November 2025. This is an exploratory study, not a measured failure rate for today's tools. Product response: require concrete acceptance criteria and user review. Runquay's agent-reported completion is not an independent quality certification.

Our launch risks include unverified live integrations beyond Codex, no real macOS runtime test yet, no long-duration reliability study, approval interruptions for tools with unknown billing, and dependence on the machine staying awake. Naming cannot solve these. See [VERIFICATION.md](VERIFICATION.md).

## Search language to target

These are **intent hypotheses**, derived from project wording, topics and the issues above. They are not measured popular queries. Priorities reflect product fit and specificity, not volume or keyword difficulty.

| Priority | Query family / candidate phrases | Reader need | Useful content |
| --- | --- | --- | --- |
| 1 | AI coding agent orchestrator; local AI coding dashboard | Understand the category | README title, opening explanation and real workflow demo |
| 1 | Codex task queue; Codex automation; Codex quota management | Organize subscription work | Queue tutorial explaining reserve, observed limits and approvals |
| 1 | Claude Code task scheduler; Claude Code dashboard | Queue CLI tasks | Setup guide with current per-invocation approval limits |
| 1 | self-hosted AI coding tools; Windows AI coding agent manager | Run on an existing computer | Installation steps and actual platform verification matrix |
| 2 | resume AI coding tasks; coding agent checkpoints | Recover interrupted work | Worked example using a checkpoint; distinguish files from transcripts |
| 2 | Gemini CLI automation; multiple AI coding tools | Connect an existing tool | Adapter guide with verified/contract-only status |
| 2 | Codex Claude Code workflow | Use different tools across projects | Explicit per-task selection; never imply automatic cross-tool context transfer |
| 3 | Antigravity CLI automation | Find compatible CLI integration | Clearly distinguish editor from CLI and state unverified capabilities |

Provider terms already appear in [competitor topics](https://github.com/open-mercato/cezar) and descriptions. [GitHub's topic guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics) supports describing the real project with relevant topics. [Google's content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) favors useful, original explanations with descriptive titles over content produced mainly for rankings.

Use the category phrase in the README title, provider names in the support table, and problem phrases in tutorials that actually solve them. No keyword stuffing, unsupported "best" claims, fabricated reviews, or unrelated tool lists. The loopback dashboard is not the public SEO surface; search discovery will depend on the published repository and any future public docs site.

## Naming decision

| Candidate | Research result | Decision |
| --- | --- | --- |
| AutoWork | [AUTOWORK DIGITAL](https://www.autowork.com/) already operates in IT; the name is also a broad automation phrase. | Replace public brand. |
| Runstead | [Existing directly adjacent agent control plane](https://github.com/runstead/runstead). | Reject. |
| PatchRelay | [Existing developer queue product](https://github.com/krasnoperov/patchrelay/blob/main/docs/merge-queue.md). | Reject. |
| Patchloom | [Existing structured editing tool for AI agents](https://github.com/patchloom/patchloom). | Reject. |
| Keelshift | [Existing subscription intelligence software](https://www.keelshift.com/). | Reject. |
| Runwisp | [Existing self-hosted scheduler and supervisor](https://docs.runwisp.com/). | Reject. |
| Runquay | Exact and software-qualified searches surfaced unrelated text/OCR matches, with no obvious exact software product match in reviewed results. | Choose, subject to publication-time name/handle/domain and trademark checks. |

Searches included quoted candidate names plus `software`, `AI`, `GitHub`, `npm` and `PyPI`, and a follow-up exact-name search. This is a bounded collision screen, not an exhaustive registry search. An absent result does not prove availability. No name, handle, package or domain has been reserved.

**Why Runquay:** seven letters, provider-neutral, a visual idea of work arriving at a quay, and a useful connection to runs and queues. Pronounce **RUN-key**; show that once in the brand guide because "quay" is not obvious to every reader. The descriptive subtitle must carry category recognition. Its spelling is a tradeoff: test unaided recall and pronunciation with prospective users before buying a domain or commissioning merchandise.

## Earn attention with evidence

Lead with a 45–60 second demonstration: connect an existing repository, queue one bounded goal, show the checkpoint, pause, and resume. Use disposable example projects and synthetic accounts for shared media. Make installation and first useful completion easy to reproduce.

Publish a small set of original guides matching the query families above. Invite specific feedback about installation failures and interrupted work. Announce once in relevant communities after checking their rules; do not send unsolicited messages or spam issue trackers. Offer a simple star request after readers have seen a useful demo, with no incentive or purchased engagement.

Before launch, recruit a small voluntary pilot cohort. Track first-run completion, first useful milestone, return use, reproducible bugs and contributions. Repository traffic and stars are secondary signals. Use optional feedback and public GitHub aggregates; do not add silent product telemetry. Review query hypotheses using real Search Console data only after a public docs property exists.
