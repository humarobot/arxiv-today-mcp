# arXiv MCP Server

一个 MCP（模型上下文协议）服务器，让 Claude 等 LLM 能够直接搜索和获取 arXiv 论文。

[English](README.md)

### 功能特性

- 从任意 arXiv 分类抓取最新论文并存储到本地数据库
- 灵活查询论文——支持按日期、分类、标题、论文 ID 筛选
- 按需获取感兴趣论文的完整摘要
- 清理本地数据库中的旧论文
- 按发布日期和分类统计数据库中的论文数量

### 工具列表

| 工具 | 参数 | 功能 |
|------|------|------|
| `fetch_papers` | `category`, `date=None`, `num_days=3`, `max_results=100` | 从 arXiv API 抓取最新论文，存入本地数据库 |
| `count_papers_on_date` | `category`, `date` | 查询某天某分类的论文数量 |
| `query_papers` | `date=None`, `categories=None`, `title=None`, `entry_ids=None`, `fields=None`, `max_results=500` | 查询本地数据库，支持灵活过滤和字段选择 |
| `cleanup_papers` | `before_date=None`, `date=None`, `categories=None` | 按日期和/或分类删除论文 |
| `get_stats` | — | 按发布日期和热门分类统计论文数量 |

**设计原则**：`fetch_papers` 和 `query_papers` 默认只返回标题和元数据以节省上下文。需要摘要时使用 `query_papers(fields=["abstract"])`。

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
      "args": ["arxiv-today-mcp"]
    }
  }
}
```

### 使用示例

1. **浏览今日论文**：问 Claude "今天 cs.AI 有什么新论文？"——Claude 会调用 `fetch_papers` 和 `query_papers`，按主题分类返回标题。
2. **获取详情**："介绍一下第 2、5 篇"——Claude 会调用 `query_papers` 并指定 `fields=["abstract"]` 获取摘要并进行解读。

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
