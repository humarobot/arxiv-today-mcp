import logging
from datetime import datetime, timedelta, timezone
from typing import List

from arxiv import Client, Search, SortCriterion, SortOrder

from arxiv_mcp_server.models import ArxivPaper


def download_papers(
    category: str, num_days: int, max_results: int = -1
) -> List[ArxivPaper]:
    current_date = datetime.now(timezone.utc).date()

    start_date = datetime.combine(current_date, datetime.min.time()).replace(
        tzinfo=timezone.utc
    ) - timedelta(days=num_days - 1)
    end_date = datetime.combine(current_date, datetime.max.time()).replace(
        tzinfo=timezone.utc
    )

    search = Search(
        query=f"cat:{category}",
        sort_by=SortCriterion.SubmittedDate,
        sort_order=SortOrder.Descending,
    )

    client = Client()
    papers = []

    for i, result in enumerate(client.results(search)):
        if max_results > 0 and i >= max_results:
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
