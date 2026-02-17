# A2A Protocol Flow -- Deep Dive

Code, diagrams, and examples for the Medium blog post:
**"Deep Dive Into the A2A Protocol Flow -- Understanding How AI Agents Communicate"**

## What's Inside

A hands-on exploration of the A2A (Agent-to-Agent) protocol's task lifecycle, covering:

- The 9 task states and their transitions
- How **contexts** group multiple tasks into a single conversation
- Multi-turn conversation flow (discovery -> message -> input-required -> completed -> new task in context)
- A working Travel Booking Agent built with the official `a2a-sdk`

## Repository Structure

```
a2a/
├── .devcontainer/
│   ├── devcontainer.json              # Dev container configuration
│   └── post-create.sh                 # Auto-setup script
├── .vscode/
│   └── tasks.json                     # Run tasks (server, client, diagrams)
├── blog.md                            # Full Medium blog post
├── diagrams/
│   ├── task_state_diagram.mmd         # Mermaid source -- task state machine
│   ├── task_state_diagram.png         # Rendered PNG
│   ├── sequence_diagram.mmd           # Mermaid source -- protocol sequence
│   └── sequence_diagram.png           # Rendered PNG
└── TaskExamples/
    ├── requirements.txt               # Python dependencies
    ├── server.py                      # A2A server (Travel Booking Agent)
    └── client.py                      # A2A client (walks through full lifecycle)
```

## Quick Start (Dev Container)

The fastest way to get running -- works with **GitHub Codespaces** or **VS Code Dev Containers**.

1. Open this repo in a dev container (or click "Open in Codespaces" on GitHub)
2. Wait for the automatic setup to complete (installs Python deps + Mermaid CLI)
3. Use VS Code tasks (`Ctrl+Shift+P` → **Tasks: Run Task**):
   - **Start A2A Server** -- launches the Travel Booking Agent on port 9999
   - **Run A2A Client** -- runs the client demo against the server
   - **Regenerate Diagrams** -- rebuilds PNGs from `.mmd` sources

Everything is pre-configured: Python dependencies, port forwarding, extensions, and run tasks.

## Manual Setup

### Prerequisites

- Python 3.10+ (the examples were built/tested with 3.13)
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

## Running the Example

### 1. Install dependencies

```bash
cd TaskExamples

# Using uv (recommended)
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the server

```bash
cd TaskExamples
python server.py
```

The server starts on `http://localhost:9999`. You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:9999 (Press CTRL+C to quit)
```

### 3. Run the client (in a second terminal)

```bash
cd TaskExamples
source .venv/bin/activate
python client.py
```

The client walks through the full A2A task lifecycle:

1. **Discovery** -- fetches the Agent Card from `/.well-known/agent-card.json`
2. **Initial message** -- sends "Book a flight to Paris" and receives an `input-required` response
3. **Multi-turn follow-up** -- provides travel dates and gets a `completed` response with a booking artifact
4. **Task retrieval** -- fetches the task by ID to confirm its final state
5. **New task in same context** -- sends "Book a hotel near the airport in Paris" with the same `contextId` but no `taskId`, creating a second task within the same conversation

## Regenerating Diagrams

If you modify the `.mmd` files, regenerate the PNGs with:

```bash
npx @mermaid-js/mermaid-cli mmdc -i diagrams/task_state_diagram.mmd -o diagrams/task_state_diagram.png -b transparent
npx @mermaid-js/mermaid-cli mmdc -i diagrams/sequence_diagram.mmd -o diagrams/sequence_diagram.png -b transparent
```

## License

MIT
