Yes. If your goal is to create **one Agent Skills package in the `agentskills.io` / `SKILL.md` format and reuse it across multiple coding agents**, there is a much better structure than creating a separate copy for every tool.

I checked the current documentation for the major agents you listed. The important distinction is between **Agent Skills (`SKILL.md`)** and older agent-specific mechanisms such as `CLAUDE.md`, `.cursor/rules`, Kiro steering, etc.

### Recommended cross-agent location

For a project-level skill, I would use:

```text
your-project/
└── .agents/
    └── skills/
        └── your-skill/
            ├── SKILL.md
            ├── scripts/
            ├── references/
            └── assets/
```

`SKILL.md` is the standardized skill entry point. OpenCode explicitly supports `.agents/skills`, and Kilo and Cursor also support the shared `.agents/skills` convention. ([OpenCode][1])

## AI coding agents — skill locations

| Agent              | Agent Skills support            | **Project skill path**                                                             | **Global skill path**                                                  | Best shared location                 |
| ------------------ | ------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------ |
| **Claude Code**    | ✅ `SKILL.md`                    | `.claude/skills/<skill>/SKILL.md`                                                  | `~/.claude/skills/<skill>/SKILL.md`                                    | `.claude/skills` or `.agents/skills` |
| **GitHub Copilot** | ✅ `SKILL.md`                    | `.github/skills/<skill>/SKILL.md`                                                  | Depends on Copilot surface/config                                      | `.github/skills`                     |
| **Cursor**         | ✅ `SKILL.md`                    | `.cursor/skills/<skill>/SKILL.md`                                                  | `~/.cursor/skills/<skill>/SKILL.md`                                    | `.agents/skills`                     |
| **Windsurf**       | ✅ Agent Skills                  | `.windsurf/skills/<skill>/SKILL.md` / shared `.agents/skills` depending on version | Agent-specific                                                         | `.agents/skills` where supported     |
| **Kilo Code**      | ✅ `SKILL.md`                    | `.kilo/skills/<skill>/SKILL.md`                                                    | `~/.kilo/skills/<skill>/SKILL.md`                                      | **`.agents/skills`**                 |
| **Kiro**           | ✅ Agent Skills                  | `.kiro/skills/<skill>/SKILL.md`                                                    | `~/.kiro/skills/<skill>/SKILL.md`                                      | `.kiro/skills`                       |
| **OpenCode**       | ✅ `SKILL.md`                    | `.opencode/skills/<skill>/SKILL.md` **or `.agents/skills`**                        | `~/.config/opencode/skills/<skill>/SKILL.md` **or `~/.agents/skills`** | **`.agents/skills`**                 |
| **OpenAI Codex**   | ✅ `SKILL.md`                    | `.agents/skills/<skill>/SKILL.md`                                                  | `~/.agents/skills/<skill>/SKILL.md`                                    | **`.agents/skills`**                 |
| **Gemini CLI**     | ✅ Agent Skills                  | `.agents/skills/<skill>/SKILL.md`                                                  | `~/.agents/skills/<skill>/SKILL.md`                                    | **`.agents/skills`**                 |
| **Cline**          | ✅ Agent Skills                  | `.agents/skills/<skill>/SKILL.md`                                                  | Agent-specific                                                         | `.agents/skills`                     |
| **Roo Code**       | ✅ Agent Skills                  | `.agents/skills/<skill>/SKILL.md`                                                  | Agent-specific                                                         | `.agents/skills`                     |
| **Amp**            | ✅ Agent Skills                  | `.agents/skills/<skill>/SKILL.md`                                                  | Agent-specific                                                         | `.agents/skills`                     |
| **Goose**          | ✅ Agent Skills                  | Agent-specific/shared skills locations                                             | Agent-specific                                                         | Check current Goose config           |
| **OpenHands**      | Partial/implementation-specific | Agent-specific                                                                     | Agent-specific                                                         | Don't rely solely on `.agents`       |
| **Devin**          | Skills/workflows                | Platform-specific                                                                  | Platform-specific                                                      | Don't treat as filesystem-compatible |
| **Replit Agent**   | Agent-specific                  | Platform-specific                                                                  | Platform-specific                                                      | Don't treat as filesystem-compatible |
| **Bolt**           | Agent-specific                  | Platform-specific                                                                  | Platform-specific                                                      | Don't treat as filesystem-compatible |
| **Lovable**        | Agent-specific                  | Platform-specific                                                                  | Platform-specific                                                      | Don't treat as filesystem-compatible |

The standardized format itself is essentially:

```text
skill-name/
└── SKILL.md
```

with YAML frontmatter containing at least `name` and `description`. OpenCode, Kiro and Kilo explicitly document this structure. ([OpenCode][1])

---

# The important part for YOUR setup

You mentioned:

* GitHub Copilot
* Claude Code
* Cursor
* Windsurf
* Kilo
* Kiro
* OpenCode
* "command code" — I assume you mean **Claude Code**
* and potentially other agents you're using

I would **not** maintain 7–8 copies of the same skill.

Instead, structure your repository like this:

```text
my-project/
│
├── .agents/
│   └── skills/
│       ├── api-testing/
│       │   ├── SKILL.md
│       │   ├── references/
│       │   └── scripts/
│       │
│       ├── playwright-testing/
│       │   └── SKILL.md
│       │
│       └── test-case-generation/
│           └── SKILL.md
│
├── .github/
│   └── skills/             # Copilot-specific mirror/config if required
│
├── .claude/
│   └── skills/             # Claude-specific mirror if required
│
├── .cursor/
│   └── skills/             # Cursor-specific mirror if required
│
├── .kiro/
│   └── skills/             # Kiro-specific
│
└── .opencode/
    └── skills/             # OpenCode-specific, optional
```

But there is an even cleaner option.

## ⭐ My recommendation: use `.agents/skills` as your canonical source

```text
my-project/
└── .agents/
    └── skills/
        └── playwright-testing/
            └── SKILL.md
```

Then your canonical skill is:

```text
.agents/skills/playwright-testing/SKILL.md
```

### Why?

OpenCode explicitly searches:

```text
.agents/skills/<name>/SKILL.md
```

both at project level and globally:

```text
~/.agents/skills/<name>/SKILL.md
```

It also supports `.claude/skills` and `.opencode/skills`. ([OpenCode][1])

Kilo explicitly supports `.agents/skills` as a compatibility directory. ([Kilo][2])

Cursor supports `.agents/skills` in addition to `.cursor/skills`. ([Learn Cursor][3])

This is why `.agents/skills` is currently the most useful **portable location**.

---

# If you want ONE global folder

If you want the skill available across projects rather than committed into every Git repository, use:

```text
~/.agents/skills/
```

For example on macOS/Linux:

```text
~/.agents/
└── skills/
    └── playwright-testing/
        └── SKILL.md
```

So:

```text
~/.agents/skills/playwright-testing/SKILL.md
```

This is particularly attractive for **OpenCode + Codex + other Agent Skills-compatible agents**.

OpenCode officially supports:

```text
~/.agents/skills/<name>/SKILL.md
```

as a global location. ([OpenCode][1])

---

# Agent-specific paths

There are some important exceptions.

### Claude Code

Claude Code's native location is:

```text
.claude/skills/<skill>/SKILL.md
```

or globally:

```text
~/.claude/skills/<skill>/SKILL.md
```

So if you want the most conservative Claude-only setup:

```text
~/.claude/skills/my-skill/SKILL.md
```

The Agent Skills format is still the same `SKILL.md`.

### Cursor

Native:

```text
.cursor/skills/<skill>/SKILL.md
```

Global:

```text
~/.cursor/skills/<skill>/SKILL.md
```

Cursor also supports `.agents/skills`, which makes it useful for portability. ([Learn Cursor][3])

### Kilo

Native:

```text
.kilo/skills/<skill>/SKILL.md
```

Global:

```text
~/.kilo/skills/<skill>/SKILL.md
```

But Kilo explicitly loads the compatibility directory:

```text
.agents/skills/
```

So you don't need a Kilo-specific copy if you're using the shared structure. ([Kilo][2])

### Kiro

Kiro's native paths are:

```text
.kiro/skills/<skill>/SKILL.md
```

and:

```text
~/.kiro/skills/<skill>/SKILL.md
```

Kiro officially supports the Agent Skills standard, so your existing `SKILL.md` can be imported without rewriting the skill format. ([Kiro][4])

### OpenCode

OpenCode gives you several options:

```text
.opencode/skills/<skill>/SKILL.md
```

```text
.claude/skills/<skill>/SKILL.md
```

```text
.agents/skills/<skill>/SKILL.md
```

and globally:

```text
~/.config/opencode/skills/<skill>/SKILL.md
```

```text
~/.claude/skills/<skill>/SKILL.md
```

```text
~/.agents/skills/<skill>/SKILL.md
```

This is officially documented by OpenCode. ([OpenCode][1])

---

# GitHub Copilot is the main exception

For GitHub Copilot's Agent Skills, the documented repository location is:

```text
.github/skills/<skill>/SKILL.md
```

Copilot automatically decides whether a skill is relevant based on its description and injects `SKILL.md` into the agent context when selected. ([GitHub Docs][5])

So if **Copilot is important to you**, you have two practical approaches:

### Option A — portability first

```text
.agents/skills/my-skill/SKILL.md
```

and use agents that recognize the shared directory.

### Option B — maximum compatibility

Keep the canonical skill in Git and expose/copy it into each agent's native location:

```text
.agents/skills/my-skill/SKILL.md
.github/skills/my-skill/SKILL.md
.claude/skills/my-skill/SKILL.md
.cursor/skills/my-skill/SKILL.md
.kiro/skills/my-skill/SKILL.md
.opencode/skills/my-skill/SKILL.md
```

I prefer **Option A + agent-specific adapters only where necessary**.

---

# My recommended architecture for you

Since you're working across many AI coding agents, I'd standardize your repository like this:

```text
.ai/
├── skills/
│   ├── playwright/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/
│   │
│   ├── selenium/
│   │   └── SKILL.md
│   │
│   ├── api-testing/
│   │   └── SKILL.md
│   │
│   └── test-case-generation/
│       └── SKILL.md
│
.agents/
└── skills/
    ├── playwright/
    │   └── SKILL.md
    ├── selenium/
    │   └── SKILL.md
    ├── api-testing/
    │   └── SKILL.md
    └── test-case-generation/
        └── SKILL.md
```

But actually, **don't use `.ai/skills` as the discovery location**. Make `.agents/skills` the actual canonical discovery directory.

So the simplest version is:

```text
project/
└── .agents/
    └── skills/
        ├── skill-1/
        │   └── SKILL.md
        ├── skill-2/
        │   └── SKILL.md
        └── skill-3/
            └── SKILL.md
```

Then:

```text
OpenCode       → .agents/skills
Claude Code    → .agents/skills / .claude/skills
Cursor         → .agents/skills / .cursor/skills
Kilo           → .agents/skills / .kilo/skills
Codex          → .agents/skills
Kiro           → .kiro/skills
Copilot        → .github/skills
```

**Bottom line:** If your priority is **OpenCode + Claude Code + Cursor + Kilo + Codex + other Agent Skills-compatible agents**, put your canonical skills in:

```text
.agents/skills/<skill-name>/SKILL.md
```

For a global installation:

```text
~/.agents/skills/<skill-name>/SKILL.md
```

OpenCode officially recognizes both project and global `.agents/skills` locations. ([OpenCode][1])

One caution: don't blindly install third-party `SKILL.md` files. Skills are executable behavioral instructions and can include scripts/references; recent research has identified supply-chain and prompt-injection risks in skill ecosystems. ([arxiv.org][6])

[1]: https://opencode.ai/docs/skills?utm_source=chatgpt.com "Agent Skills | OpenCode"
[2]: https://kilo.ai/docs/customize/skills?utm_source=chatgpt.com "Skills"
[3]: https://www.learncursor.dev/learn/cursor-agents/cursor-agent-skills?utm_source=chatgpt.com "Cursor Agent Skills: How to Use and Create Reusable Agent Commands · Learn Cursor"
[4]: https://kiro.dev/docs/skills/?utm_source=chatgpt.com "Agent Skills - IDE - Docs - Kiro"
[5]: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills?utm_source=chatgpt.com "Adding agent skills for GitHub Copilot - GitHub Docs"
[6]: https://arxiv.org/abs/2606.16287?utm_source=chatgpt.com "Dynamic Malicious Skills in Agentic AI"

