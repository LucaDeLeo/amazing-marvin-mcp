# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Amazing Marvin MCP Server** (v2.0) - a Model Context Protocol server that connects AI assistants to Amazing Marvin's task management system. Built with **FastMCP** and **deployed on Smithery** for hosted, install-free access.

**Key Technologies:**
- FastMCP (Python MCP SDK)
- Smithery for hosted deployment
- Pydantic V2 for validation
- httpx for async HTTP
- Amazing Marvin Limited Access API

**Deployment Model:**
- **Primary**: Smithery (hosted, HTTP/SSE transport)
- **Legacy**: Local STDIO deployment (deprecated in favor of Smithery)

## Development Commands

### Setup
```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt
```

### Testing
```bash
# Test API connection (requires AMAZING_MARVIN_API_TOKEN env var)
export AMAZING_MARVIN_API_TOKEN="your-token-here"
.venv/bin/python test_server.py

# Validate Python syntax
python -m py_compile amazing_marvin_server.py
```

### Running the Server
```bash
# Run directly (will check for API token and exit if not set)
.venv/bin/python amazing_marvin_server.py

# The server is meant to be run by Claude Desktop via stdio transport
# See claude_desktop_config.json or README.md for configuration
```

## Architecture

### Single-File MCP Server Design

The entire MCP server is contained in `amazing_marvin_server.py` (1,309 lines) with a clear hierarchical structure:

```
amazing_marvin_server.py
├── FastMCP initialization (line 19)
├── Constants (API_BASE_URL, CHARACTER_LIMIT, etc.)
├── Enums & Base Models (ResponseFormat, BaseTaskInput)
├── Shared Utility Functions (5 functions)
│   ├── _get_headers() - API authentication
│   ├── _make_api_request() - Async HTTP client wrapper
│   ├── _handle_api_error() - Error formatting with guidance
│   ├── _format_timestamp() - Unix timestamp to YYYY-MM-DD
│   └── _truncate_response() - Character limit enforcement
├── Pydantic Input Models (8 models)
│   └── All inherit from BaseTaskInput with strict validation
└── Tool Implementations (9 @mcp.tool decorated functions)
    ├── Tier 1: Task Management (4 tools)
    ├── Tier 2: Organization (3 tools)
    └── Tier 3: Time Tracking (2 tools)
```

### Key Architectural Patterns

**1. Shared Utilities Pattern**
- All API calls go through `_make_api_request()` - single source of truth
- All errors formatted by `_handle_api_error()` - consistent messaging
- All timestamps formatted by `_format_timestamp()` - human-readable dates
- Follows DRY principle strictly

**2. Pydantic V2 Validation Pattern**
- Every tool has a dedicated input model (e.g., `AddTaskInput`, `GetTasksInput`)
- All models inherit from `BaseTaskInput` for common configuration
- Use `Field()` with detailed constraints (min_length, max_length, pattern, ge, le)
- `model_config` sets: `str_strip_whitespace=True`, `validate_assignment=True`, `extra='forbid'`

**3. Tool Registration Pattern**
```python
@mcp.tool(
    name="marvin_add_task",  # Always prefixed with "marvin_"
    annotations={
        "title": "Human-Readable Title",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def marvin_add_task(params: AddTaskInput) -> str:
    """Comprehensive docstring with Args, Returns, Examples, Error Handling"""
```

**4. Dual Response Format Pattern**
- Most tools accept `response_format` parameter (ResponseFormat enum)
- **Markdown** (default): Human-readable with headers, emojis, formatting
- **JSON**: Structured data with json.dumps() for programmatic use
- All responses check CHARACTER_LIMIT (25,000) and truncate with guidance

**5. Error Handling Strategy**
- Try/except wraps all tool logic
- HTTP errors mapped to actionable messages (401→token help, 404→ID verification, 429→rate limit guidance)
- Errors return as strings (not exceptions) so LLM sees them
- Every error message includes next steps

## Amazing Marvin API Integration

### Authentication
- Uses `X-API-Token` header with Limited Access API (recommended)
- Optional `X-Full-Access-Token` for advanced operations (not currently used)
- Token loaded from `AMAZING_MARVIN_API_TOKEN` environment variable

### API Endpoints Used
```
GET  /api/categories       - List all categories/projects
GET  /api/labels          - List all labels
GET  /api/children        - Get items in category (params: parentId)
GET  /api/todayItems      - Get scheduled tasks (params: date)
GET  /api/dueItems        - Get due/overdue tasks (params: by)
POST /api/addTask         - Create task (supports shortcuts)
POST /api/markDone        - Complete task (params: itemId)
POST /api/track           - Start/stop timer (params: itemId, action)
```

### API Quirks
- Timestamps are in **milliseconds** (not seconds)
- `parentId="unassigned"` gets tasks without a category
- Amazing Marvin shortcuts work in titles: `#Project @label ~60 +2024-03-20 ^1`
- Auto-completion enabled by default unless `X-Auto-Complete: false` header

## Tool Implementation Guidelines

### Adding a New Tool

1. **Create Pydantic Input Model**
   ```python
   class NewToolInput(BaseTaskInput):
       param: str = Field(..., description="Detailed description with examples")
   ```

2. **Define Tool with Decorator**
   ```python
   @mcp.tool(name="marvin_new_tool", annotations={...})
   async def marvin_new_tool(params: NewToolInput) -> str:
       """Comprehensive docstring..."""
   ```

3. **Implement with Shared Utilities**
   ```python
   try:
       data = await _make_api_request("/endpoint", method="POST", data={...})
       # Format response (Markdown or JSON based on params.response_format)
       return _truncate_response(result, item_count)
   except Exception as e:
       return _handle_api_error(e)
   ```

### Docstring Requirements
Every tool must document:
- **Purpose**: What the tool does (1-2 sentences)
- **Args**: Full Pydantic model structure with types
- **Returns**: Response format with example structure for both Markdown and JSON
- **Examples**: "Use when" and "Don't use when" scenarios
- **Error Handling**: Specific errors and HTTP status codes with guidance

### Tool Naming Convention
- Always prefix with `marvin_` to avoid conflicts with other MCP servers
- Use snake_case: `marvin_add_task`, not `marvinAddTask`
- Action-oriented: `marvin_get_*`, `marvin_start_*`, `marvin_mark_*`

## Testing Strategy

### Connection Testing (`test_server.py`)
- Validates API token format
- Tests 3 endpoints: categories, labels, todayItems
- Reports counts to verify connectivity
- Use this before deploying changes

### Manual Testing via Claude Desktop
1. Update config with absolute paths to `.venv/bin/python` and server file
2. Restart Claude Desktop completely
3. Test each tool through natural language
4. Verify both Markdown and JSON response formats

## Important Constraints

### Character Limit Enforcement
- All responses must check against `CHARACTER_LIMIT = 25000`
- Use `_truncate_response()` for large result sets
- Truncation adds guidance on using pagination/filters

### Response Format Consistency
- Default to `ResponseFormat.MARKDOWN` unless specified
- Markdown: Use headers (##), lists (-), emojis (✅⬜📁)
- JSON: Use `json.dumps(response, indent=2)` for readability
- Both formats must be truncated if needed

### Async/Await Requirement
- **All I/O operations must be async**: `await _make_api_request()`, `async with httpx.AsyncClient()`
- All tool functions are `async def`
- MCP protocol requires async for proper stdio transport

### Pydantic V2 Specifics
- Use `max_length` not deprecated `max_items` for lists
- Use `@field_validator` not deprecated `@validator`
- Use `model_dump()` not deprecated `dict()`
- All validators require `@classmethod` decorator

## Configuration Files

### `requirements.txt`
- `mcp[cli]>=1.0.0` - FastMCP support
- `httpx>=0.27.0` - Async HTTP client
- `pydantic>=2.0.0` - Validation (v2 required)

### `claude_desktop_config.json` (Example, not committed)
Must use **absolute paths**:
```json
{
  "mcpServers": {
    "amazing-marvin": {
      "command": "/absolute/path/.venv/bin/python",
      "args": ["/absolute/path/amazing_marvin_server.py"],
      "env": {"AMAZING_MARVIN_API_TOKEN": "token-here"}
    }
  }
}
```

## Security Notes

- API tokens in `.gitignore` (never commit `claude_desktop_config.json`)
- Limited Access API provides safety layer vs Full Access
- All API communication over HTTPS
- Input validation prevents injection attacks

## Future Enhancement Areas

Documented in README.md, potential additions:
- Document operations (`/api/doc/update`, `/api/doc/delete`)
- Project creation (`/api/addProject`)
- Goals integration (`/api/goals`)
- Habit tracking (`/api/habits`, `/api/updateHabit`)
- Reminders (`/api/reminder/set`)
- Time blocks (`/api/todayTimeBlocks`)
- Reward points system

When adding these, follow the same patterns: Pydantic model → @mcp.tool decorator → shared utilities → comprehensive docstring.

## Smithery Deployment Architecture

### Package Structure for Smithery

The project follows Python package conventions for Smithery deployment:

```
amazing-marvin-mcp/
├── src/
│   └── amazing_marvin_mcp/         # Python package
│       ├── __init__.py            # Package initialization (__version__)
│       └── server.py              # Main server with @smithery.server()
├── pyproject.toml                 # Package config + [tool.smithery]
├── smithery.yaml                  # Runtime: "python"
├── requirements.txt               # Local dev dependencies
├── README.md                      # Smithery-focused documentation
├── SMITHERY_DEPLOYMENT.md         # Deployment guide
└── CLAUDE.md                      # This file

Legacy files (deprecated):
├── amazing_marvin_server.py       # Old STDIO version
└── test_server.py                 # Old env var based testing
```

### Smithery-Specific Code Patterns

**1. Server Creation with @smithery.server() Decorator**

```python
from smithery.decorators import smithery
from mcp.server.fastmcp import FastMCP, Context

@smithery.server(config_schema=AmazingMarvinConfig)
def create_server():
    """
    Entry point called by Smithery to create the MCP server.
    The config_schema generates a UI form for users to provide their API token.
    """
    mcp = FastMCP("amazing_marvin_mcp")

    # Register all tools here using @mcp.tool() decorators

    return mcp
```

**2. Configuration Schema Pattern**

```python
class AmazingMarvinConfig(BaseModel):
    """User configuration collected via Smithery UI."""
    model_config = ConfigDict(str_strip_whitespace=True)

    api_token: str = Field(
        ...,
        description="Your Amazing Marvin API token. Get it from: https://app.amazingmarvin.com/pre?api=",
        min_length=10
    )
```

This schema:
- Generates a configuration form in Smithery UI
- Validates user input (min_length=10)
- Provides help text (description field)
- Stored encrypted per user session

**3. Context Parameter Flow**

Every tool must accept `ctx: Context` to access session configuration:

```python
@mcp.tool(name="marvin_add_task", annotations={...})
async def marvin_add_task(params: AddTaskInput, ctx: Context) -> str:
    """
    Args:
        params: Validated Pydantic input model
        ctx: Smithery context with session_config
    """
    # Pass ctx to API request function
    result = await _make_api_request("/addTask", ctx, method="POST", data=data)
    return result
```

**4. Context-Aware API Authentication**

```python
def _get_headers(ctx: Context, full_access: bool = False) -> Dict[str, str]:
    """Extract API token from session config instead of environment variable."""
    config: AmazingMarvinConfig = ctx.session_config
    return {"X-API-Token": config.api_token}

async def _make_api_request(endpoint: str, ctx: Context, ...):
    """All API requests require ctx parameter."""
    headers = _get_headers(ctx)
    # ... make request with authenticated headers
```

### Critical Smithery Differences vs STDIO

| Aspect | STDIO (old) | Smithery (new) |
|--------|-------------|----------------|
| **Imports** | `from mcp.server.fastmcp import FastMCP` | `+ from smithery.decorators import smithery`<br>`+ from mcp.server.fastmcp import Context` |
| **Server Init** | `mcp = FastMCP("...")` at module level | `@smithery.server()` wrapping `create_server()` function |
| **API Token** | `os.getenv("AMAZING_MARVIN_API_TOKEN")` | `ctx.session_config.api_token` |
| **Tool Signature** | `async def tool(params: Model) -> str` | `async def tool(params: Model, ctx: Context) -> str` |
| **Entry Point** | `if __name__ == "__main__": mcp.run()` | `create_server()` function (NO main block) |
| **Transport** | STDIO | HTTP/SSE |
| **Configuration** | Environment variables | Session config via Pydantic schema |
| **Testing** | `test_server.py` with env vars | `uv run playground` or `uv run dev` |

### Deployment Process

**1. Local Testing**

```bash
# Install dependencies including smithery
uv venv
uv pip install -r requirements.txt
uv pip install smithery

# Test with Smithery playground (ngrok tunneling)
uv run playground

# Or run in development mode
uv run dev
```

**2. Deploy to Smithery**

```bash
# Commit all changes
git add .
git commit -m "Update for Smithery deployment"
git push origin main

# Then in Smithery web UI:
# 1. Go to https://smithery.ai/new
# 2. Click "Continue with GitHub"
# 3. Select repository: LucaDeLeo/amazing-marvin-mcp
# 4. Click "Deploy"
```

**3. Auto-Deployment**

Once connected, every `git push` to `main` triggers automatic redeployment.

### pyproject.toml Configuration

```toml
[tool.smithery]
server = "amazing_marvin_mcp.server:create_server"
```

This tells Smithery:
- Package is `amazing_marvin_mcp` (in `src/`)
- Module is `server.py`
- Function is `create_server()`

### smithery.yaml Configuration

```yaml
runtime: "python"
```

Minimal configuration specifying Python 3.12+ runtime.

## Adding New Tools (Smithery Version)

When adding new tools to the Smithery deployment:

1. **Define Pydantic Input Model**
   ```python
   class NewToolInput(BaseTaskInput):
       param: str = Field(..., description="...")
   ```

2. **Add Tool Inside create_server() Function**
   ```python
   @smithery.server(config_schema=AmazingMarvinConfig)
   def create_server():
       mcp = FastMCP("amazing_marvin_mcp")

       @mcp.tool(name="marvin_new_tool", annotations={...})
       async def marvin_new_tool(params: NewToolInput, ctx: Context) -> str:
           """Full docstring with Args including ctx..."""
           result = await _make_api_request("/endpoint", ctx, ...)
           return result

       return mcp
   ```

3. **Always Include ctx: Context Parameter**
   - First parameter after `params`
   - Required for authentication
   - Pass to all `_make_api_request()` calls

4. **Update Docstring**
   - Include `ctx (Context): Smithery context with session configuration` in Args
   - Document session config usage if relevant

5. **Test with Playground**
   ```bash
   uv run playground
   # Configure API token in web UI
   # Test tool through interface
   ```

6. **Deploy**
   ```bash
   git add src/amazing_marvin_mcp/server.py
   git commit -m "Add marvin_new_tool"
   git push origin main
   # Auto-deploys to Smithery
   ```

## Troubleshooting Smithery Deployment

### Build Failures

**Error**: `ModuleNotFoundError: No module named 'smithery'`
- **Fix**: Add `smithery>=0.4.2` to dependencies in `pyproject.toml`

**Error**: `ModuleNotFoundError: No module named 'amazing_marvin_mcp'`
- **Fix**: Ensure package structure: `src/amazing_marvin_mcp/__init__.py` exists

**Error**: `ImportError: cannot import name 'create_server'`
- **Fix**: Check `[tool.smithery]` server path matches actual function name

### Runtime Failures

**Error**: `AttributeError: 'NoneType' object has no attribute 'api_token'`
- **Cause**: User hasn't configured API token in Smithery UI
- **Fix**: User must fill out configuration form in Smithery

**Error**: `401 Unauthorized` from Amazing Marvin
- **Cause**: Invalid or expired API token
- **Fix**: User needs to regenerate token at https://app.amazingmarvin.com/pre?api=

### Testing Issues

**Local playground won't start**
- Check `uv pip install smithery` was run
- Verify port 8000 isn't already in use
- Try `uv run dev` instead

**Tools not receiving ctx parameter**
- Ensure function signature includes `ctx: Context`
- Check import: `from mcp.server.fastmcp import Context`
- Verify tool is inside `create_server()` function

## Migration Guide

### From STDIO to Smithery

If maintaining both versions:

1. **Keep old file**: `amazing_marvin_server.py` (STDIO)
2. **New file**: `src/amazing_marvin_mcp/server.py` (Smithery)
3. **Update README**: Guide users to Smithery as primary method
4. **Add deprecation notice**: To old STDIO instructions

If fully migrating to Smithery only:

1. **Remove/Archive**: `amazing_marvin_server.py`, `test_server.py`
2. **Update all docs**: Remove STDIO instructions
3. **Update Claude Desktop instructions**: Point to Smithery connection link
4. **Commit migration**: `git commit -m "Complete migration to Smithery"`

Current status: **Fully migrated to Smithery** (v2.0.0)
