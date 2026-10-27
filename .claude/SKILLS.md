# Project skills

Claude Code skills in `.claude/skills/`, committed so every team member's Claude session (robot or Mac) has
them. Chosen 2026-10-26. Licences: `THIRD-PARTY-LICENSES.md`.

| Skill | Source | Use it for |
| :--- | :--- | :--- |
| `slop-prose` | petergyang/no-ai-slop via KornLabs/truss | edit or audit our docs and slide text for AI patterns, keeping our voice |
| `slop-humanizer` | blader/humanizer via KornLabs/truss | the stricter rewrite pass. Use one of the two per text, not both (they over-correct together) |
| `slop-diagrams` | cathrynlavery/diagram-design via KornLabs/truss | static diagrams and charts (HTML/SVG/PNG) for the slides: state machine, system flow, results. Imports Mermaid |
| `diagrams-archify` | tt-a1i/archify via KornLabs/truss | the explorable code visualization: architecture (perception -> decision -> control) and lifecycle (state machine), with links to file and line |
| `systematic-debugging` | obra/superpowers | root cause before a fix (driving problems, model regressions); matches our "rule out the code first" lessons (AB1) |
| `verification-before-completion` | obra/superpowers | evidence before "done": a step is approved only after a test run (CLAUDE.md 6.1) |

## Running Archify

Archify needs Node 18 or newer, and the robot (Ubuntu 18.04, glibc 2.27) cannot run it. `scripts/archify.sh`
runs it in the official `node:20-bookworm-slim` container (pulled 2026-10-26). Validation, rendering and the
strict check pass there; the in-browser check is skipped (no Chrome in the container). For a visual check, open
the HTML in a browser. On the Mac with Node installed, call `node .claude/skills/diagrams-archify/bin/archify.mjs`
directly.

## Not installed, and why

| Candidate | Reason |
| :--- | :--- |
| Truss engine (`.truss/`, `AGENTS.md`, `VISION.md`, `state/`) | Needs Node 20 on the host; duplicates our `DECISIONS.md`, `HANDOVER.md`, `GOAL.md`, `PLAN.md`. Only its skills were taken |
| superpowers as a whole plugin | Its mandatory workflows conflict with CLAUDE.md: feature branches and worktrees (we work on `master`), autonomous subagent runs (we approve every step), TDD that deletes code written before a test |
| Design plugins (impeccable, taste-skill, ui-ux-pro-max) | Made for web UI and landing pages. Slides come from the built-in `pptx` skill or Claude's slide artifacts, charts from the built-in `dataviz` skill. ui-ux-pro-max also reads `.env` files |
| Third-party computer-vision / PyTorch skills from skill registries | Generic advice, sources not verifiable; our pipeline and its decisions are already documented |
| Truss marketing, SEO, sales, code-* groups | Not relevant to a robot project |

## Notes

- Imported skill files are kept verbatim (licence, easy update), so a few contain emoji. The no-emoji rule
  (CLAUDE.md 10) applies to everything we write, including text these skills produce.
- `slop-diagrams` asks once about a style guide before its first diagram; it may then edit its own
  `references/style-guide.md`.
- Update: re-copy from the upstream repositories and keep the header line after each `SKILL.md` frontmatter.
