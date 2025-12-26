"""
HKEXnews scraper - Official Hong Kong Stock Exchange announcements
Source: https://www.hkexnews.hk
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import re
import time


class HKEXScraper:
    """Scraper for HKEX official announcements"""

    BASE_URL = "https://www1.hkexnews.hk"
    SEARCH_URL = f"{BASE_URL}/search/titlesearch.xhtml"

    # Rumor indicators - words that suggest speculation or unconfirmed info
    RUMOR_KEYWORDS = [
        "rumor", "rumour", "speculation", "alleged", "unconfirmed",
        "reportedly", "sources say", "insider claims", "whispers",
        "市场传闻", "传言", "据悉", "传", "有消息称", "知情人士"
    ]

    # Important keywords for relevance scoring
    IMPORTANT_KEYWORDS = [
        "earnings", "profit", "loss", "revenue", "dividend",
        "acquisition", "merger", "takeover", "buyout",
        "regulation", "investigation", "lawsuit", "settlement",
        "ceo", "chairman", "resignation", "appointment",
        "profit warning", "guidance", "forecast",
        "盈利", "收益", "亏损", "营收", "股息",
        "收购", "合并", "监管", "调查", "诉讼"
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_company_news(self, ticker: str, days_back: int = 1) -> List[Dict]:
        """
        Scrape news for a specific HKEX company

        Args:
            ticker: HKEX stock code (e.g., "0700" for Tencent)
            days_back: How many days to look back

        Returns:
            List of news articles with metadata
        """
        articles = []

        # Remove .HK suffix if present
        stock_code = ticker.replace(".HK", "").replace(".", "").zfill(5)

        try:
            # Search for company announcements
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
            to_date = datetime.now().strftime("%Y%m%d")

            # HKEXnews search parameters
            params = {
                'sortDir': '0',  # 0 = descending (newest first)
                'sortBy': 'datetime',
                'dateOfReleaseFrom': from_date,
                'dateOfReleaseTo': to_date,
                'stockId': stock_code,
                'documentType': '-1',  # All types
                't1code': '-2',  # All categories
                't2Gcode': '-2',
                't2code': '-2',
                'rowRange': '100',  # Get up to 100 results
            }

            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all announcement rows
            rows = soup.find_all('div', class_='row')

            for row in rows:
                try:
                    article = self._parse_announcement_row(row, ticker, stock_code)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue

            print(f"✓ Scraped {len(articles)} articles from HKEXnews for {ticker}")

        except Exception as e:
            print(f"✗ Error scraping HKEXnews for {ticker}: {e}")

        return articles

    def _parse_announcement_row(self, row, ticker: str, stock_code: str) -> Dict:
        """Parse a single announcement row"""

        # Extract date
        date_elem = row.find('div', class_='col-date')
        if not date_elem:
            return None

        date_text = date_elem.get_text(strip=True)
        published_date = self._parse_date(date_text)

        # Extract title and link
        title_elem = row.find('div', class_='col-dn-title')
        if not title_elem:
            return None

        title_link = title_elem.find('a')
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        doc_url = title_link.get('href', '')

        if doc_url and not doc_url.startswith('http'):
            doc_url = f"{self.BASE_URL}{doc_url}"

        # Detect language (contains Chinese characters?)
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', title))
        language = 'zh' if is_chinese else 'en'

        # Detect if this might be a rumor
        is_rumor, rumor_confidence = self._detect_rumor(title)

        # Calculate relevance score
        relevance_score = self._calculate_relevance(title)

        # Extract keywords
        keywords = self._extract_keywords(title)

        article = {
            'ticker': ticker,
            'company_name': None,  # Will be filled later
            'title': title,
            'content_original': title,  # For announcements, title is often the content
            'content_translated': None,
            'language': language,
            'source': 'HKEXnews (Official)',
            'source_url': doc_url,
            'is_rumor': is_rumor,
            'rumor_confidence': rumor_confidence,
            'published_date': published_date,
            'relevance_score': relevance_score,
            'keywords': keywords,
        }

        return article

    def _parse_date(self, date_str: str) -> datetime:
        """Parse HKEX date format"""
        try:
            # Format: DD/MM/YYYY HH:MM
            return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        except:
            try:
                # Format: DD/MM/YYYY
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                # Default to now if parsing fails
                return datetime.now()

    def _detect_rumor(self, text: str) -> tuple:
        """
        Detect if text contains rumor indicators

        Returns:
            (is_rumor, confidence_score)
        """
        text_lower = text.lower()
        rumor_count = sum(1 for keyword in self.RUMOR_KEYWORDS if keyword in text_lower)

        if rumor_count == 0:
            return False, 0.0

        # HKEXnews is official, so even if rumor keywords present, confidence is low
        # (these would be announcements ABOUT rumors, not rumors themselves)
        confidence = min(rumor_count * 0.2, 0.8)
        return True, confidence

    def _calculate_relevance(self, text: str) -> float:
        """
        Calculate relevance score based on important keywords

        Returns:
            Score from 0.0 to 1.0
        """
        text_lower = text.lower()
        matches = sum(1 for keyword in self.IMPORTANT_KEYWORDS if keyword in text_lower)

        if matches == 0:
            return 0.3  # Base relevance for official announcements

        # Scale: 1 match = 0.5, 2+ matches = 1.0
        score = min(0.3 + (matches * 0.25), 1.0)
        return score

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        text_lower = text.lower()
        found_keywords = [
            keyword for keyword in self.IMPORTANT_KEYWORDS
            if keyword in text_lower
        ]
        return found_keywords


def test_scraper():
    """Test the HKEXnews scraper"""
    scraper = HKEXScraper()

    # Test with Tencent (0700)
    print("Testing HKEXnews scraper with Tencent (0700.HK)...")
    articles = scraper.scrape_company_news("0700.HK", days_back=7)

    print(f"\nFound {len(articles)} articles")

    if articles:
        print("\nSample article:")
        article = articles[0]
        for key, value in article.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    test_scraper()
