# Amazing Marvin MCP Server

A high-quality Model Context Protocol (MCP) server that connects AI assistants like Claude to Amazing Marvin, the powerful task management and productivity system. Built with **FastMCP** following MCP best practices for agent-centric design.

## ✨ What's New in v2.0

This server has been rebuilt from the ground up using **FastMCP** with modern best practices:

- **FastMCP Framework**: Cleaner, more maintainable code with decorator-based tool registration
- **Pydantic V2 Validation**: Robust input validation with detailed constraints and error messages
- **Agent-Centric Design**: Tools optimized for AI workflows, not just API wrappers
- **Dual Response Formats**: Both Markdown (human-readable) and JSON (machine-readable) support
- **Enhanced Error Handling**: Actionable, educational error messages that guide next steps
- **Character Limits & Truncation**: Intelligent handling of large responses with guidance
- **Tool Annotations**: Proper hints for read-only, destructive, and idempotent operations
- **Comprehensive Docstrings**: Detailed documentation with examples for every tool

## Features

This MCP server provides 10 powerful tools for Amazing Marvin:

### Task Management
- ✅ **marvin_add_task** - Create tasks with full support for scheduling, labels, time estimates, and Amazing Marvin shortcuts
- 📅 **marvin_get_todays_tasks** - View all tasks scheduled for today or a specific date
- ✔️ **marvin_mark_done** - Mark tasks as complete (idempotent)
- ⚠️ **marvin_get_due_tasks** - See all tasks due today or overdue with smart overdue indicators

### Organization
- 📁 **marvin_get_categories** - List all your projects and categories with IDs
- 🏷️ **marvin_get_labels** - View all available labels with IDs
- 📋 **marvin_get_children** - Browse tasks within a specific project, category, or unassigned area

### Time Tracking
- ⏱️ **marvin_start_tracking** - Start time tracking on a task
- ⏹️ **marvin_stop_tracking** - Stop the currently running timer

### Response Formats

All list operations support two output formats:
- **Markdown** (default): Human-readable with headers, emojis, and formatting
- **JSON**: Structured data for programmatic processing

## Prerequisites

- Python 3.10 or higher
- An Amazing Marvin account
- Claude Desktop or another MCP-compatible client

## Installation

### 1. Get Your Amazing Marvin API Token

1. Log in to Amazing Marvin
2. Go to https://app.amazingmarvin.com/pre?api=
3. Copy your **API_TOKEN** (for limited access, recommended)

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv venv
uv pip install -r requirements.txt
```

Or with pip:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Test Your Connection

```bash
export AMAZING_MARVIN_API_TOKEN="your-api-token-here"
python test_server.py
```

You should see: ✅ All tests passed!

### 4. Configure Claude Desktop

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "amazing-marvin": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/amazing_marvin_server.py"],
      "env": {
        "AMAZING_MARVIN_API_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

**Important**:
- Use **absolute paths**, not relative paths (e.g., `/Users/you/amazing-marvin-mcp/.venv/bin/python`)
- Use the Python executable from your virtual environment

### 5. Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

## Usage Examples

Once configured, you can interact with Amazing Marvin through Claude:

### Creating Tasks

```
"Create a task called 'Review Q4 budget' due tomorrow with a 2-hour time estimate"

"Add a task 'Call dentist' with 15 minute estimate and schedule it for Friday"

"Create a task 'Finish presentation slides #Work @urgent ~120 +2024-03-20'"
```

Amazing Marvin shortcuts in task titles:
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

"Show me tasks for March 15, 2024"
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

## Available Tools

### marvin_add_task
Create a new task with optional properties:
- `title` (required): Task name with Amazing Marvin shortcuts support
- `note`: Additional details
- `day`: Schedule date (YYYY-MM-DD)
- `due_date`: Due date (YYYY-MM-DD)
- `parent_id`: Category or project ID
- `label_ids`: Array of label IDs
- `time_estimate`: Time in milliseconds (3600000 = 1 hour)
- `is_starred`: Boolean to star the task

**Response**: Success message with task ID, title, and scheduled/due dates

### marvin_get_todays_tasks
Retrieve all tasks scheduled for a specific date (defaults to today).

**Parameters**:
- `date` (optional): Date in YYYY-MM-DD format
- `response_format` (optional): "markdown" (default) or "json"

**Response**: List of scheduled tasks with status, due dates, estimates, and notes

### marvin_mark_done
Mark a specific task as complete using its ID.

**Parameters**:
- `item_id` (required): The task ID to mark complete

**Response**: Success confirmation (idempotent operation)

### marvin_get_due_tasks
Get all tasks due today or overdue, with overdue indicators.

**Parameters**:
- `date` (optional): Check due tasks up to this date (YYYY-MM-DD)
- `response_format` (optional): "markdown" or "json"

**Response**: List with [OVERDUE] and [DUE TODAY] tags

### marvin_get_categories
List all your categories and projects with their IDs.

**Parameters**:
- `response_format` (optional): "markdown" or "json"

**Response**: Complete list of categories/projects with types and parent relationships

### marvin_get_labels
List all your labels with their IDs.

**Parameters**:
- `response_format` (optional): "markdown" or "json"

**Response**: Complete list of labels

### marvin_get_children
Get all tasks and projects within a specific category or project.

**Parameters**:
- `parent_id` (required): Category/project ID or "unassigned"
- `response_format` (optional): "markdown" or "json"

**Response**: All items under the specified parent

### marvin_start_tracking
Start time tracking for a specific task.

**Parameters**:
- `item_id` (required): The task ID to track

**Response**: Confirmation (stops any previously running timer)

### marvin_stop_tracking
Stop the currently running time tracker.

**Response**: Confirmation with saved time

## Technical Details

### Architecture

- **Framework**: FastMCP (Python MCP SDK)
- **Validation**: Pydantic v2 with strict schemas
- **HTTP Client**: httpx with async support
- **Character Limit**: 25,000 characters with intelligent truncation
- **Tool Annotations**: readOnlyHint, destructiveHint, idempotentHint, openWorldHint

### Error Handling

The server provides actionable error messages:
- **401 Unauthorized**: Guides you to check API token configuration
- **404 Not Found**: Suggests verifying IDs and item existence
- **429 Rate Limit**: Advises waiting before retry
- **500 Server Error**: Indicates Amazing Marvin service issues
- **Timeouts**: Provides retry guidance

All errors include specific next steps for resolution.

### Response Truncation

For large result sets exceeding 25,000 characters, the server:
1. Truncates at the last complete item before the limit
2. Adds clear truncation notice
3. Suggests using pagination, filters, or specific ID queries

## Troubleshooting

### Server Not Connecting

1. Check that your API token is correctly set in the environment variables
2. Verify the path to the Python script is absolute, not relative
3. Ensure you're using the virtual environment's Python executable
4. Check Claude Desktop logs for error messages

### API Token Issues

- Use the `API_TOKEN` (not the Full Access Token) unless specifically needed
- Token can be rotated in Amazing Marvin settings if compromised
- Verify the token is correctly copied without extra spaces
- Test with `python test_server.py` to validate connection

### Tasks Not Showing Up

- Check if the API feature is enabled in Marvin (Settings → Features/Strategies)
- Verify your tasks exist in the web or desktop app
- Use the correct date format (YYYY-MM-DD)
- Ensure the task is actually scheduled for the date you're querying

### Import or Dependency Errors

```bash
# Recreate virtual environment
rm -rf .venv
uv venv
uv pip install -r requirements.txt
```

## API Reference

This server uses Amazing Marvin's Limited Access API. For more details:
- API Documentation: https://github.com/amazingmarvin/MarvinAPI/wiki
- Help Center: https://help.amazingmarvin.com/

## Security Notes

- The Limited Access Token (API_TOKEN) is recommended for security
- Never share your API tokens publicly or commit them to git
- Use environment variables for token management
- The Limited Access API provides an additional security layer
- All communication uses HTTPS with the Amazing Marvin API

## Development

### Code Structure

```
amazing_marvin_server.py       # Main server implementation
├── FastMCP initialization
├── Shared utilities
│   ├── _make_api_request()    # Async HTTP client
│   ├── _handle_api_error()    # Error formatting
│   ├── _format_timestamp()    # Date formatting
│   ├── _format_time_estimate()# Time formatting
│   └── _truncate_response()   # Character limit handling
├── Pydantic input models      # Validation schemas
└── Tool implementations       # @mcp.tool decorators
```

### Best Practices Applied

✅ Agent-centric tool design for complete workflows
✅ Pydantic V2 validation with detailed constraints
✅ Comprehensive docstrings with examples
✅ Tool annotations (readOnlyHint, etc.)
✅ Dual response formats (Markdown/JSON)
✅ Character limits with truncation guidance
✅ Actionable error messages
✅ DRY principle with shared utilities
✅ Async/await throughout
✅ Type hints on all functions

## Contributing

Potential future enhancements:
- Document update/delete operations (using `/api/doc/update`, `/api/doc/delete`)
- Project creation tool (using `/api/addProject`)
- Goals integration (using `/api/goals`)
- Habit tracking (using `/api/habits`, `/api/updateHabit`)
- Reminders management (using `/api/reminder/set`)
- Time blocks viewing (using `/api/todayTimeBlocks`)
- Tracked item status (using `/api/trackedItem`)
- Reward points system
- Smart lists integration

## License

This MCP server is provided as-is for use with Amazing Marvin's public API.
Follow Amazing Marvin's Terms & Conditions when using their API.

## Support

For issues related to:
- **MCP Server**: Create an issue in this repository
- **Amazing Marvin API**: Contact support@amazingmarvin.com
- **Claude Desktop**: Check https://support.claude.com

---

Built with ❤️ using FastMCP for the Amazing Marvin and Claude communities

**Version**: 2.0.0 (FastMCP Rebuild)
