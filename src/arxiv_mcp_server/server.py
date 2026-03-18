import json
import logging
import sys
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from arxiv_mcp_server.config import DATABASE_PATH
from arxiv_mcp_server.db import ArxivDatabase
from arxiv_mcp_server.fetch import count_papers, download_papers

# Configure logging to stderr so stdout stays clean for stdio transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("arxiv")

VALID_FIELDS = {"entry_id", "title", "authors", "abstract", "url", "published", "updated", "categories"}
DEFAULT_FIELDS = ["entry_id", "title", "authors", "published", "url"]


def _get_db() -> ArxivDatabase:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return ArxivDatabase(str(DATABASE_PATH))


def _build_paper_dict(paper, fields: List[str]) -> dict:
    result = {}
    for f in fields:
        if f == "abstract":
            result["abstract"] = paper.summary
        elif f == "url":
            result["url"] = paper.entry_id
        elif f == "authors":
            result["authors"] = paper.authors[:3]
        elif f == "published":
            result["published"] = paper.published.date().isoformat()
        elif f == "updated":
            result["updated"] = paper.updated.date().isoformat()
        else:
            result[f] = getattr(paper, f)
    return result


@mcp.tool()
def fetch_papers(
    category: str, num_days: int = 3, max_results: int = 100
) -> str:
    """Fetch recent papers from arXiv API and store them in the local database.

    Args:
        category: arXiv category (e.g. "cs.AI", "cs.CL", "stat.ML")
        num_days: Number of days to look back (default: 3)
        max_results: Maximum number of papers to fetch (default: 100)
    """
    logger.info(
        f"Fetching papers: category={category}, days={num_days}, max={max_results}"
    )
    papers = download_papers(category, num_days, max_results)
    db = _get_db()
    db.save_papers(papers)
    return json.dumps(
        {
            "status": "ok",
            "category": category,
            "num_days": num_days,
            "papers_fetched": len(papers),
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def count_papers_on_date(category: str, date: str) -> str:
    """Count how many papers were published in an arXiv category on a specific date.

    Use this before fetch_papers to check the volume of papers for a given day,
    so you can decide how many to fetch with fetch_papers(max_results=N).

    Args:
        category: arXiv category (e.g. "cs.AI", "cs.CL", "stat.ML")
        date: Date in YYYY-MM-DD format (e.g. "2026-03-18")
    """
    logger.info(f"Counting papers: category={category}, date={date}")
    count = count_papers(category, date)
    return json.dumps(
        {
            "category": category,
            "date": date,
            "count": count,
            "suggestion": f"Use fetch_papers(category='{category}', num_days=1, max_results={count}) to fetch them all.",
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def query_papers(
    date: Optional[str] = None,
    categories: Optional[List[str]] = None,
    title: Optional[str] = None,
    entry_ids: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,
    max_results: int = 500,
) -> str:
    """Query papers from the local database with flexible filtering and field selection.

    All filter parameters are combined with AND logic. Within categories, OR logic is used.
    If no filter parameters are provided, returns the most recent papers up to max_results.

    Args:
        date: Filter by publication date in YYYY-MM-DD format (e.g. "2026-03-18")
        categories: Filter by one or more arXiv categories (OR logic), e.g. ["cs.AI", "cs.LG"]
        title: Filter by title keyword (title field only, not abstract; case-insensitive for ASCII)
        entry_ids: Fetch specific papers by their arXiv entry IDs. Typically used alone;
                   combining with other filters applies AND logic and may return fewer results
                   than expected if the other conditions do not match.
        fields: Fields to return. Valid: entry_id, title, authors, abstract, url, published, updated, categories.
                Defaults to: entry_id, title, authors, published, url
        max_results: Maximum number of results to return (default: 500)
    """
    active_fields = fields if fields is not None else DEFAULT_FIELDS

    invalid = [f for f in active_fields if f not in VALID_FIELDS]
    if invalid:
        return json.dumps(
            {"error": f"Invalid field(s): {invalid}. Valid fields: {sorted(VALID_FIELDS)}"},
            ensure_ascii=False,
        )

    logger.info(
        f"Querying papers: date={date!r}, categories={categories}, "
        f"title={title!r}, entry_ids={entry_ids}, fields={active_fields}, max={max_results}"
    )
    db = _get_db()
    papers = db.query_papers(
        date=date,
        categories=categories,
        title=title,
        entry_ids=entry_ids,
        max_results=max_results,
    )
    return json.dumps(
        {
            "total": len(papers),
            "papers": [_build_paper_dict(p, active_fields) for p in papers],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def get_stats() -> str:
    """Get statistics about papers stored in the local database.

    Returns total count, date range, per-date breakdown, and top categories.
    """
    logger.info("Getting stats")
    db = _get_db()
    stats = db.get_enhanced_stats()
    return json.dumps(stats.model_dump(), ensure_ascii=False, indent=2)
