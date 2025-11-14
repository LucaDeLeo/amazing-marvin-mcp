# Quick Start Guide - Amazing Marvin MCP Server v2.0

## 5-Minute Setup

### Step 1: Get Your API Token (2 minutes)
1. Open Amazing Marvin
2. Visit: https://app.amazingmarvin.com/pre?api=
3. Copy your **API_TOKEN**

### Step 2: Install Dependencies (1 minute)

Using `uv` (recommended):
```bash
cd /path/to/amazing-marvin-mcp
uv venv
uv pip install -r requirements.txt
```

Or with pip:
```bash
pip install mcp[cli] httpx pydantic
```

### Step 3: Test Your Connection (1 minute)
```bash
export AMAZING_MARVIN_API_TOKEN="paste-your-token-here"
.venv/bin/python test_server.py
```

You should see: ✅ All tests passed!

### Step 4: Configure Claude Desktop (1 minute)

**Find your config file:**
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Add this configuration:**
```json
{
  "mcpServers": {
    "amazing-marvin": {
      "command": "/full/path/to/amazing-marvin-mcp/.venv/bin/python",
      "args": ["/full/path/to/amazing-marvin-mcp/amazing_marvin_server.py"],
      "env": {
        "AMAZING_MARVIN_API_TOKEN": "your-actual-token"
      }
    }
  }
}
```

**Important**:
- Use **FULL absolute paths**, not relative paths!
- Use the Python executable from your virtual environment (`.venv/bin/python`)
- Example: `/Users/yourname/amazing-marvin-mcp/.venv/bin/python`

### Step 5: Restart Claude Desktop

Completely quit and restart Claude Desktop.

## Verify It's Working

In Claude, try saying:
```
"Show me my tasks for today"
```

You should see your Amazing Marvin tasks! 🎉

## What's New in v2.0?

This rebuilt server offers:
- **Better Performance**: FastMCP framework for faster, more reliable operations
- **Smarter Errors**: Actionable messages that tell you exactly what to do
- **Dual Formats**: Get responses in Markdown (pretty) or JSON (structured)
- **Tool Prefixes**: All tools now start with `marvin_` to avoid conflicts
- **Enhanced Validation**: Pydantic v2 catches errors before they reach the API
- **Idempotency**: Operations like mark_done can be safely repeated

## Common Issues

### "Module not found" error
```bash
uv venv
uv pip install -r requirements.txt
```

### "Server not connecting"
- Check the path is **absolute** (e.g., `/Users/you/amazing-marvin-mcp/.venv/bin/python` not `~/...` or `./...`)
- Verify your API token is correct (no extra spaces)
- Make sure you restarted Claude Desktop completely
- Check you're using the `.venv/bin/python` executable, not system Python

### "No tasks showing up"
- Enable the API feature in Marvin: Settings → Features/Strategies → API
- Check tasks exist in the Marvin app
- Verify the date is today (or specify a different date)
- Try running `test_server.py` to validate your connection

### "Invalid API token" error
- Re-copy your token from https://app.amazingmarvin.com/pre?api=
- Ensure there are no extra spaces or quotes
- Check you're setting `AMAZING_MARVIN_API_TOKEN` (not `MARVIN_API_TOKEN`)

## Example Commands

Once working, try these:

**View tasks:**
- "What's on my schedule today?"
- "Show me all overdue tasks"
- "List tasks in my Work category"
- "What's due this week?"

**Create tasks:**
- "Add a task to call mom tomorrow"
- "Create a task 'Review budget #Work @urgent ~120 +2024-03-25'"
- "Add 'Buy groceries' with 30 minute estimate"

**Manage tasks:**
- "Mark task [id] as done"
- "Start timer on task [id]"
- "Stop the timer"

**Organize:**
- "What categories do I have?"
- "Show me all my labels"
- "List all unassigned tasks"

## Advanced Features

### Amazing Marvin Shortcuts

Use these in task titles for quick organization:
- `#ProjectName` - Assign to project
- `@label` - Add a label
- `~60` - Set 60-minute time estimate
- `+YYYY-MM-DD` - Set due date
- `^1` - Set priority level

Example:
```
"Create task 'Finish report #Q1Planning @urgent ~120 +2024-03-20'"
```

### Response Formats

Request JSON output for programmatic processing:
```
"Show me today's tasks in JSON format"
```

Or use the default Markdown for pretty, readable output:
```
"Show me today's tasks"  # Uses Markdown by default
```

## Need Help?

Check the full README.md for detailed documentation and troubleshooting.

**Quick Links:**
- Get API Token: https://app.amazingmarvin.com/pre?api=
- API Docs: https://github.com/amazingmarvin/MarvinAPI/wiki
- MCP Docs: https://modelcontextprotocol.io

---

Happy productivity! 🚀

**Version 2.0.0** - Rebuilt with FastMCP
