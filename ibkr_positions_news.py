#!/usr/bin/env python3
"""
IBKR Daily Positions News Script
Fetches open positions from Interactive Brokers using Flex Web Service
Posts to Discord with latest news for each ticker
"""

import os
import sys
import requests
import csv
import io
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
IBKR_FLEX_TOKEN = os.getenv('IBKR_FLEX_TOKEN', '')
IBKR_QUERY_ID = os.getenv('IBKR_QUERY_ID', '')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')

# Flex Web Service endpoints
FLEX_BASE_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"


def get_positions():
    """Fetch open positions from IBKR using Flex Web Service"""
    
    request_url = f"{FLEX_BASE_URL}/SendRequest"
    params = {
        't': IBKR_FLEX_TOKEN,
        'q': IBKR_QUERY_ID,
        'v': 3
    }
    
    response = requests.get(request_url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"Error sending request: {response.status_code}")
        return None, None
    
    response_text = response.text
    
    if '<ReferenceCode>' in response_text:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response_text)
        ref_code_elem = root.find('.//ReferenceCode')
        
        if ref_code_elem is None or not ref_code_elem.text:
            return None, None
        
        reference_code = ref_code_elem.text
        
        statement_url = f"{FLEX_BASE_URL}/GetStatement"
        params = {
            't': IBKR_FLEX_TOKEN,
            'q': reference_code,
            'v': 3
        }
        
        response = requests.get(statement_url, params=params, timeout=30)
        
        if response.status_code != 200:
            return None, None
        
        return parse_csv(response.text)
    
    return parse_csv(response_text)


def parse_csv(csv_string):
    """Parse positions from Flex Web Service CSV response"""
    try:
        reader = csv.DictReader(io.StringIO(csv_string))
        
        positions = []
        
        for row in reader:
            if row.get('Symbol') in [None, ''] or row.get('Symbol') == 'Symbol':
                continue
            
            symbol = row.get('Symbol', '')
            if not symbol:
                continue
            
            try:
                quantity = float(row.get('Quantity', 0))
                if quantity == 0:
                    continue
            except:
                quantity = 0
            
            try:
                position_value = float(row.get('PositionValue', 0))
            except:
                position_value = 0
            
            try:
                pnl = float(row.get('FifoPnlUnrealized', 0))
            except:
                pnl = 0
            
            position = {
                'symbol': symbol,
                'description': row.get('Description', ''),
                'quantity': quantity,
                'position_value': position_value,
                'pnl': pnl,
            }
            
            positions.append(position)
        
        return positions, {}
        
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return [], {}


def get_news_for_ticker(ticker):
    """Search for latest news for a ticker using web search"""
    try:
        # Use a simple web search - in production, use a proper news API
        search_url = f"https://ddg-api.vercel.app/search?q={ticker}+stock+news"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(search_url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', [])
            
            if results:
                # Get top 1-2 news items
                news_items = []
                for item in results[:2]:
                    title = item.get('title', '')[:80]
                    href = item.get('href', '')
                    if title and href:
                        news_items.append(f"• {title}\n  {href}")
                return news_items
        
        return []
        
    except Exception as e:
        print(f"Error getting news for {ticker}: {e}")
        return []


def format_message(positions, news_dict):
    """Format the positions as a message"""
    message = "📊 **IBKR Daily Positions + News Update**\n"
    message += f"_{datetime.now().strftime('%Y-%m-%d %H:%M %Z')}_\n\n"
    
    if not positions:
        message += "No open positions found."
        return message
    
    # Calculate totals
    total_value = sum(p.get('position_value', 0) for p in positions)
    total_pnl = sum(p.get('pnl', 0) for p in positions)
    
    message += f"**Total Position Value:** ${total_value:,.2f}\n"
    emoji = "🟢" if total_pnl >= 0 else "🔴"
    message += f"{emoji} **Total Unrealized P&L:** ${total_pnl:,.2f}\n\n"
    
    message += "**Open Positions:**\n"
    
    # Sort by position value descending
    positions.sort(key=lambda x: x.get('position_value', 0), reverse=True)
    
    # Limit to top positions to keep message short
    top_positions = positions[:10]
    
    for pos in top_positions:
        symbol = pos.get('symbol', 'Unknown')
        description = pos.get('description', '')
        quantity = pos.get('quantity', 0)
        position_value = pos.get('position_value', 0)
        pnl = pos.get('pnl', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        message += f"\n{emoji} **{symbol}**\n"
        if description:
            message += f"   {description}\n"
        message += f"   Shares: {quantity} | Value: ${position_value:,.2f} | P&L: ${pnl:,.2f}\n"
        
        # Add news if available
        if symbol in news_dict and news_dict[symbol]:
            message += f"   📰 **Latest News:**\n"
            for news in news_dict[symbol]:
                message += f"   {news}\n"
    
    if len(positions) > 10:
        message += f"\n_... and {len(positions) - 10} more positions_"
    
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
    print("IBKR Daily Positions + News")
    print("=" * 50)
    
    if not IBKR_FLEX_TOKEN or not IBKR_QUERY_ID:
        print("ERROR: Missing credentials in .env")
        sys.exit(1)
    
    print(f"Fetching positions...")
    
    try:
        positions, _ = get_positions()
        if positions is None:
            print("Failed to get positions")
            sys.exit(1)
        print(f"Found {len(positions)} positions")
    except Exception as e:
        print(f"Error: {e}")
        positions = []
    
    if not positions:
        send_discord("📊 **IBKR Daily Update**\nNo open positions found.")
        return
    
    # Get news for each ticker
    print("Fetching news for tickers...")
    news_dict = {}
    tickers = [p['symbol'] for p in positions[:10]]  # Top 10 by value
    
    for ticker in tickers:
        print(f"  Getting news for {ticker}...")
        news = get_news_for_ticker(ticker)
        news_dict[ticker] = news
    
    # Format and send message
    message = format_message(positions, news_dict)
    
    print("\n" + "=" * 50)
    print("MESSAGE OUTPUT:")
    print("=" * 50)
    print(message[:500] + "..." if len(message) > 500 else message)
    print("=" * 50)
    
    send_discord(message)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
