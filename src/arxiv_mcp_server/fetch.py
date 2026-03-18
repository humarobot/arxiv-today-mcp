import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from arxiv import Client, Search, SortCriterion, SortOrder

from arxiv_mcp_server.models import ArxivPaper


def count_papers(category: str, date: str) -> int:
    """Count papers published on a specific date via the arXiv API.

    Uses date range in the query to avoid scanning unrelated papers.

    Args:
        category: arXiv category (e.g. "cs.AI", "cs.CL")
        date: Date string in YYYY-MM-DD format

    Returns:
        Number of papers published on that date.
    """
    target_date = datetime.fromisoformat(date).date()
    # Use next day as exclusive upper bound
    next_date = target_date + timedelta(days=1)
    date_str = target_date.strftime("%Y%m%d")
    next_str = next_date.strftime("%Y%m%d")

    search = Search(
        query=f"cat:{category} AND submittedDate:[{date_str}0000 TO {next_str}0000]",
        sort_by=SortCriterion.SubmittedDate,
        sort_order=SortOrder.Descending,
    )

    client = Client()
    count = sum(1 for _ in client.results(search))
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
        query = f"cat:{category}"

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
