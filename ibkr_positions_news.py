#!/usr/bin/env python3
"""
IBKR Daily Positions News Script
Fetches open positions from Interactive Brokers and gets latest news for each ticker
Posts to Discord/Telegram

Usage:
    python ibkr_positions_news.py
"""

import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
IBKR_API_KEY = os.getenv('IBKR_API_KEY', '')
IBKR_ACCOUNT_ID = os.getenv('IBKR_ACCOUNT_ID', '')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')

# IBKR Client Portal API - use ibkr.cloud for production
# For local testing, use https://localhost:5000/v1/api
BASE_URL = "https://ibkr.cloud/v1/api"


def get_positions():
    """Fetch open positions from IBKR using API key authentication"""
    headers = {
        "Authorization": f"Bearer {IBKR_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get portfolio positions
    positions_resp = requests.get(
        f"{BASE_URL}/portfolio/{IBKR_ACCOUNT_ID}/positions",
        headers=headers,
        timeout=30
    )
    
    if positions_resp.status_code == 200:
        positions = positions_resp.json()
        # Filter for non-zero positions
        return [p for p in positions if float(p.get('position', 0)) != 0]
    else:
        print(f"Error getting positions: {positions_resp.status_code} - {positions_resp.text}")
        return []


def get_account_info():
    """Get account information"""
    headers = {
        "Authorization": f"Bearer {IBKR_API_KEY}",
        "Content-Type": "application/json"
    }
    
    resp = requests.get(f"{BASE_URL}/portfolio/{IBKR_ACCOUNT_ID}/summary", headers=headers, timeout=30)
    if resp.status_code == 200:
        return resp.json()
    return {}


def format_message(positions, account_info):
    """Format the positions as a message"""
    message = "📊 **IBKR Daily Positions Update**\n"
    message += f"_{datetime.now().strftime('%Y-%m-%d %H:%M %Z')}_\n\n"
    
    # Account summary
    if account_info:
        net_liquidation = float(account_info.get('NetLiquidation', 0))
        cash = float(account_info.get('CashBalance', 0))
        pnl = float(account_info.get('UnrealizedPnL', 0))
        
        message += f"**Account Value:** ${net_liquidation:,.2f}\n"
        message += f"**Cash:** ${cash:,.2f}\n"
        emoji = "🟢" if pnl >= 0 else "🔴"
        message += f"{emoji} **Daily P&L:** ${pnl:,.2f}\n\n"
    
    if not positions:
        message += "No open positions found."
        return message
    
    message += "**Open Positions:**\n"
    
    for pos in positions:
        symbol = pos.get('symbol', 'Unknown')
        position = pos.get('position', 0)
        market_value = pos.get('marketValue', 0)
        cost_basis = pos.get('costBasis', 0)
        
        # Calculate P&L
        try:
            mkt = float(market_value) if market_value else 0
            cost = float(cost_basis) if cost_basis else 0
            pnl_val = mkt - cost
        except:
            pnl_val = 0
        
        emoji = "🟢" if pnl_val >= 0 else "🔴"
        
        message += f"\n{emoji} **{symbol}**\n"
        message += f"   Shares: {position}\n"
        message += f"   Value: ${market_value}\n"
        message += f"   P&L: ${pnl_val:,.2f}\n"
    
    return message


def send_discord(message):
    """Send message to Discord webhook"""
    if not DISCORD_WEBHOOK:
        print("No Discord webhook configured - skipping")
        return
    
    payload = {"content": message}
    resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    if resp.status_code == 204:
        print("Sent to Discord successfully")
    else:
        print(f"Failed to send to Discord: {resp.status_code}")


def main():
    print("=" * 50)
    print("IBKR Daily Positions News")
    print("=" * 50)
    
    # Check for required credentials
    if not IBKR_API_KEY:
        print("ERROR: IBKR_API_KEY not set in environment")
        print("Please create a .env file with your credentials")
        sys.exit(1)
    
    if not IBKR_ACCOUNT_ID:
        print("ERROR: IBKR_ACCOUNT_ID not set in environment")
        sys.exit(1)
    
    print(f"Fetching positions for account: {IBKR_ACCOUNT_ID}")
    
    # Fetch positions
    try:
        positions = get_positions()
        print(f"Found {len(positions)} positions")
    except Exception as e:
        print(f"Error fetching positions: {e}")
        positions = []
    
    # Get account info
    try:
        account_info = get_account_info()
    except Exception as e:
        print(f"Error fetching account info: {e}")
        account_info = {}
    
    # Format and send message
    message = format_message(positions, account_info)
    
    print("\n" + "=" * 50)
    print("MESSAGE OUTPUT:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    
    send_discord(message)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
