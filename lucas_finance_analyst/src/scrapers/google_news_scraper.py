"""
Google News RSS scraper for additional news and rumors
Free RSS feed access - no API key needed
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
import re
from urllib.parse import quote


class GoogleNewsScraper:
    """Scraper for Google News RSS feeds"""

    BASE_URL = "https://news.google.com/rss/search"

    # Enhanced rumor keywords for Google News (more likely to have speculation)
    RUMOR_KEYWORDS = [
        "rumor", "rumour", "speculation", "alleged", "unconfirmed",
        "reportedly", "sources say", "insider claims", "whispers",
        "could be", "might be", "potential", "possible", "expected to",
        "plans to", "considering", "may", "sources close to",
        "市场传闻", "传言", "据悉", "传", "有消息称", "知情人士",
        "据报道", "消息人士", "据称"
    ]

    IMPORTANT_KEYWORDS = [
        "earnings", "profit", "loss", "revenue", "dividend",
        "acquisition", "merger", "takeover", "buyout",
        "regulation", "investigation", "lawsuit", "settlement",
        "ceo", "chairman", "resignation", "appointment",
        "profit warning", "guidance", "forecast", "upgrade", "downgrade",
        "analyst", "rating", "price target", "ipo", "listing",
        "盈利", "收益", "亏损", "营收", "股息",
        "收购", "合并", "监管", "调查", "诉讼", "上市"
    ]

    def scrape_company_news(self, company_name: str, ticker: str,
                           max_articles: int = 20, days_back: int = 7) -> List[Dict]:
        """
        Scrape Google News for a company

        Args:
            company_name: Company name to search for
            ticker: Stock ticker for reference
            max_articles: Maximum articles to return
            days_back: How many days to look back

        Returns:
            List of news articles
        """
        articles = []

        try:
            # Search for company name + stock market related terms
            search_query = f"{company_name} stock OR {company_name} shares"

            # Add time filter (when:7d for 7 days)
            search_query += f" when:{days_back}d"

            encoded_query = quote(search_query)
            rss_url = f"{self.BASE_URL}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

            response = requests.get(rss_url, timeout=15)
            response.raise_for_status()

            # Parse RSS XML
            root = ET.fromstring(response.content)

            # Find all items in the feed
            items = root.findall('.//item')

            for item in items[:max_articles]:
                try:
                    article = self._parse_rss_item(item, ticker, company_name)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"  Error parsing RSS item: {e}")
                    continue

            print(f"✓ Scraped {len(articles)} articles from Google News for {company_name}")

        except Exception as e:
            print(f"✗ Error scraping Google News for {company_name}: {e}")

        return articles

    def _parse_rss_item(self, item: ET.Element, ticker: str, company_name: str) -> Dict:
        """Parse a single RSS item"""

        title_elem = item.find('title')
        link_elem = item.find('link')
        pub_date_elem = item.find('pubDate')
        source_elem = item.find('source')

        if title_elem is None or title_elem.text is None:
            return None

        title = title_elem.text.strip()
        link = link_elem.text if link_elem is not None else ''

        # Parse publication date
        pub_date_str = pub_date_elem.text if pub_date_elem is not None else None
        published_date = self._parse_date(pub_date_str)

        # Get source
        source_name = source_elem.text if source_elem is not None else 'Unknown'

        # Detect language
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', title))
        language = 'zh' if is_chinese else 'en'

        # Detect rumors (Google News more likely to have speculation)
        is_rumor, rumor_confidence = self._detect_rumor(title)

        # Calculate relevance
        relevance_score = self._calculate_relevance(title)

        # Extract keywords
        keywords = self._extract_keywords(title)

        article = {
            'ticker': ticker,
            'company_name': company_name,
            'title': title,
            'content_original': title,
            'content_translated': None,
            'language': language,
            'source': f'Google News ({source_name})',
            'source_url': link,
            'is_rumor': is_rumor,
            'rumor_confidence': rumor_confidence,
            'published_date': published_date,
            'relevance_score': relevance_score,
            'keywords': keywords,
        }

        return article

    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS date format"""
        if not date_str:
            return datetime.now()

        try:
            # RSS format: Mon, 23 Dec 2024 10:30:00 GMT
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
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

        # Google News aggregates from many sources, so higher rumor confidence
        confidence = min(rumor_count * 0.35, 0.95)
        return rumor_count > 0, confidence

    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score"""
        text_lower = text.lower()
        matches = sum(1 for keyword in self.IMPORTANT_KEYWORDS if keyword in text_lower)

        if matches == 0:
            return 0.5  # Base relevance for Google News

        score = min(0.5 + (matches * 0.2), 1.0)
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
    """Test the Google News scraper"""
    scraper = GoogleNewsScraper()

    print("Testing Google News scraper with Tencent...")
    articles = scraper.scrape_company_news("Tencent", "0700.HK", max_articles=10)

    print(f"\nFound {len(articles)} articles")

    if articles:
        print("\nSample articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Rumor: {article['is_rumor']} (confidence: {article['rumor_confidence']:.2f})")
            print(f"   Relevance: {article['relevance_score']:.2f}")
            print(f"   Published: {article['published_date']}")


if __name__ == "__main__":
    test_scraper()
