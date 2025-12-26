# Lucas II Finance Analyst - Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Gmail account (for email reports)

## Installation Steps

### 1. Install Dependencies

```bash
cd lucas_finance_analyst
pip install -r requirements.txt
```

This will install all required packages (may take 5-10 minutes on first run due to FinBERT model).

### 2. Configure Email (Optional)

If you want daily email reports:

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Get a Gmail App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Create a new app password
   - Copy the 16-character password

3. Edit `.env` and add your credentials:
   ```
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-16-char-app-password
   RECIPIENT_EMAIL=your-email@gmail.com
   ```

4. Edit `config.yaml` and set `email.enabled: true`

### 3. Customize Your Watchlist

Edit `config.yaml` to add/remove HKEX stocks:

```yaml
watchlist:
  - "0700.HK"  # Tencent
  - "0941.HK"  # China Mobile
  # Add more stocks here
```

## Usage

### Manual Run

```bash
python src/main.py
```

This will:
1. Scrape news from HKEXnews, Yahoo Finance, and Google News
2. Translate Chinese articles to English
3. Analyze sentiment
4. Generate an HTML report (saved locally or emailed)

### First Run Notes

- First run will download the FinBERT model (~450MB) - this is one-time
- Report will be saved as `report_YYYYMMDD.html` if email is disabled
- Open the HTML file in your browser to preview

### Schedule Daily Runs

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Daily at your preferred time (e.g., 8:00 AM)
4. Set action to "Start a program"
5. Program: `python`
6. Arguments: `C:\Users\lucas\Claude_tests\lucas_finance_analyst\scripts\run_daily.py`
7. Start in: `C:\Users\lucas\Claude_tests\lucas_finance_analyst`

#### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 8 AM)
0 8 * * * cd /path/to/lucas_finance_analyst && python3 scripts/run_daily.py
```

## Troubleshooting

### "No module named X"
```bash
pip install -r requirements.txt
```

### Translation not working
The system uses `deep-translator` by default. If it fails, it will use a simple keyword-based fallback.

### FinBERT model download fails
Check your internet connection. The model is downloaded from Hugging Face on first run.

### Email not sending
- Verify Gmail App Password is correct (not your regular password)
- Check that 2FA is enabled on your Google account
- Ensure SMTP settings in config.yaml are correct

### No news found
- Check your internet connection
- Verify stock tickers in watchlist are correct (format: "0700.HK")
- Try increasing `days_lookback` in config.yaml

## Configuration Options

See `config.yaml` for all available options:

- **watchlist**: List of HKEX tickers to monitor
- **scraping.days_lookback**: How many days of historical news to fetch (default: 1)
- **scraping.max_articles_per_source**: Limit per source (default: 50)
- **report.max_items**: Number of articles in daily report (default: 15)
- **filtering.keywords_important**: Keywords that boost relevance score
- **filtering.keywords_exclude**: Keywords to filter out

## Data Storage

- Database: `data/news.db` (SQLite)
- Stores all articles, translations, and sentiment scores
- Tracks which articles have been reported to avoid duplicates

## Free Tier Limits

This system uses 100% free resources:

- ✅ HKEXnews: Unlimited scraping
- ✅ Yahoo Finance (yfinance): Unlimited (unofficial API)
- ✅ Google News RSS: Unlimited
- ✅ Translation: Unlimited (deep-translator)
- ✅ FinBERT: Unlimited (local model)
- ✅ Email: Unlimited (Gmail SMTP)

## Next Steps

After setup, consider:

1. **Test Run**: Run manually first to verify everything works
2. **Review Report**: Check the generated HTML report
3. **Tune Filters**: Adjust keywords in config.yaml based on results
4. **Schedule**: Set up daily automated runs
5. **Expand**: Add more stocks to your watchlist

## Support

For issues or questions:
- Check the main README.md
- Review config.yaml comments
- Ensure all dependencies are installed

Enjoy your daily financial news digest! 📊
