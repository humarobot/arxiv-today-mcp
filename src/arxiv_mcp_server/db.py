import logging
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

from arxiv_mcp_server.models import ArxivPaper, ArxivStats


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
            authors=row[5].split(","),
            categories=row[6].split(","),
            viewed=(row[7] == 1),
        )

    def save_papers(self, papers: List[ArxivPaper]):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_id FROM papers")
            existing_ids = set(row[0] for row in cursor.fetchall())

            num_inserted = 0
            num_updated = 0
            for paper in papers:
                if paper.entry_id in existing_ids:
                    cursor.execute(
                        """
                        UPDATE papers SET
                            updated=?,
                            published=?,
                            title=?,
                            summary=?,
                            authors=?,
                            categories=?
                        WHERE entry_id=?
                    """,
                        (
                            paper.updated.isoformat(),
                            paper.published.isoformat(),
                            paper.title,
                            paper.summary,
                            ",".join(paper.authors),
                            ",".join(paper.categories),
                            paper.entry_id,
                        ),
                    )
                    num_updated += 1
                else:
                    cursor.execute(
                        """
                        INSERT INTO papers (
                            entry_id, updated, published, title, summary,
                            authors, categories, viewed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            paper.entry_id,
                            paper.updated.isoformat(),
                            paper.published.isoformat(),
                            paper.title,
                            paper.summary,
                            ",".join(paper.authors),
                            ",".join(paper.categories),
                            0,
                        ),
                    )
                    num_inserted += 1

            conn.commit()

        logging.info(f"Inserted {num_inserted} papers")
        logging.info(f"Updated {num_updated} papers")

    def get_papers(
        self, published_after: Optional[datetime] = None
    ) -> List[ArxivPaper]:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            if published_after is not None:
                cursor.execute(
                    """
                    SELECT entry_id, updated, published, title, summary,
                           authors, categories, viewed
                    FROM papers
                    WHERE published >= ?
                    ORDER BY published ASC
                """,
                    (published_after.isoformat(),),
                )
            else:
                cursor.execute(
                    """
                    SELECT entry_id, updated, published, title, summary,
                           authors, categories, viewed
                    FROM papers
                    ORDER BY published ASC
                """
                )

            papers = []
            for row in cursor.fetchall():
                papers.append(self.convert_to_paper(row))

        return papers

    def search_papers(self, query: str) -> List[ArxivPaper]:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT entry_id, updated, published, title, summary,
                       authors, categories, viewed
                FROM papers
                WHERE title LIKE ? OR summary LIKE ?
                ORDER BY published ASC
            """,
                (f"%{query}%", f"%{query}%"),
            )

            papers = []
            for row in cursor.fetchall():
                papers.append(self.convert_to_paper(row))

        return papers

    def get_stats(self) -> List[ArxivStats]:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DATE(published) as date, COUNT(*) as count
                FROM papers
                GROUP BY DATE(published)
                ORDER BY DATE(published) ASC
            """
            )

            stats = []
            for row in cursor.fetchall():
                stats.append(ArxivStats(date=row[0], count=row[1]))

        return stats
