import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from arxiv import Client, Search, SortCriterion, SortOrder

from arxiv_mcp_server.models import ArxivPaper


def count_papers(category: str, date: str, max_results: int = 500) -> int:
    """Count papers published on a specific date via the arXiv API.

    Uses date range in the query to avoid scanning unrelated papers.

    Args:
        category: arXiv category (e.g. "cs.AI", "cs.CL")
        date: Date string in YYYY-MM-DD format
        max_results: Maximum number of papers to count (default: 500)

    Returns:
        Number of papers published on that date (capped at max_results).
    """
    target_date = datetime.fromisoformat(date).date()
    next_date = target_date + timedelta(days=1)
    date_str = target_date.strftime("%Y%m%d")
    next_str = next_date.strftime("%Y%m%d")

    search = Search(
        query=f"cat:{category} AND submittedDate:[{date_str}0000 TO {next_str}0000]",
        sort_by=SortCriterion.SubmittedDate,
        sort_order=SortOrder.Descending,
    )

    client = Client()
    count = 0
    for _ in client.results(search):
        count += 1
        if count >= max_results:
            break
    return count


def download_papers(
    category: str, num_days: int = 3, max_results: int = -1, date: Optional[str] = None
) -> List[ArxivPaper]:
    if date is not None:
        target_date = datetime.fromisoformat(date).date()
        next_date = target_date + timedelta(days=1)
        date_str = target_date.strftime("%Y%m%d")
        next_str = next_date.strftime("%Y%m%d")
        start_date = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_date = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        query = f"cat:{category} AND submittedDate:[{date_str}0000 TO {next_str}0000]"
    else:
        current_date = datetime.now(timezone.utc).date()
        start_date = datetime.combine(current_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        ) - timedelta(days=num_days - 1)
        end_date = datetime.combine(current_date, datetime.max.time()).replace(
            tzinfo=timezone.utc
        )
        start_str = start_date.strftime("%Y%m%d")
        end_str = (current_date + timedelta(days=1)).strftime("%Y%m%d")
        query = f"cat:{category} AND submittedDate:[{start_str}0000 TO {end_str}0000]"

    search = Search(
        query=query,
        sort_by=SortCriterion.SubmittedDate,
        sort_order=SortOrder.Descending,
    )

    client = Client()
    papers = []

    for result in client.results(search):
        if max_results > 0 and len(papers) >= max_results:
            break

        paper = ArxivPaper(
            entry_id=result.entry_id,
            updated=result.updated,
            published=result.published,
            title=result.title,
            summary=result.summary,
            authors=[a.name for a in result.authors],
            categories=result.categories,
            viewed=False,
        )
        if paper.published >= start_date and paper.published <= end_date:
            papers.append(paper)
        elif paper.published < start_date:
            break

    return papers
