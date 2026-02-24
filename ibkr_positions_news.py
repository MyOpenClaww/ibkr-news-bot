#!/usr/bin/env python3
"""
IBKR Daily Positions News Script
Fetches open positions from Interactive Brokers using Flex Web Service
Posts to Discord

Usage:
    python ibkr_positions_news.py
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
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
    
    # Step 1: Send request to generate report
    request_url = f"{FLEX_BASE_URL}/SendRequest"
    params = {
        't': IBKR_FLEX_TOKEN,
        'q': IBKR_QUERY_ID,
        'v': 3
    }
    
    response = requests.get(request_url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"Error sending request: {response.status_code} - {response.text}")
        return None, None
    
    # Parse XML response
    root = ET.fromstring(response.text)
    
    # Get reference code
    ref_code_elem = root.find('.//{http://www.iborkers.com/TWS}referenceCode')
    if ref_code_elem is None:
        # Try without namespace
        ref_code_elem = root.find('.//referenceCode')
    
    if ref_code_elem is None or not ref_code_elem.text:
        print(f"Could not find reference code in response: {response.text}")
        return None, None
    
    reference_code = ref_code_elem.text
    
    # Step 2: Fetch the report using reference code
    statement_url = f"{FLEX_BASE_URL}/GetStatement"
    params = {
        't': IBKR_FLEX_TOKEN,
        'q': reference_code,
        'v': 3
    }
    
    response = requests.get(statement_url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"Error getting statement: {response.status_code}")
        return None, None
    
    # Parse positions from response
    return parse_positions(response.text)


def parse_positions(xml_string):
    """Parse positions from Flex Web Service XML response"""
    try:
        root = ET.fromstring(xml_string)
        
        positions = []
        account_value = {}
        
        # Find AccountInfo section for NetLiquidation
        account_info = root.find('.//AccountInformation')
        if account_info is not None:
            account_value['NetLiquidation'] = account_info.get('netLiquidation', '0')
            account_value['CashBalance'] = account_info.get('cashBalance', '0')
            account_value['DailyPnL'] = account_info.get('dailyPnL', '0')
        
        # Find all position entries
        for pos in root.findall('.//Position'):
            symbol = pos.get('symbol', '')
            if not symbol:
                continue
                
            position = {
                'symbol': symbol,
                'position': pos.get('quantity', '0'),
                'marketValue': pos.get('marketValue', '0'),
                'costBasis': pos.get('costBasis', '0'),
                'openPnL': pos.get('openPnL', '0'),
            }
            
            # Calculate P&L
            try:
                mkt = float(position['marketValue']) if position['marketValue'] else 0
                cost = float(position['costBasis']) if position['costBasis'] else 0
                position['pnl'] = mkt - cost
            except:
                position['pnl'] = 0
            
            positions.append(position)
        
        return positions, account_value
        
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        print(f"Response was: {xml_string[:500]}")
        return [], {}


def format_message(positions, account_info):
    """Format the positions as a message"""
    message = "📊 **IBKR Daily Positions Update**\n"
    message += f"_{datetime.now().strftime('%Y-%m-%d %H:%M %Z')}_\n\n"
    
    # Account summary
    if account_info:
        net_liq = float(account_info.get('NetLiquidation', 0))
        cash = float(account_info.get('CashBalance', 0))
        daily_pnl = float(account_info.get('DailyPnL', 0))
        
        message += f"**Account Value:** ${net_liq:,.2f}\n"
        message += f"**Cash:** ${cash:,.2f}\n"
        emoji = "🟢" if daily_pnl >= 0 else "🔴"
        message += f"{emoji} **Daily P&L:** ${daily_pnl:,.2f}\n\n"
    
    if not positions:
        message += "No open positions found."
        return message
    
    message += "**Open Positions:**\n"
    
    # Sort by market value descending
    positions.sort(key=lambda x: float(x.get('marketValue', 0)), reverse=True)
    
    for pos in positions:
        symbol = pos.get('symbol', 'Unknown')
        position = pos.get('position', 0)
        market_value = pos.get('marketValue', 0)
        pnl_val = pos.get('pnl', 0)
        
        emoji = "🟢" if pnl_val >= 0 else "🔴"
        
        message += f"\n{emoji} **{symbol}**\n"
        message += f"   Shares: {position}\n"
        message += f"   Value: ${float(market_value):,.2f}\n"
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
        print(f"Failed to send to Discord: {resp.status_code} - {resp.text}")


def main():
    print("=" * 50)
    print("IBKR Daily Positions News (Flex Web Service)")
    print("=" * 50)
    
    # Check for required credentials
    if not IBKR_FLEX_TOKEN:
        print("ERROR: IBKR_FLEX_TOKEN not set in environment")
        print("Please create a .env file with your credentials")
        print("\nTo get Flex Token:")
        print("1. Go to IBKR Account Management")
        print("2. Reports → Flex Queries → Flex Web Service")
        print("3. Enable Flex Web Service and copy token")
        sys.exit(1)
    
    if not IBKR_QUERY_ID:
        print("ERROR: IBKR_QUERY_ID not set in environment")
        print("Please create a .env file with your credentials")
        sys.exit(1)
    
    print(f"Fetching positions...")
    
    # Fetch positions
    try:
        positions, account_info = get_positions()
        if positions is None:
            print("Failed to get positions")
            sys.exit(1)
        print(f"Found {len(positions)} positions")
    except Exception as e:
        print(f"Error fetching positions: {e}")
        positions = []
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
