"""
Lucas II Finance Analyst - Main Orchestrator
Coordinates all modules to scrape, analyze, and report financial news
"""
import yaml
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.scrapers.hkex_scraper import HKEXScraper
from src.scrapers.yahoo_scraper import YahooScraper
from src.scrapers.google_news_scraper import GoogleNewsScraper
from src.translation.translator import Translator
from src.sentiment.finbert_analyzer import FinBERTAnalyzer
from src.sentiment.snownlp_analyzer import SnowNLPAnalyzer
from src.reports.email_generator import EmailReportGenerator


class LucasFinanceAnalyst:
    """Main orchestrator for the finance analyst system"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the system

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.db = DatabaseManager(self.config.get('database', {}).get('path', 'data/news.db'))
        self.translator = Translator(cache_manager=self.db)
        self.finbert = FinBERTAnalyzer()
        self.snownlp = SnowNLPAnalyzer()

        print("=" * 70)
        print("Lucas II Finance Analyst - Initialized")
        print("=" * 70)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✓ Configuration loaded from {config_path}")
            return config
        except Exception as e:
            print(f"✗ Error loading config: {e}")
            print("  Using default configuration")
            return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            'watchlist': ['0700.HK'],
            'scraping': {
                'hkex_enabled': True,
                'yahoo_enabled': True,
                'google_news_enabled': True,
                'max_articles_per_source': 20,
                'days_lookback': 1
            },
            'email': {'enabled': False},
            'translation': {'enabled': True},
            'sentiment': {'use_finbert': True, 'use_snownlp': True}
        }

    def run_news_collection(self):
        """Collect news from all sources"""
        print("\n" + "=" * 70)
        print("PHASE 1: NEWS COLLECTION")
        print("=" * 70)

        watchlist = self.config.get('watchlist', [])
        scraping_config = self.config.get('scraping', {})
        days_lookback = scraping_config.get('days_lookback', 1)
        max_articles = scraping_config.get('max_articles_per_source', 20)

        all_articles = []

        for ticker in watchlist:
            print(f"\n📊 Processing {ticker}...")

            # HKEXnews
            if scraping_config.get('hkex_enabled', True):
                print("  Scraping HKEXnews...")
                hkex_scraper = HKEXScraper()
                hkex_articles = hkex_scraper.scrape_company_news(ticker, days_back=days_lookback)
                all_articles.extend(hkex_articles)

            # Yahoo Finance
            if scraping_config.get('yahoo_enabled', True):
                print("  Scraping Yahoo Finance...")
                yahoo_scraper = YahooScraper()
                yahoo_articles = yahoo_scraper.scrape_company_news(ticker, max_articles=max_articles)
                all_articles.extend(yahoo_articles)

            # Google News
            if scraping_config.get('google_news_enabled', True):
                print("  Scraping Google News...")
                # Extract company name from ticker (simplified)
                company_map = {
                    '0700.HK': 'Tencent',
                    '0941.HK': 'China Mobile',
                    '1299.HK': 'AIA',
                    '0388.HK': 'Hong Kong Exchanges',
                    '0005.HK': 'HSBC',
                    '0939.HK': 'China Construction Bank',
                    '1398.HK': 'ICBC',
                    '2318.HK': 'Ping An',
                    '0883.HK': 'CNOOC',
                    '0011.HK': 'Hang Seng Bank'
                }
                company_name = company_map.get(ticker, ticker.replace('.HK', ''))

                google_scraper = GoogleNewsScraper()
                google_articles = google_scraper.scrape_company_news(
                    company_name, ticker, max_articles=max_articles, days_back=days_lookback
                )
                all_articles.extend(google_articles)

        print(f"\n✓ Total articles collected: {len(all_articles)}")
        return all_articles

    def process_articles(self, articles: list):
        """Translate and analyze sentiment for articles"""
        print("\n" + "=" * 70)
        print("PHASE 2: TRANSLATION & SENTIMENT ANALYSIS")
        print("=" * 70)

        translation_enabled = self.config.get('translation', {}).get('enabled', True)
        sentiment_config = self.config.get('sentiment', {})

        processed_count = 0

        for i, article in enumerate(articles, 1):
            print(f"\rProcessing article {i}/{len(articles)}...", end='', flush=True)

            # Skip if already exists in database
            if self.db.check_if_exists(article['title'], article['source']):
                continue

            # Translation
            if translation_enabled and article.get('language') == 'zh':
                original_text = article.get('content_original') or article.get('title')
                translated = self.translator.translate(original_text)
                article['content_translated'] = translated
            else:
                article['content_translated'] = article.get('content_original') or article.get('title')

            # Sentiment analysis
            text_for_sentiment = article['content_translated'] or article['title']

            if article.get('language') == 'zh' and sentiment_config.get('use_snownlp', True):
                # Use SnowNLP for Chinese
                sentiment = self.snownlp.analyze(article['content_original'])
            elif sentiment_config.get('use_finbert', True):
                # Use FinBERT for English
                sentiment = self.finbert.analyze(text_for_sentiment)
            else:
                sentiment = {'label': 'neutral', 'score': 0.0, 'confidence': 0.5}

            if sentiment:
                article['sentiment_label'] = sentiment['label']
                article['sentiment_score'] = sentiment['score']
                article['sentiment_confidence'] = sentiment['confidence']

            # Save to database
            try:
                self.db.insert_article(article)
                processed_count += 1
            except Exception as e:
                print(f"\n  Error saving article: {e}")

        print(f"\n✓ Processed and saved {processed_count} new articles")

    def generate_report(self):
        """Generate and optionally send email report"""
        print("\n" + "=" * 70)
        print("PHASE 3: REPORT GENERATION")
        print("=" * 70)

        report_config = self.config.get('report', {})
        max_items = report_config.get('max_items', 15)

        # Get top articles (excluding already reported)
        articles = self.db.get_top_articles(
            limit=max_items,
            exclude_duplicates=True,
            exclude_reported=True,
            max_age_days=7
        )

        # Get statistics
        stats = self.db.get_statistics()

        print(f"\n📊 Report Statistics:")
        print(f"  • Articles in report: {len(articles)}")
        print(f"  • Total in database: {stats.get('total_articles', 0)}")
        print(f"  • Rumors detected: {stats.get('rumors_count', 0)}")
        print(f"  • Sentiment: {stats.get('sentiment_breakdown', {})}")

        # Send email if enabled
        email_config = self.config.get('email', {})
        if email_config.get('enabled', False):
            print("\n📧 Sending email report...")
            email_generator = EmailReportGenerator(email_config)

            if email_generator.send_daily_report(articles, stats):
                # Mark articles as reported
                article_ids = [a['id'] for a in articles if 'id' in a]
                self.db.mark_as_reported(article_ids)
        else:
            print("\n⚠ Email disabled in config. Generating HTML preview...")
            email_generator = EmailReportGenerator({})
            html = email_generator.generate_html_report(articles, stats)

            # Save to file
            output_path = f"report_{datetime.now().strftime('%Y%m%d')}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✓ Report saved to: {output_path}")

    def run(self):
        """Run the complete workflow"""
        start_time = datetime.now()

        print(f"\n🚀 Starting news analysis workflow at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Step 1: Collect news
            articles = self.run_news_collection()

            if not articles:
                print("\n⚠ No articles collected. Exiting.")
                return

            # Step 2: Process articles
            self.process_articles(articles)

            # Step 3: Generate report
            self.generate_report()

            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print("\n" + "=" * 70)
            print(f"✓ Workflow completed in {duration:.1f} seconds")
            print("=" * 70)

        except KeyboardInterrupt:
            print("\n\n⚠ Workflow interrupted by user")
        except Exception as e:
            print(f"\n\n✗ Error in workflow: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    analyst = LucasFinanceAnalyst()
    analyst.run()


if __name__ == "__main__":
    main()
