#!/usr/bin/env python3
"""
Executive Email Assistant & MCP Server
Handles drafting, validation, and SMTP email sending with strict user verification.
Compatible with both Claude Code and Antigravity.
"""

import sys
import os
import json
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

# Paths to search for .env configuration
CONFIG_DIR = Path.home() / ".config" / "executive-email"
ENV_PATHS = [
    CONFIG_DIR / ".env",
    Path.cwd() / ".env.development",
    Path.cwd() / ".env",
    Path.home() / "code" / "hrms-project" / "hrms-notifications" / ".env.development",
]

def load_env_config():
    """Load SMTP configuration from known env files and environment variables."""
    config = {
        "SMTP_HOST": "",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "FROM_EMAIL": "",
    }
    
    for path in ENV_PATHS:
        if path.exists() and path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("\"'")
                            if k in config and not config[k]:
                                config[k] = v
            except Exception:
                pass

    # Process environment variable overrides
    for k in config.keys():
        if os.environ.get(k):
            config[k] = os.environ[k]
            
    if not config["FROM_EMAIL"] and config["SMTP_USERNAME"]:
        config["FROM_EMAIL"] = config["SMTP_USERNAME"]

    return config

def validate_email_address(email_str):
    """Basic validation for email address format."""
    if not email_str or not isinstance(email_str, str):
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email_str.strip()))

def format_draft(to, subject, body, cc="", bcc=""):
    """Format an email draft and prompt according to Executive Assistant rules."""
    subj_len = len(subject.strip())
    length_warning = ""
    if subj_len > 50:
        length_warning = f" ⚠️ (Warning: {subj_len} chars exceeds recommended 50 chars)"

    lines = [
        "📧 **Executive Email Draft**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"**Recipient (To):** {to.strip()}",
    ]
    if cc:
        lines.append(f"**CC:** {cc.strip()}")
    if bcc:
        lines.append(f"**BCC:** {bcc.strip()}")
    lines.extend([
        f"**Subject Line:** {subject.strip()}{length_warning}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "**Body:**",
        body.strip(),
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "**Should I send this now?**"
    ])
    return "\n".join(lines)

def execute_send_email(to, subject, body, cc="", bcc="", confirmed=False):
    """Send an email via SMTP after verifying all rules and confirmation."""
    if not confirmed:
        draft = format_draft(to, subject, body, cc, bcc)
        return (
            False,
            f"❌ REFUSED TO SEND: Confirmation required.\n\n"
            f"You MUST show this draft to the user and receive their explicit confirmation ('Yes' / 'Send') first:\n\n"
            f"{draft}"
        )

    # Validate recipient
    to_clean = to.strip()
    if not validate_email_address(to_clean):
        return False, f"❌ Invalid recipient email address: '{to_clean}'"

    config = load_env_config()
    host = config["SMTP_HOST"]
    port = int(config.get("SMTP_PORT", 587))
    user = config["SMTP_USERNAME"]
    password = config["SMTP_PASSWORD"]
    from_addr = config.get("FROM_EMAIL") or user

    if not host or not user or not password:
        return False, "❌ Incomplete SMTP configuration. Check SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD."

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_clean
    msg["Subject"] = subject.strip()

    recipients = [to_clean]

    if cc and cc.strip():
        msg["Cc"] = cc.strip()
        recipients.extend([c.strip() for c in cc.split(",") if c.strip()])

    if bcc and bcc.strip():
        recipients.extend([b.strip() for b in bcc.split(",") if b.strip()])

    msg.set_content(body.strip())

    try:
        server = smtplib.SMTP(host, port, timeout=15)
        server.ehlo()
        context = ssl.create_default_context()
        server.starttls(context=context)
        server.ehlo()
        server.login(user, password)
        server.send_message(msg, from_addr=from_addr, to_addrs=recipients)
        server.quit()
        return True, f"✅ Email successfully sent to {to_clean} with subject: '{subject.strip()}'."
    except Exception as e:
        return False, f"❌ Failed to send email via {host}:{port}: {type(e).__name__}: {str(e)}"

# ==============================================================================
# Model Context Protocol (MCP) Server Implementation (Stdio JSON-RPC 2.0)
# ==============================================================================

TOOLS_DEFINITION = [
    {
        "name": "draft_email",
        "description": (
            "Format and preview an email draft according to Executive Assistant guidelines. "
            "Presents the exact Recipient, Subject Line, and Body, checks subject length, "
            "and prompts: 'Should I send this now?'. Call this before sending."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line (under 50 characters)"
                },
                "body": {
                    "type": "string",
                    "description": "Email body (short paragraphs, 2-3 sentences max, bullet points for lists)"
                },
                "cc": {
                    "type": "string",
                    "description": "Optional CC recipient(s), comma-separated"
                },
                "bcc": {
                    "type": "string",
                    "description": "Optional BCC recipient(s), comma-separated"
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "send_email",
        "description": (
            "Send an email via SMTP. "
            "STRICT RULE: Only call this tool AFTER the user has seen the draft "
            "(Recipient, Subject Line, Body) and explicitly answered 'Yes' or confirmed sending. "
            "Parameter 'confirmed' must be set to true."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line (under 50 characters)"
                },
                "body": {
                    "type": "string",
                    "description": "Email body text"
                },
                "cc": {
                    "type": "string",
                    "description": "Optional CC email address"
                },
                "bcc": {
                    "type": "string",
                    "description": "Optional BCC email address"
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "Must be True ONLY when user explicitly confirmed sending. If False, the send will be rejected."
                }
            },
            "required": ["to", "subject", "body", "confirmed"]
        }
    }
]

def run_mcp_server():
    """Run the stdio JSON-RPC MCP server."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue

            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            # Notification methods don't expect a response
            if method == "notifications/initialized":
                continue

            response = {"jsonrpc": "2.0", "id": req_id}

            if method == "initialize":
                response["result"] = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "executive-email",
                        "version": "1.0.0"
                    }
                }
            elif method == "tools/list":
                response["result"] = {
                    "tools": TOOLS_DEFINITION
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "draft_email":
                    to = args.get("to", "")
                    subject = args.get("subject", "")
                    body = args.get("body", "")
                    cc = args.get("cc", "")
                    bcc = args.get("bcc", "")
                    draft_text = format_draft(to, subject, body, cc, bcc)
                    response["result"] = {
                        "content": [{"type": "text", "text": draft_text}],
                        "isError": False
                    }
                elif tool_name == "send_email":
                    to = args.get("to", "")
                    subject = args.get("subject", "")
                    body = args.get("body", "")
                    cc = args.get("cc", "")
                    bcc = args.get("bcc", "")
                    confirmed = bool(args.get("confirmed", False))

                    success, msg = execute_send_email(to, subject, body, cc, bcc, confirmed)
                    response["result"] = {
                        "content": [{"type": "text", "text": msg}],
                        "isError": not success
                    }
                else:
                    response["error"] = {
                        "code": -32601,
                        "message": f"Method '{tool_name}' not found."
                    }
            elif method == "ping":
                response["result"] = {}
            else:
                response["error"] = {
                    "code": -32601,
                    "message": f"Unhandled method '{method}'."
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Executive Email Assistant CLI & MCP Server")
    subparsers = parser.add_subparsers(dest="command")

    # mcp command
    subparsers.add_parser("mcp", help="Run as an MCP stdio server")

    # test command
    subparsers.add_parser("test", help="Test SMTP credentials and connectivity")

    # draft command
    draft_p = subparsers.add_parser("draft", help="Preview an email draft")
    draft_p.add_argument("--to", required=True, help="Recipient email")
    draft_p.add_argument("--subject", required=True, help="Subject line")
    draft_p.add_argument("--body", required=True, help="Body text")
    draft_p.add_argument("--cc", default="", help="CC recipients")
    draft_p.add_argument("--bcc", default="", help="BCC recipients")

    # send command
    send_p = subparsers.add_parser("send", help="Send an email via SMTP")
    send_p.add_argument("--to", required=True, help="Recipient email")
    send_p.add_argument("--subject", required=True, help="Subject line")
    send_p.add_argument("--body", required=True, help="Body text")
    send_p.add_argument("--cc", default="", help="CC recipients")
    send_p.add_argument("--bcc", default="", help="BCC recipients")
    send_p.add_argument("--confirm", action="store_true", help="Explicit user confirmation")

    args = parser.parse_args()

    if args.command == "mcp" or not args.command:
        # Default to mcp if invoked without subcommand or with 'mcp'
        run_mcp_server()
    elif args.command == "test":
        config = load_env_config()
        print(f"Testing SMTP connection to {config['SMTP_HOST']}:{config['SMTP_PORT']} as {config['SMTP_USERNAME']}...")
        try:
            server = smtplib.SMTP(config['SMTP_HOST'], int(config.get('SMTP_PORT', 587)), timeout=10)
            server.ehlo()
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()
            server.login(config['SMTP_USERNAME'], config['SMTP_PASSWORD'])
            print("✅ SMTP connection and authentication SUCCESSFUL!")
            server.quit()
        except Exception as e:
            print(f"❌ SMTP Error: {type(e).__name__}: {e}")
            sys.exit(1)
    elif args.command == "draft":
        print(format_draft(args.to, args.subject, args.body, args.cc, args.bcc))
    elif args.command == "send":
        success, msg = execute_send_email(
            args.to, args.subject, args.body, args.cc, args.bcc, confirmed=args.confirm
        )
        print(msg)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
