# Executive Email Assistant (`send_email`)

An executive email assistant and Model Context Protocol (MCP) server for **Antigravity** and **Claude Code** with strict verification before sending.

---

## 1. Core Rules & Behavior

1. **Verify Before Sending:** Never sends an email without explicit user confirmation. Always displays the exact **Recipient**, **Subject Line**, and **Body** first, and asks:
   > *"Should I send this now?"*
2. **Tool Usage:** Only triggers `send_email` after the user replies "Yes" or confirms the draft (`confirmed: true`).
3. **Missing Details:** Asks for missing recipient, core message, or attachments before drafting.

### Writing & Formatting Guidelines
- **Tone:** Professional, clear, polite (matches user's requested tone).
- **Structure:** Short paragraphs (2–3 sentences max), bullet points for lists.
- **Subject Lines:** Specific and under 50 characters.
- **Sign-off:** Clean closing (e.g., *"Best regards, [Name]"*).

---

## 2. Quick Setup

Run the automated installer:

```bash
chmod +x install.sh
./install.sh
```

Or configure manually:

### Environment Configuration
Copy `.env.example` to `~/.config/executive-email/.env` or current directory `.env`:

```bash
mkdir -p ~/.config/executive-email
cp .env.example ~/.config/executive-email/.env
chmod 600 ~/.config/executive-email/.env
```

Fill in your SMTP details:
```ini
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@example.com
```

### Antigravity Setup
Add to `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "executive-email": {
      "command": "python3",
      "args": ["/path/to/send_email/executive_email.py", "mcp"]
    }
  }
}
```

Copy the skill to `~/.gemini/config/skills/executive-email/SKILL.md`.

### Claude Code Setup
Register MCP server globally in Claude Code:

```bash
claude mcp add -s user executive-email python3 /path/to/send_email/executive_email.py mcp
```

Copy slash command to `~/.claude/commands/email.md`.

---

## 3. Usage

### In Antigravity (Chat)
Ask directly in chat:
> *"Draft an email to alex@example.com informing them about tomorrow's deployment."*

The assistant presents the draft with the prompt *"Should I send this now?"*, and only sends when you reply *"Yes"*.

### In Claude Code
Use the slash command or prompt:
```text
/email Send an update to team@example.com about the sprint demo
```

### In Terminal (CLI)
- **Preview a draft:**
  ```bash
  python3 executive_email.py draft --to "user@example.com" --subject "Status Update" --body "Everything is on track."
  ```
- **Send an email (requires `--confirm`):**
  ```bash
  python3 executive_email.py send --to "user@example.com" --subject "Status Update" --body "Everything is on track." --confirm
  ```
- **Test SMTP connection:**
  ```bash
  python3 executive_email.py test
  ```

---

## License
MIT
