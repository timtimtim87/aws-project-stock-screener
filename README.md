# AWS Serverless Stock Screener

A serverless system that screens Russell 1000 stocks for contrarian value opportunities using drawdown analysis.

A written article about this project is available at [timtimtim87.github.io](https://timtimtim87.github.io).

## Overview

Collects daily price data for Russell 1000 stocks, calculates 180-day drawdowns, and surfaces the worst-performing stocks as potential buy candidates. A Telegram bot provides real-time access to the data.

## Architecture

- **AWS Lambda** - Data collection and Telegram bot handler
- **Amazon S3** - CSV data storage
- **AWS Parameter Store** - Credential storage
- **Telegram Bot** - Command interface
- **Polygon.io** - Market data feed
- **Alpaca Markets** - Portfolio tracking

## Cost

- S3: ~$0.30/month
- Lambda: ~$2-5/month
- Total: under $10/month

## Strategy

Buy signal: Russell 1000 stocks with the worst 180-day drawdowns.
Exit signal: When the top 5 positions average 100% unrealized gains.

## Setup

### Prerequisites

- AWS account with CLI configured
- AWS SAM CLI
- Alpaca Markets account
- Telegram bot token
- Polygon.io API key
- Python 3.12

### Deploy

```bash
git clone https://github.com/YOUR_USERNAME/aws-stock-screener.git
cd aws-stock-screener
pip install -r requirements.txt
sam build
sam deploy --guided
```

### Parameter Store

Store credentials at these paths before deploying:

```
/screener/polygon/api_key
/screener/alpaca/api_key
/screener/alpaca/secret_key
/screener/alpaca/base_url
/screener/telegram/bot_token
/screener/telegram/chat_id   (optional — restricts access to one user)
```

### Set Telegram Webhook

After deploying, run:

```bash
./deploy_telegram_bot.sh
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| /dashboard | Daily overview: account, portfolio, top candidates |
| /screen | Top 10 worst drawdown stocks |
| /portfolio | Current positions |
| /monitor | Profit target check |
| /account | Alpaca account balance |
| /stats | Data file status |
| /trigger | Manually invoke data collection |
| /download | Presigned S3 download links |

## Project Structure

```
aws-stock-screener/
├── src/
│   ├── daily_collector/    # Lambda: daily data collection
│   └── telegram_bot/       # Lambda: Telegram webhook handler
├── analysis/               # Local analysis notebooks
├── docs/                   # Additional documentation
├── template.yaml           # SAM deployment template
├── build_historical_data.py
└── russell_1000_symbols.py
```

## Data Files (S3)

| File | Description |
|------|-------------|
| russell_1000_drawdown_results.csv | Full daily drawdown data |
| daily_top_candidates.csv | Top 10 candidates per day |
| portfolio_snapshots.csv | Daily portfolio positions |

## Security

- Credentials stored in AWS Parameter Store, not in code
- IAM roles scoped to required resources only
- Telegram webhook restricted to authorized chat ID (optional)

## Disclaimer

For educational and informational purposes only. Not financial advice.

## License

MIT — see [LICENSE](LICENSE).
