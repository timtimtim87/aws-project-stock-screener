# AWS Stock Screener

A serverless stock screening system built on AWS with a Telegram bot interface.

For a written article about this project, visit [timtimtim87.github.io](https://timtimtim87.github.io).

## What it does

Runs on a daily schedule, pulling market data for Russell 1000 stocks, calculating screening metrics, and ranking candidates. Results are stored in S3 and accessible in real time via a Telegram bot that handles commands for screening results, portfolio tracking, and data exports.

## Stack

**Application**
- Python 3.12
- AWS Lambda — two functions: daily data collector and Telegram webhook handler
- Polygon.io — market data feed
- Alpaca Markets — portfolio data

**Infrastructure**
- S3 — CSV data storage
- API Gateway — Telegram webhook endpoint
- CloudWatch — scheduling and logs
- AWS Parameter Store — secrets and credentials
- AWS SAM — infrastructure as code and deployment

## Architecture notes

- Two-Lambda design: one scheduled function for data collection, one event-driven function for the bot
- Data layer is plain CSV on S3 — no database; keeps cost under $10/month
- Credentials kept out of code entirely via Parameter Store; IAM roles scoped to required resources
- Telegram webhook restricted to a single authorised chat ID

## Project structure

```
├── template.yaml                 # SAM template — all AWS resources
├── src/
│   ├── daily_collector/          # Scheduled Lambda: data collection and ranking
│   └── telegram_bot/             # Webhook Lambda: Telegram command handler
├── build_historical_data.py      # One-off script to backfill historical data
└── russell_1000_symbols.py       # Russell 1000 ticker list
```
