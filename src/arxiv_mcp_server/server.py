import json
import logging
import sys
from typing import List

from mcp.server.fastmcp import FastMCP

from arxiv_mcp_server.config import DATABASE_PATH
from arxiv_mcp_server.db import ArxivDatabase
from arxiv_mcp_server.fetch import download_papers

# Configure logging to stderr so stdout stays clean for stdio transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("arxiv")


def _get_db() -> ArxivDatabase:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return ArxivDatabase(str(DATABASE_PATH))


def _paper_title_entry(paper) -> dict:
    """Return lightweight title-only dict for a paper."""
    return {
        "entry_id": paper.entry_id,
        "title": paper.title,
        "authors": paper.authors[:3],  # first 3 authors only
        "categories": paper.categories,
        "published": paper.published.date().isoformat(),
        "url": paper.entry_id,
    }


@mcp.tool()
def fetch_papers(
    category: str, num_days: int = 3, max_results: int = 100
) -> str:
    """Fetch recent papers from arXiv API and store them in the local database.

    Returns only paper titles (not abstracts) to save context.
    Use get_paper_details() to retrieve abstracts for specific papers.

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
            "papers": [_paper_title_entry(p) for p in papers],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def list_papers(date: str = "", max_results: int = 100) -> str:
    """List paper titles from the local database, optionally filtered by date.

    Returns only titles and metadata (no abstracts) to save context.
    Use get_paper_details() to retrieve abstracts for papers of interest.

    Args:
        date: Filter by publication date in YYYY-MM-DD format (e.g. "2024-01-15").
              Leave empty to list all stored papers.
        max_results: Maximum number of results to return (default: 100)
    """
    logger.info(f"Listing papers: date={date!r}, max={max_results}")
    db = _get_db()

    if date:
        from datetime import datetime
        published_after = datetime.fromisoformat(date)
        papers = db.get_papers(published_after=published_after)
        # Also filter to same day
        papers = [p for p in papers if p.published.date().isoformat() == date]
    else:
        papers = db.get_papers()

    papers = papers[:max_results]
    return json.dumps(
        {
            "total": len(papers),
            "papers": [_paper_title_entry(p) for p in papers],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def search_papers(query: str, max_results: int = 100) -> str:
    """Search for papers in the local database by keyword.

    Performs case-insensitive search against titles and abstracts,
    but returns only titles (no abstracts) to save context.
    Use get_paper_details() to retrieve abstracts for matched papers.

    Args:
        query: Search keyword or phrase
        max_results: Maximum number of results to return (default: 100)
    """
    logger.info(f"Searching papers: query={query!r}, max={max_results}")
    db = _get_db()
    papers = db.search_papers(query)[:max_results]
    return json.dumps(
        {
            "query": query,
            "total_results": len(papers),
            "papers": [_paper_title_entry(p) for p in papers],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def get_paper_details(entry_ids: List[str]) -> str:
    """Get full details including abstracts for specific papers by their entry IDs.

    Use this after list_papers or search_papers when the user wants to know
    more about specific papers. Pass the entry_id values from previous results.

    Args:
        entry_ids: List of arXiv entry IDs (e.g. ["http://arxiv.org/abs/2401.12345v1"])
    """
    logger.info(f"Getting details for {len(entry_ids)} papers")
    db = _get_db()
    all_papers = db.get_papers()
    id_set = set(entry_ids)
    matched = [p for p in all_papers if p.entry_id in id_set]

    return json.dumps(
        {
            "total": len(matched),
            "papers": [p.model_dump(mode="json") for p in matched],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def get_stats() -> str:
    """Get statistics about papers stored in the local database.

    Returns the count of papers grouped by publication date.
    """
    logger.info("Getting stats")
    db = _get_db()
    stats = db.get_stats()
    return json.dumps(
        {
            "total_papers": sum(s.count for s in stats),
            "by_date": [s.model_dump() for s in stats],
        },
        ensure_ascii=False,
        indent=2,
    )
