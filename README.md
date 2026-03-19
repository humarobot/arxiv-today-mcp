# arXiv MCP Server

An MCP (Model Context Protocol) server that lets LLMs like Claude search and fetch arXiv papers directly.

[中文文档](README_CN.md)

### Features

- Fetch recent papers from any arXiv category and store them locally
- Query papers with flexible filtering by date, category, title, and entry ID
- Retrieve full abstracts on demand for papers of interest
- Clean up old papers from the local database
- Database statistics by publication date and category

### Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `fetch_papers` | `category`, `date=None`, `num_days=3`, `max_results=100` | Fetch recent papers from arXiv API and store in local database |
| `count_papers_on_date` | `category`, `date` | Count how many papers were published in a category on a specific date |
| `query_papers` | `date=None`, `categories=None`, `title=None`, `entry_ids=None`, `fields=None`, `max_results=500` | Query local database with flexible filtering and field selection |
| `cleanup_papers` | `before_date=None`, `date=None`, `categories=None` | Delete papers by date and/or category |
| `get_stats` | — | Paper counts by publication date and top categories |

**Design principle**: `fetch_papers` and `query_papers` return only titles and metadata by default to save context. Use `query_papers(fields=["abstract"])` when you need abstracts for specific papers.

### Installation

#### Claude Code (recommended)

Add to your `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uvx",
      "args": ["arxiv-today-mcp"],
      "type": "stdio"
    }
  }
}
```

#### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uvx",
      "args": ["arxiv-today-mcp"]
    }
  }
}
```

### Usage Example

1. **Browse today's papers**: Ask Claude "What's new in cs.AI today?" — Claude will call `fetch_papers` then `query_papers`, returning titles grouped by topic.
2. **Get details**: "Tell me more about papers 2 and 5" — Claude will call `query_papers` with those entry IDs and `fields=["abstract"]` to summarize the abstracts.

### Configuration

The database path can be overridden with an environment variable:

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uvx",
      "args": ["arxiv-today-mcp"],
      "env": {
        "ARXIV_MCP_DB_PATH": "/your/custom/path/papers.db"
      }
    }
  }
}
```

### Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) or [uvx](https://docs.astral.sh/uv/guides/tools/)
