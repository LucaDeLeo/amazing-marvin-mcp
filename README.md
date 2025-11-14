# Amazing Marvin MCP Server

> **🌐 Hosted on Smithery** - Install-free access to Amazing Marvin through Claude and other MCP clients

A high-quality Model Context Protocol (MCP) server that connects AI assistants to [Amazing Marvin](https://amazingmarvin.com), the powerful task management and productivity system. Built with **FastMCP** and deployed on **Smithery** for hosted, zero-installation access.

[![Deploy to Smithery](https://smithery.ai/badge)](https://smithery.ai)

## ✨ What's New in v2.0 (Smithery)

**Complete migration to Smithery for hosted deployment:**

- 🌐 **Hosted Infrastructure**: No local installation, Python, or dependencies required
- 🔐 **Secure Configuration**: API tokens managed through Smithery's session config
- 📊 **Usage Monitoring**: Track server usage and performance
- 🚀 **Auto-deployment**: Push to GitHub → Automatic deployment
- 🔄 **Auto-scaling**: Handle multiple concurrent users
- 💪 **Same Power**: All 10 tools with identical functionality

**Technical improvements:**
- FastMCP framework with `@smithery.server()` decorator
- Pydantic V2 validation with session config schemas
- Context-aware API authentication
- Dual response formats (Markdown/JSON)
- Enhanced error handling with actionable guidance

## Quick Start

### For Users

1. **Get your Amazing Marvin API token**
   - Visit https://app.amazingmarvin.com/pre?api=
   - Copy your `API_TOKEN`

2. **Connect via Smithery**
   - Visit: https://smithery.ai/server/amazing-marvin-mcp
   - Click "Connect"
   - Paste your API token when prompted
   - Use in Claude Desktop or other MCP clients

3. **Start using**
   ```
   "Show me my tasks for today"
   "Create a task to review Q4 budget tomorrow"
   "What categories do I have?"
   ```

### For Developers

See [SMITHERY_DEPLOYMENT.md](./SMITHERY_DEPLOYMENT.md) for deployment guide.

**Local testing:**
```bash
uv venv
uv pip install -r requirements.txt
uv run playground
```

## Features

This MCP server provides 10 powerful tools for Amazing Marvin:

### 📋 Task Management
- **marvin_add_task** - Create tasks with full support for scheduling, labels, time estimates, and Amazing Marvin shortcuts
- **marvin_get_todays_tasks** - View all tasks scheduled for today or a specific date
- **marvin_mark_done** - Mark tasks as complete (idempotent)
- **marvin_get_due_tasks** - See all tasks due today or overdue with smart overdue indicators

### 🗂️ Organization
- **marvin_get_categories** - List all your projects and categories with IDs
- **marvin_get_labels** - View all available labels with IDs
- **marvin_get_children** - Browse tasks within a specific project, category, or unassigned area

### ⏱️ Time Tracking
- **marvin_start_tracking** - Start time tracking on a task
- **marvin_stop_tracking** - Stop the currently running timer

### 🎨 Response Formats

All list operations support two output formats:
- **Markdown** (default): Human-readable with headers, emojis, and formatting
- **JSON**: Structured data for programmatic processing

## Usage Examples

### Creating Tasks

```
"Create a task called 'Review Q4 budget' due tomorrow with a 2-hour time estimate"

"Add a task 'Call dentist' with 15 minute estimate and schedule it for Friday"

"Create a task 'Finish presentation slides #Work @urgent ~120 +2024-03-20'"
```

**Amazing Marvin shortcuts in task titles:**
- `#ProjectName` - Assign to project
- `@label` - Add a label
- `~60` - Time estimate (60 minutes)
- `+2024-03-15` - Set due date
- `^1` - Set priority

### Viewing Tasks

```
"Show me my tasks for today"

"What tasks are due today or overdue?"

"List all tasks in my Personal category"

"Show me tasks for March 15, 2024 in JSON format"
```

### Managing Tasks

```
"Mark task task_abc123xyz as complete"

"Start tracking time on task task_abc123xyz"

"Stop the timer"
```

### Organizing

```
"Show me all my categories and projects"

"What labels do I have?"

"List all unassigned tasks"
```

## Technical Details

### Architecture

**Smithery Deployment:**
- Python 3.12+ runtime
- FastMCP framework with `@smithery.server()` decorator
- Context-aware authentication via `ctx.session_config`
- HTTP/SSE transport (not STDIO)

**Configuration:**
```python
class AmazingMarvinConfig(BaseModel):
    api_token: str = Field(
        ...,
        description="Your Amazing Marvin API token. Get it from: https://app.amazingmarvin.com/pre?api=",
        min_length=10
    )
```

**Package Structure:**
```
src/amazing_marvin_mcp/
├── __init__.py          # Package initialization
└── server.py            # Main server with tools
```

### Key Features

- **Pydantic V2 Validation**: Robust input validation with detailed constraints
- **Agent-Centric Design**: Tools optimized for AI workflows, not just API wrappers
- **Dual Response Formats**: Markdown (human-readable) and JSON (machine-readable)
- **Character Limits**: Intelligent handling of large responses (25,000 char limit)
- **Tool Annotations**: Proper hints for read-only, destructive, and idempotent operations
- **Comprehensive Docstrings**: Detailed documentation with examples for every tool

### Error Handling

The server provides actionable error messages:
- **401 Unauthorized**: Guides to check API token configuration
- **404 Not Found**: Suggests verifying IDs and item existence
- **429 Rate Limit**: Advises waiting before retry
- **500 Server Error**: Indicates Amazing Marvin service issues

All errors include specific next steps for resolution.

## Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/LucaDeLeo/amazing-marvin-mcp.git
cd amazing-marvin-mcp

# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt
```

### Testing

```bash
# Use Smithery playground (ngrok port-forwarding)
uv run playground

# Or run in development mode
uv run dev
```

### Building Package

```bash
# Build distribution
python -m build

# Verify build
ls dist/
# Should show: amazing_marvin_mcp-2.0.0-py3-none-any.whl and .tar.gz
```

### Deployment

See [SMITHERY_DEPLOYMENT.md](./SMITHERY_DEPLOYMENT.md) for complete deployment guide.

**Quick deploy:**
1. Push to GitHub: `git push origin main`
2. Go to https://smithery.ai/new
3. Connect repository
4. Click "Deploy"

## API Reference

This server uses Amazing Marvin's Limited Access API:
- **API Documentation**: https://github.com/amazingmarvin/MarvinAPI/wiki
- **Help Center**: https://help.amazingmarvin.com/
- **API Base URL**: `https://serv.amazingmarvin.com/api`

**Endpoints used:**
```
GET  /api/categories       - List all categories/projects
GET  /api/labels          - List all labels
GET  /api/children        - Get items in category
GET  /api/todayItems      - Get scheduled tasks
GET  /api/dueItems        - Get due/overdue tasks
POST /api/addTask         - Create task
POST /api/markDone        - Complete task
POST /api/track           - Start/stop timer
```

## Security Notes

- **API Tokens**: Stored encrypted in Smithery's session config, never in code
- **HTTPS Only**: All communication over TLS 1.2+
- **Input Validation**: Pydantic models prevent injection attacks
- **Limited Access API**: Additional security layer vs Full Access

## Contributing

Potential future enhancements:
- Document update/delete operations (`/api/doc/update`, `/api/doc/delete`)
- Project creation tool (`/api/addProject`)
- Goals integration (`/api/goals`)
- Habit tracking (`/api/habits`, `/api/updateHabit`)
- Reminders management (`/api/reminder/set`)
- Time blocks viewing (`/api/todayTimeBlocks`)
- Tracked item status (`/api/trackedItem`)
- Reward points system

When adding features, follow the same patterns: Pydantic model → `@mcp.tool` decorator → `ctx: Context` parameter → shared utilities → comprehensive docstring.

## Support

**Server Issues**:
- GitHub Issues: https://github.com/LucaDeLeo/amazing-marvin-mcp/issues

**Smithery Platform**:
- Email: support@smithery.ai
- Discord: https://discord.gg/Afd38S5p9A

**Amazing Marvin API**:
- Email: support@amazingmarvin.com

## License

MIT License - See LICENSE file

## Acknowledgments

- Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
- Deployed on [Smithery](https://smithery.ai)
- Powered by [Amazing Marvin](https://amazingmarvin.com)

---

**Version**: 2.0.0 (Smithery Deployment)
**Repository**: https://github.com/LucaDeLeo/amazing-marvin-mcp
**Smithery**: https://smithery.ai/server/amazing-marvin-mcp
