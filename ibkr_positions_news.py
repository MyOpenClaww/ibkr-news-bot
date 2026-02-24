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
import csv
import io
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
    
    # Parse response - could be XML or query response
    response_text = response.text
    
    # Check if it's a query response with reference code
    if '<ReferenceCode>' in response_text:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response_text)
        ref_code_elem = root.find('.//ReferenceCode')
        
        if ref_code_elem is None or not ref_code_elem.text:
            print(f"Could not find reference code in response")
            return None, None
        
        reference_code = ref_code_elem.text
        
        # Step 2: Fetch the report using reference code
        # Use the URL from the response or default
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
        
        return parse_csv(response.text)
    
    # If it's already CSV data, parse it directly
    return parse_csv(response_text)


def parse_csv(csv_string):
    """Parse positions from Flex Web Service CSV response"""
    try:
        # Read CSV data
        reader = csv.DictReader(io.StringIO(csv_string))
        
        positions = []
        
        for row in reader:
            # Skip rows that are headers or empty
            if row.get('Symbol') in [None, ''] or row.get('Symbol') == 'Symbol':
                continue
            
            symbol = row.get('Symbol', '')
            if not symbol:
                continue
            
            # Parse numeric values
            try:
                quantity = float(row.get('Quantity', 0))
                # Skip closed positions
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
        print(f"Response was: {csv_string[:500]}")
        return [], {}


def format_message(positions, account_info):
    """Format the positions as a message"""
    message = "📊 **IBKR Daily Positions Update**\n"
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
    
    for pos in positions:
        symbol = pos.get('symbol', 'Unknown')
        description = pos.get('description', '')
        quantity = pos.get('quantity', 0)
        position_value = pos.get('position_value', 0)
        pnl = pos.get('pnl', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        message += f"\n{emoji} **{symbol}**\n"
        if description:
            message += f"   {description}\n"
        message += f"   Shares: {quantity}\n"
        message += f"   Value: ${position_value:,.2f}\n"
        message += f"   P&L: ${pnl:,.2f}\n"
    
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
