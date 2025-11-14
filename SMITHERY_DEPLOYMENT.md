# Smithery Deployment Guide

## Overview

The Amazing Marvin MCP Server is deployed on **Smithery** for hosted, install-free access. Users can connect to the server without installing Python, dependencies, or managing local processes.

**Smithery Benefits:**
- 🌐 **Hosted Infrastructure**: No local installation required
- 🔒 **Secure Configuration**: API tokens stored securely per user session
- 📊 **Usage Monitoring**: Track server usage and performance
- 🚀 **Auto-scaling**: Handles multiple concurrent users
- 🔄 **Auto-deployment**: Push to GitHub → Auto-deploy

## Architecture

### Package Structure

```
amazing-marvin-mcp/
├── src/
│   └── amazing_marvin_mcp/
│       ├── __init__.py         # Package initialization
│       └── server.py           # Main server with @smithery.server()
├── pyproject.toml              # Python package configuration
├── smithery.yaml               # Smithery runtime config
├── README.md                   # User documentation
└── .gitignore                  # Excludes build artifacts
```

### Key Differences from STDIO Version

| Aspect | STDIO (Local) | Smithery (Hosted) |
|--------|---------------|-------------------|
| **Transport** | stdio | HTTP/SSE |
| **Authentication** | Environment variable | Session config (UI) |
| **Deployment** | Manual installation | Auto-deploy from GitHub |
| **Context** | N/A | `ctx: Context` parameter |
| **Configuration** | `.env` or shell exports | Smithery UI config form |

## Deployment Steps

### 1. Prerequisites

- GitHub account
- Smithery account (free at https://smithery.ai)
- Amazing Marvin API token from https://app.amazingmarvin.com/pre?api=

### 2. Push to GitHub

```bash
# Ensure all files are committed
git add .
git commit -m "Smithery deployment ready"
git push origin main
```

**Required files for deployment:**
- ✅ `smithery.yaml` (runtime specification)
- ✅ `pyproject.toml` (package config with [tool.smithery])
- ✅ `src/amazing_marvin_mcp/` (package directory)
- ✅ `src/amazing_marvin_mcp/__init__.py` (package init)
- ✅ `src/amazing_marvin_mcp/server.py` (server implementation)

### 3. Deploy on Smithery

1. Go to https://smithery.ai/new
2. Click **"Continue with GitHub"**
3. Select repository: `LucaDeLeo/amazing-marvin-mcp`
4. Grant necessary permissions (read code, webhooks for auto-deploy)
5. Click **"Deploy"**

Smithery will:
- Clone your repository
- Read `smithery.yaml` for runtime configuration
- Install dependencies from `pyproject.toml`
- Build the Python package
- Start the MCP server
- Generate a connection URL

### 4. Connect from Claude Desktop

After deployment, Smithery provides a connection link. Users click the link and:

1. **Configure API Token**: Smithery shows a form with:
   - `api_token` field (from `AmazingMarvinConfig` schema)
   - Description: "Your Amazing Marvin API token. Get it from: https://app.amazingmarvin.com/pre?api="

2. **Save Configuration**: Token is stored securely in Smithery's session config

3. **Use Tools**: Tools are now available in Claude Desktop

## Configuration Schema

### `AmazingMarvinConfig` (in server.py)

```python
class AmazingMarvinConfig(BaseModel):
    api_token: str = Field(
        ...,
        description="Your Amazing Marvin API token. Get it from: https://app.amazingmarvin.com/pre?api=",
        min_length=10
    )
```

This schema generates a configuration UI in Smithery where users enter their API token.

## Local Development & Testing

### Setup Local Environment

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt

# Install smithery package for local testing
uv pip install smithery
```

### Test Locally with Smithery Playground

```bash
# Run the server in development mode
uv run dev

# Or use the Smithery playground (ngrok port-forwarding)
uv run playground
```

**Note**: You'll need to configure your API token in the playground UI.

### Validate Package Structure

```bash
# Check package can be built
python -m build

# Verify dist/ contains wheel and tar.gz
ls dist/
```

## Server Implementation Details

### Context Flow

Every tool receives `ctx: Context` which provides access to session configuration:

```python
@mcp.tool(name="marvin_add_task", annotations={...})
async def marvin_add_task(params: AddTaskInput, ctx: Context) -> str:
    # ctx.session_config contains user's AmazingMarvinConfig
    # Pass ctx to _make_api_request for authentication
    result = await _make_api_request("/addTask", ctx, method="POST", data=task_data)
    return result
```

### API Authentication with Context

```python
def _get_headers(ctx: Context, full_access: bool = False) -> Dict[str, str]:
    """Extract API token from session config."""
    config: AmazingMarvinConfig = ctx.session_config
    return {"X-API-Token": config.api_token}

async def _make_api_request(endpoint: str, ctx: Context, ...):
    """Use context for authentication."""
    headers = _get_headers(ctx)
    # Make request with authenticated headers
    ...
```

### Server Creation Function

```python
@smithery_server(config_schema=AmazingMarvinConfig)
def create_server():
    """
    Called by Smithery to initialize the server.
    Returns FastMCP instance with all tools registered.
    """
    mcp = FastMCP("amazing_marvin_mcp")

    # Register all tools with @mcp.tool() decorator
    @mcp.tool(name="marvin_add_task", annotations={...})
    async def marvin_add_task(params: AddTaskInput, ctx: Context) -> str:
        ...

    return mcp
```

## Monitoring & Debugging

### View Server Logs

In Smithery dashboard:
1. Go to your server deployment
2. Click "Logs" tab
3. View real-time logs of server activity

### Check Server Status

```bash
# Via Smithery CLI (if installed)
smithery status amazing-marvin-mcp
```

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'smithery'`
- **Solution**: Ensure `smithery>=0.4.2` is in `pyproject.toml` dependencies

**Issue**: `AttributeError: 'NoneType' object has no attribute 'api_token'`
- **Solution**: User hasn't configured their API token in Smithery UI
- **Fix**: Check Smithery configuration form is filled out

**Issue**: `401 Unauthorized` from Amazing Marvin API
- **Solution**: User's API token is invalid or expired
- **Fix**: User should regenerate token at https://app.amazingmarvin.com/pre?api=

## Auto-Deployment

Smithery supports GitHub webhooks for automatic deployment:

1. **Push to Main**: `git push origin main`
2. **Webhook Triggered**: GitHub notifies Smithery
3. **Auto-Build**: Smithery pulls latest code, builds, and deploys
4. **Zero Downtime**: Rolling deployment, no service interruption

### Deployment Triggers

- Push to `main` branch
- Manual deploy via Smithery dashboard
- Release tag creation (e.g., `v2.0.0`)

## Security Considerations

### API Token Storage

- Tokens never committed to git (`.gitignore` includes `claude_desktop_config.json`)
- Tokens stored encrypted in Smithery's session config
- Each user has their own isolated token
- Tokens not shared between users

### HTTPS Transport

- All communication over HTTPS
- TLS 1.2+ enforced
- Certificate verification enabled

### Input Validation

- All inputs validated by Pydantic models
- Type checking enforced
- SQL/command injection prevented
- File path sanitization

## Cost & Limits

**Smithery Free Tier** (as of deployment):
- Unlimited tool calls
- Reasonable rate limits
- Shared infrastructure
- Community support

**Usage Monitoring**:
- View calls per day/week/month in dashboard
- Track response times
- Monitor error rates

## Migration from STDIO to Smithery

For users transitioning from local STDIO deployment:

### What Changes

1. **No Local Installation**: Remove `.venv`, no `pip install`
2. **No Environment Variables**: Use Smithery UI instead of `.env`
3. **No Claude Desktop Config**: Use Smithery connection link
4. **Automatic Updates**: Push to GitHub auto-deploys

### What Stays the Same

1. **Same Tools**: All 9 tools work identically
2. **Same API**: Amazing Marvin API unchanged
3. **Same Responses**: Markdown/JSON formats identical
4. **Same Validation**: Pydantic models unchanged

## Support

**Smithery Issues**:
- Email: support@smithery.ai
- Discord: https://discord.gg/Afd38S5p9A

**Server Issues**:
- GitHub: https://github.com/LucaDeLeo/amazing-marvin-mcp/issues

**Amazing Marvin API**:
- Email: support@amazingmarvin.com
- Docs: https://github.com/amazingmarvin/MarvinAPI/wiki

---

**Version**: 2.0.0 (Smithery Deployment)
**Last Updated**: 2025-11-14
