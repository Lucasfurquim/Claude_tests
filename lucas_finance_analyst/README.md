# Lucas II: Finance Analyst

A free, automated financial news analysis tool focused on HKEX-listed companies.

## Features

### Phase 1: News Flow Screener (Current)
- Daily scraping of HKEX announcements
- Multi-source news aggregation (HKEXnews, Yahoo Finance, Google News)
- Automatic Chinese-to-English translation
- AI-powered sentiment analysis
- Smart filtering and ranking
- Daily email reports

## Tech Stack

- Python 3.10+
- Beautiful Soup 4 (web scraping)
- yfinance (Yahoo Finance data)
- googletrans/argostranslate (translation)
- FinBERT (financial sentiment analysis)
- SnowNLP (Chinese sentiment analysis)
- SQLite (local database)
- 100% Free - No paid APIs

## Installation

```bash
cd lucas_finance_analyst
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to set:
- Target HKEX stock codes
- Email settings
- Scraping schedule
- Filter preferences

## Usage

```bash
# Run manual news scan
python src/main.py

# Set up daily automated run
python scripts/run_daily.py
```

## Project Structure

```
lucas_finance_analyst/
├── src/
│   ├── scrapers/        # News scrapers
│   ├── translation/     # Translation engines
│   ├── sentiment/       # Sentiment analysis
│   ├── database/        # SQLite management
│   ├── reports/         # Email report generation
│   └── main.py          # Main orchestrator
├── data/                # SQLite database
├── tests/               # Unit tests
└── scripts/             # Automation scripts
```

## Future Modules

- Company Research Engine
- Whale & Insider Tracker
- AI Investment Recommendations

## License

Personal use only
