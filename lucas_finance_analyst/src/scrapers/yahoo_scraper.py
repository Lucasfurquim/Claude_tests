"""
Yahoo Finance news scraper
Source: Yahoo Finance via yfinance library
"""
import yfinance as yf
from datetime import datetime
from typing import List, Dict
import re


class YahooScraper:
    """Scraper for Yahoo Finance news"""

    # Rumor indicators
    RUMOR_KEYWORDS = [
        "rumor", "rumour", "speculation", "alleged", "unconfirmed",
        "reportedly", "sources say", "insider claims", "whispers",
        "could be", "might be", "potential", "possible",
        "市场传闻", "传言", "据悉", "传", "有消息称", "知情人士"
    ]

    # Important keywords
    IMPORTANT_KEYWORDS = [
        "earnings", "profit", "loss", "revenue", "dividend",
        "acquisition", "merger", "takeover", "buyout",
        "regulation", "investigation", "lawsuit", "settlement",
        "ceo", "chairman", "resignation", "appointment",
        "profit warning", "guidance", "forecast", "upgrade", "downgrade",
        "analyst", "rating", "price target",
        "盈利", "收益", "亏损", "营收", "股息",
        "收购", "合并", "监管", "调查", "诉讼"
    ]

    def scrape_company_news(self, ticker: str, max_articles: int = 20) -> List[Dict]:
        """
        Scrape news for a company from Yahoo Finance

        Args:
            ticker: Stock ticker (e.g., "0700.HK")
            max_articles: Maximum number of articles to return

        Returns:
            List of news articles
        """
        articles = []

        try:
            stock = yf.Ticker(ticker)
            news_items = stock.news

            if not news_items:
                print(f"  No news found for {ticker} on Yahoo Finance")
                return articles

            for item in news_items[:max_articles]:
                try:
                    article = self._parse_news_item(item, ticker)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"  Error parsing news item: {e}")
                    continue

            print(f"✓ Scraped {len(articles)} articles from Yahoo Finance for {ticker}")

        except Exception as e:
            print(f"✗ Error scraping Yahoo Finance for {ticker}: {e}")

        return articles

    def _parse_news_item(self, item: Dict, ticker: str) -> Dict:
        """Parse a single Yahoo Finance news item"""

        title = item.get('title', '')
        link = item.get('link', '')
        publisher = item.get('publisher', 'Yahoo Finance')
        timestamp = item.get('providerPublishTime', None)

        if not title:
            return None

        # Convert timestamp to datetime
        if timestamp:
            published_date = datetime.fromtimestamp(timestamp)
        else:
            published_date = datetime.now()

        # Detect language
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', title))
        language = 'zh' if is_chinese else 'en'

        # Detect rumors
        is_rumor, rumor_confidence = self._detect_rumor(title)

        # Calculate relevance
        relevance_score = self._calculate_relevance(title)

        # Extract keywords
        keywords = self._extract_keywords(title)

        article = {
            'ticker': ticker,
            'company_name': None,
            'title': title,
            'content_original': title,
            'content_translated': None,
            'language': language,
            'source': f'Yahoo Finance ({publisher})',
            'source_url': link,
            'is_rumor': is_rumor,
            'rumor_confidence': rumor_confidence,
            'published_date': published_date,
            'relevance_score': relevance_score,
            'keywords': keywords,
        }

        return article

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

        # Yahoo Finance is semi-reliable, so rumor confidence is moderate
        confidence = min(rumor_count * 0.3, 0.9)
        return rumor_count > 0, confidence

    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score based on important keywords"""
        text_lower = text.lower()
        matches = sum(1 for keyword in self.IMPORTANT_KEYWORDS if keyword in text_lower)

        if matches == 0:
            return 0.4  # Base relevance for Yahoo Finance news

        score = min(0.4 + (matches * 0.2), 1.0)
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
    """Test the Yahoo Finance scraper"""
    scraper = YahooScraper()

    print("Testing Yahoo Finance scraper with Tencent (0700.HK)...")
    articles = scraper.scrape_company_news("0700.HK")

    print(f"\nFound {len(articles)} articles")

    if articles:
        print("\nSample articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Rumor: {article['is_rumor']} ({article['rumor_confidence']:.2f})")
            print(f"   Relevance: {article['relevance_score']:.2f}")
            print(f"   Keywords: {article['keywords']}")


if __name__ == "__main__":
    test_scraper()
