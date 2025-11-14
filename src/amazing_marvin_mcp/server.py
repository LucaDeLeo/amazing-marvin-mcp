"""
Amazing Marvin MCP Server - Smithery Deployment

This MCP server provides tools to interact with Amazing Marvin's task management system.
Built with FastMCP and deployed on Smithery for hosted, install-free access.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP, Context
from smithery import server as smithery_server

# Constants
API_BASE_URL = "https://serv.amazingmarvin.com/api"
CHARACTER_LIMIT = 25000  # Maximum response size in characters
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


# ============================================================================
# Configuration Schema
# ============================================================================

class AmazingMarvinConfig(BaseModel):
    """Configuration schema for user-provided API token."""
    model_config = ConfigDict(str_strip_whitespace=True)

    api_token: str = Field(
        ...,
        description="Your Amazing Marvin API token. Get it from: https://app.amazingmarvin.com/pre?api=",
        min_length=10
    )


# ============================================================================
# Enums and Shared Models
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class BaseTaskInput(BaseModel):
    """Base model with common configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )


# ============================================================================
# Shared Utility Functions
# ============================================================================

def _get_headers(ctx: Context, full_access: bool = False) -> Dict[str, str]:
    """
    Get appropriate headers for API requests.

    Args:
        ctx: Smithery context with session config
        full_access: Whether to use full access token (not currently supported)

    Returns:
        Headers dict with API token
    """
    config: AmazingMarvinConfig = ctx.session_config
    return {"X-API-Token": config.api_token}


async def _make_api_request(
    endpoint: str,
    ctx: Context,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    full_access: bool = False
) -> Any:
    """
    Reusable function for all API calls to Amazing Marvin.

    Args:
        endpoint: API endpoint (e.g., "/todayItems")
        ctx: Smithery context with session config
        method: HTTP method (GET or POST)
        data: JSON data for POST requests
        params: Query parameters for GET requests
        full_access: Whether to use full access token

    Returns:
        JSON response from API

    Raises:
        httpx.HTTPStatusError: For HTTP errors
        httpx.TimeoutException: For timeout errors
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = _get_headers(ctx, full_access)

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = await client.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()


def _handle_api_error(e: Exception) -> str:
    """
    Consistent error formatting across all tools with actionable messages.

    Args:
        e: Exception to format

    Returns:
        Human-readable error message with guidance
    """
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return ("Error: Invalid API token. Please check that your API token is correct. "
                   "Get your token at https://app.amazingmarvin.com/pre?api=")
        elif status == 403:
            return ("Error: Permission denied. This operation may require full access token.")
        elif status == 404:
            return ("Error: Resource not found. Please check that the ID is correct and "
                   "the item still exists in Amazing Marvin.")
        elif status == 429:
            return ("Error: Rate limit exceeded. Please wait a moment before making more "
                   "requests to the Amazing Marvin API.")
        elif status >= 500:
            return ("Error: Amazing Marvin server error. The service may be temporarily "
                   "unavailable. Please try again in a few moments.")
        return f"Error: API request failed with status {status}. Please try again."
    elif isinstance(e, httpx.TimeoutException):
        return ("Error: Request timed out. The Amazing Marvin API is taking too long to "
               "respond. Please try again.")
    elif isinstance(e, httpx.ConnectError):
        return ("Error: Cannot connect to Amazing Marvin API. Please check your internet "
               "connection and try again.")
    return f"Error: Unexpected error occurred - {type(e).__name__}: {str(e)}"


def _format_timestamp(timestamp: Optional[int], default: str = "Not set") -> str:
    """
    Convert Unix timestamp (milliseconds) to human-readable format.

    Args:
        timestamp: Unix timestamp in milliseconds
        default: Default string if timestamp is None

    Returns:
        Formatted date string (YYYY-MM-DD) or default
    """
    if not timestamp:
        return default
    try:
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return default


def _format_time_estimate(ms: Optional[int]) -> str:
    """
    Convert time estimate in milliseconds to human-readable format.

    Args:
        ms: Time in milliseconds

    Returns:
        Formatted time string (e.g., "2h 30m")
    """
    if not ms:
        return "Not set"

    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000

    if hours and minutes:
        return f"{hours}h {minutes}m"
    elif hours:
        return f"{hours}h"
    elif minutes:
        return f"{minutes}m"
    else:
        return "< 1m"


def _truncate_response(content: str, items_count: int) -> str:
    """
    Truncate response if it exceeds CHARACTER_LIMIT with helpful guidance.

    Args:
        content: Response content to check
        items_count: Number of items in the response

    Returns:
        Original content or truncated content with guidance
    """
    if len(content) <= CHARACTER_LIMIT:
        return content

    # Truncate to CHARACTER_LIMIT and add guidance
    truncated = content[:CHARACTER_LIMIT]
    last_newline = truncated.rfind('\n')
    if last_newline > 0:
        truncated = truncated[:last_newline]

    truncated += (
        f"\n\n---\n**Response Truncated**: Showing partial results due to size limit "
        f"({len(content):,} characters). To see more:\n"
        f"- Use pagination with `limit` and `offset` parameters\n"
        f"- Add filters to narrow down results\n"
        f"- Request specific items by ID\n"
    )
    return truncated


# ============================================================================
# Pydantic Input Models
# ============================================================================

class AddTaskInput(BaseTaskInput):
    """Input model for creating a new task."""
    title: str = Field(
        ...,
        description=(
            "Task title. Supports Amazing Marvin shortcuts: "
            "#ProjectName (parent), @label (label), ~60 (time estimate in minutes), "
            "+YYYY-MM-DD (due date), ^1 (priority). "
            "Examples: 'Review budget #Work @urgent ~120 +2024-03-20', "
            "'Call dentist ~15 +tomorrow'"
        ),
        min_length=1,
        max_length=500
    )
    note: Optional[str] = Field(
        default=None,
        description="Additional notes or description for the task",
        max_length=5000
    )
    day: Optional[str] = Field(
        default=None,
        description=(
            "Schedule date in YYYY-MM-DD format to add task to daily schedule "
            "(e.g., '2024-03-15', '2024-12-25')"
        ),
        pattern=r'^\d{4}-\d{2}-\d{2}$'
    )
    due_date: Optional[str] = Field(
        default=None,
        description=(
            "Due date in YYYY-MM-DD format for deadline tracking "
            "(e.g., '2024-03-20')"
        ),
        pattern=r'^\d{4}-\d{2}-\d{2}$'
    )
    parent_id: Optional[str] = Field(
        default=None,
        description=(
            "ID of parent project or category (get from marvin_get_categories). "
            "Example: 'cat_abc123xyz'"
        )
    )
    label_ids: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of label IDs to attach to task (get from marvin_get_labels). "
            "Example: ['label_1', 'label_2']"
        ),
        max_length=20
    )
    time_estimate: Optional[int] = Field(
        default=None,
        description=(
            "Estimated time in milliseconds. "
            "Common values: 900000 (15 min), 1800000 (30 min), 3600000 (1 hour), "
            "7200000 (2 hours)"
        ),
        ge=60000,  # Minimum 1 minute
        le=86400000  # Maximum 24 hours
    )
    is_starred: Optional[bool] = Field(
        default=None,
        description="Whether to star/prioritize this task (true/false)"
    )


class GetTasksInput(BaseTaskInput):
    """Input model for retrieving tasks with optional filters."""
    date: Optional[str] = Field(
        default=None,
        description=(
            "Date in YYYY-MM-DD format (defaults to today). "
            "Examples: '2024-03-15', '2024-12-25'"
        ),
        pattern=r'^\d{4}-\d{2}-\d{2}$'
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description=(
            "Output format: 'markdown' for human-readable (default) or "
            "'json' for machine-readable structured data"
        )
    )


class MarkDoneInput(BaseTaskInput):
    """Input model for marking a task as complete."""
    item_id: str = Field(
        ...,
        description=(
            "The ID of the task to mark as done (shown when viewing tasks). "
            "Example: 'task_abc123xyz'"
        ),
        min_length=1
    )


class GetChildrenInput(BaseTaskInput):
    """Input model for getting items within a category/project."""
    parent_id: str = Field(
        ...,
        description=(
            "ID of parent category/project (from marvin_get_categories) or "
            "'unassigned' for tasks without a parent. Example: 'cat_abc123xyz'"
        ),
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (default) or 'json'"
    )


class StartTrackingInput(BaseTaskInput):
    """Input model for starting time tracking."""
    item_id: str = Field(
        ...,
        description=(
            "The ID of the task to start tracking (from task lists). "
            "Example: 'task_abc123xyz'"
        ),
        min_length=1
    )


class SimpleFormatInput(BaseTaskInput):
    """Input model for simple list operations with format option."""
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (default) or 'json'"
    )


# ============================================================================
# Server Creation Function with Smithery Decorator
# ============================================================================

@smithery_server(config_schema=AmazingMarvinConfig)
def create_server():
    """
    Create and configure the Amazing Marvin MCP server.

    This function is called by Smithery to initialize the server with user configuration.
    The config_schema specifies that users must provide their API token.

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP("amazing_marvin_mcp")

    # ============================================================================
    # Tool Implementations - Tier 1: Essential Task Management
    # ============================================================================

    @mcp.tool(
        name="marvin_add_task",
        annotations={
            "title": "Add Task to Amazing Marvin",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def marvin_add_task(params: AddTaskInput, ctx: Context) -> str:
        """
        Create a new task in Amazing Marvin with full support for scheduling, labels, and organization.

        This tool creates tasks with auto-completion support for shortcuts in the title.
        Amazing Marvin shortcuts: #Project, @label, ~timeEstimate, +dueDate, ^priority.

        Args:
            params (AddTaskInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: Success message with task ID and title, or error message
        """
        try:
            # Build task data from validated input
            task_data = {
                "title": params.title,
                "done": False
            }

            # Add optional fields if provided
            if params.note is not None:
                task_data["note"] = params.note
            if params.day is not None:
                task_data["day"] = params.day
            if params.due_date is not None:
                task_data["dueDate"] = params.due_date
            if params.parent_id is not None:
                task_data["parentId"] = params.parent_id
            if params.label_ids is not None:
                task_data["labelIds"] = params.label_ids
            if params.time_estimate is not None:
                task_data["timeEstimate"] = params.time_estimate
            if params.is_starred is not None:
                task_data["isStarred"] = params.is_starred

            # Make API request
            result = await _make_api_request("/addTask", ctx, method="POST", data=task_data)

            # Format success response
            lines = [
                "✅ Task created successfully!",
                "",
                f"**ID**: {result.get('_id', 'N/A')}",
                f"**Title**: {result.get('title', 'N/A')}"
            ]

            if result.get('day'):
                lines.append(f"**Scheduled**: {_format_timestamp(result.get('day'))}")
            if result.get('dueDate'):
                lines.append(f"**Due**: {_format_timestamp(result.get('dueDate'))}")
            if result.get('timeEstimate'):
                lines.append(f"**Time Estimate**: {_format_time_estimate(result.get('timeEstimate'))}")

            return "\n".join(lines)

        except Exception as e:
            return _handle_api_error(e)

    @mcp.tool(
        name="marvin_get_todays_tasks",
        annotations={
            "title": "Get Today's Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_get_todays_tasks(params: GetTasksInput, ctx: Context) -> str:
        """
        Retrieve all tasks scheduled for today (or a specific date) in Amazing Marvin.

        Args:
            params (GetTasksInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: List of tasks formatted as markdown or JSON
        """
        try:
            # Use provided date or default to today
            target_date = params.date or datetime.now().strftime("%Y-%m-%d")

            # Make API request
            tasks = await _make_api_request(
                "/todayItems",
                ctx,
                params={"date": target_date}
            )

            if not tasks:
                return f"No tasks scheduled for {target_date}."

            # Format response based on requested format
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [
                    f"# Today's Tasks ({target_date})",
                    "",
                    f"Found {len(tasks)} task{'s' if len(tasks) != 1 else ''}",
                    ""
                ]

                for task in tasks:
                    status = "✅" if task.get("done") else "⬜"
                    title = task.get("title", "Untitled")
                    task_id = task.get("_id", "")

                    lines.append(f"## {status} {title}")
                    lines.append(f"- **ID**: {task_id}")

                    if task.get("dueDate"):
                        lines.append(f"- **Due**: {_format_timestamp(task.get('dueDate'))}")
                    if task.get("timeEstimate"):
                        lines.append(f"- **Estimate**: {_format_time_estimate(task.get('timeEstimate'))}")
                    if task.get("parentId"):
                        lines.append(f"- **Project**: {task.get('parentId')}")
                    if task.get("note"):
                        note = task.get("note", "")[:200]
                        lines.append(f"- **Note**: {note}")

                    lines.append("")

                result = "\n".join(lines)
                return _truncate_response(result, len(tasks))

            else:  # JSON format
                response = {
                    "date": target_date,
                    "total": len(tasks),
                    "tasks": [
                        {
                            "id": t.get("_id"),
                            "title": t.get("title"),
                            "done": t.get("done", False),
                            "dueDate": _format_timestamp(t.get("dueDate")) if t.get("dueDate") else None,
                            "timeEstimate": _format_time_estimate(t.get("timeEstimate")) if t.get("timeEstimate") else None,
                            "parentId": t.get("parentId"),
                            "note": t.get("note")
                        }
                        for t in tasks
                    ]
                }
                result = json.dumps(response, indent=2)
                return _truncate_response(result, len(tasks))

        except Exception as e:
            return _handle_api_error(e)

    @mcp.tool(
        name="marvin_mark_done",
        annotations={
            "title": "Mark Task as Done",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_mark_done(params: MarkDoneInput, ctx: Context) -> str:
        """
        Mark a specific task as complete in Amazing Marvin.

        Args:
            params (MarkDoneInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: Success confirmation with task ID
        """
        try:
            # Make API request
            await _make_api_request(
                "/markDone",
                ctx,
                method="POST",
                data={"itemId": params.item_id}
            )

            return (
                f"✅ Task marked as complete!\n\n"
                f"**Task ID**: {params.item_id}"
            )

        except Exception as e:
            return _handle_api_error(e)

    @mcp.tool(
        name="marvin_get_due_tasks",
        annotations={
            "title": "Get Due and Overdue Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_get_due_tasks(params: GetTasksInput, ctx: Context) -> str:
        """
        Get all tasks that are due today or overdue in Amazing Marvin.

        Args:
            params (GetTasksInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: List of due/overdue tasks formatted as markdown or JSON
        """
        try:
            # Use provided date or default to today
            target_date = params.date or datetime.now().strftime("%Y-%m-%d")

            # Make API request
            tasks = await _make_api_request(
                "/dueItems",
                ctx,
                params={"by": target_date}
            )

            if not tasks:
                return f"No due or overdue tasks as of {target_date}."

            # Calculate days overdue for each task
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")

            # Format response based on requested format
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [
                    f"# Due & Overdue Tasks (as of {target_date})",
                    "",
                    f"Found {len(tasks)} task{'s' if len(tasks) != 1 else ''} requiring attention",
                    ""
                ]

                for task in tasks:
                    status = "✅" if task.get("done") else "⬜"
                    title = task.get("title", "Untitled")
                    task_id = task.get("_id", "")
                    due_date_str = _format_timestamp(task.get("dueDate"))

                    # Calculate if overdue
                    overdue_tag = ""
                    if task.get("dueDate"):
                        due_dt = datetime.fromtimestamp(task.get("dueDate") / 1000)
                        days_diff = (target_dt - due_dt).days
                        if days_diff > 0:
                            overdue_tag = " [OVERDUE]"
                        elif days_diff == 0:
                            overdue_tag = " [DUE TODAY]"

                    lines.append(f"## {status} {title}{overdue_tag}")
                    lines.append(f"- **ID**: {task_id}")
                    lines.append(f"- **Due**: {due_date_str}")

                    if task.get("timeEstimate"):
                        lines.append(f"- **Estimate**: {_format_time_estimate(task.get('timeEstimate'))}")
                    if task.get("note"):
                        note = task.get("note", "")[:200]
                        lines.append(f"- **Note**: {note}")

                    lines.append("")

                result = "\n".join(lines)
                return _truncate_response(result, len(tasks))

            else:  # JSON format
                response = {
                    "asOf": target_date,
                    "total": len(tasks),
                    "tasks": []
                }

                for task in tasks:
                    task_data = {
                        "id": task.get("_id"),
                        "title": task.get("title"),
                        "done": task.get("done", False),
                        "dueDate": _format_timestamp(task.get("dueDate")) if task.get("dueDate") else None,
                        "timeEstimate": _format_time_estimate(task.get("timeEstimate")) if task.get("timeEstimate") else None,
                    }

                    # Add days overdue if applicable
                    if task.get("dueDate"):
                        due_dt = datetime.fromtimestamp(task.get("dueDate") / 1000)
                        days_diff = (target_dt - due_dt).days
                        if days_diff > 0:
                            task_data["daysOverdue"] = days_diff

                    response["tasks"].append(task_data)

                result = json.dumps(response, indent=2)
                return _truncate_response(result, len(tasks))

        except Exception as e:
            return _handle_api_error(e)

    # ============================================================================
    # Tool Implementations - Tier 2: Organization & Context
    # ============================================================================

    @mcp.tool(
        name="marvin_get_categories",
        annotations={
            "title": "List All Categories and Projects",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_get_categories(params: SimpleFormatInput, ctx: Context) -> str:
        """
        List all categories and projects in Amazing Marvin to help identify parent IDs.

        Args:
            params (SimpleFormatInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: List of categories/projects formatted as markdown or JSON
        """
        try:
            # Make API request
            categories = await _make_api_request("/categories", ctx)

            if not categories:
                return "No categories or projects found."

            # Format response based on requested format
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [
                    "# Categories & Projects",
                    "",
                    f"Found {len(categories)} categor{'ies' if len(categories) != 1 else 'y'} and projects",
                    ""
                ]

                for cat in categories:
                    title = cat.get("title", "Untitled")
                    cat_id = cat.get("_id", "")
                    cat_type = cat.get("type", "unknown")

                    lines.append(f"## {title} ({cat_type})")
                    lines.append(f"- **ID**: {cat_id}")
                    lines.append(f"- **Type**: {cat_type}")

                    if cat.get("parentId"):
                        lines.append(f"- **Parent**: {cat.get('parentId')}")
                    if cat.get("note"):
                        note = cat.get("note", "")[:150]
                        lines.append(f"- **Note**: {note}")

                    lines.append("")

                result = "\n".join(lines)
                return _truncate_response(result, len(categories))

            else:  # JSON format
                response = {
                    "total": len(categories),
                    "categories": [
                        {
                            "id": c.get("_id"),
                            "title": c.get("title"),
                            "type": c.get("type"),
                            "parentId": c.get("parentId"),
                            "note": c.get("note")
                        }
                        for c in categories
                    ]
                }
                result = json.dumps(response, indent=2)
                return _truncate_response(result, len(categories))

        except Exception as e:
            return _handle_api_error(e)

    @mcp.tool(
        name="marvin_get_labels",
        annotations={
            "title": "List All Labels",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_get_labels(params: SimpleFormatInput, ctx: Context) -> str:
        """
        List all labels in Amazing Marvin to help identify label IDs for task creation.

        Args:
            params (SimpleFormatInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: List of labels formatted as markdown or JSON
        """
        try:
            # Make API request
            labels = await _make_api_request("/labels", ctx)

            if not labels:
                return "No labels found."

            # Format response based on requested format
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [
                    "# Labels",
                    "",
                    f"Found {len(labels)} label{'s' if len(labels) != 1 else ''}",
                    ""
                ]

                for label in labels:
                    title = label.get("title", "Untitled")
                    label_id = label.get("_id", "")

                    lines.append(f"## {title}")
                    lines.append(f"- **ID**: {label_id}")
                    lines.append("")

                result = "\n".join(lines)
                return _truncate_response(result, len(labels))

            else:  # JSON format
                response = {
                    "total": len(labels),
                    "labels": [
                        {
                            "id": l.get("_id"),
                            "title": l.get("title")
                        }
                        for l in labels
                    ]
                }
                result = json.dumps(response, indent=2)
                return _truncate_response(result, len(labels))

        except Exception as e:
            return _handle_api_error(e)

    @mcp.tool(
        name="marvin_get_children",
        annotations={
            "title": "Get Items in Category/Project",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_get_children(params: GetChildrenInput, ctx: Context) -> str:
        """
        Get all tasks and projects within a specific category or project in Amazing Marvin.

        Args:
            params (GetChildrenInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: List of child items formatted as markdown or JSON
        """
        try:
            # Make API request
            items = await _make_api_request(
                "/children",
                ctx,
                params={"parentId": params.parent_id}
            )

            if not items:
                return f"No items found under parent ID: {params.parent_id}"

            # Format response based on requested format
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [
                    f"# Items in: {params.parent_id}",
                    "",
                    f"Found {len(items)} item{'s' if len(items) != 1 else ''}",
                    ""
                ]

                for item in items:
                    status = "✅" if item.get("done") else "⬜"
                    title = item.get("title", "Untitled")
                    item_type = item.get("type", "task")
                    item_id = item.get("_id", "")

                    type_emoji = "📁" if item_type == "project" else status
                    lines.append(f"## {type_emoji} {title} ({item_type})")
                    lines.append(f"- **ID**: {item_id}")
                    lines.append(f"- **Type**: {item_type}")

                    if item.get("dueDate"):
                        lines.append(f"- **Due**: {_format_timestamp(item.get('dueDate'))}")
                    if item.get("timeEstimate"):
                        lines.append(f"- **Estimate**: {_format_time_estimate(item.get('timeEstimate'))}")
                    if item.get("note"):
                        note = item.get("note", "")[:150]
                        lines.append(f"- **Note**: {note}")

                    lines.append("")

                result = "\n".join(lines)
                return _truncate_response(result, len(items))

            else:  # JSON format
                response = {
                    "parent_id": params.parent_id,
                    "total": len(items),
                    "items": [
                        {
                            "id": i.get("_id"),
                            "title": i.get("title"),
                            "type": i.get("type"),
                            "done": i.get("done", False),
                            "dueDate": _format_timestamp(i.get("dueDate")) if i.get("dueDate") else None,
                            "timeEstimate": _format_time_estimate(i.get("timeEstimate")) if i.get("timeEstimate") else None,
                            "note": i.get("note")
                        }
                        for i in items
                    ]
                }
                result = json.dumps(response, indent=2)
                return _truncate_response(result, len(items))

        except Exception as e:
            return _handle_api_error(e)

    # ============================================================================
    # Tool Implementations - Tier 3: Time Management
    # ============================================================================

    @mcp.tool(
        name="marvin_start_tracking",
        annotations={
            "title": "Start Time Tracking",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def marvin_start_tracking(params: StartTrackingInput, ctx: Context) -> str:
        """
        Start time tracking for a specific task in Amazing Marvin.

        Args:
            params (StartTrackingInput): Validated input parameters
            ctx (Context): Smithery context with session configuration

        Returns:
            str: Success confirmation with task ID
        """
        try:
            # Make API request using the /track endpoint with START action
            await _make_api_request(
                "/track",
                ctx,
                method="POST",
                data={"itemId": params.item_id, "action": "START"}
            )

            return (
                f"⏱️ Timer started for task!\n\n"
                f"**Task ID**: {params.item_id}\n\n"
                f"_Note: Any previously running timer has been stopped._"
            )

        except Exception as e:
            return _handle_api_error(e)

    @mcp.tool(
        name="marvin_stop_tracking",
        annotations={
            "title": "Stop Time Tracking",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def marvin_stop_tracking(ctx: Context) -> str:
        """
        Stop the currently running time tracker in Amazing Marvin.

        Args:
            ctx (Context): Smithery context with session configuration

        Returns:
            str: Success confirmation
        """
        try:
            # Make API request using the /track endpoint with STOP action
            await _make_api_request(
                "/track",
                ctx,
                method="POST",
                data={"action": "STOP"}
            )

            return (
                "⏱️ Timer stopped successfully!\n\n"
                "_Time tracking has been saved to the task._"
            )

        except Exception as e:
            return _handle_api_error(e)

    # Return the configured server
    return mcp
