# IBKR News Bot

Daily automation script that fetches your Interactive Brokers positions and posts updates to Discord using Flex Web Service.

## Features

- ✅ Fetches open positions from IBKR
- ✅ Shows P&L for each position
- ✅ Posts daily updates to Discord
- ✅ Uses Flex Web Service (no local software needed!)
- ✅ Secure token-based authentication

## Setup

### 1. Get IBKR Flex Web Service Token

1. Log into [IBKR Account Management](https://interactivebrokers.com)
2. Go to **Reports** → **Flex Queries**
3. Click **Flex Web Service** (or "Flex Web Configuration")
4. Toggle **Enable Flex Web Service** to ON
5. **Copy the Token** shown (starts with `eyJ...`)

### 2. Get Flex Query ID

1. Still in **Reports** → **Flex Queries**
2. Click **Create a Flex Query**
3. Choose **Positions** or **Account Information**
4. Name it (e.g., "Daily Positions")
5. Save and **copy the Query ID** (a number like `12345`)

### 3. Get Discord Webhook

1. Discord Server → **Server Settings** → **Integrations**
2. Create **Webhook**
3. Choose **#alerts** channel
4. Copy the Webhook URL

### 4. Configure

```bash
# Clone the repo
git clone https://github.com/MyOpenClaww/ibkr-news-bot.git
cd ibkr-news-bot

# Copy the example config
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Fill in:
- `IBKR_FLEX_TOKEN` = your Flex token
- `IBKR_QUERY_ID` = your Query ID
- `DISCORD_WEBHOOK` = your Discord webhook URL

### 5. Test

```bash
# Install dependencies
pip install -r requirements.txt

# Test the script
python ibkr_positions_news.py
```

## Automation

### Option A: Cron (Local - Recommended for now)

```bash
# Add to crontab
crontab -e

# Add this line for daily 8am Melbourne time:
0 8 * * * /usr/bin/python3 /path/to/ibkr_positions_news.py >> /path/to/log.txt 2>&1
```

### Option B: GitHub Actions (Cloud)

Can be set up to run automatically without your machine.

## Files

```
ibkr-news-bot/
├── ibkr_positions_news.py   # Main script
├── requirements.txt        # Python dependencies
├── .env.example          # Config template
├── .gitignore
└── README.md
```

## Support

- IBKR Flex Web Service: https://www.ibkrguides.com/complianceportal/complianceportal/flexweb.htm
- IBKR API Docs: https://www.interactivebrokers.com/en/trading/ib-api.php
