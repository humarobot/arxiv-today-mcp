# arXiv MCP Server

**[English](#english)** · **[中文](#中文)**

---

## English

An MCP (Model Context Protocol) server that lets LLMs like Claude search and fetch arXiv papers directly.

### Features

- Fetch recent papers from any arXiv category and store them locally
- List papers by date — titles only, to keep context lean
- Keyword search across titles and abstracts
- Retrieve full abstracts on demand for papers of interest
- Database statistics by publication date

### Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `fetch_papers` | `category`, `num_days=3`, `max_results=100` | Fetch recent papers from arXiv API and store in local database |
| `list_papers` | `date=""`, `max_results=100` | List paper titles from local database, optionally filtered by date |
| `search_papers` | `query`, `max_results=100` | Keyword search against titles and abstracts, returns titles only |
| `get_paper_details` | `entry_ids: list` | Get full details including abstracts for specific papers |
| `get_stats` | — | Paper counts grouped by publication date |

**Design principle**: `fetch_papers`, `list_papers`, and `search_papers` return only titles and metadata to save context. Call `get_paper_details` when you need abstracts for specific papers.

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
      "args": ["arxiv-mcp-server"]
    }
  }
}
```

### Usage Example

1. **Browse today's papers**: Ask Claude "What's new in cs.AI today?" — Claude will call `fetch_papers` then `list_papers`, returning titles grouped by topic.
2. **Get details**: "Tell me more about papers 2 and 5" — Claude will call `get_paper_details` with those entry IDs and summarize the abstracts.

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

---

## 中文

一个 MCP（模型上下文协议）服务器，让 Claude 等 LLM 能够直接搜索和获取 arXiv 论文。

### 功能特性

- 从任意 arXiv 分类抓取最新论文并存储到本地数据库
- 按日期浏览论文——只返回标题，节省上下文
- 对标题和摘要进行关键词搜索
- 按需获取感兴趣论文的完整摘要
- 按发布日期统计数据库中的论文数量

### 工具列表

| 工具 | 参数 | 功能 |
|------|------|------|
| `fetch_papers` | `category`, `num_days=3`, `max_results=100` | 从 arXiv API 抓取最新论文，存入本地数据库 |
| `list_papers` | `date=""`, `max_results=100` | 列出本地数据库中的论文标题，可按日期筛选 |
| `search_papers` | `query`, `max_results=100` | 在标题和摘要中关键词搜索，只返回标题 |
| `get_paper_details` | `entry_ids: list` | 获取指定论文的完整信息（含摘要） |
| `get_stats` | — | 按发布日期统计论文数量 |

**设计原则**：`fetch_papers`、`list_papers`、`search_papers` 只返回标题和元数据以节省上下文。需要摘要时再调用 `get_paper_details`。

### 安装配置

#### Claude Code（推荐）

在 `~/.claude.json` 的 `mcpServers` 中添加：

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

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uvx",
      "args": ["arxiv-mcp-server"]
    }
  }
}
```

### 使用示例

1. **浏览今日论文**：问 Claude "今天 cs.AI 有什么新论文？"——Claude 会调用 `fetch_papers` 和 `list_papers`，按主题分类返回标题。
2. **获取详情**："介绍一下第 2、5 篇"——Claude 会调用 `get_paper_details` 获取摘要并进行解读。

### 自定义数据库路径

通过环境变量覆盖默认数据库路径：

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uvx",
      "args": ["arxiv-today-mcp"],
      "env": {
        "ARXIV_MCP_DB_PATH": "/你的/自定义/路径/papers.db"
      }
    }
  }
}
```

### 依赖要求

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) 或 [uvx](https://docs.astral.sh/uv/guides/tools/)
