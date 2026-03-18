import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, List, Optional, Tuple

from arxiv_mcp_server.models import ArxivPaper, ArxivStats, CategoryStats, EnhancedStats


class ArxivDatabase:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.create_database()

    def create_database(self):
        logging.info(f"Create database at {self.database_path}")
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    entry_id TEXT PRIMARY KEY,
                    updated TIMESTAMP,
                    published TIMESTAMP,
                    title TEXT,
                    summary TEXT,
                    authors TEXT,
                    categories TEXT,
                    viewed BOOLEAN DEFAULT 0
                )
            """
            )
            conn.commit()

    @staticmethod
    def convert_to_paper(row: Tuple) -> ArxivPaper:
        return ArxivPaper(
            entry_id=row[0],
            updated=datetime.fromisoformat(row[1]),
            published=datetime.fromisoformat(row[2]),
            title=row[3],
            summary=row[4],
            authors=json.loads(row[5]),
            categories=json.loads(row[6]),
            viewed=(row[7] == 1),
        )

    def save_papers(self, papers: List[ArxivPaper]):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO papers (
                    entry_id, updated, published, title, summary,
                    authors, categories, viewed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    (
                        paper.entry_id,
                        paper.updated.isoformat(),
                        paper.published.isoformat(),
                        paper.title,
                        paper.summary,
                        json.dumps(paper.authors),
                        json.dumps(paper.categories),
                        0,
                    )
                    for paper in papers
                ],
            )
            conn.commit()

        logging.info(f"Saved {len(papers)} papers")


    @staticmethod
    def _escape_like(s: str) -> str:
        """Escape LIKE special characters (\\, %, _) for use with ESCAPE '\\'."""
        return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def query_papers(
        self,
        date: Optional[str] = None,
        categories: Optional[List[str]] = None,
        title: Optional[str] = None,
        entry_ids: Optional[List[str]] = None,
        max_results: int = 500,
    ) -> List[ArxivPaper]:
        conditions = []
        params: List[Any] = []

        if date:
            conditions.append("DATE(published) = ?")
            params.append(date)

        if categories:
            cat_clauses = ["categories LIKE ? ESCAPE '\\'" for _ in categories]
            conditions.append("(" + " OR ".join(cat_clauses) + ")")
            params.extend(f'%"{self._escape_like(c)}"%' for c in categories)

        if title:
            conditions.append("title LIKE ?")
            params.append(f"%{title}%")

        if entry_ids:
            placeholders = ",".join("?" for _ in entry_ids)
            conditions.append(f"entry_id IN ({placeholders})")
            params.extend(entry_ids)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT entry_id, updated, published, title, summary,
                   authors, categories, viewed
            FROM papers
            {where}
            ORDER BY published DESC
            LIMIT ?
        """
        params.append(max_results)

        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [self.convert_to_paper(row) for row in cursor.fetchall()]

    def get_enhanced_stats(self, top_n_categories: int = 20) -> EnhancedStats:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*), MIN(DATE(published)), MAX(DATE(published)) FROM papers"
            )
            row = cursor.fetchone()
            total, earliest, latest = row[0], row[1], row[2]

            cursor.execute(
                """
                SELECT DATE(published), COUNT(*)
                FROM papers
                GROUP BY DATE(published)
                ORDER BY DATE(published) ASC
                """
            )
            by_date = [ArxivStats(date=r[0], count=r[1]) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT value, COUNT(*)
                FROM papers, json_each(papers.categories)
                GROUP BY value
                ORDER BY COUNT(*) DESC
                LIMIT ?
                """,
                (top_n_categories,),
            )
            by_category = [
                CategoryStats(category=r[0], count=r[1]) for r in cursor.fetchall()
            ]

        return EnhancedStats(
            total_papers=total,
            earliest_date=earliest,
            latest_date=latest,
            by_date=by_date,
            by_category=by_category,
        )
