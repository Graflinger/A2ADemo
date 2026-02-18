# A2A Protocol -- Blog Series

Code, diagrams, and examples accompanying the Medium blog series on the A2A (Agent-to-Agent) protocol.

Each part lives in its own folder with a dedicated README covering what's inside and how to run it.

## Parts

| # | Topic | Folder | Blog Post |
|---|-------|--------|-----------|
| 1 | [Task Lifecycle](TaskExamples/README.md) | `TaskExamples/` | [Deep Dive Into the A2A Protocol Flow](https://medium.com/codex/deep-dive-into-the-a2a-protocol-flow-understanding-how-ai-agents-communicate-25dd43be4ec2?sk=81ea89585485398d6fe1df397f25efbe) |

## Quick Start (Dev Container)

The fastest way to get running -- works with **GitHub Codespaces** or **VS Code Dev Containers**.

1. Open this repo in a dev container (or click "Open in Codespaces" on GitHub)
2. Wait for the automatic setup to complete (installs Python deps + Mermaid CLI)
3. Use VS Code tasks (`Ctrl+Shift+P` -> **Tasks: Run Task**) -- each part defines its own run tasks

Everything is pre-configured: Python dependencies, port forwarding, extensions, and run tasks.

## Manual Setup

### Prerequisites

- Python 3.10+ (the examples were built/tested with 3.13)
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

### Install dependencies

From the repository root:

```bash
# Using uv (recommended)
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then head to the part you're interested in and follow its README.

## License

MIT
