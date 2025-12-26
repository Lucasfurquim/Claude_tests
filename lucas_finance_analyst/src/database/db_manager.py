"""
Database manager for storing news articles, rumors, and sentiment analysis
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json


class DatabaseManager:
    """Manages SQLite database for news and sentiment data"""

    def __init__(self, db_path: str = "data/news.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # News articles table with source tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                company_name TEXT,
                title TEXT NOT NULL,
                content_original TEXT,
                content_translated TEXT,
                language TEXT,
                source TEXT NOT NULL,
                source_url TEXT,
                is_rumor BOOLEAN DEFAULT 0,
                rumor_confidence REAL,
                published_date DATETIME,
                scraped_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                sentiment_score REAL,
                sentiment_label TEXT,
                sentiment_confidence REAL,
                relevance_score REAL,
                keywords TEXT,
                is_duplicate BOOLEAN DEFAULT 0,
                duplicate_of INTEGER,
                FOREIGN KEY (duplicate_of) REFERENCES news_articles(id)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticker
            ON news_articles(ticker)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_published_date
            ON news_articles(published_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source
            ON news_articles(source)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sentiment
            ON news_articles(sentiment_label, sentiment_score)
        """)

        # Translation cache to avoid re-translating
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT UNIQUE,
                translated_text TEXT,
                source_lang TEXT,
                target_lang TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User feedback for future ML improvements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                feedback_type TEXT,
                feedback_value INTEGER,
                notes TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES news_articles(id)
            )
        """)

        # Track which articles have been sent in daily reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reported_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER UNIQUE,
                report_date DATE,
                FOREIGN KEY (article_id) REFERENCES news_articles(id)
            )
        """)

        conn.commit()
        conn.close()

    def insert_article(self, article: Dict) -> int:
        """
        Insert a news article into the database

        Args:
            article: Dictionary containing article data

        Returns:
            Article ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO news_articles (
                ticker, company_name, title, content_original, content_translated,
                language, source, source_url, is_rumor, rumor_confidence,
                published_date, sentiment_score, sentiment_label, sentiment_confidence,
                relevance_score, keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article.get('ticker'),
            article.get('company_name'),
            article.get('title'),
            article.get('content_original'),
            article.get('content_translated'),
            article.get('language'),
            article.get('source'),
            article.get('source_url'),
            article.get('is_rumor', False),
            article.get('rumor_confidence'),
            article.get('published_date'),
            article.get('sentiment_score'),
            article.get('sentiment_label'),
            article.get('sentiment_confidence'),
            article.get('relevance_score'),
            json.dumps(article.get('keywords', []))
        ))

        article_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return article_id

    def get_cached_translation(self, original_text: str) -> Optional[str]:
        """Get cached translation if exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT translated_text FROM translation_cache
            WHERE original_text = ?
        """, (original_text,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def cache_translation(self, original_text: str, translated_text: str,
                         source_lang: str = "zh", target_lang: str = "en"):
        """Cache a translation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO translation_cache
            (original_text, translated_text, source_lang, target_lang)
            VALUES (?, ?, ?, ?)
        """, (original_text, translated_text, source_lang, target_lang))

        conn.commit()
        conn.close()

    def get_recent_articles(self, days: int = 1, ticker: Optional[str] = None) -> List[Dict]:
        """Get recent articles"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT * FROM news_articles
            WHERE datetime(published_date) >= datetime('now', '-{} days')
        """.format(days)

        if ticker:
            query += " AND ticker = ?"
            cursor.execute(query, (ticker,))
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        articles = [dict(row) for row in rows]

        # Parse keywords back to list
        for article in articles:
            if article.get('keywords'):
                article['keywords'] = json.loads(article['keywords'])

        conn.close()
        return articles

    def mark_duplicate(self, article_id: int, duplicate_of: int):
        """Mark an article as duplicate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE news_articles
            SET is_duplicate = 1, duplicate_of = ?
            WHERE id = ?
        """, (duplicate_of, article_id))

        conn.commit()
        conn.close()

    def get_top_articles(self, limit: int = 15, exclude_duplicates: bool = True,
                        exclude_reported: bool = True, max_age_days: int = 7) -> List[Dict]:
        """
        Get top-ranked articles based on sentiment and relevance

        Args:
            limit: Number of articles to return
            exclude_duplicates: Whether to exclude duplicate articles
            exclude_reported: Whether to exclude already reported articles
            max_age_days: Maximum age of articles in days (default 7)

        Returns:
            List of article dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT a.* FROM news_articles a
            WHERE datetime(a.published_date) >= datetime('now', '-{} days')
        """.format(max_age_days)

        if exclude_duplicates:
            query += " AND a.is_duplicate = 0"

        if exclude_reported:
            query += """
                AND a.id NOT IN (
                    SELECT article_id FROM reported_articles
                    WHERE report_date >= date('now', '-1 days')
                )
            """

        query += """
            ORDER BY
                (ABS(a.sentiment_score) * 0.6 + a.relevance_score * 0.4) DESC,
                a.published_date DESC
            LIMIT ?
        """

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        articles = [dict(row) for row in rows]

        # Parse keywords
        for article in articles:
            if article.get('keywords'):
                article['keywords'] = json.loads(article['keywords'])

        conn.close()
        return articles

    def mark_as_reported(self, article_ids: List[int]):
        """Mark articles as reported in daily email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for article_id in article_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO reported_articles (article_id, report_date)
                VALUES (?, date('now'))
            """, (article_id,))

        conn.commit()
        conn.close()

    def check_if_exists(self, title: str, source: str, days_back: int = 7) -> bool:
        """
        Check if an article with similar title already exists

        Args:
            title: Article title
            source: News source
            days_back: How many days to look back

        Returns:
            True if exists, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM news_articles
            WHERE title = ? AND source = ?
            AND datetime(published_date) >= datetime('now', '-{} days')
        """.format(days_back), (title, source))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total articles
        cursor.execute("SELECT COUNT(*) FROM news_articles")
        stats['total_articles'] = cursor.fetchone()[0]

        # Articles today
        cursor.execute("""
            SELECT COUNT(*) FROM news_articles
            WHERE date(published_date) = date('now')
        """)
        stats['articles_today'] = cursor.fetchone()[0]

        # Rumors count
        cursor.execute("SELECT COUNT(*) FROM news_articles WHERE is_rumor = 1")
        stats['rumors_count'] = cursor.fetchone()[0]

        # Sentiment breakdown
        cursor.execute("""
            SELECT sentiment_label, COUNT(*) as count
            FROM news_articles
            WHERE datetime(published_date) >= datetime('now', '-1 days')
            GROUP BY sentiment_label
        """)
        stats['sentiment_breakdown'] = dict(cursor.fetchall())

        # Source breakdown
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM news_articles
            WHERE datetime(published_date) >= datetime('now', '-1 days')
            GROUP BY source
        """)
        stats['source_breakdown'] = dict(cursor.fetchall())

        conn.close()
        return stats
