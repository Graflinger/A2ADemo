#!/usr/bin/env bash
set -euo pipefail

# Install Python dependencies into system Python
pip install --break-system-packages --upgrade pip
pip install --break-system-packages -r TaskExamples/requirements.txt

# Install mermaid CLI for diagram generation
npm install -g @mermaid-js/mermaid-cli
