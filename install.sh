#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/executive-email"
BIN_DIR="$HOME/.local/bin"

echo "=== Installing Executive Email Assistant ==="

# 1. Config directory & env
mkdir -p "$CONFIG_DIR" "$BIN_DIR"
if [ ! -f "$CONFIG_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        cp "$SCRIPT_DIR/.env" "$CONFIG_DIR/.env"
    else
        cp "$SCRIPT_DIR/.env.example" "$CONFIG_DIR/.env"
        echo "Created $CONFIG_DIR/.env from template. Please update with your SMTP credentials."
    fi
    chmod 600 "$CONFIG_DIR/.env"
fi

# 2. Symlink CLI
chmod +x "$SCRIPT_DIR/executive_email.py"
ln -sf "$SCRIPT_DIR/executive_email.py" "$BIN_DIR/executive-email"
echo "Linked executive-email to $BIN_DIR/executive-email"

# 3. Antigravity Skill
GEMINI_SKILLS="$HOME/.gemini/config/skills/executive-email"
mkdir -p "$GEMINI_SKILLS"
if [ -f "$SCRIPT_DIR/skills/executive-email/SKILL.md" ]; then
    cp "$SCRIPT_DIR/skills/executive-email/SKILL.md" "$GEMINI_SKILLS/SKILL.md"
    echo "Installed Antigravity skill to $GEMINI_SKILLS/SKILL.md"
fi

# 4. Claude Code Slash Command
CLAUDE_CMD_DIR="$HOME/.claude/commands"
mkdir -p "$CLAUDE_CMD_DIR"
if [ -f "$SCRIPT_DIR/claude/commands/email.md" ]; then
    cp "$SCRIPT_DIR/claude/commands/email.md" "$CLAUDE_CMD_DIR/email.md"
    echo "Installed Claude Code command to $CLAUDE_CMD_DIR/email.md"
fi

# 5. Register with Claude Code MCP if claude is installed
if command -v claude &>/dev/null; then
    echo "Registering MCP server with Claude Code..."
    claude mcp add -s user executive-email python3 "$SCRIPT_DIR/executive_email.py" mcp || true
fi

echo "=== Installation complete ==="
