"""
Email report generator for daily news digest
Sends HTML-formatted emails with news summaries
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import os


class EmailReportGenerator:
    """Generate and send HTML email reports"""

    def __init__(self, smtp_config: Dict):
        """
        Initialize email generator

        Args:
            smtp_config: SMTP configuration dictionary
        """
        self.smtp_server = smtp_config.get('smtp_server')
        self.smtp_port = smtp_config.get('smtp_port')
        self.sender_email = smtp_config.get('sender_email')
        self.sender_password = smtp_config.get('sender_password')
        self.recipient_email = smtp_config.get('recipient_email')

    def generate_html_report(self, articles: List[Dict], stats: Dict) -> str:
        """
        Generate HTML report from articles

        Args:
            articles: List of article dictionaries
            stats: Database statistics

        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header .date {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .article {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .article-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        .article-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0 0 10px 0;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            margin-right: 8px;
        }}
        .badge-positive {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-negative {{
            background: #f8d7da;
            color: #721c24;
        }}
        .badge-neutral {{
            background: #e2e3e5;
            color: #383d41;
        }}
        .badge-rumor {{
            background: #fff3cd;
            color: #856404;
        }}
        .meta {{
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }}
        .meta-item {{
            margin-right: 15px;
            display: inline-block;
        }}
        .ticker {{
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        .source {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .keywords {{
            margin-top: 10px;
        }}
        .keyword-tag {{
            display: inline-block;
            background: #e8eaf6;
            color: #5c6bc0;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 6px;
            margin-bottom: 6px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #e0e0e0;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Lucas II: Finance Analyst</h1>
        <div class="date">Daily News Digest - {datetime.now().strftime("%B %d, %Y")}</div>
    </div>

    <div class="stats">
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{len(articles)}</div>
                <div class="stat-label">New Articles</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats.get('rumors_count', 0)}</div>
                <div class="stat-label">Rumors</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats.get('sentiment_breakdown', {}).get('positive', 0)}</div>
                <div class="stat-label">Positive</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats.get('sentiment_breakdown', {}).get('negative', 0)}</div>
                <div class="stat-label">Negative</div>
            </div>
        </div>
    </div>
"""

        # Add articles
        if not articles:
            html += """
    <div class="article">
        <p>No new articles to report today. The system is working correctly - there's just no news matching your criteria!</p>
    </div>
"""
        else:
            for i, article in enumerate(articles, 1):
                sentiment_class = f"badge-{article.get('sentiment_label', 'neutral')}"
                sentiment_label = article.get('sentiment_label', 'neutral').upper()

                rumor_badge = ''
                if article.get('is_rumor'):
                    rumor_badge = '<span class="badge badge-rumor">🔔 RUMOR</span>'

                keywords_html = ''
                if article.get('keywords'):
                    keywords_html = '<div class="keywords">'
                    for keyword in article['keywords'][:5]:  # Limit to 5 keywords
                        keywords_html += f'<span class="keyword-tag">{keyword}</span>'
                    keywords_html += '</div>'

                title = article.get('content_translated') or article.get('title', 'No title')
                source_url = article.get('source_url', '#')
                source_name = article.get('source', 'Unknown')

                html += f"""
    <div class="article">
        <div class="article-header">
            <div>
                <span class="ticker">{article.get('ticker', 'N/A')}</span>
                {rumor_badge}
                <span class="badge {sentiment_class}">{sentiment_label}</span>
            </div>
        </div>
        <h2 class="article-title">{i}. {title}</h2>
        <div class="meta">
            <span class="meta-item">📅 {article.get('published_date', 'Unknown date')}</span>
            <span class="meta-item">📰 <a href="{source_url}" class="source" target="_blank">{source_name}</a></span>
            <span class="meta-item">⭐ Relevance: {article.get('relevance_score', 0):.1%}</span>
        </div>
        {keywords_html}
    </div>
"""

        html += """
    <div class="footer">
        <p>This report was generated automatically by Lucas II Finance Analyst</p>
        <p>100% Free • No Paid APIs • Open Source</p>
    </div>
</body>
</html>
"""

        return html

    def send_email(self, subject: str, html_content: str) -> bool:
        """
        Send HTML email

        Args:
            subject: Email subject
            html_content: HTML content

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Connect to SMTP server
            print(f"Connecting to {self.smtp_server}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()

            # Login
            print("Logging in...")
            server.login(self.sender_email, self.sender_password)

            # Send email
            print(f"Sending email to {self.recipient_email}...")
            server.sendmail(self.sender_email, self.recipient_email, msg.as_string())

            # Close connection
            server.quit()

            print("✓ Email sent successfully!")
            return True

        except Exception as e:
            print(f"✗ Error sending email: {e}")
            return False

    def send_daily_report(self, articles: List[Dict], stats: Dict) -> bool:
        """
        Generate and send daily report

        Args:
            articles: List of articles to include
            stats: Database statistics

        Returns:
            True if sent successfully
        """
        subject = f"📊 Daily News Digest - {datetime.now().strftime('%b %d, %Y')}"

        # Add article count to subject
        if articles:
            subject += f" ({len(articles)} articles)"
        else:
            subject += " (No new articles)"

        html_content = self.generate_html_report(articles, stats)

        return self.send_email(subject, html_content)


def test_generator():
    """Test the email generator"""
    # Test with sample data
    sample_articles = [
        {
            'ticker': '0700.HK',
            'title': 'Tencent reports strong Q3 earnings',
            'content_translated': 'Tencent reports strong Q3 earnings',
            'source': 'Yahoo Finance',
            'source_url': 'https://finance.yahoo.com/example',
            'is_rumor': False,
            'sentiment_label': 'positive',
            'relevance_score': 0.9,
            'published_date': datetime.now(),
            'keywords': ['earnings', 'profit', 'growth']
        },
        {
            'ticker': '0941.HK',
            'title': 'China Mobile merger speculation',
            'content_translated': 'Rumors suggest potential merger talks',
            'source': 'Google News',
            'source_url': 'https://news.google.com/example',
            'is_rumor': True,
            'sentiment_label': 'neutral',
            'relevance_score': 0.7,
            'published_date': datetime.now(),
            'keywords': ['merger', 'speculation']
        }
    ]

    sample_stats = {
        'total_articles': 100,
        'articles_today': 2,
        'rumors_count': 1,
        'sentiment_breakdown': {'positive': 1, 'negative': 0, 'neutral': 1}
    }

    # Note: You need to set actual email credentials to test sending
    smtp_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'test@example.com',
        'sender_password': 'password',
        'recipient_email': 'test@example.com'
    }

    generator = EmailReportGenerator(smtp_config)

    # Generate HTML (don't send)
    html = generator.generate_html_report(sample_articles, sample_stats)

    # Save to file for preview
    with open('sample_report.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✓ Sample report generated: sample_report.html")
    print("  Open this file in a browser to preview the email")


if __name__ == "__main__":
    test_generator()
