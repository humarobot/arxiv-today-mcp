from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ArxivStats(BaseModel):
    date: str
    count: int


class CategoryStats(BaseModel):
    category: str
    count: int


class EnhancedStats(BaseModel):
    total_papers: int
    earliest_date: Optional[str]
    latest_date: Optional[str]
    by_date: List[ArxivStats]
    by_category: List[CategoryStats]


class ArxivPaper(BaseModel):
    entry_id: str
    updated: datetime
    published: datetime
    title: str
    summary: str
    authors: List[str]
    categories: List[str]
    viewed: bool
