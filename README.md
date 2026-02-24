# IBKR News Bot

Daily automation script that fetches your Interactive Brokers positions and posts updates to Discord.

## Features

- ✅ Fetches open positions from IBKR
- ✅ Shows P&L for each position
- ✅ Posts daily updates to Discord
- ✅ Uses API key (not username/password)

## Setup

### 1. Get IBKR API Key

1. Log into [Interactive Brokers](https://www.interactivebrokers.com)
2. Go to Account Settings → API Settings
3. Create API Key
4. Copy the API Key and Account ID

### 2. Get Discord Webhook

1. Discord Server → Server Settings → Integrations
2. Create Webhook
3. Choose #alerts channel
4. Copy the Webhook URL

### 3. Configure

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 4. Install & Test

```bash
# Install dependencies
pip install -r requirements.txt

# Test the script
python ibkr_positions_news.py
```

## Usage

```bash
python ibkr_positions_news.py
```

## Automation

### Option A: Cron (Local)

```bash
# Add to crontab
crontab -e

# Add this line for daily 8am:
0 8 * * * /path/to/python /path/to/ibkr_positions_news.py >> /path/to/log.txt 2>&1
```

### Option B: Cloudflare Worker (Recommended)

Deploy to Cloudflare Workers for serverless execution.

## Files

```
ibkr-news-bot/
├── ibkr_positions_news.py   # Main script
├── requirements.txt          # Python dependencies
├── .env.example             # Config template
└── README.md                # This file
```

## Support

- IBKR API Docs: https://www.interactivebrokers.com/en/trading/ib-api.php
